import requests
import json
import yaml
from collections import namedtuple
import copy
import pandas as pd
from datetime import datetime

import jwt
import uuid
import hashlib
from urllib.parse import urlencode

with open(r'backtest.cfg', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)

_last_auth_time = datetime.now()
_autoReAuth = False

default_headers = {
        }
#### 아래에 작성
class Stock:
    def __init__(self):
        self.default_headers = {
                "Content-Type": "application/json",
                "Accept": "text/plain",
                "charset": "UTF-8",
                'User-Agent': _cfg['my_agent']
            }
        self.app_token = None

    def getDefaultHeaders(self):
        return self.default_headers
        
    def auth(self):
        url = f'{_cfg[svr]}/oauth2/tokenP'
        headers = getDefaultHeaders()
        body = {
                "grant_type": "client_credentials",
                }
        body["appkey"] = _cfg['app_key']
        body["appsecret"] = _cfg['app_secret']
        response = requests.post(url, headers = headers, data = json.dumps(body))
        if response.status_code == 200:
            self.app_token = response.json()['access_token']
            print("app_token: ", app_token)
        else:
            print('Get Authentitation token fail!\nYou have to restart your app!')

stock = Stock()
stock.auth()


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
class CryptoCurrency():
    def auth(self):
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
        authorization_token = 'Bearer {}'.format(jwt_token)
        return authorization_token

cryptoCurrency = CryptoCurrency()
cryptoCurrency.auth()
