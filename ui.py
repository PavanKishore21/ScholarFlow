import os
import time
from html import escape
from typing import Any, Dict, Tuple

import requests
import streamlit as st


DEFAULT_BACKEND_URL = os.getenv("SCHOLARFLOW_BACKEND_URL", "https://scholarflow.onrender.com")
DEFAULT_ADMIN_TOKEN = os.getenv("SCHOLARFLOW_ADMIN_TOKEN", "")
PAGES = ["Getting Started", "Knowledge Base", "Research", "RAG Studio", "Admin"]
PAGE_META = {
    "Getting Started": {
        "label": "1. Start Here",
        "subtitle": "",
    },
    "Knowledge Base": {
        "label": "2. Knowledge Base",
        "subtitle": "Upload documents and track corpus health.",
    },
    "Research": {
        "label": "3. Research Chat",
        "subtitle": "Ask questions and get cited answers.",
    },
    "RAG Studio": {
        "label": "4. RAG Studio",
        "subtitle": "Check retrieval, score answers, and compare prompts.",
    },
    "Admin": {
        "label": "5. Admin",
        "subtitle": "Maintenance and diagnostics controls.",
    },
}


st.set_page_config(
    page_title="ScholarFlow",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
  --sf-bg: #121417;
  --sf-bg-elev: #171b21;
  --sf-bg-soft: #1e242d;
  --sf-surface: #202631;
  --sf-border: #2d3542;
  --sf-text: #eceff4;
  --sf-text-soft: #d9e1ec;
  --sf-muted: #9aa3b5;
  --sf-primary: #10a37f;
  --sf-primary-strong: #0f8e70;
  --sf-danger: #f87171;
  --sf-warn: #fbbf24;
  --sf-info: #60a5fa;
}

html, body, [class*="css"] {
  font-family: 'Inter', sans-serif;
  color: var(--sf-text) !important;
  line-height: 1.45;
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] section.main {
  background: radial-gradient(circle at 10% 0%, #1a1e25 0%, #121417 45%, #0e1116 100%) !important;
}

[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #171b21 0%, #13171d 100%) !important;
  border-right: 1px solid var(--sf-border);
  min-width: 370px !important;
  max-width: 370px !important;
}

[data-testid="stSidebar"] * {
  color: var(--sf-text) !important;
}

[data-testid="stSidebar"] > div:first-child {
  padding-top: 0.6rem;
  padding-left: 0.75rem;
  padding-right: 0.75rem;
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { background: transparent !important; }

.block-container {
  max-width: 1200px;
  padding-top: 0.95rem;
  padding-bottom: 1.55rem;
}

h1, h2, h3, h4, h5, h6,
p, label, span, li,
.stMarkdown, .stCaption {
  color: var(--sf-text) !important;
}

a {
  color: #8ab4ff !important;
}

.sf-brand {
  border: 1px solid var(--sf-border);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  padding: 0.75rem 0.8rem;
  margin-bottom: 0.7rem;
}

.sf-brand h3 {
  margin: 0;
  font-size: 1.04rem;
  font-weight: 700;
}

.sf-brand p {
  margin: 0.22rem 0 0;
  color: var(--sf-muted) !important;
  font-size: 0.81rem;
}

.sf-side-card {
  border: 1px solid var(--sf-border);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  padding: 0.76rem 0.8rem;
  margin-bottom: 0.62rem;
}

.sf-side-title {
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #8ab4ff !important;
  font-weight: 700;
  margin-bottom: 0.56rem;
}

.sf-side-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.8rem;
  margin-bottom: 0.34rem;
}

.sf-side-key {
  color: var(--sf-muted) !important;
  font-size: 0.8rem;
}

.sf-side-val {
  color: var(--sf-text) !important;
  font-size: 0.8rem;
  font-weight: 600;
}

.sf-side-muted {
  color: var(--sf-muted) !important;
  font-size: 0.78rem;
}

.sf-side-query {
  border-left: 2px solid var(--sf-border);
  padding-left: 0.55rem;
  margin-bottom: 0.42rem;
  color: var(--sf-muted) !important;
  font-size: 0.79rem;
}

.sf-side-stack {
  border: 1px solid var(--sf-border);
  border-radius: 12px;
  background: #181d25;
  padding: 0.55rem 0.6rem;
  margin-bottom: 0.52rem;
}

.sf-side-item {
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.015);
  padding: 0.44rem 0.5rem;
  margin-bottom: 0.42rem;
}

.sf-side-item:last-child {
  margin-bottom: 0;
}

.sf-side-tag {
  display: inline-block;
  font-size: 0.64rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #93c5fd !important;
  font-weight: 700;
  margin-bottom: 0.2rem;
}

.sf-side-item-text {
  color: var(--sf-text) !important;
  font-size: 0.78rem;
  line-height: 1.38;
}

.sf-side-dim {
  color: var(--sf-muted) !important;
  font-size: 0.72rem;
}

.sf-guide {
  border: 1px solid rgba(16, 163, 127, 0.42);
  border-radius: 12px;
  background: rgba(16, 163, 127, 0.08);
  border-left: 4px solid rgba(16, 163, 127, 0.95);
  padding: 0.8rem 0.84rem;
  margin: 0.22rem 0 0.92rem;
}

.sf-guide strong {
  color: #d1fae5 !important;
}

.sf-guide p {
  margin: 0.24rem 0 0;
  color: var(--sf-text-soft) !important;
  font-size: 0.86rem;
  line-height: 1.48;
}

.sf-top {
  border: 1px solid var(--sf-border);
  border-radius: 14px;
  background: linear-gradient(130deg, #1b2028 0%, #171c24 70%, #161b22 100%);
  padding: 1.02rem 1.08rem;
  margin-bottom: 0.9rem;
}

.sf-top-title {
  margin: 0;
  font-size: 1.52rem;
  letter-spacing: -0.02em;
  font-weight: 800;
}

.sf-top-sub {
  margin-top: 0.34rem;
  color: var(--sf-muted) !important;
  font-size: 0.93rem;
  line-height: 1.45;
}

.sf-inline {
  display: flex;
  gap: 0.42rem;
  flex-wrap: wrap;
  margin-top: 0.62rem;
}

.sf-badge {
  display: inline-block;
  border-radius: 999px;
  padding: 0.2rem 0.58rem;
  font-size: 0.69rem;
  font-weight: 700;
  border: 1px solid transparent;
}

.sf-badge-neutral {
  color: #cbd5e1 !important;
  background: rgba(148, 163, 184, 0.14);
  border-color: rgba(148, 163, 184, 0.28);
}

.sf-badge-ok {
  color: #86efac !important;
  background: rgba(34, 197, 94, 0.15);
  border-color: rgba(34, 197, 94, 0.35);
}

.sf-badge-warn {
  color: #fde68a !important;
  background: rgba(234, 179, 8, 0.13);
  border-color: rgba(234, 179, 8, 0.32);
}

.sf-badge-danger {
  color: #fca5a5 !important;
  background: rgba(239, 68, 68, 0.13);
  border-color: rgba(239, 68, 68, 0.3);
}

.sf-panel {
  border: 1px solid var(--sf-border);
  border-radius: 12px;
  background: var(--sf-bg-elev);
  padding: 0.9rem;
}

.sf-panel-title {
  font-size: 1.03rem;
  font-weight: 700;
  margin-bottom: 0.2rem;
}

.sf-panel-sub {
  color: var(--sf-muted) !important;
  font-size: 0.87rem;
  line-height: 1.46;
}

.sf-metric {
  border: 1px solid var(--sf-border);
  border-radius: 10px;
  background: #1a2029;
  padding: 0.68rem 0.72rem;
}

.sf-metric-label {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.66rem;
  color: var(--sf-muted) !important;
  font-weight: 700;
}

.sf-metric-value {
  margin-top: 0.16rem;
  font-size: 1.12rem;
  font-weight: 800;
}

.sf-kicker {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 0.68rem;
  color: #8ab4ff !important;
  font-weight: 700;
  margin: 0.18rem 0 0.5rem;
}

.sf-mono {
  font-family: 'IBM Plex Mono', monospace;
}

.stButton > button,
.stDownloadButton > button {
  border-radius: 10px;
  border: 1px solid var(--sf-border);
  background: #1b212a;
  color: var(--sf-text);
  font-weight: 600;
  min-height: 2.36rem;
  padding-top: 0.35rem;
  padding-bottom: 0.35rem;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
  border-color: var(--sf-primary);
  color: #ffffff;
}

.stButton > button[kind="primary"] {
  background: linear-gradient(130deg, var(--sf-primary) 0%, var(--sf-primary-strong) 100%);
  color: #ffffff;
  border: none;
}

.stButton > button[kind="primary"]:hover {
  color: #ffffff;
}

[data-testid="stChatMessage"] {
  border: 1px solid var(--sf-border);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  padding: 0.68rem 0.78rem;
  margin-bottom: 0.34rem;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span {
  color: var(--sf-text) !important;
}

[data-testid="stChatInput"] {
  border-top: 1px solid var(--sf-border);
  padding-top: 0.88rem;
  margin-top: 0.34rem;
}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
  color: var(--sf-text) !important;
  border-color: var(--sf-border) !important;
  background: #181d25 !important;
}

.stDataFrame, .stTable {
  border: 1px solid var(--sf-border);
  border-radius: 10px;
}

.stTabs [role="tablist"] {
  gap: 0.45rem;
}

.stTabs [role="tab"] {
  border: 1px solid var(--sf-border);
  border-radius: 10px;
  background: #1a2029;
  height: 2.18rem;
  font-size: 0.86rem;
}

.stTabs [role="tab"][aria-selected="true"] {
  border-color: var(--sf-primary);
  color: #d1fae5 !important;
}

@media (max-width: 1250px) {
  [data-testid="stSidebar"] {
    min-width: 320px !important;
    max-width: 320px !important;
  }
}

@media (max-width: 920px) {
  .sf-top-title {
    font-size: 1.3rem;
  }

  [data-testid="stSidebar"] {
    min-width: auto !important;
    max-width: none !important;
  }
}
</style>
""",
    unsafe_allow_html=True,
)


def _safe(value: Any) -> str:
    return escape(str(value))


def badge(text: str, tone: str = "neutral") -> str:
    cls = {
        "ok": "sf-badge-ok",
        "warn": "sf-badge-warn",
        "danger": "sf-badge-danger",
        "neutral": "sf-badge-neutral",
    }.get(tone, "sf-badge-neutral")
    return f'<span class="sf-badge {cls}">{_safe(text)}</span>'


def panel(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
<div class="sf-panel">
  <div class="sf-panel-title">{_safe(title)}</div>
  <div class="sf-panel-sub">{_safe(subtitle)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def metric(label: str, value: Any) -> None:
    st.markdown(
        f"""
<div class="sf-metric">
  <div class="sf-metric-label">{_safe(label)}</div>
  <div class="sf-metric-value">{_safe(value)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# State
# -----------------------------------------------------------------------------
if "backend_url" not in st.session_state:
    st.session_state.backend_url = DEFAULT_BACKEND_URL
if "admin_token" not in st.session_state:
    st.session_state.admin_token = DEFAULT_ADMIN_TOKEN
if "page_mode" not in st.session_state:
    st.session_state.page_mode = "Getting Started"
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "working_messages" not in st.session_state:
    st.session_state.working_messages = []
if "run_mode" not in st.session_state:
    st.session_state.run_mode = "balanced"
if "run_max_plan_queries" not in st.session_state:
    st.session_state.run_max_plan_queries = 3
if "run_max_citations" not in st.session_state:
    st.session_state.run_max_citations = 9
if "run_score_threshold" not in st.session_state:
    st.session_state.run_score_threshold = 0.0
if "run_include_graph" not in st.session_state:
    st.session_state.run_include_graph = True
if "run_include_diagnostics" not in st.session_state:
    st.session_state.run_include_diagnostics = True
if "studio_retrieve_result" not in st.session_state:
    st.session_state.studio_retrieve_result = None
if "studio_eval_result" not in st.session_state:
    st.session_state.studio_eval_result = None
if "studio_compare_result" not in st.session_state:
    st.session_state.studio_compare_result = None
if "_http_get_cache" not in st.session_state:
    st.session_state._http_get_cache = {}
if "kb_view" not in st.session_state:
    st.session_state.kb_view = "Upload documents"
if "admin_view" not in st.session_state:
    st.session_state.admin_view = "Operations"

if st.session_state.page_mode not in set(PAGES):
    st.session_state.page_mode = "Getting Started"


# -----------------------------------------------------------------------------
# API
# -----------------------------------------------------------------------------
def _base_url() -> str:
    return st.session_state.backend_url.rstrip("/")


def _admin_headers() -> Dict[str, str]:
    token = (st.session_state.admin_token or "").strip()
    return {"x-admin-token": token} if token else {}


def api_request(
    method: str,
    path: str,
    timeout: int = 20,
    use_admin_token: bool = False,
    **kwargs,
) -> Tuple[bool, Any, str, int]:
    url = f"{_base_url()}{path}"
    headers = kwargs.pop("headers", {}) or {}
    if use_admin_token:
        headers.update(_admin_headers())

    try:
        response = requests.request(
            method=method,
            url=url,
            timeout=timeout,
            headers=headers,
            **kwargs,
        )
    except requests.exceptions.Timeout:
        return False, None, "Request timed out", 0
    except requests.exceptions.ConnectionError:
        return False, None, f"Cannot connect to backend at {_base_url()}", 0
    except Exception as e:
        return False, None, str(e), 0

    try:
        body = response.json()
    except Exception:
        body = response.text

    if response.status_code >= 400:
        detail = body.get("detail") if isinstance(body, dict) else str(body)
        return False, body, f"HTTP {response.status_code}: {detail}", response.status_code

    return True, body, "ok", response.status_code


def clear_get_cache() -> None:
    st.session_state._http_get_cache = {}


def cached_get(
    path: str,
    timeout: int = 10,
    use_admin_token: bool = False,
    ttl_sec: int = 12,
    force: bool = False,
) -> Tuple[bool, Any, str, int]:
    now = time.time()
    token_part = (st.session_state.admin_token or "").strip() if use_admin_token else ""
    cache_key = f"{_base_url()}|{path}|{int(use_admin_token)}|{token_part}"
    cache = st.session_state._http_get_cache

    if not force and cache_key in cache:
        entry = cache.get(cache_key, {})
        age = now - float(entry.get("ts", 0))
        if age <= ttl_sec:
            return (
                bool(entry.get("ok", False)),
                entry.get("payload"),
                str(entry.get("err", "ok")),
                int(entry.get("code", 0) or 0),
            )

    ok, payload, err, code = api_request(
        "GET",
        path,
        timeout=timeout,
        use_admin_token=use_admin_token,
    )
    cache[cache_key] = {
        "ts": now,
        "ok": ok,
        "payload": payload,
        "err": err,
        "code": code,
    }
    st.session_state._http_get_cache = cache
    return ok, payload, err, code


# -----------------------------------------------------------------------------
# Conversation
# -----------------------------------------------------------------------------
def get_active_conversation() -> Dict[str, Any] | None:
    cid = st.session_state.active_chat_id
    if cid is None:
        return None
    for c in st.session_state.conversations:
        if c["id"] == cid:
            return c
    return None


def start_new_chat() -> None:
    st.session_state.active_chat_id = None
    st.session_state.working_messages = []


def persist_chat(title_hint: str) -> None:
    snapshot = [dict(m) for m in st.session_state.working_messages]
    active = get_active_conversation()

    if active is None:
        next_id = max((c["id"] for c in st.session_state.conversations), default=0) + 1
        st.session_state.conversations.append(
            {
                "id": next_id,
                "title": title_hint[:64],
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "messages": snapshot,
            }
        )
        st.session_state.active_chat_id = next_id
    else:
        active["messages"] = snapshot


def run_query(prompt: str) -> None:
    prompt = (prompt or "").strip()
    if not prompt:
        return

    st.session_state.working_messages.append({"role": "user", "content": prompt})

    with st.spinner("Generating response..."):
        ok, payload, err, _ = api_request(
            "POST",
            "/generate",
            timeout=180,
            json={
                "topic": prompt,
                "mode": st.session_state.run_mode,
                "max_plan_queries": int(st.session_state.run_max_plan_queries),
                "max_citations": int(st.session_state.run_max_citations),
                "score_threshold": float(st.session_state.run_score_threshold),
                "include_graph": bool(st.session_state.run_include_graph),
                "include_diagnostics": bool(st.session_state.run_include_diagnostics),
            },
        )

    if not ok:
        st.session_state.working_messages.append(
            {"role": "assistant", "content": f"Request failed: {err}"}
        )
        persist_chat(prompt)
        st.rerun()
        return

    review = payload.get("review", "") if isinstance(payload, dict) else ""
    queries = payload.get("queries", []) if isinstance(payload, dict) else []
    critique = payload.get("critique", "") if isinstance(payload, dict) else ""
    stats = payload.get("stats", {}) if isinstance(payload, dict) else {}
    citations = payload.get("citations", []) if isinstance(payload, dict) else []
    diagnostics = payload.get("diagnostics", {}) if isinstance(payload, dict) else {}
    mode = payload.get("mode", st.session_state.run_mode) if isinstance(payload, dict) else st.session_state.run_mode

    st.session_state.working_messages.append(
        {
            "role": "assistant",
            "content": review or "No response generated.",
            "queries": queries,
            "critique": critique,
            "stats": stats,
            "citations": citations,
            "diagnostics": diagnostics,
            "mode": mode,
        }
    )

    persist_chat(prompt)
    st.rerun()


with st.sidebar:
    st.markdown(
        """
<div class="sf-brand">
  <h3>ScholarFlow</h3>
  <p>Production RAG workspace</p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="sf-guide">
  <strong>Recommended flow</strong>
  <p>1) Start Here -> 2) Knowledge Base -> 3) Research Chat -> 4) RAG Studio -> 5) Admin</p>
</div>
""",
        unsafe_allow_html=True,
    )

    if st.button("1) Start Here", use_container_width=True, key="goto_start_here"):
        st.session_state.page_mode = "Getting Started"
        st.rerun()
    if st.button("2) Knowledge Base", use_container_width=True, key="goto_kb"):
        st.session_state.page_mode = "Knowledge Base"
        st.rerun()
    if st.button("3) Research Chat", use_container_width=True, key="goto_research"):
        st.session_state.page_mode = "Research"
        st.rerun()
    if st.button("4) RAG Studio", use_container_width=True, key="goto_studio"):
        st.session_state.page_mode = "RAG Studio"
        st.rerun()
    if st.button("5) Admin", use_container_width=True, key="goto_admin"):
        st.session_state.page_mode = "Admin"
        st.rerun()

    st.caption(PAGE_META.get(st.session_state.page_mode, {}).get("subtitle", ""))

    if st.button(
        "New chat",
        type="primary",
        use_container_width=True,
        help="Clears the current thread and starts a fresh chat.",
    ):
        start_new_chat()
        st.session_state.page_mode = "Research"
        st.rerun()

    st.markdown("---")
    st.markdown("#### Conversation history")
    history_filter = st.text_input(
        "Find conversation",
        value="",
        placeholder="Filter by title",
        key="history_filter_sidebar",
    ).strip().lower()

    history_rows = list(reversed(st.session_state.conversations))
    if history_filter:
        history_rows = [c for c in history_rows if history_filter in str(c.get("title", "")).lower()]

    show_all_history = st.checkbox(
        "Show full history",
        value=False,
        key="show_full_history_sidebar",
    )
    if not show_all_history and len(history_rows) > 30:
        st.caption("Showing latest 30 conversations. Enable full history to view all.")
        history_rows = history_rows[:30]

    if not history_rows:
        st.caption("No saved conversations.")
    else:
        conv_ids = [int(conv.get("id")) for conv in history_rows]
        conv_lookup = {int(conv.get("id")): conv for conv in history_rows}

        def _history_label(cid: int) -> str:
            row = conv_lookup.get(cid, {})
            title = str(row.get("title") or "Untitled")[:34]
            turns = len(row.get("messages", []) or [])
            created = str(row.get("created_at", "—"))
            return f"{title} | {turns} turns | {created}"

        selected_id = st.selectbox(
            "Saved threads",
            options=conv_ids,
            format_func=_history_label,
            key="selected_conv_sidebar",
        )

        selected_conv = conv_lookup.get(int(selected_id), {})
        selected_msgs = selected_conv.get("messages", []) if isinstance(selected_conv, dict) else []
        is_active = int(selected_id) == int(st.session_state.active_chat_id or -1)
        st.markdown(
            badge("Selected thread is active" if is_active else "Selected thread is saved", "ok" if is_active else "neutral"),
            unsafe_allow_html=True,
        )
        if selected_msgs:
            preview = str(selected_msgs[-1].get("content", "")).strip().replace("\n", " ")
            st.caption(preview[:220] if preview else "No message preview available.")

        if st.button("Open selected conversation", use_container_width=True):
            st.session_state.active_chat_id = int(selected_id)
            st.session_state.working_messages = [dict(m) for m in selected_msgs]
            st.session_state.page_mode = "Research"
            st.rerun()


# -----------------------------------------------------------------------------
# Global top shell
# -----------------------------------------------------------------------------
active_page = st.session_state.page_mode
page_subtitle = PAGE_META.get(active_page, {}).get("subtitle", "")
st.markdown(
    f"""
<div class="sf-top">
  <h1 class="sf-top-title">ScholarFlow</h1>
  <div class="sf-top-sub">{_safe(page_subtitle)}</div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="sf-inline">
  {badge(f"Workspace: {PAGE_META.get(active_page, {}).get('label', active_page)}", "neutral")}
  {badge("Theme: Dark", "neutral")}
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("---")


# -----------------------------------------------------------------------------
# Getting Started page
# -----------------------------------------------------------------------------
if st.session_state.page_mode == "Getting Started":
    st.markdown('<div class="sf-kicker">Getting Started</div>', unsafe_allow_html=True)
    panel(
        "Welcome to ScholarFlow",
        "Follow these steps to get value quickly.",
    )

    st.markdown(
        """
1. **Upload a PDF** in `Knowledge Base -> Upload Documents`.
2. **Ask a question** in `Research Chat`.
3. **Verify quality** in `RAG Studio`.
4. Use **Admin** only for maintenance tasks.
"""
    )

    st.markdown("### Quick actions")
    s1, s2, s3 = st.columns(3)
    with s1:
        if st.button("Go to Knowledge Base", use_container_width=True, key="start_go_kb"):
            st.session_state.page_mode = "Knowledge Base"
            st.rerun()
    with s2:
        if st.button("Go to Research Chat", use_container_width=True, key="start_go_research"):
            st.session_state.page_mode = "Research"
            st.rerun()
    with s3:
        if st.button("Go to RAG Studio", use_container_width=True, key="start_go_studio"):
            st.session_state.page_mode = "RAG Studio"
            st.rerun()

    st.markdown("---")
    st.markdown("### What each section does")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
- **Research Chat**: Ask questions and get grounded answers with citations.
- **Run Controls**: Tune speed vs depth (`fast`, `balanced`, `deep`).
- **Response Details**: View planner queries, citations, diagnostics, and latency.
"""
        )
    with c2:
        st.markdown(
            """
- **RAG Studio**: Test retrieval quality and score answer grounding.
- **Knowledge Base**: Upload PDFs that become your retrieval corpus.
- **Admin**: Logs, maintenance, and operational diagnostics.
"""
        )


# -----------------------------------------------------------------------------
# Research page
# -----------------------------------------------------------------------------
elif st.session_state.page_mode == "Research":
    st.markdown('<div class="sf-kicker">Research</div>', unsafe_allow_html=True)
    st.caption("Ask a question, review evidence, and iterate.")

    st.markdown(
        """
<div class="sf-guide">
  <strong>How to use Research Chat</strong>
  <p>Choose a preset, send your question, then open "How this answer was built" to review evidence and diagnostics.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    p1, p2, p3 = st.columns(3)
    with p1:
        if st.button(
            "Quick",
            use_container_width=True,
            key="preset_quick",
            help="Fast response, lighter retrieval.",
        ):
            st.session_state.run_mode = "fast"
            st.session_state.run_max_plan_queries = 2
            st.session_state.run_max_citations = 6
            st.session_state.run_score_threshold = 0.0
    with p2:
        if st.button(
            "Balanced",
            use_container_width=True,
            key="preset_balanced",
            help="Best default for most queries.",
        ):
            st.session_state.run_mode = "balanced"
            st.session_state.run_max_plan_queries = 3
            st.session_state.run_max_citations = 9
            st.session_state.run_score_threshold = 0.0
    with p3:
        if st.button(
            "Deep",
            use_container_width=True,
            key="preset_deep",
            help="Broader retrieval and more evidence.",
        ):
            st.session_state.run_mode = "deep"
            st.session_state.run_max_plan_queries = 5
            st.session_state.run_max_citations = 14
            st.session_state.run_score_threshold = 0.0

    with st.expander("Advanced Controls", expanded=False):
        st.caption(
            "Mode sets speed vs depth. Planner queries set search breadth. "
            "Citation budget sets evidence count. Threshold filters weak matches."
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            st.session_state.run_mode = st.selectbox(
                "Mode",
                ["fast", "balanced", "deep"],
                index=["fast", "balanced", "deep"].index(st.session_state.run_mode)
                if st.session_state.run_mode in {"fast", "balanced", "deep"}
                else 1,
                help="fast: quicker answers, deep: broader retrieval and heavier evidence.",
                key="run_mode_select",
            )
        with c2:
            st.session_state.run_max_plan_queries = st.slider(
                "Planner queries",
                min_value=1,
                max_value=6,
                value=int(st.session_state.run_max_plan_queries),
                key="run_max_plan_slider",
            )
        with c3:
            st.session_state.run_max_citations = st.slider(
                "Citation budget",
                min_value=3,
                max_value=20,
                value=int(st.session_state.run_max_citations),
                key="run_max_citations_slider",
            )

        c4, c5 = st.columns(2)
        with c4:
            st.session_state.run_score_threshold = st.slider(
                "Score threshold",
                min_value=0.0,
                max_value=1.0,
                value=float(st.session_state.run_score_threshold),
                step=0.01,
                help="Filter out low-score retrieved chunks.",
                key="run_threshold_slider",
            )
        with c5:
            st.session_state.run_include_graph = st.checkbox(
                "Include graph-linked sources",
                value=bool(st.session_state.run_include_graph),
                key="run_include_graph_checkbox",
            )
            st.session_state.run_include_diagnostics = st.checkbox(
                "Return diagnostics",
                value=bool(st.session_state.run_include_diagnostics),
                help="Includes retrieval metadata in response details.",
                key="run_include_diag_checkbox",
            )

    if not st.session_state.working_messages:
        st.markdown("### What should we research?")
        st.caption("Starter prompts below are examples. Click one to auto-run a full RAG response.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(
                "Compare vector databases for enterprise RAG",
                use_container_width=True,
                help="Compares Qdrant, Pinecone, and Weaviate from a production perspective.",
            ):
                run_query("Compare Qdrant, Pinecone, and Weaviate for enterprise RAG in production.")
            if st.button(
                "Design evaluation plan for RAG quality",
                use_container_width=True,
                help="Generates metrics and testing strategy for quality/reliability.",
            ):
                run_query("Design an end-to-end evaluation plan for RAG quality, reliability, and latency.")
        with c2:
            if st.button(
                "Long-document architecture",
                use_container_width=True,
                help="Design guidance for legal/compliance long-context RAG.",
            ):
                run_query("Design a robust RAG architecture for long legal and compliance documents.")
            if st.button(
                "Metadata strategy",
                use_container_width=True,
                help="Explains metadata schema choices for retrieval quality.",
            ):
                run_query("What metadata schema improves retrieval precision and grounding quality?")
        st.markdown("---")

    for msg in st.session_state.working_messages:
        role = msg.get("role", "assistant")
        with st.chat_message(role):
            st.markdown(msg.get("content", ""))

            if role == "assistant" and any(
                k in msg for k in ["queries", "critique", "stats", "citations", "diagnostics", "mode"]
            ):
                with st.expander("How this answer was built", expanded=False):
                    run_mode = str(msg.get("mode", "balanced")).strip()
                    st.markdown(f"**Run mode**: `{run_mode}`")

                    queries = msg.get("queries") or []
                    if queries:
                        st.markdown("**Search plan**")
                        for i, q in enumerate(queries, start=1):
                            st.write(f"{i}. {q}")

                    critique = (msg.get("critique") or "").strip()
                    if critique:
                        st.markdown("**Self-check**")
                        st.write(critique)

                    stats = msg.get("stats") or {}
                    if stats:
                        st.markdown("**Run metrics**")
                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            metric("LLM tokens", int(stats.get("llm_tokens", 0) or 0))
                        with m2:
                            metric("Retrieved", int(stats.get("retrieved_tokens", 0) or 0))
                        with m3:
                            metric("Citations", int(stats.get("citation_count", 0) or 0))
                        with m4:
                            metric("Latency ms", int(stats.get("latency_ms", 0) or 0))

                    citations = msg.get("citations") or []
                    if citations:
                        st.markdown("**Evidence**")
                        for c in citations[:12]:
                            title = c.get("title", "Source")
                            url = (c.get("url") or "").strip()
                            snippet = (c.get("snippet") or "").strip()
                            src = str(c.get("source", "Vector"))
                            score = float(c.get("score", 0.0) or 0.0)
                            if url:
                                st.markdown(f"- [{title}]({url}) · `{src}` · score `{score:.3f}`")
                            else:
                                st.markdown(f"- {title} · `{src}` · score `{score:.3f}`")
                            if snippet:
                                st.caption(snippet[:240])

                    diagnostics = msg.get("diagnostics") or {}
                    if diagnostics:
                        retrieval_meta = diagnostics.get("retrieval_meta", {})
                        if retrieval_meta:
                            st.markdown("**Retrieval details**")
                            st.json(retrieval_meta)

    prompt = st.chat_input("Message ScholarFlow")
    if prompt:
        run_query(prompt)


# -----------------------------------------------------------------------------
# RAG Studio page
# -----------------------------------------------------------------------------
elif st.session_state.page_mode == "RAG Studio":
    st.markdown('<div class="sf-kicker">RAG Studio</div>', unsafe_allow_html=True)
    panel("RAG quality workspace", "Run checks in order: retrieval -> answer score -> prompt comparison.")

    st.markdown(
        """
<div class="sf-guide">
  <strong>When to use this page</strong>
  <p>After generating an answer in Research Chat, use this page to validate quality and improve prompts.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    last_user_prompt = next(
        (m.get("content", "") for m in reversed(st.session_state.working_messages) if m.get("role") == "user"),
        "",
    )
    last_assistant_answer = next(
        (m.get("content", "") for m in reversed(st.session_state.working_messages) if m.get("role") == "assistant"),
        "",
    )

    t_retrieve, t_eval, t_arena = st.tabs(
        ["1) Check Retrieval", "2) Score Answer", "3) Compare Prompts"]
    )

    with t_retrieve:
        st.caption("Check which chunks were retrieved, with rank and score.")
        rq = st.text_input(
            "Query",
            value=last_user_prompt[:260],
            placeholder="Enter a retrieval query",
            key="studio_retrieve_query",
        )
        rc1, rc2, rc3, rc4 = st.columns(4)
        with rc1:
            r_top_k = st.slider("Top K", 1, 30, 10, key="studio_retrieve_top_k")
        with rc2:
            r_threshold = st.slider("Threshold", 0.0, 1.0, 0.0, 0.01, key="studio_retrieve_threshold")
        with rc3:
            r_mode = st.selectbox(
                "Mode",
                ["focused", "balanced", "broad"],
                index=1,
                key="studio_retrieve_mode",
            )
        with rc4:
            r_graph = st.checkbox("Include graph", value=True, key="studio_retrieve_graph")

        if st.button(
            "Run Retrieval Check",
            type="primary",
            use_container_width=True,
            help="Calls /retrieve and returns ranked evidence chunks plus retrieval diagnostics.",
        ):
            with st.spinner("Running retrieval inspection..."):
                ok, payload, err, _ = api_request(
                    "POST",
                    "/retrieve",
                    timeout=45,
                    json={
                        "query": rq,
                        "top_k": int(r_top_k),
                        "score_threshold": float(r_threshold),
                        "include_graph": bool(r_graph),
                        "retrieval_mode": r_mode,
                    },
                )
            if ok and isinstance(payload, dict):
                st.session_state.studio_retrieve_result = payload
            else:
                st.session_state.studio_retrieve_result = {"error": err}

        retrieve_result = st.session_state.studio_retrieve_result
        if isinstance(retrieve_result, dict):
            if retrieve_result.get("error"):
                st.error(str(retrieve_result.get("error")))
            else:
                docs = retrieve_result.get("results") or []
                diag = retrieve_result.get("diagnostics") or {}
                st.markdown(
                    f"""
<div class="sf-inline">
  {badge(f"Docs: {len(docs)}", "ok" if docs else "warn")}
  {badge(f"Mode: {diag.get('mode', 'balanced')}", "neutral")}
  {badge(f"Vector hits: {diag.get('vector_hits_after_filter', 0)}", "neutral")}
</div>
""",
                    unsafe_allow_html=True,
                )

                if docs:
                    rows = [
                        {
                            "rank": d.get("rank"),
                            "source": d.get("source"),
                            "score": round(float(d.get("score", 0.0) or 0.0), 4),
                            "paper_id": d.get("paper_id"),
                            "title": d.get("title"),
                        }
                        for d in docs
                    ]
                    st.dataframe(rows, use_container_width=True)
                    for d in docs[:8]:
                        with st.expander(
                            f"#{d.get('rank', '?')} {d.get('title', 'Untitled')} ({d.get('source', 'Vector')})",
                            expanded=False,
                        ):
                            st.write(f"Score: `{float(d.get('score', 0.0) or 0.0):.4f}`")
                            st.write(f"Paper ID: `{d.get('paper_id', '')}`")
                            st.caption(str(d.get("text", ""))[:1200])

                with st.expander("Diagnostics JSON", expanded=False):
                    st.json(diag)
                with st.expander("Context preview", expanded=False):
                    st.write(retrieve_result.get("context_preview", ""))

    with t_eval:
        st.caption("Score how well an answer is grounded in available context.")
        eq = st.text_area(
            "Question",
            value=last_user_prompt[:1000],
            placeholder="Question that the answer should satisfy",
            key="studio_eval_question",
            height=90,
        )
        ea = st.text_area(
            "Answer to evaluate",
            value=last_assistant_answer[:6000],
            placeholder="Paste an answer here",
            key="studio_eval_answer",
            height=200,
        )
        ec = st.text_area(
            "Context (optional)",
            value="",
            placeholder="Leave empty to auto-retrieve context for this question",
            key="studio_eval_context",
            height=130,
        )

        if st.button(
            "Run Answer Score",
            type="primary",
            use_container_width=True,
            help="Calls /evaluate and returns grounding/relevance metrics with suggestions.",
        ):
            with st.spinner("Evaluating answer quality..."):
                ok, payload, err, _ = api_request(
                    "POST",
                    "/evaluate",
                    timeout=60,
                    json={
                        "question": eq,
                        "answer": ea,
                        "context": ec,
                    },
                )
            if ok and isinstance(payload, dict):
                st.session_state.studio_eval_result = payload
            else:
                st.session_state.studio_eval_result = {"error": err}

        eval_result = st.session_state.studio_eval_result
        if isinstance(eval_result, dict):
            if eval_result.get("error"):
                st.error(str(eval_result.get("error")))
            else:
                metrics = eval_result.get("metrics") or {}
                if metrics:
                    e1, e2, e3, e4 = st.columns(4)
                    with e1:
                        metric("Overall score", metrics.get("overall_score", 0))
                    with e2:
                        metric("Grounding", metrics.get("grounding_coverage", 0))
                    with e3:
                        metric("Sentence ratio", metrics.get("grounded_sentence_ratio", 0))
                    with e4:
                        metric("Citations", metrics.get("citation_markers", 0))
                    st.markdown(f"**Verdict**: `{metrics.get('verdict', 'unknown')}`")
                    suggestions = metrics.get("suggestions") or []
                    if suggestions:
                        st.markdown("**Suggestions**")
                        for s in suggestions:
                            st.write(f"- {s}")

                preview = eval_result.get("retrieval_preview") or []
                if preview:
                    st.markdown("**Auto-retrieved evidence preview**")
                    st.dataframe(
                        [
                            {
                                "rank": d.get("rank"),
                                "source": d.get("source"),
                                "score": round(float(d.get("score", 0.0) or 0.0), 4),
                                "title": d.get("title"),
                            }
                            for d in preview
                        ],
                        use_container_width=True,
                    )

    with t_arena:
        st.caption("Compare two prompt variants and review quality/latency tradeoffs.")
        a1, a2 = st.columns(2)
        with a1:
            left_prompt = st.text_area(
                "Prompt A",
                value=last_user_prompt[:1000],
                key="studio_arena_prompt_a",
                height=140,
            )
            left_mode = st.selectbox(
                "Mode A",
                ["fast", "balanced", "deep"],
                index=1,
                key="studio_arena_mode_a",
            )
        with a2:
            right_prompt = st.text_area(
                "Prompt B",
                value="",
                placeholder="Alternative wording to compare",
                key="studio_arena_prompt_b",
                height=140,
            )
            right_mode = st.selectbox(
                "Mode B",
                ["fast", "balanced", "deep"],
                index=2,
                key="studio_arena_mode_b",
            )

        if st.button(
            "Compare Prompts",
            type="primary",
            use_container_width=True,
            help="Runs two /generate calls side-by-side for prompt A/B comparison.",
        ):
            if not left_prompt.strip() or not right_prompt.strip():
                st.error("Provide both Prompt A and Prompt B.")
            else:
                with st.spinner("Running side-by-side comparison..."):
                    l_ok, l_payload, l_err, _ = api_request(
                        "POST",
                        "/generate",
                        timeout=180,
                        json={
                            "topic": left_prompt,
                            "mode": left_mode,
                            "include_diagnostics": True,
                        },
                    )
                    r_ok, r_payload, r_err, _ = api_request(
                        "POST",
                        "/generate",
                        timeout=180,
                        json={
                            "topic": right_prompt,
                            "mode": right_mode,
                            "include_diagnostics": True,
                        },
                    )
                st.session_state.studio_compare_result = {
                    "left": l_payload if l_ok and isinstance(l_payload, dict) else {"error": l_err},
                    "right": r_payload if r_ok and isinstance(r_payload, dict) else {"error": r_err},
                }

        compare_result = st.session_state.studio_compare_result
        if isinstance(compare_result, dict):
            c_left, c_right = st.columns(2)
            left_data = compare_result.get("left") or {}
            right_data = compare_result.get("right") or {}

            with c_left:
                st.markdown("### Prompt A")
                if left_data.get("error"):
                    st.error(str(left_data.get("error")))
                else:
                    left_stats = left_data.get("stats") or {}
                    metric("Latency ms", int(left_stats.get("latency_ms", 0) or 0))
                    metric("Citations", int(left_stats.get("citation_count", 0) or 0))
                    st.markdown(str(left_data.get("review", ""))[:1400])

            with c_right:
                st.markdown("### Prompt B")
                if right_data.get("error"):
                    st.error(str(right_data.get("error")))
                else:
                    right_stats = right_data.get("stats") or {}
                    metric("Latency ms", int(right_stats.get("latency_ms", 0) or 0))
                    metric("Citations", int(right_stats.get("citation_count", 0) or 0))
                    st.markdown(str(right_data.get("review", ""))[:1400])


# -----------------------------------------------------------------------------
# Knowledge Base page
# -----------------------------------------------------------------------------
elif st.session_state.page_mode == "Knowledge Base":
    st.markdown('<div class="sf-kicker">Knowledge Base</div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="sf-guide">
  <strong>Start here for your data</strong>
  <p>Upload PDFs first. They become the evidence used in Research Chat and RAG Studio.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    stats_ok, stats_payload, stats_err, stats_code = cached_get(
        "/admin/stats",
        timeout=10,
        use_admin_token=True,
        ttl_sec=20,
    )
    stats = stats_payload if stats_ok and isinstance(stats_payload, dict) else {}

    m1, m2, m3 = st.columns(3)
    with m1:
        metric("Documents", int(stats.get("documents", 0) or 0))
    with m2:
        metric("Passages", int(stats.get("passages", 0) or 0))
    with m3:
        metric("Embeddings", int(stats.get("embeddings", 0) or 0))

    if not stats_ok:
        tone = "warn" if stats_code in (401, 403) else "danger"
        st.markdown(badge("Stats unavailable", tone), unsafe_allow_html=True)
        st.caption(stats_err)

    st.session_state.kb_view = st.radio(
        "Knowledge Base view",
        ["Upload documents", "Corpus health"],
        index=0 if st.session_state.kb_view == "Upload documents" else 1,
        horizontal=True,
        key="kb_view_select",
    )

    if st.session_state.kb_view == "Upload documents":
        panel("Upload and index documents", "Each upload becomes searchable retrieval evidence.")

        file = st.file_uploader(
            "Upload PDF",
            type=["pdf"],
            help="Text is extracted, chunked, embedded, and indexed.",
        )

        if file is not None:
            st.write(f"Name: `{file.name}`")
            st.write(f"Size: `{file.size / 1024:.1f} KB`")

            if st.button(
                "Ingest document",
                type="primary",
                use_container_width=True,
                help="Extracts text, chunks it, embeds chunks, and indexes them in Qdrant.",
            ):
                with st.spinner("Ingesting document..."):
                    files = {
                        "file": (
                            file.name,
                            file.getvalue(),
                            "application/pdf",
                        )
                    }
                    ok, payload, err, _ = api_request(
                        "POST",
                        "/upload",
                        timeout=120,
                        files=files,
                    )

                if ok and isinstance(payload, dict):
                    st.success(
                        f"Indexed `{payload.get('title', file.name)}` with `{payload.get('chunks', 0)}` chunks."
                    )
                    clear_get_cache()
                    time.sleep(0.4)
                    st.rerun()
                else:
                    st.error(f"Ingestion failed: {err}")

    else:
        panel("Corpus health", "Check indexed vectors and paper coverage.")

        col_ok, col_payload, col_err, col_code = cached_get(
            "/admin/collection_info",
            timeout=10,
            use_admin_token=True,
            ttl_sec=20,
        )
        paper_ok, paper_payload, paper_err, paper_code = cached_get(
            "/admin/paper_count",
            timeout=10,
            use_admin_token=True,
            ttl_sec=20,
        )

        if col_ok and isinstance(col_payload, dict):
            st.write(f"Collection: `{col_payload.get('collection_name', 'N/A')}`")
            st.write(f"Vectors: `{col_payload.get('total_vectors', 0)}`")
        else:
            tone = "warn" if col_code in (401, 403) else "danger"
            st.markdown(badge("Collection info unavailable", tone), unsafe_allow_html=True)
            st.caption(col_err)

        if paper_ok and isinstance(paper_payload, dict):
            st.write(f"Unique papers: `{paper_payload.get('unique_papers', 0)}`")
            st.write(f"Sampled chunks: `{paper_payload.get('total_chunks_sampled', 0)}`")
        else:
            tone = "warn" if paper_code in (401, 403) else "danger"
            st.markdown(badge("Paper count unavailable", tone), unsafe_allow_html=True)
            st.caption(paper_err)


# -----------------------------------------------------------------------------
# Admin page
# -----------------------------------------------------------------------------
elif st.session_state.page_mode == "Admin":
    st.markdown('<div class="sf-kicker">Admin</div>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="sf-guide">
  <strong>Admin is optional</strong>
  <p>Use this page only for maintenance. Daily usage is Research + Knowledge Base.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.session_state.admin_view = st.radio(
        "Admin view",
        ["Operations", "Logs", "Diagnostics"],
        index=["Operations", "Logs", "Diagnostics"].index(st.session_state.admin_view)
        if st.session_state.admin_view in {"Operations", "Logs", "Diagnostics"}
        else 0,
        horizontal=True,
        key="admin_view_select",
    )

    status_ok, status_payload, status_err, status_code = cached_get(
        "/admin/migration_status",
        timeout=10,
        use_admin_token=True,
        ttl_sec=8,
    )
    status = status_payload if status_ok and isinstance(status_payload, dict) else {}

    info_ok = True
    info_payload: Any = {}
    info_err = ""
    info_code = 0
    if st.session_state.admin_view in {"Operations", "Diagnostics"}:
        info_ok, info_payload, info_err, info_code = cached_get(
            "/admin/system_info",
            timeout=10,
            use_admin_token=True,
            ttl_sec=20,
        )
    info = info_payload if info_ok and isinstance(info_payload, dict) else {}

    if not status_ok:
        tone = "warn" if status_code in (401, 403) else "danger"
        st.markdown(badge("Migration status unavailable", tone), unsafe_allow_html=True)
        st.caption(status_err)

    if st.session_state.admin_view in {"Operations", "Diagnostics"} and not info_ok:
        tone = "warn" if info_code in (401, 403) else "danger"
        st.markdown(badge("System info unavailable", tone), unsafe_allow_html=True)
        st.caption(info_err)

    ms1, ms2, ms3, ms4 = st.columns(4)
    with ms1:
        state = "Running" if status.get("running") else "Finished" if status.get("finished") else "Idle"
        metric("State", state)
    with ms2:
        metric("Migrated", int(status.get("migrated", 0) or 0))
    with ms3:
        metric("Errors", int(status.get("errors", 0) or 0))
    with ms4:
        metric("Uptime", status.get("uptime", "N/A"))

    if st.session_state.admin_view == "Operations":
        left, right = st.columns([1.35, 1], gap="large")

        with left:
            panel("Maintenance", "Operational actions for backend data and jobs.")
            confirm = st.checkbox("I understand this will permanently remove indexed vectors")

            if st.button(
                "Clear vector database",
                type="primary",
                use_container_width=True,
                disabled=not confirm,
                help="Deletes all indexed vectors. This is irreversible.",
            ):
                ok, _, err, _ = api_request(
                    "POST",
                    "/admin/clear_vector_db",
                    timeout=40,
                    use_admin_token=True,
                )
                if ok:
                    st.success("Vector database cleared")
                    clear_get_cache()
                    time.sleep(0.4)
                    st.rerun()
                else:
                    st.error(f"Clear failed: {err}")

            if st.button(
                "Restart migration",
                use_container_width=True,
                help="Restarts background schema migration on existing points.",
            ):
                ok, _, err, _ = api_request(
                    "POST",
                    "/admin/restart_migration",
                    timeout=10,
                    use_admin_token=True,
                )
                if ok:
                    st.success("Migration restarted")
                    clear_get_cache()
                    time.sleep(0.4)
                    st.rerun()
                else:
                    st.error(f"Restart failed: {err}")

        with right:
            panel("System profile", "Backend runtime profile")
            if info:
                st.write(f"Version: `{info.get('version', 'N/A')}`")
                st.write(f"Vector DB: `{info.get('vector_db', 'N/A')}`")
                st.write(f"Embedding model: `{info.get('embedding_model', 'N/A')}`")
                st.write(f"Collection: `{info.get('collection', 'N/A')}`")
                st.write(f"Migration ready: `{info.get('migration_ready', False)}`")

    elif st.session_state.admin_view == "Logs":
        panel("Activity logs", "Recent migration and maintenance activity")
        logs_ok, logs_payload, logs_err, logs_code = cached_get(
            "/admin/logs",
            timeout=10,
            use_admin_token=True,
            ttl_sec=8,
        )

        if not logs_ok:
            tone = "warn" if logs_code in (401, 403) else "danger"
            st.markdown(badge("Logs unavailable", tone), unsafe_allow_html=True)
            st.caption(logs_err)
        else:
            rows = logs_payload.get("logs", []) if isinstance(logs_payload, dict) else []
            if rows:
                level = st.selectbox("Filter level", ["all", "info", "warning", "error"], index=0)
                if level != "all":
                    rows = [r for r in rows if str(r.get("level", "")).lower() == level]

                if rows:
                    st.dataframe(rows[-60:], use_container_width=True)
                else:
                    st.caption("No logs for selected level")
            else:
                st.caption("No activity logs available")

    else:
        panel("Diagnostics", "Raw endpoint payloads")

        h_ok, h_payload, h_err, _ = cached_get("/health", timeout=8, ttl_sec=8)
        if h_ok:
            hs = str(h_payload.get("status", "unknown")).lower() if isinstance(h_payload, dict) else "unknown"
            st.markdown(badge(f"Service status: {hs}", "ok" if hs == "ok" else "warn"), unsafe_allow_html=True)
            st.json(h_payload)
        else:
            st.markdown(badge("Status endpoint unavailable", "danger"), unsafe_allow_html=True)
            st.caption(h_err)

        st.markdown("##### System info")
        st.json(info)

        st.markdown("##### Migration status")
        st.json(status)
