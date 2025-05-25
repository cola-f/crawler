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


load_dotenv()
ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

file_handler = logging.FileHandler("upbit.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class Invest:
    assets = {"BTC": 0, "ETH": 0, "XRP": 0, "KRW": 0}
    portfolio = {"BTC": 0.4, "ETH": 0.4, "XRP": 0.1}
    record = {}
    automation = False
    def __init__(self, krw):
        self.assets["KRW"] = krw
        print(self.assets)

    def load(self, xlsx_path):
        if os.path.exists(xlsx_path):
            df_existing = pd.read_excel(xlsx_path, sheet_name = None)
            self.record = df_existing
            for item in self.record:
                self.record[item].set_index("candle_date_time_kst", inplace = True)

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
                sum+=price * self.assets[item]
        return sum

    def getOhlcv(self, start_dt, end_dt):
        # 10분단위로 필터링하는 코드가 필요
        dates = pd.date_range(start_dt, end_dt, freq = "10min")[::-1]
        for item in self.portfolio:
            if item not in self.record:
                self.record[item] = pd.DataFrame({
                    "candle_date_time_kst": pd.Series(dtype='datetime64[ns]'),
                    "trade_price": pd.Series(dtype='float')
                    })
                self.record[item].set_index("candle_date_time_kst", inplace = True)

            for date in dates:
                if date not in self.record[item].index:
                    print("item: " + item + " date: " + str(date) + " 값을 가져옵니다.")
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
                    if df.index.max() != date:
                        self.record[item].loc[date] = df.loc[df.index.max()]
                        self.record[item].sort_index()
                        continue
                    self.record[item] = pd.concat([self.record[item], df]).sort_index()
                    self.record[item] = self.record[item][~self.record[item].index.duplicated(keep='last')].sort_index() 
                    time.sleep(0.1)

    def rebalance(self, date_dt = None):
        self.portfolio = {"BTC": 0.3, "ETH": 0.3, "XRP": 0.2}
        allowedDeviation = {"BTC": (0.98, 1.02), "ETH": (0.98, 1.02), "XRP": (0.98, 1.02)}
        if date_dt == None and self.automation == True:
            print("자동매매")
        else:
            for item in self.portfolio:
                price = self.record[item].loc[date_dt, "trade_price"]
                totalValue = self.valueSum(date_dt)
                if price * self.assets[item] < totalValue*self.portfolio[item]*allowedDeviation[item][0]:
                    # buy
                    quantity = round((totalValue * self.portfolio[item] - price * self.assets[item])/price, 6)
                    self.assets[item] += quantity
                    self.assets["KRW"] -= quantity * price
                    self.record[item].loc[date_dt, "trade_quantity"] = quantity
                    self.status(date_dt)
                elif totalValue*self.portfolio[item] * allowedDeviation[item][1] < price * self.assets[item]:
                    # sell
                    quantity = round((price * self.assets[item] - totalValue * self.portfolio[item])/price, 6)
                    self.assets[item] -= quantity
                    self.assets["KRW"] += quantity * price
                    self.record[item].loc[date_dt, "trade_quantity"] = -quantity
                    self.status(date_dt)
                else:
                    self.record[item].loc[date_dt, "trade_quantity"] = 0
    
    def status(self, date_dt):
        for item in self.assets:
            if item != "KRW":
                quantity = self.assets[item]
                price = self.record[item].loc[date_dt, "trade_price"]
                value = quantity * price
                ratio = price / self.valueSum(date_dt)
                logger.info(item  + ": " + str(quantity) + "\t" + str(price) + "\t" + str(value) + "\t" + str(ratio))
            else:
                logger.info(item + ": " + str(self.assets[item]))
        print("Total: " + str(self.valueSum(date_dt)))

    def backtest(self, start_dt, end_dt):
        logger.info("backtest")
        allDates = [
                pd.Series(df.index[(start_dt <= df.index)&(df.index<= end_dt)])
                for df in self.record.values()
                ]
        dates = pd.concat(allDates).drop_duplicates().sort_values().reset_index(drop=True)
        for date in dates:
           self.rebalance(date)

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
    def account():
        payload = {
                'access_key': ACCESS_KEY,
                'nonce': str(uuid.uuid4()),
                }
        jwt_token = jwt.encode(payload, secret_key, algorithm = 'HS256')
        authorization_token = 'Bearer {}'.format(jwt_token)

        headers = {
                'Authorization': authorization_token,
                }
        res = requests.get("https://api.upbit.com/v1/accounts", headers=headers)

        if res.status_code == 200:
            balances = res.json()
            text = ""
            for item in balances:
                self.assets[item['currency']] = item['balance']
            logger.info(text)
        else:
            print(f"에러 발생: {res.status_code}")
            print(res.text)

def main():
    invest = Invest(10000000)
    xlsx_path = "./price.xlsx"
    start = "2024-4-1 00:00:00"
    end = "2024-10-1 00:00:00"
    start_dt = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
    print("load")
    invest.load(xlsx_path)
    print("crawling")
    invest.getOhlcv(start_dt, end_dt)
    print("save")
    invest.save(xlsx_path)
    print("backtest")
    invest.backtest(start_dt, end_dt)
    print("plot")
    invest.plot(start_dt, end_dt)
    
if __name__ == "__main__":
    main()

#import jwt
#import uuid
#import hashlib
#from urllib.parse import urlencode

#with open(r'backtest.cfg', encoding='UTF-8') as f:
#    _cfg = yaml.load(f, Loader=yaml.FullLoader)
#
#_last_auth_time = datetime.now()
#_autoReAuth = False
#
#default_headers = {
#        }
##### 아래에 작성
#class Stock:
#    def __init__(self):
#        self.default_headers = {
#                "Content-Type": "application/json",
#                "Accept": "text/plain",
#                "charset": "UTF-8",
#                'User-Agent': _cfg['my_agent']
#            }
#        self.app_token = None
#
#    def getDefaultHeaders(self):
#        return self.default_headers
#        
#    def auth(self):
#        url = f'{_cfg["prod"]}/oauth2/tokenP'
#        headers = self.getDefaultHeaders()
#        body = {
#                "grant_type": "client_credentials",
#                }
#        body["appkey"] = _cfg['app_key']
#        body["appsecret"] = _cfg['app_secret']
#        response = requests.post(url, headers = headers, data = json.dumps(body), verify = False)
#        print("response: ", response.text)
#        if response.status_code == 200:
#            self.app_token = response.json()['access_token']
#            print("app_token: ", app_token)
#        else:
#            print('Get Authentitation token fail!\nYou have to restart your app!')


#### 위에 작성
#def _getBaseHeader():
#    if _autoReAuth: reAuth()
#    return copy.deepcopy(_base_headers)
#
#def _getResultObject(json_data):
#    _tc_ = namedtuple('res', json_data.keys())
#    return _tc_(**json_data)
#
#def auth(svr='prod', product='01'):
#    body = {
#            "grant_type": "client_credentials",
#            }
#    print(svr)
#    if svr == 'prod':
#        ak1 = 'app_key'
#        ak2 = 'app_secret'
#    elif svr == 'vps':
#        ak1 = 'paper_app'
#        ak2 = 'paper_sec'
#
#    body["appkey"] = _cfg[ak1]
#    body["appsecret"] = _cfg[ak2]
#
#    url = f'{_cfg[svr]}/oauth2/tokenP'
#
#    response = requests.post(url, headers = _getBaseHeader(), data = json.dumps(body))
#
#    if response.status_code == 200:
#        my_token = _getResultObject(response.json()).access_token
#        print("my_token: " + my_token)
#    else:
#        print('Get Authentication token fail!\nYou have to restart your app!')
#        return
#
#def _url_fetch(api_url, ptr_id, param, appendHeaders=None, postFlag=False):
#    url = f"{getTREnv().my_url}{api_url}"
#    headers = _getBaseHeader()
#
#    # 추가 header 설정
#    tr_id = ptr_id
#    if ptr_id[0] in {'T', 'J', 'C'}:
#        if isPaperTrading():
#            tr_id = 'V' + ptr_id[1:]
#
#    headers["tr_id"] = tr_id
#    headers["custtype"] = "P"
#
#    if appendHeaders is not None:
#        if len(appendHeaders) > 0:
#            for x in appendHeaders.keys():
#                headers[x] = appendHeaders.get(x)
#    if(_DEBUG):
#        print("< Sending Info >")
#        print(f"URL: {url}, TR: {tr_id}")
#        print(f"<header>\n{headers}")
#        print(f"<body>\n{params}")
#
#    if (postFlag):
#        if(hashFlag):
#            set_order_hash_key(headers, params)
#        response = requests.post(url, headers=headers, data=json.dumps(params))
#    else:
#        response = requests.get(url, headers=headers, params=params)
#
#    if response.status_code ==200:
#        ar = APIResp(response)
#        if(_DEBUG):
#            ar.printAll()
#        return ar
#    else:
#        print("Error Code: " + str(response.status_code) + " | " + response.text)
#        return None
#def get_stock_history(stock_no, gb_cd='D'):
#    url = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
#    tr_id = "FHKST01010400"
#    params = {
#            "FID_COND_MRKT_DIV_CODE": _getStockDiv(stock_no),
#            "FID_INPUT_ISCD": stock_no,
#            "FID_PERIOD_DIV_CODE": gb_cd,
#            "FID_ORG_ADJ_PRC": "0000000001"
#            }
#    t1 = _url_fetch(url, tr_id, params)
#
#    if t1.isOK():
#        return pd.DataFrame(t1.getBody().output)
#    else:
#        t1.printError()
#        return pd.DataFrame()
#    # _url_fetch
#    # _isOK()
#    # printError()
#
## 종목의 주식, ETF 선물/옵션 등의 구분값을 반환. 현재는 무조건 주식(J)만 반환
#def _getStockDid edit mode에서 nerd라고 치면 NERDTree가 나왔다 사라졌다. 함2(stock_no):
#    return 'J'
#
#class CryptoCurrency():
#    def auth(self):
#        m = hashlib.sha512()
#        m.update(urlencode(query).encode())
#        query_hash = m.hexdigest()
#
#        payload = {
#                'access_key': 'Acess_key',
#                'nonce': str(uuid.uuid4()),
#                'query_hash': query_hash,
#                'query_hash_alg': 'SHA512',
#                }
#        jwt_token = jwt.encode(payload, 'Secret_key')
#        authorization_token = 'Bearer {}'.format(jwt_token)
#        return authorization_token
#
#cryptoCurrency = CryptoCurrency()
#cryptoCurrency.auth()

