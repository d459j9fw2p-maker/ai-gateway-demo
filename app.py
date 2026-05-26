from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from litellm import completion
import sqlite3
from datetime import datetime
import re

app = FastAPI()

# =========================
# DB 초기화
# =========================

conn = sqlite3.connect("logs.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    model TEXT,
    prompt TEXT,
    result TEXT,
    created_at TEXT
)
""")

conn.commit()

# =========================
# 키워드 차단
# =========================

BLOCK_KEYWORDS = [
    "주민번호",
    "고객DB",
    "내부기밀",
    "source code",
    "비밀번호",
    "password"
]

# =========================
# Regex 기반 차단 정책
# =========================

BLOCK_PATTERNS = {

    # 주민등록번호
    "주민등록번호":
        r"\d{6}-\d{7}",

    # 이메일
    "이메일":
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",

    # 전화번호
    "전화번호":
        r"01[0-9]-\d{3,4}-\d{4}",

    # IP 주소
    "IP주소":
        r"\b(?:\d{1,3}\.){3}\d{1,3}\b",

    # SQL 문
    "SQL":
        r"SELECT\s+\*\s+FROM",

    # AWS Key
    "AWS Access Key":
        r"AKIA[0-9A-Z]{16}",

    # JWT
    "JWT":
        r"eyJ[a-zA-Z0-9_-]+\.",

    # Bearer Token
    "Bearer Token":
        r"Bearer\s+[A-Za-z0-9-_.]+",

    # Private Key
    "Private Key":
        r"BEGIN RSA PRIVATE KEY",

    # 카드번호
    "카드번호":
        r"\b(?:\d[ -]*?){13,16}\b"

}

# =========================
# 요청 모델
# =========================

class ChatRequest(BaseModel):
    user: str
    model: str
    prompt: str

# =========================
# Prompt 검사
# =========================

def validate_prompt(prompt):

    # 키워드 검사

    for keyword in BLOCK_KEYWORDS:

        if keyword.lower() in prompt.lower():

            return False, f"차단 키워드 탐지: {keyword}"

    # Regex 검사

    for name, pattern in BLOCK_PATTERNS.items():

        if re.search(pattern, prompt, re.IGNORECASE):

            return False, f"민감정보 탐지: {name}"

    return True, "ALLOW"

# =========================
# 로그 저장
# =========================

def save_log(user, model, prompt, result):

    cursor.execute("""
    INSERT INTO logs (
        user,
        model,
        prompt,
        result,
        created_at
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        user,
        model,
        prompt,
        result,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()

# =========================
# 메인 화면
# =========================

@app.get("/", response_class=HTMLResponse)
def home():

    return """
<!DOCTYPE html>
<html lang="ko">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>AI Gateway</title>

<style>

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    background: #212121;
    color: #ECECEC;
    font-family: Arial, sans-serif;
    height: 100vh;
    overflow: hidden;
}

.container {
    display: flex;
    height: 100vh;
}

/* 좌측 사이드바 */

.sidebar {
    width: 260px;
    background: #171717;
    border-right: 1px solid #2f2f2f;
    display: flex;
    flex-direction: column;
    padding: 12px;
    gap: 12px;
}

.logo {
    font-size: 22px;
    font-weight: bold;
    padding: 12px;
}

.new-chat {
    background: #2f2f2f;
    border: 1px solid #3f3f3f;
    color: white;
    padding: 14px;
    border-radius: 10px;
    cursor: pointer;
    font-size: 14px;
}

.menu-box {
    background: #202020;
    border-radius: 10px;
    padding: 14px;
}

.menu-title {
    font-size: 12px;
    color: #B4B4B4;
    margin-bottom: 10px;
}

input,
select {
    width: 100%;
    background: #2f2f2f;
    color: white;
    border: 1px solid #404040;
    border-radius: 8px;
    padding: 10px;
}

/* 메인 */

.main {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.chat-area {
    flex: 1;
    overflow-y: auto;
    padding: 40px 20px 140px 20px;
}

.welcome {
    text-align: center;
    margin-top: 140px;
    font-size: 42px;
    font-weight: bold;
    color: #FFFFFF;
}

.sub {
    text-align: center;
    margin-top: 10px;
    color: #B4B4B4;
    font-size: 16px;
}

.result-box {
    width: 80%;
    margin: 40px auto;
    line-height: 1.8;
    white-space: pre-wrap;
    font-size: 15px;
}

/* 하단 입력 */

.bottom {
    position: fixed;
    bottom: 0;
    left: 260px;
    right: 0;
    background: linear-gradient(to top, #212121 70%, transparent);
    padding: 24px;
    display: flex;
    justify-content: center;
}

.input-wrapper {
    width: 900px;
    background: #2F2F2F;
    border: 1px solid #404040;
    border-radius: 26px;
    padding: 16px;
}

textarea {
    width: 100%;
    min-height: 90px;
    max-height: 300px;
    resize: none;
    background: transparent;
    border: none;
    outline: none;
    color: white;
    font-size: 16px;
    line-height: 1.6;
}

.action-row {
    margin-top: 12px;
    display: flex;
    justify-content: flex-end;
}

.send-btn {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    border: none;
    background: white;
    color: black;
    cursor: pointer;
    font-size: 18px;
    font-weight: bold;
}

.footer {
    text-align: center;
    margin-top: 10px;
    color: #8f8f8f;
    font-size: 12px;
}

</style>

</head>

<body>

<div class="container">

    <!-- 좌측 사이드바 -->

    <div class="sidebar">

        <div class="logo">
            AI Gateway
        </div>
