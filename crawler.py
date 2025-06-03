from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from urllib.parse import urlencode
import hashlib
import pymysql
import datetime
import asyncio
import urllib
import re

import requests
import json
from collections import namedtuple
import copy
import numpy as np
import pandas as pd
import datetime
import time
import os
import sys
from dotenv import load_dotenv
import logging
import uuid
import jwt


load_dotenv()
UPBIT_ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
UPBIT_SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")
ip_NAT_mariadb = os.getenv("ip_NAT_mariadb")
ID_mariadb = os.getenv("ID_mariadb")
PW_mariadb = os.getenv("PW_mariadb")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler("upbit.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

local_environment = True
users = {}

class Invest:
    assets = {}
    portfolio = {}
    key = ""
    allowedDeviation = {}
    record = {}
    value = pd.DataFrame()
    automation = False
    rebalanceTask = {}
    messageStack = []
    def __init__(self):
        self.portfolio = {"BTC": 0.3, "ETH": 0.3, "XRP": 0.2}
        self.key = "KRW"
        self.assets[self.key] = {"quantity": 0, "price": 1}
        self.allowedDeviation = {"BTC": (0.98, 1.02), "ETH": (0.98, 1.02), "XRP": (0.98, 1.02)}
        self.queueLock = asyncio.Lock()
        for item in self.portfolio:
            self.assets[item] = {"quantity": 0, "price": 0}
            self.record[f"{self.key}-{item}"] = pd.DataFrame({
                "datetime": pd.Series(dtype='datetime64[ns]'),
                "price": pd.Series(dtype='float'),
                "trade_quantity": pd.Series(dtype='float'),
                "quantity": pd.Series(dtype='float'),
                })
            self.record[f"{self.key}-{item}"].set_index("datetime", inplace = True)
        self.record[self.key] = pd.DataFrame({
            "datetime": pd.Series(dtype='datetime64[ns]'),
            "price": pd.Series(dtype='float'),
            "trade_quantity": pd.Series(dtype='float'),
            "quantity": pd.Series(dtype='float'),
            })
        self.record[self.key].set_index("datetime", inplace = True)
        self.value = pd.DataFrame({
            "datetime": pd.Series(dtype = 'datetime64[ns]'),
            })
        self.value.set_index("datetime", inplace = True)

    async def setCondition(self, key = None, initial=None, portfolio=None, allowedDeviation=None):
        if key != self.key and key is not None:
            async with self.queueLock:
                del self.record[self.key]
                self.key = key
                self.messageStack.append("기본통화: " + self.key)
                self.record[self.key] = pd.DataFrame({
                    "datetime": pd.Series(dtype='datetime64[ns]'),
                    "price": pd.Series(dtype='float'),
                    "trade_quantity": pd.Series(dtype='float'),
                    "quantity": pd.Series(dtype='float'),
                    })
                self.record[self.key].set_index("datetime", inplace = True)
        async with self.queueLock:
            for item in self.portfolio:
                self.assets[item] = {"quantity": 0, "price": 0}
        if initial:
            async with self.queueLock:
                self.assets[self.key] = {"quantity": initial, "price": 1}
                self.messageStack.append("초기값: " + numberFormat(self.assets[self.key]["quantity"]))
        if portfolio:
            async with self.queueLock:
                self.portfolio = portfolio
                self.messageStack.append("Portfolio: " + str(self.portfolio))
        if allowedDeviation:
            async with self.queueLock:
                self.allowedDeviation = allowedDeviation
                self.messageStack.append("Allowed deviation: " + str(self.allowedDeviation))
        self.value = pd.DataFrame({
            "datetime": pd.Series(dtype = 'datetime64[ns]'),
            })
        self.value.set_index("datetime", inplace = True)

    async def load(self, xlsx_path):
        json = {}
        async with self.queueLock:
            self.messageStack.append("📂 Loading")
            if os.path.exists(xlsx_path):
                df_existing = pd.read_excel(xlsx_path, sheet_name = None)
                self.record = df_existing
                for item in self.record:
                    self.record[item].set_index("datetime", inplace = True)
                    self.record[item]["quantity"] = self.record[item]["quantity"].fillna(0)
                    self.record[item]["trade_quantity"] = self.record[item]["trade_quantity"].fillna(0)
                for item, df in self.record.items():
                    df["norm_y"] = df["price"] / df.loc[df.index[-1], "price"]
                    df_clean = df.reset_index()
                    df_clean["datetime"] = df_clean["datetime"].dt.strftime('%Y-%m-%dT%H:%M:%S')
                    df_clean.rename(columns = {"datetime": "x"}, inplace=True)
                    df_clean.rename(columns = {"price": "y"}, inplace=True)
                    json[item] = df_clean.to_dict(orient="records")
                    print(json)
                self.messageStack.append("✅ Done")
        return json

    async def save(self, xlsx_path):
        with pd.ExcelWriter(xlsx_path, engine = "openpyxl") as writer:
            record = {}
            async with self.queueLock:
                record = self.record
                self.messageStack.append("💾 Saving")
            if record:
                for item, df in record.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name = item, index=True)
                async with self.queueLock:
                    self.messageStack.append("✅ Done")
            else:
                async with self.queueLock:
                    self.messageStack.append("No data")
                pd.DataFrame({"message": ["No data"]}).to_excel(writer, sheet_name="Empty", index=False)

    # assets의 가치를 반환
    def valueSum(self):
        print(self.assets)
        sum = 0
        sum += float(self.assets[self.key]["quantity"]) * self.assets[self.key]["price"]
        for item in self.portfolio:
            sum += float(self.assets[item]["quantity"]) * self.assets[item]["price"] 
        return sum

    async def getOhlcv(self, start_dt, end_dt):
        key = ""
        portfolio = {}
        record = {}
        async with self.queueLock:
            self.messageStack.append("📈 OHLCV 수집 시작")
            key = self.key
            portfolio = self.portfolio
            record = self.record
        # 60분단위로 필터링하는 코드가 필요
        dates = pd.date_range(start_dt, end_dt, freq = "60min")[::-1]
        for item in portfolio:
            for date in dates:
                if date not in record[f"{key}-{item}"].index:
                    await self.queueLock.acquire()
                    print("item: " + item + " date: " + str(date) + " 값을 가져옵니다.")
                    self.messageStack.append("item: " + item + " date: " + str(date) + "값을 가져옵니다.")
                    market = f"{key}-{item}"
                    url = "https://api.upbit.com/v1/candles/minutes/60"
                    headers = {"Accept": "application/json"}
                    params = {
                            "market": market,
                            "to": (date+datetime.timedelta(minutes=60)).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                            "count": 200
                            }
                    response = requests.get(url, headers=headers, params=params)
                    if response.status_code != 200:
                        print(f"Error: {response.status_code} - {response.text}")
                        await self.queueLock.release()
                        break

                    data = response.json()
                    if not data:
                        await self.queueLock.release()
                        break

                    df = pd.DataFrame(data)
                    df['datetime'] = pd.to_datetime(df['candle_date_time_kst'])
                    df["price"] = df["trade_price"]
                    df["trade_volume"] = df["candle_acc_trade_volume"]
                    df.set_index('datetime', inplace = True)
                    df = df[["price", "trade_volume"]]
                    if df.index.max() != date:
                        self.record[f"{key}-{item}"].loc[date] = df.loc[df.index.max()]
                        self.record[f"{key}-{item}"] = self.record[f"{key}-{item}"].sort_index()
                    else:
                        self.record[f"{key}-{item}"] = pd.concat([self.record[f"{key}-{item}"], df]).sort_index()
                        self.record[f"{key}-{item}"] = self.record[f"{key}-{item}"][~self.record[f"{key}-{item}"].index.duplicated(keep='last')].sort_index() 
                    self.queueLock.release()
                    await asyncio.sleep(0.1)
        async with self.queueLock:
            for date in dates:
                self.record[key].loc[date, "price"] = 1
            self.messageStack.append("✅ OHLCV 수집 완료")
        

    async def calculateBand(self):
        async with self.queueLock:
            for item in self.portfolio:
                ma20 = self.record[f"{self.key}-{item}"]['price'].rolling(480, min_periods=1).mean()
                stddev20 = self.record[f"{self.key}-{item}"]['price'].rolling(480, min_periods=1).std()
                self.record[f"{self.key}-{item}"]['upper_band'] = ma20 + 2 * stddev20
                self.record[f"{self.key}-{item}"]['lower_band'] = ma20 - 2 * stddev20
                self.record[f"{self.key}-{item}"] = self.record[f"{self.key}-{item}"].dropna(subset=["upper_band"])
                self.record[f"{self.key}-{item}"] = self.record[f"{self.key}-{item}"].dropna(subset=["lower_band"])

    async def rebalanceLoop(self):
        async with self.queueLock:
            automation = self.automation
            portfolio = self.portfolio
            key = self.key
        while automation:
            async with self.queueLock:
                self.messageStack.append("Rebalancing " + str(datetime.datetime.now()))
            await self.cancelAllOrder()
            # portfolio의 모든 price를 가져온다.
            payload = {'access_key': UPBIT_ACCESS_KEY, 'nonce': str(uuid.uuid4())}
            jwt_token = jwt.encode(payload, UPBIT_SECRET_KEY, algorithm='HS256')
            url="https://api.upbit.com/v1/ticker"
            params = {"markets": ",".join(f"{key}-{m}" for m in portfolio)}
            res = requests.get(url, params = params)
            res.raise_for_status()
            prices = {item["market"].split("-")[1]: item["trade_price"] for item in res.json()}
            # 현재 계정의 quantity를 불러온다.
            url = "https://api.upbit.com/v1/accounts"
            headers = {"Authorization": f"Bearer {jwt_token}"}
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            accounts = res.json()
            quantities = {item["currency"]: float(item["balance"]) for item in accounts}
            print("3")
            async with self.queueLock:
                # KRW일 때와 USDT일 때 이렇게 나눠야 될까? 의문 굳이 안나눠도 될 것 같다.
                if key != "KRW":
                    self.assets["KRW"] = {"quantity": quantities.get("KRW", 0), "price": 1}
                    self.messageStack.append("KRW: {quantity: " + f"{self.assets['KRW']['quantity']:,.0f}" + ", price: " + f"{self.assets['KRW']['price']:,.0f}" + "}")
                self.assets[self.key] = {"quantity": quantities.get(key, 0), "price": 1}
                self.messageStack.append(key + ": {quantity: " + f"{self.assets[self.key]['quantity']:,.0f}" + ", price: " + f"{self.assets[self.key]['price']:,.0f}" + "}")
                for item in portfolio:
                    self.assets[item] = {"quantity": quantities.get(item, 0), "price": prices.get(item, 0)}
                    self.messageStack.append(item + ": {quantity: " + numberFormat(self.assets[item]["quantity"]) + ", price: " + numberFormat(self.assets[item]["price"]) + "}")
                
                for item in portfolio:
                    price = adjustPrice(self.assets[item]["price"])
                    quantity = self.assets[item]["quantity"]
                    valueSum = self.valueSum()
                    if price * quantity < valueSum * portfolio[item] * self.allowedDeviation[item][0]:
                        #buy
                        quantity = round((valueSum * portfolio[item] - price * quantity)/price, 6)
                        self.messageStack.append(item + "을 " + numberFormat(price) + "에 " + numberFormat(quantity) + "개 구매를 주문할 예정.")
                        #buyOrder(self.key, item, quantity, price)
                    elif valueSum * portfolio[item] * self.allowedDeviation[item][1] < price * quantity:
                        #sell
                        quantity = round((price * quantity - valueSum * portfolio[item])/price, 6)
                        self.messageStack.append(item + "을 " + numberFormat(price) + "에 " + numberFormat(quantity) + "개 판매를 주문할 예정.")
                        #sellOrder(self.key, item, quantity, price)
                    else:
                        #buy
                        buy_price = adjustPrice(valueSum * portfolio[item] * self.allowedDeviation[item][0]/quantity)
                        buy_quantity = round((1 - self.allowedDeviation[item][0]) * (1 - portfolio[item]) * quantity / self.allowedDeviation[item][0], 6)
                        self.messageStack.append(item + "을 " + numberFormat(buy_price) + "에 " + numberFormat(buy_quantity) + "개 구매를 주문할 예정.")
                        #buyOrder(self.key, item, buy_quantity, buy_price)
                        #sell
                        sell_price = adjustPrice(valueSum * portfolio[item] * self.allowedDeviation[item][1]/quantity)
                        sell_quantity = round((self.allowedDeviation[item][1] - 1)*(1 - portfolio[item]) * quantity / self.allowedDeviation[item][1], 6)
                        self.messageStack.append(item + "을 " + numberFormat(sell_price) + "에 " + numberFormat(sell_quantity) + "개 판매를 주문할 예정.")
                        #sellOrder(self.key, item, sell_quantity, sell_price)

            await asyncio.sleep(600)
            async with self.queueLock:
                automation = self.automation
            
    async def rebalance(self, date_dt):
        async with self.queueLock:
            for item in self.portfolio:
                self.assets[item]["price"] = self.record[f"{self.key}-{item}"].loc[date_dt, "price"]
            for item in self.portfolio:
                quantity = self.assets[item]["quantity"]
                price = self.assets[item]["price"]
                valueSum = self.valueSum()
                if price * quantity < valueSum * self.portfolio[item] * self.allowedDeviation[item][0]:
                    # buy
                    trade_quantity = round((valueSum * self.portfolio[item] - price * quantity)/price, 6)
                    self.assets[item]["quantity"] += trade_quantity
                    self.assets[self.key]["quantity"] -= trade_quantity * price
                    self.record[f"{self.key}-{item}"].loc[date_dt, "trade_quantity"] = trade_quantity
                    self.record[f"{self.key}-{item}"].loc[date_dt, "quantity"] = self.assets[item]["quantity"]
                    self.record[self.key].loc[date_dt, "trade_quantity"] = - trade_quantity * price
                    self.record[self.key].loc[date_dt, "quantity"] = self.assets[self.key]["quantity"]
                    self.messageStack.append("@" + str(date_dt) + ";" + item + ": [" + numberFormat(quantity) + "] [" + numberFormat(price) + "]")
                elif valueSum*self.portfolio[item] * self.allowedDeviation[item][1] < price * quantity:
                    # sell
                    trade_quantity = round((price * quantity - valueSum * self.portfolio[item])/price, 6)
                    self.assets[item]["quantity"] -= trade_quantity
                    self.assets[self.key]["quantity"] += trade_quantity * price
                    self.record[f"{self.key}-{item}"].loc[date_dt, "trade_quantity"] = -trade_quantity
                    self.record[f"{self.key}-{item}"].loc[date_dt, "quantity"] = self.assets[item]["quantity"]
                    self.record[self.key].loc[date_dt, "trade_quantity"] = trade_quantity * price
                    self.record[self.key].loc[date_dt, "quantity"] = self.assets[self.key]["quantity"]
                    self.messageStack.append("@" + str(date_dt) + ";" + item + ": [" + numberFormat(-quantity) + "] [" + numberFormat(price) + "]")
                else:
                    self.record[f"{self.key}-{item}"].loc[date_dt, "trade_quantity"] = 0
                    self.record[f"{self.key}-{item}"].loc[date_dt, "quantity"] = self.assets[item]["quantity"]
                    self.record[self.key].loc[date_dt, "trade_quantity"] = 0
                    self.record[self.key].loc[date_dt, "quantity"] = self.assets[self.key]["quantity"]
            self.value = self.value.sort_index()
            self.value.loc[date_dt, self.key] = self.valueSum()

    async def rebalance_bolinger(self, date_dt):
        async with self.queueLock:
            for item in self.portfolio:
                self.assets[item]["price"] = self.record[f"{self.key}-{item}"].loc[date_dt, "price"]
                self.assets[item]["lower_band"] = self.record[f"{self.key}-{item}"].loc[date_dt, "lower_band"]
                self.assets[item]["upper_band"] = self.record[f"{self.key}-{item}"].loc[date_dt, "upper_band"]
            for item in self.portfolio:
                quantity = self.assets[item]["quantity"]
                price = self.assets[item]["price"]
                upper = self.assets[item]["upper_band"]
                lower = self.assets[item]["lower_band"]
                portfolio = self.portfolio[item] * (1+0.1*(2*price-upper-lower)/(upper-lower))
                valueSum = self.valueSum()
                if price * quantity < valueSum * portfolio * self.allowedDeviation[item][0]:
                    # buy
                    trade_quantity = round((valueSum * portfolio - price * quantity)/price, 6)
                    self.assets[item]["quantity"] += trade_quantity
                    self.assets[self.key]["quantity"] -= trade_quantity * price
                    self.record[f"{self.key}-{item}"].loc[date_dt, "trade_quantity"] = trade_quantity
                    self.record[f"{self.key}-{item}"].loc[date_dt, "quantity"] = self.assets[item]["quantity"]
                    self.record[self.key].loc[date_dt, "trade_quantity"] = -trade_quantity * price
                    self.record[self.key].loc[date_dt, "quantity"] = self.assets[self.key]["quantity"]
                    self.messageStack.append("@" + str(date_dt) + ";" + item + ": [" + numberFormat(quantity) + "] [" + numberFormat(price) + "]")
                elif valueSum * portfolio * self.allowedDeviation[item][1] < price * quantity:
                    # sell
                    trade_quantity = round((price * quantity - valueSum * portfolio)/price, 6)
                    self.assets[item]["quantity"] -= trade_quantity
                    self.assets[self.key]["quantity"] += trade_quantity * price
                    self.record[f"{self.key}-{item}"].loc[date_dt, "trade_quantity"] = -trade_quantity
                    self.record[f"{self.key}-{item}"].loc[date_dt, "quantity"] = self.assets[item]["quantity"]
                    self.record[self.key].loc[date_dt, "trade_quantity"] = trade_quantity * price
                    self.record[self.key].loc[date_dt, "quantity"] = self.assets[self.key]["quantity"]
                    self.messageStack.append("@" + str(date_dt) + ";" + item + ": [" + numberFormat(-quantity) + "] [" + numberFormat(price) + "]")
                else:
                    self.record[f"{self.key}-{item}"].loc[date_dt, "trade_quantity"] = 0
                    self.record[f"{self.key}-{item}"].loc[date_dt, "quantity"] = self.assets[item]["quantity"]
                    self.record[self.key].loc[date_dt, "trade_quantity"] = 0
                    self.record[self.key].loc[date_dt, "quantity"] = self.assets[self.key]["quantity"]
            self.value = self.value.sort_index()
            self.value.loc[date_dt, self.key] = self.valueSum()
    
    async def status(self):
        async with self.queueLock:
            for item in self.assets:
                if item != "KRW":
                    quantity = self.assets[item]["quantity"]
                    price = self.assets[item]["price"]
                    value = quantity * price
                    ratio = price / self.valueSum()
                    logger.info(item  + ": " + numberFormat(quantity) + "\t" + numberFormat(price) + "\t" + numberFormat(value) + "\t" + numberFormat(ratio))
                    self.messageStack.append(item + ": " + numberFormat(quantity) + "\t" + numberFormat(price) + "\t" + numberFormat(value) + "\t" + numberFormat(ratio))
                else:
                    logger.info(item + ": " + str(self.assets[item]["quantity"]))
                    self.messageStack.append(item + ": " + numberFormat(self.assets[item]["quantity"]))
            print("Total: " + str(self.valueSum()))
    async def result(self, start_dt, end_dt):
        async with self.queueLock:
            initial_value = 0
            without_rebalance = 0
            with_rebalance = 0
            for item in self.portfolio:
                initial_value += self.record[f"{self.key}-{item}"].loc[start_dt, "price"] * self.record[f"{self.key}-{item}"].loc[start_dt, "quantity"]
                without_rebalance += self.record[f"{self.key}-{item}"].loc[end_dt, "price"] * self.record[f"{self.key}-{item}"].loc[start_dt, "quantity"]
                with_rebalance += self.record[f"{self.key}-{item}"].loc[end_dt, "price"] * self.record[f"{self.key}-{item}"].loc[end_dt, "quantity"]
            print(self.record[self.key])
            initial_value += self.record[self.key].loc[start_dt, "price"] * self.record[self.key].loc[start_dt, "quantity"]
            without_rebalance += self.record[self.key].loc[end_dt, "price"] * self.record[self.key].loc[start_dt, "quantity"]
            with_rebalance += self.record[self.key].loc[end_dt, "price"] * self.record[self.key].loc[end_dt, "quantity"]
            self.messageStack.append("초기 가치: " + numberFormat(initial_value))
            self.messageStack.append("투자 결과 without rebalance: " + numberFormat(without_rebalance))
            self.messageStack.append("투자 결과 with rebalance: " + numberFormat(with_rebalance))

    async def backtest(self, start_dt, end_dt, method = "normal"):
        async with self.queueLock:
            self.messageStack.append("📊 백테스트 시작")
            logger.info("📊 백테스트 시작")
            allDates = [
                    pd.Series(df.index[(start_dt <= df.index)&(df.index<= end_dt)])
                    for df in self.record.values()
                    ]
            if allDates ==[]:
                print("no data loaded")
                self.messageStack.append("no data loaded")
                return
        dates = pd.concat(allDates).drop_duplicates().sort_values().reset_index(drop=True)
        for date in dates:
            if method == "normal":
                await self.rebalance(date)
            elif method == "bolinger":
                await self.rebalance_bolinger(date)
            await asyncio.sleep(0.001)
        async with self.queueLock:
            self.messageStack.append("✅ 백테스트 완료")

    async def plot(self, start_dt, end_dt):
        portfolio = {}
        record = {}
        key = ""
        data = {}
        async with self.queueLock:
            portfolio = self.portfolio
            key = self.key
            record = self.record.copy()
            value = self.value.copy()
        for item in portfolio:
            basis = record[f"{key}-{item}"].loc[end_dt, "price"] # normalize하기 위한 숫자
            record[f"{key}-{item}"]["trade_quantity"] = record[f"{key}-{item}"]["trade_quantity"].fillna(0)
            record[f"{key}-{item}"]["quantity"] = record[f"{key}-{item}"]["quantity"].fillna(0)
            df = record[f"{key}-{item}"]
            df = df[(start_dt <= df.index) & (df.index <= end_dt)].copy()
            if len(df) > 1000:      # 1000개만 샘플링을 함
                index = np.linspace(0, len(df)-1, 1000, dtype=int)
                df = df.iloc[index]
            df.index.name = "x"
            df["norm_y"] = df["price"] / basis
            df = df.rename(columns = {"price": "y"})
            if "upper_band" in df.columns:
                df["upper_band"] = df["upper_band"] / basis
                df = df.rename(columns = {"upper_band": "norm_upper"})
            if "lower_band" in df.columns:
                df["lower_band"] = df["lower_band"] / basis
                df = df.rename(columns = {"lower_band": "norm_lower"})
            df = df.reset_index()
            df["x"] = df["x"].dt.strftime('%Y-%m-%dT%H:%M:%S')
            data[item] = df.to_dict(orient="records")
        if not value.empty:
            basis = value.loc[start_dt, key]
            df = value[(start_dt <= value.index) & (value.index <= end_dt)].copy()
            if len(df) > 1000:      # 1000개만 샘플링을 함
                index = np.linspace(0, len(df)-1, 1000, dtype=int)
                df = df.iloc[index]
            df.index.name = "x"
            df["norm_y"] = df[key] / basis
            df = df.rename(columns = {key: "y"})
            df = df.reset_index()
            df["x"] = df["x"].dt.strftime('%Y-%m-%dT%H:%M:%S')
            data["value"] = df.to_dict(orient="records")
        return data

    async def accounts(self):
        async with self.queueLock:
            payload = {
                'access_key': UPBIT_ACCESS_KEY,
                'nonce': str(uuid.uuid4()),
                }
            jwt_token = jwt.encode(payload, UPBIT_SECRET_KEY, algorithm = 'HS256')
            authorization_token = 'Bearer {}'.format(jwt_token)

            headers = {
                'Authorization': authorization_token,
            }
            res = requests.get("https://api.upbit.com/v1/accounts", headers=headers)

            if res.status_code == 200:
                balances = res.json()
                text = ""
                for item in balances:
                    if item['currency'] == "KRW":
                        self.messageStack.append(item['currency'] + ": " + f"{float(item['balance']):,.0f}")
                    else:
                        print("self.key: " + self.key)
                        url = "https://api.upbit.com/v1/ticker"
                        params = {"markets": f"{self.key}-{item['currency']}"}
                        response = requests.get(url, params=params)
                        if response.status_code == 200:
                            price = response.json()[0]["trade_price"]
                            self.assets[item['currency']] = item['balance']
                            self.messageStack.append(item['currency'] + ": {quantity: " + numberFormat(item['balance']) + ", price: " + numberFormat(price) + "}")
                        elif response.status_code == 404:
                            self.messageStack.append(item['currency'] + ": {quantity: " + numberFormat(item['balance']) + ", price: 0}")
                        else:
                            raise Exception(f"Upbit 시세 조회 실패: {response.text}")
                logger.info(text)
            else:
                print(f"에러 발생: {res.status_code}")
                print(res.text)
    async def cancelAllOrder(self):
        openOrders = getOrder()
        if not openOrders:
            async with self.queueLock:
                self.messageStack.append("🟢 취소할 미체결 주문이 없습니다.")
        else:
            for order in openOrders:
                result = cancelOrder(order["uuid"])
                async with self.queueLock:
                    self.messageStack.append(result)
    async def getMessageStack(self):
        async with self.queueLock:
            json = []
            while self.messageStack:
                json.append({"message": self.messageStack.pop(0)})
        return json
    async def stop(self):
        async with self.queueLock:
            self.automation = False
            if self.rebalanceTask:
                self.rebalanceTask.cancel()
                try:
                    await self.rebalanceTask
                except asyncio.CancelledError:
                    print("[INFO] 리밸런싱 루프 중지됨")
        await self.cancelAllOrder()

    async def execute(self):
        async with self.queueLock:
            if not self.automation:
                self.automation = True
                self.rebalanceTask = asyncio.create_task(self.rebalanceLoop())



def adjustPrice(price: float) -> float:
    if price >= 2000000:
        unit = 1000
    elif price >= 1000000:
        unit = 500
    elif price >= 100000:
        unit = 100
    elif price >= 10000:
        unit = 50
    elif price >= 1000:
        unit = 10
    elif price >= 100:
        unit = 5
    elif price >= 10:
        unit = 1
    elif price >= 1:
        unit = 0.1
    elif price >= 0.1:
        unit = 0.01
    else:
        unit = 0.001

    # 호가 단위로 반올림
    return round(price / unit) * unit
def numberFormat(num):
    return f"{float(num):,.6f}".rstrip('0').rstrip('.')
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS 허용
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:9902", "https://colaf.net", "https://colaf.net:9900"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
def buyOrder(key, item, quantity, price):
    orderData = {
            'market': f"{key}-{item}",
            'side': 'bid',
            'volume': quantity,
            'price': price,
            'ord_type': 'limit'
            }
    query_string = urlencode(orderData).encode()
    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()
    payload = {
            'access_key': UPBIT_ACCESS_KEY,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
            }
    jwt_token = jwt.encode(payload, UPBIT_SECRET_KEY, algorithm='HS256')
    if isinstance(jwt_token, bytes):
        jwt_token = jwt_token.decode("utf-8")
    url = "https://api.upbit.com/v1/orders"
    headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
            }
    response = requests.post(url, json=orderData, headers=headers)
    if response.status_code == 201:
        self.messageStack.append(item + "을 " + numberFormat(price) + "에 " + numberFormat(quantity) + "개 구매를 주문한다.")
    else:
        self.messageStack.append(f"❌ 오류 발생: {response.status_code} - {response.text}")

def sellOrder(key, item, quantity, price):
    orderData = {
            'market': f"{key}-{item}",
            'side': 'ask',
            'volume': quantity,
            'price': price,
            'ord_type': 'limit'
            }
    query_string = urlencode(orderData).encode()
    m = hashlib.sha512()
    m.update(query_string)
    query_hash = m.hexdigest()
    payload = {
            'access_key': UPBIT_ACCESS_KEY,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
            }
    jwt_token = jwt.encode(payload, UPBIT_SECRET_KEY, algorithm='HS256')
    if isinstance(jwt_token, bytes):
        jwt_token = jwt_token.decode("utf-8")
    url = "https://api.upbit.com/v1/orders"
    headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
            }
    response = requests.post(url, json=orderData, headers=headers)
    if response.status_code == 201:
        self.messageStack.append(item + "을 " + numberFormat(price) + "에 " + numberFormat(quantity) + "개 판매를 주문한다.")
    else:
        self.messageStack.append(f"❌ 오류 발생: {response.status_code} - {response.text}")

def getOrder():
    payload = {
            'access_key': UPBIT_ACCESS_KEY,
            'nonce': str(uuid.uuid4())
            }
    jwt_token = jwt.encode(payload, UPBIT_SECRET_KEY, algorithm='HS256')
    if isinstance(jwt_token, bytes):
        jwt_token = jwt_token.decode("utf-8")
    url = "https://api.upbit.com/v1/orders"
    headers = {
            "Authorization": f"Bearer {jwt_token}",
            }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    openOrders = response.json()
    return openOrders

def cancelOrder(uuid_str):
    url = "https://api.upbit.com/v1/order"
    params = {"uuid": uuid_str}
    query_string = '&'.join([f'{key}={value}' for key, value in params.items()])
    m = hashlib.sha512()
    m.update(query_string.encode())
    query_hash = m.hexdigest()
    payload = {
            'access_key': UPBIT_ACCESS_KEY,
            'nonce': str(uuid.uuid4()),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512',
            }
    jwt_token = jwt.encode(payload, UPBIT_SECRET_KEY, algorithm='HS256')
    if isinstance(jwt_token, bytes):
        jwt_token = jwt_token.decode("utf-8")
    headers = {
            "Authorization": f"Bearer {jwt_token}",
            }
    response = requests.delete(url, headers=headers, params=params)
    if response.status_code ==200:
        return "주문이 성공적으로 취소되었습니다."
    else:
        return response.text

clients = set()

def isAuthenticated(request: Request):
    if local_environment:
        if "local user" in users:
            return users.get("local user", None)
        else:
            users["local user"] = Invest()
            return users["local user"]
    db_config = {
            'host': ip_NAT_mariadb,
            'user': ID_mariadb,
            'password': PW_mariadb,
            'db': 'auth_session',
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
            }
    sid_encoded = request.cookies.get("connect.sid", "")
    sid_decoded = urllib.parse.unquote(sid_encoded)
    match = re.match(r"s:(\w+)\.",sid_decoded)
    if match:
        match = match.group(1)
    else:
        match = ""

    dbResult = []
    try:
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            sql = "SELECT data FROM sessions WHERE session_id = %s;"
            cursor.execute(sql, (match,))
            dbResult = cursor.fetchone()
            data = json.loads(dbResult['data'])
            userId = data["passport"]["user"]
            if userId in users:
                userInvest = users.get(userId, None)
            else:
                users[userId] = Invest()
                userInvest = users[userId]
            
    except pymysql.MySQLError as e:
        userId = 'local user'
    finally:
        if 'connection' in locals() and conn.open:
            conn.close()
    return userInvest


class DateRange(BaseModel):
    start: str
    end: str
class backtestData(BaseModel):
    start: str
    end: str
    initial: int
class conditionData(BaseModel):
    key: str
    portfolio: dict[str, float]
    allowedDeviation: dict[str, list[float]]
    initial: int

@app.get("/")
async def get():
    return HTMLResponse(open("static/index.html", encoding="utf-8").read())

@app.get("/messages")
async def get_messages(request: Request):
    userInvest = isAuthenticated(request)
    if not userInvest:
        return
    json = await userInvest.getMessageStack()
    return JSONResponse(content = json)

@app.post("/load")
async def load(request: Request):
    userInvest = isAuthenticated(request)
    if not userInvest:
        return
    json = await userInvest.load("./price.xlsx")
    return JSONResponse(content = json)
@app.post("/save")
async def save(request: Request):
    userInvest = isAuthenticated(request)
    if not userInvest:
        return
    await userInvest.save("./price.xlsx")

@app.post("/getOhlcv")
async def getOhlcv(request: Request, body: DateRange):
    userInvest = isAuthenticated(request)
    if not userInvest:
        return
    start_dt = datetime.datetime.strptime(body.start, "%Y-%m-%dT%H:%M")
    end_dt = datetime.datetime.strptime(body.end, "%Y-%m-%dT%H:%M")
    await userInvest.setCondition()
    await userInvest.getOhlcv(start_dt, end_dt)
    await userInvest.calculateBand()
    json = await userInvest.plot(start_dt, end_dt)
    return JSONResponse(content = json)

@app.post("/backtest")
async def backtest(request: Request, body: backtestData):
    userInvest = isAuthenticated(request)
    if not userInvest:
        return
    start_dt = datetime.datetime.strptime(body.start, "%Y-%m-%dT%H:%M")
    end_dt = datetime.datetime.strptime(body.end, "%Y-%m-%dT%H:%M")
    initial = body.initial
    await userInvest.setCondition(initial=initial)
    await userInvest.backtest(start_dt, end_dt)
    json = {}
    json = await userInvest.plot(start_dt, end_dt)
    await userInvest.result(start_dt, end_dt)
    return JSONResponse(content = json)

@app.post("/backtest-bolinger")
async def backtest(request: Request, body: backtestData):
    userInvest = isAuthenticated(request)
    if not userInvest:
        return
    start_dt = datetime.datetime.strptime(body.start, "%Y-%m-%dT%H:%M")
    end_dt = datetime.datetime.strptime(body.end, "%Y-%m-%dT%H:%M")
    initial = body.initial
    await userInvest.setCondition(initial=initial)
    await userInvest.backtest(start_dt, end_dt, method = "bolinger")
    json = {}
    json = await userInvest.plot(start_dt, end_dt)
    await userInvest.result(start_dt, end_dt)
    return JSONResponse(content = json)

@app.post("/accounts")
async def accounts(request: Request):
    userInvest = isAuthenticated(request)
    if not userInvest:
        return
    await userInvest.accounts() 
@app.post("/setCondition")
async def setCondition(request: Request, body: conditionData):
    userInvest = isAuthenticated(request)
    if not userInvest:
        return
    await userInvest.setCondition(key = body.key, initial = body.initial, portfolio = body.portfolio, allowedDeviation = body.allowedDeviation)
@app.post("/execute")
async def execute(request: Request):
    userInvest = isAuthenticated(request)
    if not userInvest:
        return
    print("hello")
    await userInvest.execute()
@app.post("/stop")
async def stop(request: Request):
    userInvest = isAuthenticated(request)
    if not userInvest:
        return
    await userInvest.stop()
