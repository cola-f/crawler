import Upbit

client = Upbit()
resp = client.Candle.Candle_days(
    market='KRW-BTC'
)
print(resp['result'])
