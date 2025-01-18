import requests
import json
import yaml
from collections import namedtuple
import copy
import pandas as pd
from datetime import datetime, timedelta

import jwt
import uuid
import hashlib
from urllib.parse import urlencode
import dotenv
import os

dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)

with open(r'backtest.cfg', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)

import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
ID_db = os.getenv('ID_mariadb')
PW_db = os.getenv('PW_mariadb')
host_db = os.getenv('host_mariadb')
port_db = os.getenv('port_mariadb')
name_db = os.getenv('name_mariadb')
engine = create_engine("mysql+pymysql://" + ID_db + ":" + PW_db + "@" + host_db + ":" + port_db + "/" + name_db, pool_size=5, max_overflow=5, echo=True)

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

Base = declarative_base()

class Authorization(Base):
    __tablename__ = 'authorization'
    access_token = Column(String, primary_key=True)
    expiration = Column(DateTime)


Session = sessionmaker(bind=engine)
session = Session()

results = session.query(Authorization).filter().first()
print("results: ", str(results))

default_headers = {
        }
#### 아래에 작성
class Stock:
    def __init__(self):
        self.default_headers = {
                "Content-Type": "application/json",
                "Accept": "text/plain",
                "charset": "UTF-8",
                "User-Agent": _cfg['my_agent'],
                "appkey": os.getenv('app_key'),
                "appsecret": os.getenv('app_secret'),
            }
        self.access_token = None

    def getDefaultHeaders(self):
        return self.default_headers
        
    def auth(self):
        authorization = session.query(Authorization).filter().first()
        if authorization == None or (datetime.now() - authorization.expiration)>timedelta(days=1):
            url = f'{_cfg["prod"]}/oauth2/tokenP'
            headers = self.getDefaultHeaders()
            body = {
                    "grant_type": "client_credentials",
                        }
            body["appkey"] = os.getenv('app_key')
            body["appsecret"] = os.getenv('app_secret')
            response = requests.post(url, headers = headers, data = json.dumps(body), verify = True)
            print("response: ", response.text)
            if response.status_code == 200:
                self.access_token = response.json()['access_token']
                print("access_token: ", self.access_token)
                self.expiration = response.json()['access_token_token_expired']
                authorization = Authorization(access_token = self.access_token, expiration=self.expiration)
                session.add(authorization)
                session.commit()
            else:
                print('Get Authentitation token fail!\nYou have to restart your app!')

        else:
            self.access_token = authorization.access_token

    def getDailyPrice(self, stock_no, start, end):
        url = f'{_cfg["prod"]}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice'
        headers = self.getDefaultHeaders()
        headers["authorization"] = f'Bearer {self.access_token}'
        print("authorization: ", headers["authorization"])
        headers["tr_id"] = "FHKST03010100"
        headers["custtype"]= "P"

        params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": stock_no,
                "FID_INPUT_DATE_1": start,
                "FID_INPUT_DATE_2": end,
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": 1,
        }
        response = requests.get(url, headers = headers, params = params, verify = True)
        print("response: ", response.text)

stock = Stock()
stock.auth()
stock.getDailyPrice("04020000", "20230930", "20230930")

class CryptoCurrency():
    def __init__(self):
        self.default_headers = {
                "accept": "application/json",
            }
        self.authorization_token = None
    def getDefaultHeaders(self):
        return self.default_headers
    def auth(self):
        # auth 는 미완성입니다. 안만들어도 조회는 되니까.
        m = hashlib.sha512()
        m.update(urlencode(query).encode())
        query_hash = m.hexdigest()

        payload = {
                'access_key': 'Acess_key',
                'nonce': str(uuid.uuid4()),
                'query_hash': query_hash,
                'query_hash_alg': 'SHA512',
                }
        jwt_token = jwt.encode(payload, 'Secret_key')
        self.authorization_token = 'Bearer {}'.format(jwt_token)

    def getDailyPrice(self, item, datetime):
        url = f'{_cfg["host_upbit"]}/v1/candles/days'
        headers = self.getDefaultHeaders()
        params = {
                "market": item,
                "to": datetime,
                "count": "1",
                "convertingPriceUnit": "KRW",
        }
        response = requests.get(url, headers = headers, params = params)
        print(response.text)

cryptoCurrency = CryptoCurrency()
cryptoCurrency.getDailyPrice("KRW-BTC", "2023-10-27 09:00:00")
