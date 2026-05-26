```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from litellm import completion
import sqlite3
from datetime import datetime

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

.new-chat:hover {
    background: #3a3a3a;
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

.send-btn:hover {
    opacity: 0.9;
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

        <button class="new-chat">
            + New Chat
        </button>

        <div class="menu-box">

            <div class="menu-title">
                사용자
            </div>

            <input id="user" value="testuser">

        </div>

        <div class="menu-box">

            <div class="menu-title">
                모델 선택
            </div>

            <select id="model">

                <option value="gpt-4o-mini">
                    ChatGPT
                </option>

                <option value="gemini/gemini-2.0-flash-exp">
                    Gemini
                </option>

            </select>

        </div>

    </div>

    <!-- 메인 -->

    <div class="main">

        <div class="chat-area">

            <div class="welcome">
                무엇을 도와드릴까요?
            </div>

            <div class="sub">
                Secure Enterprise AI Gateway
            </div>

            <div class="result-box" id="result">
            </div>

        </div>

    </div>

</div>

<!-- 하단 입력창 -->

<div class="bottom">

    <div>

        <div class="input-wrapper">

            <textarea
                id="prompt"
                placeholder="메시지를 입력하세요"
            ></textarea>

            <div class="action-row">

                <button
                    class="send-btn"
                    id="sendBtn"
                >
                    ↑
                </button>

            </div>

        </div>

        <div class="footer">
            AI Gateway PoC · Prompt Filtering Enabled
        </div>

    </div>

</div>

<script>

const textarea = document.getElementById("prompt")

textarea.addEventListener("input", () => {

    textarea.style.height = "auto"
    textarea.style.height = textarea.scrollHeight + "px"

})


document.getElementById("sendBtn").addEventListener("click", async function() {

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

            resultBox.innerHTML =
                "<div style='color:#ff6b6b;'>[차단]</div><br>" + result.response

        }
        else if(result.status === "error") {

            resultBox.innerHTML =
                "<div style='color:#ff6b6b;'>[에러]</div><br>" + result.response

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
```
