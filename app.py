from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from litellm import completion
import sqlite3
from datetime import datetime

app = FastAPI()

# =========================
# SQLite DB 초기화
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
# 차단 키워드
# =========================

BLOCK_KEYWORDS = [
    "주민번호",
    "고객DB",
    "내부기밀",
    "source code"
]

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

    for keyword in BLOCK_KEYWORDS:

        if keyword.lower() in prompt.lower():
            return False

    return True

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

# Gemini 스타일 AI Gateway UI

```python
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
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: white;
            height: 100vh;
            display: flex;
        }

        /* 좌측 사이드바 */

        .sidebar {
            width: 260px;
            background: #111827;
            border-right: 1px solid #1e293b;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #8b5cf6;
        }

        .new-chat {
            background: #1e293b;
            border: 1px solid #334155;
            color: white;
            padding: 12px;
            border-radius: 12px;
            cursor: pointer;
            transition: 0.2s;
        }

        .new-chat:hover {
            background: #334155;
        }

        .menu-box {
            background: #111827;
            border: 1px solid #1e293b;
            border-radius: 16px;
            padding: 16px;
        }

        .menu-title {
            font-size: 13px;
            color: #94a3b8;
            margin-bottom: 10px;
        }

        select,
        input {
            width: 100%;
            padding: 12px;
            border-radius: 12px;
            border: 1px solid #334155;
            background: #1e293b;
            color: white;
        }

        /* 메인 */

        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .top {
            padding: 30px;
            overflow-y: auto;
        }

        .welcome {
            font-size: 42px;
            font-weight: bold;
            margin-top: 120px;
            text-align: center;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .sub {
            text-align: center;
            margin-top: 14px;
            color: #94a3b8;
            font-size: 18px;
        }

        /* 결과창 */

        .result-box {
            margin: 40px auto;
            width: 80%;
            background: #111827;
            border: 1px solid #1e293b;
            border-radius: 20px;
            padding: 24px;
            min-height: 120px;
            white-space: pre-wrap;
            line-height: 1.7;
            font-size: 15px;
        }

        /* 하단 입력창 */

        .bottom {
            padding: 20px;
            display: flex;
            justify-content: center;
        }

        .input-box {
            width: 80%;
            background: #111827;
            border: 1px solid #334155;
            border-radius: 24px;
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        textarea {
            width: 100%;
            min-height: 120px;
            resize: none;
            border: none;
            outline: none;
            background: transparent;
            color: white;
            font-size: 16px;
        }

        .send-row {
            display: flex;
            justify-content: flex-end;
        }

        button {
            background: linear-gradient(to right, #6366f1, #8b5cf6);
            border: none;
            color: white;
            padding: 12px 24px;
            border-radius: 14px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: 0.2s;
        }

        button:hover {
            opacity: 0.9;
            transform: translateY(-1px);
        }

    </style>
</head>

<body>

    <!-- 사이드바 -->

    <div class="sidebar">

        <div class="logo">
            ✨ AI Gateway
        </div>

        <button class="new-chat">
            + 새 대화
        </button>

        <div class="menu-box">

            <div class="menu-title">
                사용자
            </div>

            <input id="user" value="testuser">

        </div>

        <div class="menu-box">

            <div class="menu-title">
                AI 모델
            </div>

            <select id="model">

                <option value="gpt-4o-mini">
                    ChatGPT
                </option>

                <option value="gemini/gemini-1.5-flash">
                    Gemini
                </option>

            </select>

        </div>

    </div>

    <!-- 메인 -->

    <div class="main">

        <div class="top">

            <div class="welcome">
                AI Gateway
            </div>

            <div class="sub">
                Secure Enterprise Generative AI Portal
            </div>

            <div class="result-box" id="result">
                AI 응답 결과가 여기에 표시됩니다.
            </div>

        </div>

        <!-- 입력창 -->

        <div class="bottom">

            <div class="input-box">

                <textarea
                    id="prompt"
                    placeholder="프롬프트를 입력하세요..."
                ></textarea>

                <div class="send-row">
                    <button id="sendBtn">
                        전송
                    </button>
                </div>

            </div>

        </div>

    </div>

<script>

document.getElementById("sendBtn").addEventListener("click", async () => {

    const resultBox = document.getElementById("result")

    resultBox.innerText = "처리중..."

    try {

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

        console.log(result)

        if(result.status === "blocked") {

            resultBox.innerText =
                "[차단]\n\n" + result.response

        }
        else if(result.status === "error") {

            resultBox.innerText =
                "[에러]\n\n" + result.response

        }
        else {

            resultBox.innerText =
                result.response || "응답 없음"

        }

    }
    catch(err) {

        console.log(err)

        resultBox.innerText =
            "JavaScript 오류: " + err

    }

})

</script>

</body>
</html>
    """
# =========================
# Chat API
# =========================

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
            "response": "보안정책 위반"
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

        print("FULL RESPONSE:")
        print(response)

        answer = response.choices[0].message.content

        if answer is None:
            answer = "응답 없음"

        save_log(
            req.user,
            req.model,
            req.prompt,
            "ALLOW"
        )

        return {
            "status": "ok",
            "response": str(answer)
        }

    except Exception as e:

        print("ERROR:")
        print(str(e))

        return {
            "status": "error",
            "response": str(e)
        }
