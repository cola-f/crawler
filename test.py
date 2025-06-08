import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()
KIS_APP_KEY = os.getenv("KIS_APP_KEY")
KIS_APP_SECRET = os.getenv("KIS_APP_SECRET")
def getAccessToken():
    url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
    headers = {"content-type": "application/x-www-form-urlencoded"}
    print("KIS_APP_KEY: " + KIS_APP_KEY)
    print("KIS_APP_SECRET: " + KIS_APP_SECRET)
    body = {
        "grant_type": "client_credentials",
        "appkey": KIS_APP_KEY,
        "appsecret": KIS_APP_SECRET
    }
    res = requests.post(url, headers=headers, data=json.dumps(body))
    print("in getAccessToken(), res: " + str(res.json()))
    return res.json()["access_token"]

getAccessToken()
