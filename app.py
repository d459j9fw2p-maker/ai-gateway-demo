from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from litellm import completion
import sqlite3
from datetime import datetime

app = FastAPI()

# DB 생성
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

# 차단 키워드
BLOCK_KEYWORDS = [
    "주민번호",
    "고객DB",
    "내부기밀",
    "source code"
]

# 요청 구조
class ChatRequest(BaseModel):
    user: str
    model: str
    prompt: str

# Prompt 검사
def validate_prompt(prompt):
    for keyword in BLOCK_KEYWORDS:
        if keyword.lower() in prompt.lower():
            return False
    return True

# 로그 저장
def save_log(user, model, prompt, result):
    cursor.execute("""
    INSERT INTO logs (user, model, prompt, result, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (
        user,
        model,
        prompt,
        result,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()

# 메인 페이지
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>AI Gateway</title>
    </head>
    <body style="font-family:Arial; margin:40px;">
        <h2>사내 AI Gateway</h2>

        <label>사용자</label><br>
        <input id="user" value="testuser"/><br><br>

        <label>모델</label><br>
        <select id="model">
            <option value="gpt-4o-mini">GPT-4o-mini</option>
            <option value="claude-3-5-sonnet-20241022">Claude</option>
            <option value="gemini/gemini-1.5-pro">Gemini</option>
        </select><br><br>

        <label>프롬프트</label><br>
        <textarea id="prompt" rows="10" cols="80"></textarea><br><br>

        <button onclick="send()">전송</button>

        <h3>결과</h3>
        <pre id="result"></pre>

        <script>
        async function send() {

            document.getElementById("result").innerText = "처리중..."

            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    user: document.getElementById("user").value,
                    model: document.getElementById("model").value,
                    prompt: document.getElementById("prompt").value
                })
            })

            const result = await response.json()

            if(result.status == "blocked") {
                document.getElementById("result").innerText =
                    "[차단]\\n" + result.reason
            }
            else {
                document.getElementById("result").innerText =
                    result.response
            }
        }
        </script>
    </body>
    </html>
    """

# 채팅 API
@app.post("/chat")
def chat(req: ChatRequest):

    # Prompt 차단
    if not validate_prompt(req.prompt):

        save_log(
            req.user,
            req.model,
            req.prompt,
            "BLOCK"
        )

        return {
            "status": "blocked",
            "reason": "보안정책 위반"
        }

    try:

        response = completion(
            model=req.model,
            messages=[
                {
                    "role": "user",
                    "content": req.prompt
                }
            ]
        )

        answer = response["choices"][0]["message"]["content"]

        save_log(
            req.user,
            req.model,
            req.prompt,
            "ALLOW"
        )

        return {
            "status": "ok",
            "response": answer
        }

    except Exception as e:

        return {
            "status": "error",
            "reason": str(e)
        }