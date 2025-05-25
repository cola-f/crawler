from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime
import asyncio

import requests
import json
from collections import namedtuple
import copy
import pandas as pd
import matplotlib.pyplot as plt
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

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler("upbit.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

messageStack = []
queue_lock = asyncio.Lock()

class Invest:
    assets = {"BTC": 0, "ETH": 0, "XRP": 0, "KRW": 0}
    portfolio = {"BTC": 0.4, "ETH": 0.4, "XRP": 0.1}
    record = {}
    automation = False
    def __init__(self, krw):
        self.assets["KRW"] = krw
        print(self.assets)

    async def initialize(self, krw):
        async with queue_lock:
            self.assets["KRW"] = krw
            for item in self.portfolio:
                self.assets[item] = 0
            messageStack.append("Initialized");
    async def setPortfolio(self, portfolio):
        async with queue_lock:
            self.portfolio = portfolio
            print(portfolio)
            messageStack.append(str(self.portfolio))

    async def load(self, xlsx_path):
        if os.path.exists(xlsx_path):
            df_existing = pd.read_excel(xlsx_path, sheet_name = None)
            self.record = df_existing
            for item in self.record:
                self.record[item].set_index("candle_date_time_kst", inplace = True)
        return self.record[item]

    def save(self, xlsx_path):
        with pd.ExcelWriter(xlsx_path, engine = "openpyxl") as writer:
            if self.record:
                for item, df in self.record.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name = item, index=True)
            else:
                print("No data")
                pd.DataFrame({"message": ["No data"]}).to_excel(writer, sheet_name="Empty", index=False)


    def valueSum(self, date_dt):
        sum = 0
        for item in self.assets:
            if item == "KRW":
                sum += self.assets[item]
            else:
                price = self.record[item].loc[date_dt, "trade_price"]
                sum+=price * float(self.assets[item])
        return sum

    async def getOhlcv(self, start_dt, end_dt):
        # 10분단위로 필터링하는 코드가 필요
        dates = pd.date_range(start_dt, end_dt, freq = "10min")[::-1]
        for item in self.portfolio:
            if item not in self.record:
                self.record[item] = pd.DataFrame({
                    "candle_date_time_kst": pd.Series(dtype='datetime64[ns]'),
                    "trade_price": pd.Series(dtype='float'),
                    "trade_quantity": pd.Series(dtype='float'),
                    "backtest_quantity": pd.Series(dtype='float')
                    })
                self.record[item].set_index("candle_date_time_kst", inplace = True)
    
            for date in dates:
                if date not in self.record[item].index:
                    await queue_lock.acquire()
                    print("item: " + item + " date: " + str(date) + " 값을 가져옵니다.")
                    messageStack.append("item: " + item + " date: " + str(date) + "값을 가져옵니다.")
                    market = f"KRW-{item}"
                    url = "https://api.upbit.com/v1/candles/minutes/10"
                    headers = {"Accept": "application/json"}
                    params = {
                            "market": market,
                            "to": (date+datetime.timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                            "count": 200
                            }
                    response = requests.get(url, headers=headers, params=params)
                    if response.status_code != 200:
                        print(f"Error: {response.status_code} - {response.text}")
                        break

                    data = response.json()
                    if not data:
                        break

                    df = pd.DataFrame(data)
                    df['candle_date_time_kst'] = pd.to_datetime(df['candle_date_time_kst'])
                    df.set_index('candle_date_time_kst', inplace = True)
                    df = df[["trade_price"]]
                    if df.index.max() != date:
                        self.record[item].loc[date] = df.loc[df.index.max()]
                        self.record[item].sort_index()
                        continue
                    self.record[item] = pd.concat([self.record[item], df]).sort_index()
                    self.record[item] = self.record[item][~self.record[item].index.duplicated(keep='last')].sort_index() 
                    queue_lock.release()
                    await asyncio.sleep(0.1)

    async def rebalance(self, date_dt = None):
        async with queue_lock:
            allowedDeviation = {"BTC": (0.98, 1.02), "ETH": (0.98, 1.02), "XRP": (0.98, 1.02)}
            if date_dt == None and self.automation == True:
                messageStack.append("자동매매 중")
                for item in self.portfolio:
                    print("")
                
            else:
                for item in self.portfolio:
                    price = self.record[item].loc[date_dt, "trade_price"]
                    totalValue = self.valueSum(date_dt)
                    if price * self.assets[item] < totalValue*self.portfolio[item]*allowedDeviation[item][0]:
                        # buy
                        quantity = round((totalValue * self.portfolio[item] - price * self.assets[item])/price, 6)
                        self.assets[item] += quantity
                        self.assets["KRW"] -= quantity * price
                        self.record[item].loc[date_dt, "backtest_quantity"] = quantity
                        messageStack.append("@" + str(date_dt) + ";" + item + ": [" + str(quantity) + "] [" + str(price) + "]")
                    elif totalValue*self.portfolio[item] * allowedDeviation[item][1] < price * self.assets[item]:
                        # sell
                        quantity = round((price * self.assets[item] - totalValue * self.portfolio[item])/price, 6)
                        self.assets[item] -= quantity
                        self.assets["KRW"] += quantity * price
                        self.record[item].loc[date_dt, "backtest_quantity"] = -quantity
                        messageStack.append("@" + str(date_dt) + ";" + item + ": [" + str(-quantity) + "] [" + str(price) + "]")
                    else:
                        self.record[item].loc[date_dt, "backtest_quantity"] = 0
    
    async def status(self, date_dt):
        async with queue_lock:
            for item in self.assets:
                if item != "KRW":
                    quantity = self.assets[item]
                    price = self.record[item].loc[date_dt, "trade_price"]
                    value = quantity * price
                    ratio = price / self.valueSum(date_dt)
                    logger.info(item  + ": " + str(quantity) + "\t" + str(price) + "\t" + str(value) + "\t" + str(ratio))
                    messageStack.append(item + ": " + str(quantity) + "\t" + str(price) + "\t" + str(value) + "\t" + str(ratio))
                else:
                    logger.info(item + ": " + str(self.assets[item]))
                    messageStack.append(item + ": " + str(self.assets[item]))
            print("Total: " + str(self.valueSum(date_dt)))

    async def backtest(self, start_dt, end_dt):
        async with queue_lock:
            logger.info("backtest")
            allDates = [
                    pd.Series(df.index[(start_dt <= df.index)&(df.index<= end_dt)])
                    for df in self.record.values()
                    ]
            if allDates ==[]:
                print("no data loaded")
                messageStack.append("no data loaded")
                return
        dates = pd.concat(allDates).drop_duplicates().sort_values().reset_index(drop=True)
        for date in dates:
           await self.rebalance(date)

    def plot(self, start_dt, end_dt):
        plt.figure(figsize=(12, 6))
        for item in self.record:
            df = self.record[item][(start_dt <= self.record[item].index)&(self.record[item].index <= end_dt)].copy()
            df["normalized_price"] = df["trade_price"] / df["trade_price"].iloc[-1]
            plt.plot(df.index, df["normalized_price"], label=item)
            for x, normalized_y, y, qty in zip(df.index, df["normalized_price"], df["trade_price"], df["trade_quantity"]):
                if pd.notna(qty) & (qty > 0):
                    plt.text(x, normalized_y, f"{y}\n{qty:.6f}", fontsize=8, ha='center', va='bottom', color='red')
                elif pd.notna(qty) & (qty < 0):
                    plt.text(x, normalized_y, f"{y}\n{qty:.6f}", fontsize=8, ha='center', va='bottom', color='blue')

        plt.yscale("log")
        plt.xlabel("Datetime")
        plt.ylabel("Price(log scale)")
        plt.legend()
        plt.grid(True, which="both", linestyle="--", linewidth=0.5)
        plt.tight_layout()
        plt.show()
    def execute():
        inputStr = input("자동매매를 실행하시겠습니까?(YES/NO)")
        if inputStr != "YES":
            self.automation = False
            return
        else:
            self.automation = True
        logger.warning("execute")
        while True:
            rebalance()
            time.sleep(600)
    async def accounts(self):
        async with queue_lock:
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
                    print("item output")
                    print(item)
                    if item['currency'] == "KRW":
                        messageStack.append(item['currency'] + ": " + f"{float(item['balance']):,.0f}")
                    else:
                        url = "https://api.upbit.com/v1/ticker"
                        params = {"markets": f"KRW-{item['currency']}"}
                        response = requests.get(url, params=params)
                        if response.status_code == 200:
                            price = response.json()[0]["trade_price"]
                            self.assets[item['currency']] = item['balance']
                            messageStack.append(item['currency'] + ": {quantity: " + str(item['balance']) + ", price: " + str(price) + "}")
                        elif response.status_code == 404:
                            messageStack.append(item['currency'] + ": {quantity: " + str(item['balance']) + ", price: 0}")
                        else:
                            raise Exception(f"Upbit 시세 조회 실패: {response.text}")
                logger.info(text)
            else:
                print(f"에러 발생: {res.status_code}")
                print(res.text)
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS 허용
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

invest = Invest(10000000)
clients = set()

class DateRange(BaseModel):
    start: str
    end: str
class backtestData(BaseModel):
    start: str
    end: str
    krw: int
class portfolioData(BaseModel):
    portfolio: dict

@app.get("/")
async def get():
    return HTMLResponse(open("static/index.html", encoding="utf-8").read())

@app.get("/messages")
async def get_messages():
    async with queue_lock:
        data = []
        while messageStack:
            data.append({"message": messageStack.pop(0)})
        return JSONResponse(content = data)

@app.post("/load")
async def load():
    async with queue_lock:
        messageStack.append("loading")
        data = await invest.load("./price.xlsx")
        messageStack.append("done")
        json = {}
        for item, df in invest.record.items():
            df_clean = df.reset_index()
            df_clean["candle_date_time_kst"] = df_clean["candle_date_time_kst"].dt.strftime('%Y-%m-%dT%H:%M:%S')
            json[item] = df_clean.to_dict(orient="records")
    return JSONResponse(content = json)
@app.post("/save")
async def load():
    async with queue_lock:
        messageStack.append("saving")
        invest.save("./price.xlsx")
        messageStack.append("done")
@app.post("/save")
async def save():
    async with queue_lock:
        messageStack.append("saving")
        invest.save("./price.xlsx")
        messageStock.append("done")

@app.post("/getOhlcv")
async def getOhlcv(request: DateRange):
    start_dt = datetime.datetime.strptime(request.start, "%Y-%m-%dT%H:%M")
    end_dt = datetime.datetime.strptime(request.end, "%Y-%m-%dT%H:%M")
    async with queue_lock:
        messageStack.append("📈 OHLCV 수집 시작")
    await invest.getOhlcv(start_dt, end_dt)
    async with queue_lock:
        messageStack.append("✅ OHLCV 수집 완료")

        json = {}
        for item, df in invest.record.items():
            df_clean = df.reset_index()
            df_clean["candle_date_time_kst"] = df_clean["candle_date_time_kst"].dt.strftime('%Y-%m-%dT%H:%M:%S')
            df_clean["normalized_price"] = df_clean["trade_price"] / df_clean["trade_price"].iloc[-1]
            df_clean["trade_quantity"] = df_clean["trade_quantity"].fillna(0)
            df_clean["backtest_quantity"] = df_clean["backtest_quantity"].fillna(0)
            json[item] = df_clean.to_dict(orient="records")
    return JSONResponse(content = json)

@app.post("/backtest")
async def backtest(request: backtestData):
    krw = request.krw
    start_dt = datetime.datetime.strptime(request.start, "%Y-%m-%dT%H:%M")
    end_dt = datetime.datetime.strptime(request.end, "%Y-%m-%dT%H:%M")
    async with queue_lock:
        messageStack.append("📊 백테스트 시작")
        messageStack.append("초기값 " + str(krw) + "원")
    await invest.initialize(krw)
    await invest.backtest(start_dt, end_dt)
    print(invest.record)
    json = {}
    async with queue_lock:
        messageStack.append("✅ 백테스트 완료")
        for item, df in invest.record.items():
            df_clean = df.reset_index()
            df_clean["candle_date_time_kst"] = df_clean["candle_date_time_kst"].dt.strftime('%Y-%m-%dT%H:%M:%S')
            df_clean["normalized_price"] = df_clean["trade_price"] / df_clean["trade_price"].iloc[-1]
            df_clean["trade_quantity"] = df_clean["trade_quantity"].fillna(0)
            df_clean["backtest_quantity"] = df_clean["backtest_quantity"].fillna(0)
            json[item] = df_clean.to_dict(orient="records")
    return JSONResponse(content = json)

@app.post("/accounts")
async def accounts():
    async with queue_lock:
        messageStack.append("Accounts")
    await invest.accounts() 
@app.post("/setPortfolio")
async def setPortfolio(request: portfolioData):
    portfolio = request.portfolio
    await invest.setPortfolio(portfolio)
