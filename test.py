import pandas
import datetime

start = "2024-12-1 00:00:00"

start_dt = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
print(start_dt)
