from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime
import asyncio
from invest import Invest  # 위 코드를 invest_module.py로 저장

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS 허용
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

invest = Invest(10000000)
clients = set()

class DateRange(BaseModel):
    start_dt: str
    end_dt: str

@app.get("/")
async def get():
    return HTMLResponse(open("static/index.html", encoding="utf-8").read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # 계속 연결 유지
    except WebSocketDisconnect:
        clients.remove(websocket)

async def broadcast(msg: str):
    for client in clients.copy():
        try:
            await client.send_text(msg)
        except:
            clients.remove(client)

def parse_date(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

@app.post("/load")
async def load(request: DateRange):
    await broadcast("📂 데이터 로드 중...")
    invest.load("./price.xlsx")
    await broadcast("✅ 로드 완료")

@app.post("/ohlcv")
async def ohlcv(request: DateRange):
    start = parse_date(request.start_dt)
    end = parse_date(request.end_dt)
    await broadcast("📈 OHLCV 수집 시작")
    await asyncio.to_thread(invest.getOhlcv, start, end)
    await broadcast("✅ OHLCV 수집 완료")

@app.post("/backtest")
async def backtest(request: DateRange):
    start = parse_date(request.start_dt)
    end = parse_date(request.end_dt)
    await broadcast("📊 백테스트 시작")
    await asyncio.to_thread(invest.backtest, start, end)
    await broadcast("✅ 백테스트 완료")

