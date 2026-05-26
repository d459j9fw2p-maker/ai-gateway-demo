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
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Styrene+A:wght@400;500&display=swap" rel="stylesheet">
<style>

  *, *::before, *::after {
    margin: 0; padding: 0; box-sizing: border-box;
  }

  :root {
    --bg: #1c1917;
    --sidebar-bg: #141413;
    --surface: #242320;
    --surface-hover: #2c2b28;
    --border: rgba(255,255,255,0.08);
    --text-primary: #f5f0e8;
    --text-secondary: #a09a8e;
    --text-muted: #6b6560;
    --accent: #d4a574;
    --accent-hover: #e0b585;
    --input-bg: #242320;
    --btn-bg: #d4a574;
    --btn-hover: #e0b585;
    --user-bubble: #2c2b28;
    --ai-bubble: transparent;
    --scrollbar: #3a3733;
    --danger: #e07070;
  }

  body {
    background: var(--bg);
    color: var(--text-primary);
    font-family: 'Georgia', 'Times New Roman', serif;
    height: 100vh;
    overflow: hidden;
    display: flex;
  }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--scrollbar); border-radius: 4px; }

  /* ══════════════════════════
     SIDEBAR
  ══════════════════════════ */
  .sidebar {
    width: 260px;
    min-width: 260px;
    background: var(--sidebar-bg);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    padding: 0;
    overflow: hidden;
  }

  .sidebar-header {
    padding: 18px 16px 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid var(--border);
  }

  .logo-icon {
    width: 32px; height: 32px;
    background: linear-gradient(135deg, #d4a574 0%, #c4855a 100%);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; font-weight: bold; color: white;
    flex-shrink: 0;
  }

  .logo-text {
    font-size: 15px;
    font-weight: 500;
    color: var(--text-primary);
    letter-spacing: 0.01em;
    font-family: 'Georgia', serif;
  }

  .sidebar-content {
    flex: 1;
    overflow-y: auto;
    padding: 12px 8px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .new-chat-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 12px;
    border-radius: 8px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-size: 13.5px;
    cursor: pointer;
    width: 100%;
    text-align: left;
    transition: background 0.15s, color 0.15s;
    font-family: 'Georgia', serif;
    margin-bottom: 4px;
  }

  .new-chat-btn:hover {
    background: var(--surface-hover);
    color: var(--text-primary);
  }

  .new-chat-btn svg { opacity: 0.7; flex-shrink: 0; }

  .section-label {
    font-size: 11px;
    font-weight: 500;
    color: var(--text-muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 10px 12px 6px;
    font-family: sans-serif;
  }

  .settings-block {
    padding: 6px 8px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .field-label {
    font-size: 11.5px;
    color: var(--text-muted);
    margin-bottom: 4px;
    font-family: sans-serif;
  }

  .field-wrap {
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding: 2px 4px;
  }

  input.sidebar-input, select.sidebar-select {
    width: 100%;
    background: var(--surface);
    color: var(--text-primary);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 13px;
    outline: none;
    transition: border-color 0.15s;
    font-family: sans-serif;
  }

  input.sidebar-input:focus, select.sidebar-select:focus {
    border-color: var(--accent);
  }

  select.sidebar-select option { background: #242320; }

  .divider {
    height: 1px;
    background: var(--border);
    margin: 8px 12px;
  }

  .sidebar-footer {
    padding: 12px 16px;
    border-top: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .avatar {
    width: 30px; height: 30px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6b8cba, #9b6b9b);
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; color: white; font-weight: bold;
    flex-shrink: 0; font-family: sans-serif;
  }

  .avatar-name {
    font-size: 13px;
    color: var(--text-secondary);
    font-family: sans-serif;
  }

  /* ══════════════════════════
     MAIN AREA
  ══════════════════════════ */
  .main {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    position: relative;
    background: var(--bg);
  }

  /* top bar */
  .topbar {
    height: 52px;
    display: flex;
    align-items: center;
    padding: 0 24px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
    gap: 8px;
  }

  .model-pill {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    font-size: 13px;
    color: var(--text-secondary);
    cursor: default;
    font-family: sans-serif;
  }

  .model-pill span { color: var(--text-primary); font-weight: 500; }

  /* chat area */
  .chat-area {
    flex: 1;
    overflow-y: auto;
    padding: 0 0 160px;
  }

  /* welcome */
  .welcome-screen {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 40px 24px;
    gap: 8px;
    animation: fadeUp 0.5s ease both;
  }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .welcome-logo {
    width: 52px; height: 52px;
    background: linear-gradient(135deg, #d4a574 0%, #c4855a 100%);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; color: white; font-weight: bold;
    margin-bottom: 12px;
  }

  .welcome-title {
    font-size: 30px;
    font-weight: 400;
    color: var(--text-primary);
    letter-spacing: -0.02em;
    text-align: center;
  }

  .welcome-sub {
    font-size: 15px;
    color: var(--text-muted);
    text-align: center;
    font-family: sans-serif;
  }

  /* messages */
  .messages {
    display: flex;
    flex-direction: column;
    max-width: 740px;
    margin: 0 auto;
    padding: 32px 24px 0;
    gap: 0;
  }

  .msg {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 20px 0;
    border-bottom: 1px solid var(--border);
    animation: fadeUp 0.3s ease both;
  }

  .msg:last-child { border-bottom: none; }

  .msg-role {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-muted);
    font-family: sans-serif;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .msg-role-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
  }

  .msg.user .msg-role-dot { background: #6b8cba; }

  .msg-body {
    font-size: 15px;
    line-height: 1.75;
    color: var(--text-primary);
    white-space: pre-wrap;
    word-break: break-word;
    padding-left: 14px;
    font-family: sans-serif;
  }

  .msg.user .msg-body {
    color: var(--text-primary);
  }

  .msg.blocked .msg-body { color: var(--danger); }
  .msg.error   .msg-body { color: var(--danger); }

  .status-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: sans-serif;
    font-weight: 500;
    letter-spacing: 0.04em;
  }

  .status-tag.blocked { background: rgba(224,112,112,0.12); color: var(--danger); border: 1px solid rgba(224,112,112,0.25); }
  .status-tag.error   { background: rgba(224,112,112,0.12); color: var(--danger); border: 1px solid rgba(224,112,112,0.25); }
  .status-tag.ok      { background: rgba(212,165,116,0.1);  color: var(--accent);  border: 1px solid rgba(212,165,116,0.2); }

  /* thinking */
  .thinking {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--text-muted);
    font-size: 13px;
    font-family: sans-serif;
    padding: 16px 24px;
    max-width: 740px;
    margin: 0 auto;
    width: 100%;
    animation: fadeUp 0.3s ease both;
  }

  .thinking-dots {
    display: flex; gap: 4px;
  }

  .thinking-dots span {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
    animation: blink 1.2s infinite;
  }

  .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
  .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }

  @keyframes blink {
    0%, 80%, 100% { opacity: 0.2; }
    40% { opacity: 1; }
  }

  /* ══════════════════════════
     BOTTOM INPUT
  ══════════════════════════ */
  .bottom-area {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    background: linear-gradient(to top, var(--bg) 72%, transparent);
    padding: 16px 24px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }

  .input-container {
    width: 100%;
    max-width: 740px;
    background: var(--input-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 14px 16px 10px;
    transition: border-color 0.2s, box-shadow 0.2s;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
  }

  .input-container:focus-within {
    border-color: rgba(212,165,116,0.4);
    box-shadow: 0 4px 32px rgba(0,0,0,0.4), 0 0 0 1px rgba(212,165,116,0.1);
  }

  textarea#prompt {
    width: 100%;
    min-height: 56px;
    max-height: 240px;
    resize: none;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text-primary);
    font-size: 15px;
    line-height: 1.6;
    font-family: sans-serif;
    caret-color: var(--accent);
  }

  textarea#prompt::placeholder { color: var(--text-muted); }

  .input-actions {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 8px;
  }

  .input-hints {
    display: flex;
    gap: 6px;
  }

  .hint-chip {
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid var(--border);
    font-size: 12px;
    color: var(--text-muted);
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
    font-family: sans-serif;
  }

  .hint-chip:hover { background: var(--surface-hover); color: var(--text-secondary); }

  .send-btn {
    width: 36px; height: 36px;
    border-radius: 10px;
    border: none;
    background: var(--btn-bg);
    color: #1c1917;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.15s, transform 0.1s, opacity 0.15s;
    flex-shrink: 0;
  }

  .send-btn:hover { background: var(--btn-hover); }
  .send-btn:active { transform: scale(0.94); }
  .send-btn:disabled { opacity: 0.35; cursor: not-allowed; }

  .send-btn svg { width: 16px; height: 16px; }

  .bottom-note {
    font-size: 11.5px;
    color: var(--text-muted);
    font-family: sans-serif;
    text-align: center;
  }

</style>
</head>
<body>

<!-- ═══════════ SIDEBAR ═══════════ -->
<div class="sidebar">

  <div class="sidebar-header">
    <div class="logo-icon">G</div>
    <span class="logo-text">AI Gateway</span>
  </div>

  <div class="sidebar-content">

    <button class="new-chat-btn" onclick="clearChat()">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 5v14M5 12h14"/>
      </svg>
      새 대화
    </button>

    <div class="divider"></div>

    <div class="section-label">설정</div>

    <div class="settings-block">
      <div class="field-wrap">
        <div class="field-label">사용자</div>
        <input class="sidebar-input" id="user" value="testuser">
      </div>
      <div class="field-wrap">
        <div class="field-label">모델</div>
        <select class="sidebar-select" id="model" onchange="updateModelPill()">
          <option value="gpt-4o-mini">ChatGPT (GPT-4o mini)</option>
          <option value="gemini/gemini-2.0-flash-exp">Gemini 2.0 Flash</option>
        </select>
      </div>
    </div>

    <div class="divider"></div>

    <div class="section-label">보안</div>
    <div style="padding: 6px 12px;">
      <div style="font-size: 12px; color: var(--text-muted); font-family: sans-serif; line-height: 1.6;">
        ✦ 프롬프트 필터링 활성화<br>
        ✦ 전체 대화 로깅 중
      </div>
    </div>

  </div>

  <div class="sidebar-footer">
    <div class="avatar" id="avatarEl">T</div>
    <span class="avatar-name" id="avatarName">testuser</span>
  </div>

</div>

<!-- ═══════════ MAIN ═══════════ -->
<div class="main">

  <!-- topbar -->
  <div class="topbar">
    <div class="model-pill">
      모델&nbsp;
      <span id="modelPillText">ChatGPT (GPT-4o mini)</span>
    </div>
  </div>

  <!-- chat -->
  <div class="chat-area" id="chatArea">
    <div class="welcome-screen" id="welcomeScreen">
      <div class="welcome-logo">G</div>
      <div class="welcome-title">무엇을 도와드릴까요?</div>
      <div class="welcome-sub">Secure Enterprise AI Gateway · Prompt Filtering Enabled</div>
    </div>
    <div class="messages" id="messages" style="display:none;"></div>
  </div>

  <!-- bottom input -->
  <div class="bottom-area">
    <div class="input-container">
      <textarea id="prompt" placeholder="메시지를 입력하세요…" rows="1"></textarea>
      <div class="input-actions">
        <div class="input-hints">
          <div class="hint-chip">요약해줘</div>
          <div class="hint-chip">번역해줘</div>
          <div class="hint-chip">코드 작성</div>
        </div>
        <button class="send-btn" id="sendBtn" title="전송 (Enter)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="19" x2="12" y2="5"/>
            <polyline points="5 12 12 5 19 12"/>
          </svg>
        </button>
      </div>
    </div>
    <div class="bottom-note">AI Gateway PoC · 응답은 참고용이며 중요한 결정에 단독 사용하지 마세요</div>
  </div>

</div>

<script>
  const textarea   = document.getElementById('prompt');
  const sendBtn    = document.getElementById('sendBtn');
  const messagesEl = document.getElementById('messages');
  const welcomeEl  = document.getElementById('welcomeScreen');
  const chatArea   = document.getElementById('chatArea');
  const modelSel   = document.getElementById('model');
  const userInput  = document.getElementById('user');

  let isLoading = false;

  // ── auto-resize textarea ──
  textarea.addEventListener('input', () => {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 240) + 'px';
  });

  // ── Enter to send (Shift+Enter = newline) ──
  textarea.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  sendBtn.addEventListener('click', sendMessage);

  // ── hint chips ──
  document.querySelectorAll('.hint-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      textarea.value = chip.textContent.trim();
      textarea.dispatchEvent(new Event('input'));
      textarea.focus();
    });
  });

  // ── model pill ──
  function updateModelPill() {
    const opt = modelSel.options[modelSel.selectedIndex];
    document.getElementById('modelPillText').textContent = opt.text;
  }

  // ── avatar update ──
  userInput.addEventListener('input', () => {
    const v = userInput.value.trim() || '?';
    document.getElementById('avatarEl').textContent   = v[0].toUpperCase();
    document.getElementById('avatarName').textContent = v;
  });

  // ── add message bubble ──
  function addMessage(role, text, status) {
    welcomeEl.style.display  = 'none';
    messagesEl.style.display = 'flex';

    const div = document.createElement('div');
    div.className = 'msg ' + role;
    if (status === 'blocked') div.classList.add('blocked');
    if (status === 'error')   div.classList.add('error');

    const roleLabel = role === 'user' ? '사용자' : 'AI Gateway';
    const dotColor  = role === 'user' ? '#6b8cba' : 'var(--accent)';

    let statusTag = '';
    if (status === 'blocked') statusTag = '<span class="status-tag blocked">⊘ 차단됨</span>';
    else if (status === 'error') statusTag = '<span class="status-tag error">⚠ 오류</span>';
    else if (status === 'ok' && role === 'assistant') statusTag = '<span class="status-tag ok">✓ 허용</span>';

    div.innerHTML = `
      <div class="msg-role">
        <div class="msg-role-dot" style="background:${dotColor}"></div>
        ${roleLabel}
        ${statusTag}
      </div>
      <div class="msg-body">${escHtml(text)}</div>
    `;

    messagesEl.appendChild(div);
    chatArea.scrollTop = chatArea.scrollHeight;
    return div;
  }

  // ── thinking indicator ──
  let thinkingEl = null;
  function showThinking() {
    thinkingEl = document.createElement('div');
    thinkingEl.className = 'thinking';
    thinkingEl.innerHTML = `
      <div class="thinking-dots">
        <span></span><span></span><span></span>
      </div>
      응답 생성 중…
    `;
    messagesEl.parentElement.appendChild(thinkingEl);
    chatArea.scrollTop = chatArea.scrollHeight;
  }

  function hideThinking() {
    if (thinkingEl) { thinkingEl.remove(); thinkingEl = null; }
  }

  // ── escape html ──
  function escHtml(str) {
    return str
      .replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

  // ── clear chat ──
  function clearChat() {
    messagesEl.innerHTML = '';
    messagesEl.style.display = 'none';
    welcomeEl.style.display  = 'flex';
  }

  // ── main send ──
  async function sendMessage() {
    if (isLoading) return;
    const prompt = textarea.value.trim();
    if (!prompt) return;

    isLoading = true;
    sendBtn.disabled = true;

    addMessage('user', prompt, null);
    textarea.value = '';
    textarea.style.height = 'auto';

    welcomeEl.style.display  = 'none';
    messagesEl.style.display = 'flex';
    showThinking();

    try {
      const res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user:   userInput.value || 'testuser',
          model:  modelSel.value,
          prompt: prompt
        })
      });

      const data = await res.json();
      hideThinking();

      addMessage('assistant', data.response || '응답 없음', data.status);

    } catch (err) {
      hideThinking();
      addMessage('assistant', 'JavaScript 오류: ' + err.message, 'error');
    } finally {
      isLoading = false;
      sendBtn.disabled = false;
    }
  }
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
            "response": "보안정책 위반: 허용되지 않는 키워드가 포함되어 있습니다."
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
