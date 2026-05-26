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
    INSERT INTO logs (user, model, prompt, result, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (user, model, prompt, result,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()


# =========================
# 메인 화면 (모바일 최적화)
# =========================

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>AI Gateway</title>
<style>

*, *::before, *::after {
  margin: 0; padding: 0; box-sizing: border-box;
  -webkit-tap-highlight-color: transparent;
}

:root {
  --bg:           #1a1917;
  --surface:      #242220;
  --surface2:     #2e2c29;
  --border:       rgba(255,255,255,0.07);
  --border2:      rgba(255,255,255,0.12);
  --text:         #f0ebe3;
  --text2:        #9e9890;
  --text3:        #5e5a55;
  --accent:       #d4a472;
  --accent2:      #c4925e;
  --danger:       #e07575;
  --safe:         #72c472;
  --drawer-bg:    #141412;
  --overlay:      rgba(0,0,0,0.6);
  --radius:       16px;
  --radius-sm:    10px;
  --radius-xs:    7px;
  --safe-bottom:  env(safe-area-inset-bottom, 0px);
  --safe-top:     env(safe-area-inset-top, 0px);
}

html, body {
  height: 100%; width: 100%;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, 'SF Pro Text', 'Helvetica Neue', sans-serif;
  overflow: hidden;
  position: fixed;
}

/* ────────────────────────────
   LAYOUT SHELL
──────────────────────────── */
.app {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

/* ────────────────────────────
   TOP NAV BAR
──────────────────────────── */
.nav {
  flex-shrink: 0;
  height: calc(52px + var(--safe-top));
  padding-top: var(--safe-top);
  background: rgba(26,25,23,0.92);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding-left: 6px;
  padding-right: 12px;
  gap: 8px;
  position: relative;
  z-index: 10;
}

.nav-btn {
  width: 40px; height: 40px;
  border-radius: 10px;
  border: none;
  background: transparent;
  color: var(--text2);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s;
}

.nav-btn:active { background: var(--surface); }

.nav-btn svg { width: 20px; height: 20px; }

.nav-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
}

.nav-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.01em;
}

.nav-subtitle {
  font-size: 11px;
  color: var(--text3);
  letter-spacing: 0.01em;
}

.nav-model-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: 20px;
  font-size: 12px;
  color: var(--text2);
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}

.nav-model-btn:active { background: var(--surface2); }
.nav-model-btn svg { width: 12px; height: 12px; opacity: 0.6; }

/* ────────────────────────────
   CHAT AREA
──────────────────────────── */
.chat-scroll {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  padding-bottom: 16px;
}

/* welcome screen */
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  padding: 48px 32px 100px;
  gap: 10px;
  animation: fadeUp 0.45s ease both;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0);    }
}

.welcome-icon {
  width: 56px; height: 56px;
  background: linear-gradient(145deg, #d4a472 0%, #b87040 100%);
  border-radius: 18px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 8px;
  box-shadow: 0 8px 32px rgba(212,164,114,0.25);
}

.welcome-icon svg { width: 28px; height: 28px; color: white; }

.welcome-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.03em;
  text-align: center;
}

.welcome-desc {
  font-size: 14px;
  color: var(--text3);
  text-align: center;
  line-height: 1.5;
}

.suggestion-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 16px;
}

.pill {
  padding: 8px 14px;
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: 20px;
  font-size: 13px;
  color: var(--text2);
  cursor: pointer;
  transition: background 0.15s, color 0.15s, transform 0.1s;
  user-select: none;
}

.pill:active { background: var(--surface2); color: var(--text); transform: scale(0.96); }

/* messages */
.messages {
  display: flex;
  flex-direction: column;
  padding: 16px 0 8px;
}

.msg-group {
  padding: 14px 16px 14px;
  border-bottom: 1px solid var(--border);
  animation: fadeUp 0.25s ease both;
}

.msg-group:last-child { border-bottom: none; }

.msg-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.msg-avatar {
  width: 26px; height: 26px;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px;
  font-weight: 700;
  flex-shrink: 0;
}

.msg-avatar.user-av {
  background: linear-gradient(135deg, #5b7fa6, #7b5fa6);
  color: white;
}

.msg-avatar.ai-av {
  background: linear-gradient(135deg, #d4a472, #b87040);
  color: white;
}

.msg-name {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text2);
  flex: 1;
}

.status-badge {
  font-size: 10.5px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 5px;
  letter-spacing: 0.04em;
}

.status-badge.ok      { background: rgba(114,196,114,0.12); color: var(--safe);   border: 1px solid rgba(114,196,114,0.2); }
.status-badge.blocked { background: rgba(224,117,117,0.12); color: var(--danger); border: 1px solid rgba(224,117,117,0.2); }
.status-badge.error   { background: rgba(224,117,117,0.12); color: var(--danger); border: 1px solid rgba(224,117,117,0.2); }

.msg-body {
  font-size: 15px;
  line-height: 1.7;
  color: var(--text);
  white-space: pre-wrap;
  word-break: break-word;
  padding-left: 34px;
}

.msg-body.danger { color: var(--danger); }

/* thinking */
.thinking-row {
  padding: 14px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  animation: fadeUp 0.2s ease both;
}

.dots {
  display: flex; gap: 5px;
}

.dots span {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--accent);
  animation: pulse 1.2s infinite ease-in-out;
}

.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes pulse {
  0%, 80%, 100% { opacity: 0.15; transform: scale(0.85); }
  40%            { opacity: 1;    transform: scale(1);    }
}

.thinking-text {
  font-size: 13px;
  color: var(--text3);
}

/* ────────────────────────────
   BOTTOM INPUT BAR
──────────────────────────── */
.input-bar {
  flex-shrink: 0;
  background: rgba(26,25,23,0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid var(--border);
  padding: 10px 12px calc(10px + var(--safe-bottom));
}

.input-wrap {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: 22px;
  padding: 10px 10px 10px 16px;
  transition: border-color 0.2s;
}

.input-wrap:focus-within {
  border-color: rgba(212,164,114,0.45);
}

textarea#prompt {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text);
  font-size: 16px; /* 16px prevents iOS zoom */
  line-height: 1.5;
  resize: none;
  max-height: 120px;
  min-height: 24px;
  font-family: -apple-system, 'SF Pro Text', 'Helvetica Neue', sans-serif;
  caret-color: var(--accent);
  padding: 0;
}

textarea#prompt::placeholder { color: var(--text3); }

.send-btn {
  width: 34px; height: 34px;
  border-radius: 50%;
  border: none;
  background: var(--accent);
  color: #1a1917;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s, transform 0.1s, opacity 0.15s;
  align-self: flex-end;
}

.send-btn:active { transform: scale(0.9); background: var(--accent2); }
.send-btn:disabled { opacity: 0.3; }
.send-btn svg { width: 15px; height: 15px; }

/* ────────────────────────────
   DRAWER (slide-up settings)
──────────────────────────── */
.overlay {
  position: fixed; inset: 0;
  background: var(--overlay);
  z-index: 40;
  opacity: 0; pointer-events: none;
  transition: opacity 0.3s ease;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.overlay.open { opacity: 1; pointer-events: all; }

.drawer {
  position: fixed;
  left: 0; right: 0; bottom: 0;
  background: var(--drawer-bg);
  border-radius: 24px 24px 0 0;
  border-top: 1px solid var(--border2);
  z-index: 50;
  padding: 0 0 calc(24px + var(--safe-bottom));
  transform: translateY(100%);
  transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1);
  max-height: 85vh;
  overflow-y: auto;
}

.drawer.open { transform: translateY(0); }

.drawer-handle {
  width: 36px; height: 4px;
  background: var(--border2);
  border-radius: 2px;
  margin: 12px auto 0;
}

.drawer-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text);
  padding: 20px 20px 4px;
  letter-spacing: -0.02em;
}

.drawer-section {
  padding: 16px 20px 0;
}

.drawer-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text3);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.drawer-input {
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border2);
  border-radius: var(--radius-sm);
  padding: 13px 14px;
  color: var(--text);
  font-size: 16px;
  outline: none;
  font-family: -apple-system, sans-serif;
  transition: border-color 0.2s;
}

.drawer-input:focus { border-color: var(--accent); }

.model-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.model-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.model-item.selected {
  border-color: var(--accent);
  background: rgba(212,164,114,0.07);
}

.model-item:active { background: var(--surface2); }

.model-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  border: 2px solid var(--text3);
  flex-shrink: 0;
  transition: border-color 0.15s, background 0.15s;
}

.model-item.selected .model-dot {
  border-color: var(--accent);
  background: var(--accent);
}

.model-info { flex: 1; }
.model-name { font-size: 14px; font-weight: 600; color: var(--text); }
.model-desc { font-size: 12px; color: var(--text3); margin-top: 1px; }

.security-tags {
  display: flex; flex-wrap: wrap; gap: 6px;
}

.sec-tag {
  padding: 6px 12px;
  background: rgba(114,196,114,0.08);
  border: 1px solid rgba(114,196,114,0.15);
  border-radius: 20px;
  font-size: 12px;
  color: var(--safe);
}

.drawer-divider {
  height: 1px;
  background: var(--border);
  margin: 20px;
}

.clear-btn {
  width: calc(100% - 40px);
  margin: 0 20px;
  padding: 14px;
  background: rgba(224,117,117,0.08);
  border: 1px solid rgba(224,117,117,0.2);
  border-radius: var(--radius-sm);
  color: var(--danger);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
  font-family: -apple-system, sans-serif;
}

.clear-btn:active { background: rgba(224,117,117,0.16); }

/* ────────────────────────────
   MODEL PICKER (sheet)
──────────────────────────── */
.model-sheet {
  position: fixed;
  left: 0; right: 0; bottom: 0;
  background: var(--drawer-bg);
  border-radius: 24px 24px 0 0;
  border-top: 1px solid var(--border2);
  z-index: 60;
  padding-bottom: calc(20px + var(--safe-bottom));
  transform: translateY(100%);
  transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
}

.model-sheet.open { transform: translateY(0); }

.model-sheet .drawer-handle { margin-bottom: 4px; }
.model-sheet .drawer-title { padding-bottom: 12px; }

.model-sheet-list {
  padding: 0 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

</style>
</head>
<body>

<div class="app">

  <!-- ── TOP NAV ── -->
  <nav class="nav">
    <button class="nav-btn" id="menuBtn" aria-label="메뉴">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <line x1="3" y1="6"  x2="21" y2="6"/>
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>

    <div class="nav-center">
      <div class="nav-title">AI Gateway</div>
      <div class="nav-subtitle" id="navSub">보안 엔터프라이즈 AI</div>
    </div>

    <button class="nav-model-btn" id="modelPillBtn">
      <span id="modelPillLabel">ChatGPT</span>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </button>
  </nav>

  <!-- ── CHAT AREA ── -->
  <div class="chat-scroll" id="chatScroll">

    <!-- Welcome -->
    <div class="welcome" id="welcomeScreen">
      <div class="welcome-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
          <path d="M8 12h8M12 8v8"/>
        </svg>
      </div>
      <div class="welcome-title">무엇을 도와드릴까요?</div>
      <div class="welcome-desc">프롬프트 필터링이 적용된<br>보안 AI 게이트웨이입니다</div>
      <div class="suggestion-pills">
        <div class="pill" data-text="안녕하세요! 자기소개 해줘">👋 자기소개</div>
        <div class="pill" data-text="오늘 할 일 목록 만들어줘">📋 할 일 목록</div>
        <div class="pill" data-text="파이썬으로 간단한 계산기 코드 작성해줘">💻 코드 작성</div>
        <div class="pill" data-text="한국 역사에 대해 알려줘">📚 역사 질문</div>
      </div>
    </div>

    <!-- Messages -->
    <div class="messages" id="messages" style="display:none;"></div>

  </div>

  <!-- ── INPUT BAR ── -->
  <div class="input-bar">
    <div class="input-wrap">
      <textarea
        id="prompt"
        placeholder="메시지 입력…"
        rows="1"
      ></textarea>
      <button class="send-btn" id="sendBtn" disabled>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round">
          <line x1="12" y1="19" x2="12" y2="5"/>
          <polyline points="5 12 12 5 19 12"/>
        </svg>
      </button>
    </div>
  </div>

</div>

<!-- ── OVERLAY ── -->
<div class="overlay" id="overlay"></div>

<!-- ── SETTINGS DRAWER ── -->
<div class="drawer" id="drawer">
  <div class="drawer-handle"></div>
  <div class="drawer-title">설정</div>

  <div class="drawer-section">
    <div class="drawer-label">사용자 이름</div>
    <input class="drawer-input" id="userInput" value="testuser" placeholder="사용자 이름">
  </div>

  <div class="drawer-section" style="margin-top:20px;">
    <div class="drawer-label">모델 선택</div>
    <div class="model-list">
      <div class="model-item selected" data-value="gpt-4o-mini">
        <div class="model-dot"></div>
        <div class="model-info">
          <div class="model-name">ChatGPT</div>
          <div class="model-desc">GPT-4o mini · OpenAI</div>
        </div>
      </div>
      <div class="model-item" data-value="gemini/gemini-2.0-flash-exp">
        <div class="model-dot"></div>
        <div class="model-info">
          <div class="model-name">Gemini</div>
          <div class="model-desc">Gemini 2.0 Flash · Google</div>
        </div>
      </div>
    </div>
  </div>

  <div class="drawer-section" style="margin-top:20px;">
    <div class="drawer-label">보안 정책</div>
    <div class="security-tags">
      <div class="sec-tag">✓ 프롬프트 필터링</div>
      <div class="sec-tag">✓ 대화 로깅</div>
      <div class="sec-tag">✓ 키워드 차단</div>
    </div>
  </div>

  <div class="drawer-divider"></div>

  <button class="clear-btn" id="clearBtn">대화 초기화</button>
</div>

<!-- ── MODEL PICKER SHEET ── -->
<div class="model-sheet" id="modelSheet">
  <div class="drawer-handle"></div>
  <div class="drawer-title">모델 선택</div>
  <div class="model-sheet-list">
    <div class="model-item selected" data-value="gpt-4o-mini">
      <div class="model-dot"></div>
      <div class="model-info">
        <div class="model-name">ChatGPT</div>
        <div class="model-desc">GPT-4o mini · OpenAI</div>
      </div>
    </div>
    <div class="model-item" data-value="gemini/gemini-2.0-flash-exp">
      <div class="model-dot"></div>
      <div class="model-info">
        <div class="model-name">Gemini</div>
        <div class="model-desc">Gemini 2.0 Flash · Google</div>
      </div>
    </div>
  </div>
</div>

<script>
/* ──────────────────────────────
   STATE
────────────────────────────── */
let selectedModel = 'gpt-4o-mini';
let selectedModelName = 'ChatGPT';
let isLoading = false;

const textarea    = document.getElementById('prompt');
const sendBtn     = document.getElementById('sendBtn');
const messagesEl  = document.getElementById('messages');
const welcomeEl   = document.getElementById('welcomeScreen');
const chatScroll  = document.getElementById('chatScroll');
const overlay     = document.getElementById('overlay');
const drawer      = document.getElementById('drawer');
const modelSheet  = document.getElementById('modelSheet');
const modelPillLbl= document.getElementById('modelPillLabel');
const navSub      = document.getElementById('navSub');

/* ──────────────────────────────
   TEXTAREA AUTO-RESIZE
────────────────────────────── */
textarea.addEventListener('input', () => {
  textarea.style.height = 'auto';
  textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  sendBtn.disabled = !textarea.value.trim();
});

/* ──────────────────────────────
   SUGGESTION PILLS
────────────────────────────── */
document.querySelectorAll('.pill').forEach(p => {
  p.addEventListener('click', () => {
    textarea.value = p.dataset.text;
    textarea.dispatchEvent(new Event('input'));
    textarea.focus();
  });
});

/* ──────────────────────────────
   DRAWER (settings)
────────────────────────────── */
function openDrawer() {
  drawer.classList.add('open');
  overlay.classList.add('open');
}

function closeAll() {
  drawer.classList.remove('open');
  modelSheet.classList.remove('open');
  overlay.classList.remove('open');
}

document.getElementById('menuBtn').addEventListener('click', openDrawer);
overlay.addEventListener('click', closeAll);
document.getElementById('clearBtn').addEventListener('click', () => {
  clearChat(); closeAll();
});

/* ──────────────────────────────
   MODEL SELECTION (drawer)
────────────────────────────── */
function selectModel(value, name) {
  selectedModel     = value;
  selectedModelName = name;
  modelPillLbl.textContent = name;
  navSub.textContent = name + ' 사용 중';

  // update all model-item lists
  document.querySelectorAll('.model-item').forEach(item => {
    item.classList.toggle('selected', item.dataset.value === value);
  });
}

document.querySelectorAll('#drawer .model-item').forEach(item => {
  item.addEventListener('click', () => {
    const name = item.querySelector('.model-name').textContent;
    selectModel(item.dataset.value, name);
  });
});

/* model pill → model sheet */
document.getElementById('modelPillBtn').addEventListener('click', () => {
  modelSheet.classList.add('open');
  overlay.classList.add('open');
});

document.querySelectorAll('#modelSheet .model-item').forEach(item => {
  item.addEventListener('click', () => {
    const name = item.querySelector('.model-name').textContent;
    selectModel(item.dataset.value, name);
    closeAll();
  });
});

/* ──────────────────────────────
   SEND
────────────────────────────── */
sendBtn.addEventListener('click', sendMessage);

textarea.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey) {
    e.preventDefault();
    if (!sendBtn.disabled) sendMessage();
  }
});

async function sendMessage() {
  if (isLoading) return;
  const prompt = textarea.value.trim();
  if (!prompt) return;

  isLoading = true;
  sendBtn.disabled = true;

  showMessages();
  appendMsg('user', prompt, null);
  textarea.value = '';
  textarea.style.height = 'auto';

  const thinkEl = showThinking();
  scrollBottom();

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user:   document.getElementById('userInput').value || 'testuser',
        model:  selectedModel,
        prompt: prompt
      })
    });
    const data = await res.json();
    thinkEl.remove();
    appendMsg('assistant', data.response || '응답 없음', data.status);
  } catch (err) {
    thinkEl.remove();
    appendMsg('assistant', '오류: ' + err.message, 'error');
  } finally {
    isLoading = false;
    sendBtn.disabled = !textarea.value.trim();
    scrollBottom();
  }
}

/* ──────────────────────────────
   HELPERS
────────────────────────────── */
function showMessages() {
  welcomeEl.style.display  = 'none';
  messagesEl.style.display = 'flex';
}

function clearChat() {
  messagesEl.innerHTML = '';
  messagesEl.style.display = 'none';
  welcomeEl.style.display  = 'flex';
}

function scrollBottom() {
  requestAnimationFrame(() => {
    chatScroll.scrollTop = chatScroll.scrollHeight;
  });
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;')
          .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function appendMsg(role, text, status) {
  const isUser = role === 'user';
  const user   = document.getElementById('userInput').value || 'testuser';

  let badge = '';
  if (status === 'ok' && !isUser)      badge = '<span class="status-badge ok">✓ 허용</span>';
  else if (status === 'blocked')       badge = '<span class="status-badge blocked">⊘ 차단</span>';
  else if (status === 'error')         badge = '<span class="status-badge error">⚠ 오류</span>';

  const bodyClass = (status === 'blocked' || status === 'error') ? 'msg-body danger' : 'msg-body';

  const div = document.createElement('div');
  div.className = 'msg-group';
  div.innerHTML = `
    <div class="msg-header">
      <div class="msg-avatar ${isUser ? 'user-av' : 'ai-av'}">
        ${isUser ? escHtml(user[0].toUpperCase()) : 'G'}
      </div>
      <span class="msg-name">${isUser ? escHtml(user) : 'AI Gateway'}</span>
      ${badge}
    </div>
    <div class="${bodyClass}">${escHtml(text)}</div>
  `;
  messagesEl.appendChild(div);
  scrollBottom();
  return div;
}

function showThinking() {
  const div = document.createElement('div');
  div.className = 'thinking-row';
  div.innerHTML = `
    <div class="dots"><span></span><span></span><span></span></div>
    <span class="thinking-text">응답 생성 중…</span>
  `;
  messagesEl.appendChild(div);
  scrollBottom();
  return div;
}

/* init */
navSub.textContent = selectedModelName + ' 사용 중';
</script>

</body>
</html>
"""


# =========================
# Chat API
# =========================

@app.post("/chat")
def chat(req: ChatRequest):

    if not validate_prompt(req.prompt):
        save_log(req.user, req.model, req.prompt, "BLOCK")
        return {
            "status": "blocked",
            "response": "보안정책 위반: 허용되지 않는 키워드가 포함되어 있습니다."
        }

    try:
        response = completion(
            model=req.model,
            messages=[{"role": "user", "content": req.prompt}]
        )

        print("FULL RESPONSE:")
        print(response)

        answer = response.choices[0].message.content
        if answer is None:
            answer = "응답 없음"

        save_log(req.user, req.model, req.prompt, "ALLOW")

        return {"status": "ok", "response": str(answer)}

    except Exception as e:
        print("ERROR:", str(e))
        return {"status": "error", "response": str(e)}
