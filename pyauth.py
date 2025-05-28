from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
import pymysql
import json
import time

app = FastAPI()

# MySQL 연결 설정
db_config = {
    'host': 'localhost',
    'user': 'your_user',
    'password': 'your_pass',
    'db': 'your_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 세션 쿠키 이름 (express-session 설정과 일치해야 함)
SESSION_COOKIE_NAME = 'session_cookie_name'

def get_session_data(session_id: str):
    """세션 ID로부터 DB에서 세션 정보 조회"""
    conn = pymysql.connect(**db_config)
    try:
        with conn.cursor() as cursor:
            sql = "SELECT data, expires FROM sessions WHERE session_id = %s"
            cursor.execute(sql, (session_id,))
            result = cursor.fetchone()
            if not result:
                return None
            if result['expires'] < int(time.time()):
                return None  # 세션 만료
            return json.loads(result['data'])
    finally:
        conn.close()

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = get_session_data(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    user = session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="No user info in session")

    username = user.get("username", "Guest")
    return f"<h1>Welcome, {username}!</h1>"

