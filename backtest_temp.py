from datetime import datetime, timedelta
import mojito

mojito.__version__

f = open("../cert/koreainvestment.key")
lines = f.readlines()
key = line[0].strip()
secret = line[1].strip()
acc_no = line[2].strip()
f.close()

broker = mojito.KoreaInvestment(
        api_key=key,
        api_secret=secret,
        acc_no=acc_no,
        mock=True
        )
brocker.fetch_price("005930")['output']['stck_oprc'] # 시가
brocker.fetch_price("005930")['output']['stck_hgpr'] # 고가
brocker.fetch_price("005930")['output']['stck_lwpr'] # 저가
brocker.fetch_price("005930")['output']['stck_prpr'] # 종

start = '2020-1-1'
end = '2023-1-1'
start = datetime.strptime(start, '%y-%m-%d')
end = datetime.strptime(end, '%y-%m-%d')

account = {}
ratio = {}

def price(code, date):
    while !: # 가격이 없으면
        next

def next(date):

while date <= end:
    total = 0
    for ueouo: # total 값을 계산
        total +=
    
    if Account.volume*price(code, date)-total*ratio.code > price(code, date):
        sell()
    elif Account.volume*price(code, date)-total*ratio.code < price(code, date):
        buy()

    date = next(date, )
