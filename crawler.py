from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pymysql
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

messageStack = []
queue_lock = asyncio.Lock()

class Invest:
    assets = {"BTC": 0, "ETH": 0, "XRP": 0, "KRW": 0}
    portfolio = {}
    allowedDeviation = {}
    record = {}
    value = pd.DataFrame()
    automation = False
    rebalanceTask = {}
    def __init__(self, krw):
        self.assets["KRW"] = {"volume": krw, "price": 1}
        self.portfolio = {"BTC": 0.3, "ETH": 0.3, "XRP": 0.2}
        self.allowedDeviation = {"BTC": (0.98, 1.02), "ETH": (0.98, 1.02), "XRP": (0.98, 1.02)}
        for item in self.portfolio:
            self.assets[item] = {"volume": 0, "price": 0}
            self.record[item] = pd.DataFrame({
                "candle_date_time_kst": pd.Series(dtype='datetime64[ns]'),
                "trade_price": pd.Series(dtype='float'),
                "trade_quantity": pd.Series(dtype='float'),
                "quantity": pd.Series(dtype='float'),
                "backtest_trade_quantity": pd.Series(dtype = 'float'),
                "backtest_quantity": pd.Series(dtype='float')
                })
            self.record[item].set_index("candle_date_time_kst", inplace = True)
        self.value = pd.DataFrame({
            "candle_date_time_kst": pd.Series(dtype = 'datetime64[ns]'),
            "KRW": pd.Series(dtype='float')
            })
        self.value.set_index("candle_date_time_kst", inplace = True)

    def initialize(self, krw):
        for item in self.portfolio:
            self.assets[item] = {"volume": 0, "price": 0}
        self.assets["KRW"] = {"volume": krw, "price": 1}

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


    def valueSum(self):
        sum = 0
        for item in self.portfolio:
            
            sum += self.assets[item]["price"] * float(self.assets[item]["volume"])
        sum += self.assets["KRW"]["volume"] * self.assets["KRW"]["price"]
        return sum

    async def getOhlcv(self, start_dt, end_dt):
        # 10분단위로 필터링하는 코드가 필요
        dates = pd.date_range(start_dt, end_dt, freq = "10min")[::-1]
        for item in self.portfolio:
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
                        await queue_lock.release()
                        break

                    data = response.json()
                    if not data:
                        await queue_lock.release()
                        break

                    df = pd.DataFrame(data)
                    df['candle_date_time_kst'] = pd.to_datetime(df['candle_date_time_kst'])
                    df.set_index('candle_date_time_kst', inplace = True)
                    df = df[["trade_price"]]
                    if df.index.max() != date:
                        self.record[item].loc[date] = df.loc[df.index.max()]
                        self.record[item] = self.record[item].sort_index()
                    else:
                        self.record[item] = pd.concat([self.record[item], df]).sort_index()
                        self.record[item] = self.record[item][~self.record[item].index.duplicated(keep='last')].sort_index() 
                    queue_lock.release()
                    await asyncio.sleep(0.1)

    async def rebalanceLoop(self):
        async with queue_lock:
            automation = self.automation
        while automation:
            async with queue_lock:
                messageStack.append("Rebalancing")
            payload = {'access_key': UPBIT_ACCESS_KEY, 'nonce': str(uuid.uuid4())}
            jwt_token = jwt.encode(payload, UPBIT_SECRET_KEY, algorithm='HS256')
            url="https://api.upbit.com/v1/ticker"
            params = {"markets": ",".join(f"KRW-{m}" for m in self.portfolio)}
            res.raise_for_status()
            prices = {item["market"].split("-")[1]: item["trade_price"] for item in res.json()}
            url = "https://api.upbit.com/v1/accounts"
            headers = {"Authorization": f"Bearer {jwt_token}"}
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            accounts = res.json()
            volumes = {item["currency"]: float(item["balance"]) for item in accounts}
            async with queue_lock:
                for item in self.portfolio:
                    self.assets[item] = {"volume": volumes.get(item, 0), "price": prices.get(item, 0)}
                    messageStack.append(item + ": {volume: " + numberFormat(self.assets[item]["volume"]) + ", price: " + numberFormat(self.assets[item]["price"]) + "}")
                self.assets["KRW"] = {"volume": volumes.get("KRW", 0), "price": 1}
                messageStack.append("KRW: {volume: " + f"{self.assets['KRW']['volume']:,.0f}" + ", price: " + f"{self.assets['KRW']['price']:,.0f}" + "}")
                
                for item in self.portfolio:
                    price = self.assets[item]["price"]
                    volume = self.assets[item]["volume"]
                    valueSum = self.valueSum()
                    if price * volume < valueSum * self.portfolio[item] * self.allowedDeviation[item][0]:
                        #buy
                        quantity = round((valueSum * self.portfolio[item] - price * self.assets[item]["volume"])/price, 6)
                        messageStack.append(item + "을 " + numberFormat(price) + "에 " + numberFormat(quantity) + "개 구매를 주문할 예정.")
                        # buyOrder(item, quantity, price)
                    elif valueSum * self.portfolio[item] * self.allowedDeviation[item][1] < price * volume:
                        #sell
                        quantity = round((price * volume - valueSum * self.portfolio[item])/price, 6)
                        messageStack.append(item + "을 " + numberFormat(price) + "에 " + numberFormat(quantity) + "개 판매를 주문할 예정.")
                        # sellOrder(item, quantity, price)
                    else:
                        #buy
                        buy_price = round(valueSum * self.portfolio[item] * self.allowedDeviation[item][1]/volume, 6)
                        buy_quantity = round((1 - self.allowedDeviation[item][0]) * (1 - self.portfolio[item]) * volume / self.allowedDeviation[item][0], 6)
                        messageStack.append(item + "을 " + numberFormat(buy_price) + "에 " + numberFormat(buy_quantity) + "개 구매를 주문할 예정.")
                        #buyOrder(item, buy_quantity, buy_price)
                        #sell
                        sell_price = round(valueSum * self.portfolio[item]*self.allowedDeviation[item][1]/volume, 6)
                        sell_quantity = round((self.allowedDeviation[item][1] - 1)*(1 - self.portfolio[item]) * volume / self.allowedDeviation[item][1], 6)
                        messageStack.append(item + "을 " + numberFormat(sell_price) + "에 " + numberFormat(sell_quantity) + "개 판매를 주문할 예정.")
                        #sellOrder(item, sell_quantity, sell_price)

            await asyncio.sleep(300)
            openOrders = getOrder()
            if not openOrders:
                async with queue_lock:
                    messageStack.append("🟢 취소할 미체결 주문이 없습니다.")
            else:
                async with queue_lock:
                    messageStack.append(f"🔎 총 {len(openOrders)}개의 주문을 취소합니다.")
                for order in openOrder:
                    cancelOrder(order["uuid"])
            async with queue_lock:
                automation = self.automation
            
    async def rebalance(self, date_dt):
        async with queue_lock:
            for item in self.portfolio:
                self.assets[item]["price"] = self.record[item].loc[date_dt, "trade_price"]
            for item in self.portfolio:
                volume = self.assets[item]["volume"]
                price = self.assets[item]["price"]
                valueSum = self.valueSum()
                if price * volume < valueSum*self.portfolio[item]*self.allowedDeviation[item][0]:
                    # buy
                    quantity = round((valueSum * self.portfolio[item] - price * volume)/price, 6)
                    self.assets[item]["volume"] += quantity
                    self.assets["KRW"]["volume"] -= quantity * price
                    self.record[item].loc[date_dt, "backtest_trade_quantity"] = quantity
                    self.record[item].loc[date_dt, "backtest_quantity"] = self.assets[item]["volume"]
                    messageStack.append("@" + str(date_dt) + ";" + item + ": [" + numberFormat(quantity) + "] [" + numberFormat(price) + "]")
                elif valueSum*self.portfolio[item] * self.allowedDeviation[item][1] < price * volume:
                    # sell
                    quantity = round((price * volume - valueSum * self.portfolio[item])/price, 6)
                    self.assets[item]["volume"] -= quantity
                    self.assets["KRW"]["volume"] += quantity * price
                    self.record[item].loc[date_dt, "backtest_trade_quantity"] = -quantity
                    self.record[item].loc[date_dt, "backtest_quantity"] = self.assets[item]["volume"]
                    messageStack.append("@" + str(date_dt) + ";" + item + ": [" + numberFormat(-quantity) + "] [" + numberFormat(price) + "]")
                else:
                    self.record[item].loc[date_dt, "backtest_trade_quantity"] = 0
                    self.record[item].loc[date_dt, "backtest_quantity"] = self.assets[item]["volume"]
            self.value = self.value.sort_index()
            self.value.loc[date_dt, "KRW"] = self.valueSum()
    
    async def status(self):
        async with queue_lock:
            for item in self.assets:
                if item != "KRW":
                    quantity = self.assets[item]["volume"]
                    price = self.assets[item]["price"]
                    value = quantity * price
                    ratio = price / self.valueSum()
                    logger.info(item  + ": " + numberFormat(quantity) + "\t" + numberFormat(price) + "\t" + numberFormat(value) + "\t" + numberFormat(ratio))
                    messageStack.append(item + ": " + numberFormat(quantity) + "\t" + numberFormat(price) + "\t" + numberFormat(value) + "\t" + numberFormat(ratio))
                else:
                    logger.info(item + ": " + str(self.assets[item]["volume"]))
                    messageStack.append(item + ": " + numberFormat(self.assets[item]["volume"]))
            print("Total: " + str(self.valueSum()))

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
           await asyncio.sleep(0.001)

    def plot(self, start_dt, end_dt):
        plt.figure(figsize=(12, 6))
        for item in self.record:
            df = self.record[item][(start_dt <= self.record[item].index)&(self.record[item].index <= end_dt)].copy()
            df["normalized_value"] = df["trade_price"] / df["trade_price"].iloc[-1]
            plt.plot(df.index, df["normalized_value"], label=item)
            for x, normalized_y, y, qty in zip(df.index, df["normalized_value"], df["trade_price"], df["trade_quantity"]):
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
                            messageStack.append(item['currency'] + ": {quantity: " + numberFormat(item['balance']) + ", price: " + numberFormat(price) + "}")
                        elif response.status_code == 404:
                            messageStack.append(item['currency'] + ": {quantity: " + numberFormat(item['balance']) + ", price: 0}")
                        else:
                            raise Exception(f"Upbit 시세 조회 실패: {response.text}")
                logger.info(text)
            else:
                print(f"에러 발생: {res.status_code}")
                print(res.text)

def numberFormat(num):
    return f"{num:,.6f}".rstrip('0').rstrip('.')
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS 허용
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
def buyOrder(item, quantity, price):
    messageStack.append(item + "을 " + numberFormat(price) + "에 " + numberFormat(quantity) + "개 구매를 주문한다.")
    orderData = {
            'market': f"KRW-{item}",
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
        messageStack.append(item + "을 " + numberFormat(price) + "에 " + numberFormat(quantity) + "개 구매를 주문한다.")
    else:
        messageStack.append(f"❌ 오류 발생: {response.status_code} - {response.text}")

def sellOrder(item, quantity, price):
    orderData = {
            'market': f"KRW-{item}",
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
        messageStack.append(item + "을 " + numberFormat(price) + "에 " + numberFormat(quantity) + "개 판매를 주문한다.")
    else:
        messageStack.append(f"❌ 오류 발생: {response.status_code} - {response.text}")
    messageStack.append(item + "을 " + str(price) + "에 " + numberFormat(quantity) + "개 판매한다.")

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

def cancelOrder(uuid):
    url = "https://api.upbit.com/v1/order"
    query = {"uuid": uuid}
    payload = {
            'access_key': UPBIT_ACCESS_KEY,
            'nonce': str(uuid.uuid4())
            }
    jwt_token = jwt.encode(payload, UPBIT_SECRET_KEY, algorithm='HS256')
    if isinstance(jwt_token, bytes):
        jwt_token = jwt_token.decode("utf-8")
    header = {
            "Authorization": f"Bearer {jwt_token}",
            }
    response = requests.delete(url, headers=headers, params=query)
    return response

invest = Invest(10000000)
clients = set()

def isAuthenticated(request: Request):
    db_config = {
            'host': ip_NAT_mariadb,
            'user': ID_mariadb,
            'password': PW_mariadb,
            'db': 'auth_session',
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
            }
    # session_id = request.cookies
    session_id = ""
    print(session_id)
    dbResult = []
    try:
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            sql = "SELECT data FROM sessions WHERE session_id = %s;"
            cursor.execute(sql, (session_id,))
            dbResult = cursor.fetchone()
    except pymysql.MySQLError as e:
        userId = 'local user'
    finally:
        if 'connection' in locals() and conn.open:
            conn.close()
    data = json.loads(dbResult['data'])
    userId = data["passport"]["user"]
    return userId


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
async def get_messages(request: Request):
    userId = isAuthenticated(request)
    if userId =="":
        print("userIde no ")
        return
    async with queue_lock:
        data = []
        while messageStack:
            data.append({"message": messageStack.pop(0)})
        return JSONResponse(content = data)

@app.post("/load")
async def load():
    userId = isAuthenticated(request)
    if userId =="":
        return
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
async def save():
    userId = isAuthenticated(request)
    if userId =="":
        return
    async with queue_lock:
        messageStack.append("saving")
        invest.save("./price.xlsx")
        messageStack.append("done")

@app.post("/getOhlcv")
async def getOhlcv(request: DateRange):
    userId = isAuthenticated(request)
    if userId =="":
        return
    start_dt = datetime.datetime.strptime(request.start, "%Y-%m-%dT%H:%M")
    end_dt = datetime.datetime.strptime(request.end, "%Y-%m-%dT%H:%M")
    async with queue_lock:
        messageStack.append("📈 OHLCV 수집 시작")
    await invest.getOhlcv(start_dt, end_dt)
    async with queue_lock:
        messageStack.append("✅ OHLCV 수집 완료")

        json = {}
        for item, df in invest.record.items():
            df_output = df[(start_dt <= df.index) & (df.index <= end_dt)].copy()
            df_output["normalized_value"] = df_output["trade_price"] / df_output.loc[end_dt, "trade_price"]
            df_clean = df_output.reset_index()
            df_clean["candle_date_time_kst"] = df_clean["candle_date_time_kst"].dt.strftime('%Y-%m-%dT%H:%M:%S')
            df_clean = df_clean[["candle_date_time_kst", "normalized_value", "trade_price"]]
            json[item] = df_clean.to_dict(orient="records")
    return JSONResponse(content = json)

@app.post("/backtest")
async def backtest(request: backtestData):
    userId = isAuthenticated(request)
    if userId =="":
        return
    krw = request.krw
    start_dt = datetime.datetime.strptime(request.start, "%Y-%m-%dT%H:%M")
    end_dt = datetime.datetime.strptime(request.end, "%Y-%m-%dT%H:%M")
    async with queue_lock:
        messageStack.append("📊 백테스트 시작")
        messageStack.append("초기값 " + f"{krw:,.0f}" + "원")
        invest.initialize(krw)
    await invest.backtest(start_dt, end_dt)
    json = {}
    async with queue_lock:
        messageStack.append("✅ 백테스트 완료")
        messageStack.append("결과값 " + f"{invest.value.loc[end_dt, 'KRW']:,.0f}")
        for item, df in invest.record.items():
            df_output = df[(start_dt <= df.index) & (df.index <= end_dt)].copy()
            df_output["normalized_value"] = df_output["trade_price"] / df_output.loc[end_dt, "trade_price"]
            df_clean = df_output.reset_index()
            df_clean["candle_date_time_kst"] = df_clean["candle_date_time_kst"].dt.strftime('%Y-%m-%dT%H:%M:%S')
            df_clean = df_clean[["candle_date_time_kst", "normalized_value", "trade_price", "backtest_trade_quantity", "backtest_quantity"]]
            df_clean["backtest_trade_quantity"] = df_clean["backtest_trade_quantity"].fillna(0)
            df_clean["backtest_quantity"] = df_clean["backtest_quantity"].fillna(0)
            json[item] = df_clean.to_dict(orient="records")
        invest.value["normalized_value"] = invest.value["KRW"] / invest.value.loc[start_dt, "KRW"]
        invest.value["trade_price"] = invest.value["KRW"]
        value_clean = invest.value.reset_index()
        value_clean["candle_date_time_kst"] = value_clean["candle_date_time_kst"].dt.strftime('%Y-%m-%dT%H:%M:%S')
        json["value"] = value_clean.to_dict(orient="records")
    return JSONResponse(content = json)

@app.post("/accounts")
async def accounts():
    userId = isAuthenticated(request)
    if userId =="":
        return
    async with queue_lock:
        messageStack.append("Accounts")
    await invest.accounts() 
@app.post("/setPortfolio")
async def setPortfolio(request: portfolioData):
    userId = isAuthenticated(request)
    if userId =="":
        return
    portfolio = request.portfolio
    await invest.setPortfolio(portfolio)
@app.post("/execute")
async def execute():
    userId = isAuthenticated(request)
    if userId =="":
        return
    async with queue_lock:
        if not invest.automation:
            invest.automation = True
            rebalance_task = asyncio.create_task(invest.rebalanceLoop())
            messageStack.append("Starting rebalance")
        else:
            messageStack.append("Already rebalancing")
@app.post("/stop")
async def stop():
    userId = isAuthenticated(request)
    if userId =="":
        return
    async with queue_lock:
        invest.automation = False
        if invest.rebalanceTask:
            invest.rebalanceTask.cancel()
            try:
                await rebalanceTask
            except asyncio.CancelledError:
                messageStack.append("[INFO] 리밸런싱 루프 중지됨")
        messageStack.append("자동 리밸런싱 중지됨")
