import streamlit as st
import requests
import time

# ----------------------------------------------------------
# 1. PAGE CONFIG
# ----------------------------------------------------------
st.set_page_config(
    page_title="ScholarFlow",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------
# 2. MODERN PROFESSIONAL STYLES
# ----------------------------------------------------------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bg-primary: #0a0e1a;
        --bg-secondary: #111827;
        --bg-tertiary: #1a1f35;
        --bg-card: #151b2e;
        --bg-card-hover: #1e2640;
        --border-subtle: #1e293b;
        --border-medium: #2d3a52;
        --accent-primary: #7c3aed;
        --accent-secondary: #a78bfa;
        --accent-gradient: linear-gradient(135deg, #7c3aed 0%, #a78bfa 100%);
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-tertiary: #64748b;
        --success: #10b981;
        --warning: #f59e0b;
        --error: #ef4444;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
        --shadow-glow: 0 0 20px rgba(124, 58, 237, 0.3);
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: var(--text-primary);
        background-color: var(--bg-primary);
        font-size: 15px;
        line-height: 1.6;
    }

    .block-container {
        padding: 2rem 3rem;
        max-width: 1600px;
    }

    /* Hide Streamlit branding but keep toolbar (for sidebar toggle) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;}
    header {background-color: transparent !important;}

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--border-medium);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-secondary);
    }

    /* ========== SIDEBAR ========== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1419 0%, #0a0e1a 100%);
        border-right: 1px solid var(--border-subtle);
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem;
    }

    section[data-testid="stSidebar"] h3 {
        font-size: 1.5rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
    }

    section[data-testid="stSidebar"] .element-container:first-child + div p {
        color: var(--text-tertiary);
        font-size: 0.8rem;
        margin-bottom: 1.5rem;
    }

    .stRadio > div {
        background-color: var(--bg-tertiary);
        border-radius: 12px;
        padding: 0.5rem;
        border: 1px solid var(--border-subtle);
    }

    .stRadio > div > label {
        background-color: transparent !important;
        border-radius: 8px;
        padding: 0.6rem 1rem !important;
        margin: 0 !important;
        transition: all 0.2s ease;
        color: var(--text-secondary) !important;
        font-weight: 500;
        font-size: 0.9rem;
    }

    .stRadio > div > label:hover {
        background-color: var(--bg-card-hover) !important;
        color: var(--text-primary) !important;
    }

    .stRadio > div > label[data-selected="true"] {
        background: var(--accent-gradient) !important;
        color: white !important;
        box-shadow: var(--shadow-glow);
    }

    section[data-testid="stSidebar"] hr {
        border: none;
        height: 1px;
        background: var(--border-subtle);
        margin: 1.5rem 0;
    }

    /* Base button styling (for all Streamlit buttons) */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        color: var(--text-primary);
        font-weight: 500;
        font-size: 0.9rem;
        padding: 0.6rem 1.0rem;
        transition: all 0.2s ease;
        box-shadow: none;
    }

    /* Primary CTA buttons (wrapped in .primary-action) */
    .primary-action button {
        width: 100%;
        border-radius: 14px !important;
        background: var(--accent-gradient) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 0.75rem 1.3rem !important;
        transition: all 0.25s ease !important;
        box-shadow: var(--shadow-md), var(--shadow-glow);
        letter-spacing: 0.01em;
    }

    .primary-action button:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-lg), var(--shadow-glow);
    }

    /* Conversation history items (recent conversations) */
    .sidebar-btn button {
        width: 100%;
        border-radius: 12px !important;
        border: 1px solid var(--border-subtle) !important;
        background: #020617 !important;
        color: var(--text-primary) !important;
        font-size: 0.9rem !important;
        text-align: left !important;
        padding: 0.75rem 0.95rem !important;
        transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease !important;
        font-weight: 500 !important;
        box-shadow: none !important;
        opacity: 0.95;
    }

    .sidebar-btn button:hover {
        background: var(--bg-card-hover) !important;
        border-color: var(--accent-secondary) !important;
        color: var(--text-primary) !important;
        transform: translateY(-1px);
        opacity: 1;
    }


    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: var(--shadow-lg), var(--shadow-glow);
    }

    .history-header {
        color: var(--text-tertiary);
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 1.5rem 0 0.8rem 0.3rem;
    }

    /* FINAL OVERRIDE: Recent conversation buttons */
    .sidebar-btn button {
        all: unset;
        display: block;
        width: 100%;
        box-sizing: border-box;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        background: #020617;
        border: 1px solid var(--border-subtle);
        color: var(--text-primary);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        font-size: 0.9rem;
        font-weight: 500;
        cursor: pointer;
        transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
    }

    .sidebar-btn button:hover {
        background: var(--bg-card-hover);
        border-color: var(--accent-secondary);
        transform: translateY(-1px);
    }




    /* ========== MAIN CONTENT ========== */
    .section-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, var(--text-primary) 0%, var(--accent-secondary) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .section-subtitle {
        font-size: 1rem;
        color: var(--text-secondary);
        margin-bottom: 2rem;
        line-height: 1.5;
    }

    .hero-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 4rem 2rem;
        text-align: center;
    }

    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        background: var(--accent-gradient);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.04em;
    }

    .hero-subtitle {
        color: var(--text-secondary);
        font-size: 1.1rem;
        max-width: 600px;
        line-height: 1.6;
    }

    .stChatMessage {
        background-color: transparent !important;
        padding: 1.5rem 0 !important;
    }

    [data-testid="stChatMessageContent"] {
        background-color: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        box-shadow: var(--shadow-sm);
    }

    [data-testid="stChatMessageContent"] p {
        margin-bottom: 0.8rem;
        line-height: 1.7;
    }

    [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-card) 100%);
        border-color: var(--border-medium);
    }

    .stChatInput {
        border-top: 1px solid var(--border-subtle);
        padding-top: 1.5rem;
        background: linear-gradient(180deg, transparent 0%, var(--bg-primary) 20%);
    }

    .stChatInput > div > div {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-medium) !important;
        border-radius: 16px !important;
        box-shadow: var(--shadow-md);
    }

    .stChatInput textarea {
        background-color: transparent !important;
        color: var(--text-primary) !important;
        font-size: 0.95rem !important;
        padding: 0.9rem 1.2rem !important;
    }

    .stChatInput textarea::placeholder {
        color: var(--text-tertiary) !important;
    }

    .stChatInput button {
        background: var(--accent-gradient) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem !important;
        transition: all 0.2s ease !important;
    }

    .stChatInput button:hover {
        transform: scale(1.05);
        box-shadow: var(--shadow-glow);
    }

    .meta-section-title {
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 1.2rem;
        color: var(--text-primary);
        letter-spacing: -0.02em;
    }

    .meta-card {
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-tertiary) 100%);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-sm);
    }

    .meta-card:hover {
        border-color: var(--border-medium);
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }

    .meta-label {
        color: var(--accent-secondary);
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .meta-label::before {
        content: "●";
        color: var(--accent-primary);
        font-size: 0.6rem;
    }

    .meta-content {
        color: var(--text-primary);
        font-size: 0.9rem;
        line-height: 1.6;
        white-space: pre-wrap;
    }

    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .status-running {
        background: rgba(16, 185, 129, 0.15);
        color: var(--success);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .status-finished {
        background: rgba(167, 139, 250, 0.15);
        color: var(--accent-secondary);
        border: 1px solid rgba(167, 139, 250, 0.3);
    }

    .status-idle {
        background: rgba(100, 116, 139, 0.15);
        color: var(--text-tertiary);
        border: 1px solid rgba(100, 116, 139, 0.3);
    }

    .upload-area {
        border: 2px dashed var(--accent-primary);
        padding: 3rem 2rem;
        border-radius: 16px;
        text-align: center;
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-tertiary) 100%);
        margin-bottom: 2rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .upload-area::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(circle at center, rgba(124, 58, 237, 0.1) 0%, transparent 70%);
        pointer-events: none;
    }

    .upload-area:hover {
        border-color: var(--accent-secondary);
        background: linear-gradient(135deg, var(--bg-tertiary) 0%, var(--bg-card) 100%);
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }

    .upload-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: var(--text-primary);
    }

    .upload-description {
        color: var(--text-secondary);
        font-size: 0.95rem;
        line-height: 1.5;
    }

    .stFileUploader {
        border: none !important;
    }

    [data-testid="stFileUploader"] section {
        background-color: transparent !important;
        border: none !important;
    }

    [data-testid="stFileUploader"] button {
        background: var(--bg-tertiary) !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-primary) !important;
        border-radius: 10px !important;
        padding: 0.7rem 1.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stFileUploader"] button:hover {
        background: var(--bg-card-hover) !important;
        border-color: var(--accent-primary) !important;
    }

    .stat-container {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
    }

    .stat-container:hover {
        border-color: var(--accent-primary);
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }

    .stat-label {
        color: var(--text-secondary);
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }

    .stat-value {
        color: var(--accent-secondary);
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    .info-box {
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.08) 0%, rgba(167, 139, 250, 0.08) 100%);
        border: 1px solid rgba(124, 58, 237, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
    }

    .info-box h4 {
        color: var(--accent-secondary);
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
    }

    .info-box ul {
        margin: 0;
        padding-left: 1.2rem;
        color: var(--text-secondary);
    }

    .info-box li {
        margin-bottom: 0.5rem;
        line-height: 1.6;
    }

    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 1.5rem;
        }

        .section-title {
            font-size: 1.5rem;
        }

        .hero-title {
            font-size: 2.5rem;
        }

        .meta-card {
            padding: 1rem;
        }
    }
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------
# 3. STATE MANAGEMENT
# ----------------------------------------------------------
if "conversations" not in st.session_state:
    st.session_state.conversations = []
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "working_messages" not in st.session_state:
    st.session_state.working_messages = []
if "page_mode" not in st.session_state:
    st.session_state.page_mode = "Research Agent"


def get_active_conversation():
    cid = st.session_state.active_chat_id
    if cid is None:
        return None
    for c in st.session_state.conversations:
        if c["id"] == cid:
            return c
    return None


def handle_user_query(prompt: str):
    """Shared logic for chat input and quick prompts."""
    if not prompt or not prompt.strip():
        return

    st.session_state.working_messages.append(
        {"role": "user", "content": prompt}
    )

    try:
        with st.spinner(
            "🤖 Research agents at work: Planning → Retrieving → Synthesizing..."
        ):
            response = requests.post(
                "http://localhost:8000/generate",
                json={"topic": prompt},
                timeout=180,
            )

        if response.status_code != 200:
            error_msg = (
                f"⚠️ Backend error (HTTP {response.status_code}). Please try again."
            )
            st.session_state.working_messages.append(
                {"role": "assistant", "content": error_msg}
            )
        else:
            data = response.json()
            review = data.get("review", "")
            queries = data.get("queries", [])
            critique = data.get("critique", "")
            stats = data.get("stats", {}) or {}
            citations = data.get("citations", []) or []

            st.session_state.working_messages.append(
                {
                    "role": "assistant",
                    "content": review,
                    "queries": queries,
                    "critique": critique,
                    "stats": stats,
                    "citations": citations,
                }
            )

            # Save or update conversation
            active_conv = get_active_conversation()
            if active_conv is None:
                new_id = (
                    max([c["id"] for c in st.session_state.conversations]) + 1
                    if st.session_state.conversations
                    else 1
                )
                st.session_state.conversations.append(
                    {
                        "id": new_id,
                        "title": prompt[:50],
                        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "messages": st.session_state.working_messages,
                    }
                )
                st.session_state.active_chat_id = new_id
            else:
                active_conv["messages"] = st.session_state.working_messages

    except requests.exceptions.Timeout:
        st.session_state.working_messages.append(
            {
                "role": "assistant",
                "content": "⏱️ Request timed out. The query may be too complex. Please try a more specific question.",
            }
        )
    except requests.exceptions.ConnectionError:
        st.session_state.working_messages.append(
            {
                "role": "assistant",
                "content": "🔌 Cannot connect to backend server. Please ensure the API is running on http://localhost:8000",
            }
        )
    except Exception as e:
        st.session_state.working_messages.append(
            {"role": "assistant", "content": f"❌ Unexpected error: {str(e)}"}
        )

    st.rerun()


# ----------------------------------------------------------
# 4. SIDEBAR
# ----------------------------------------------------------
with st.sidebar:
    st.markdown("### ScholarFlow")
    st.caption("Autonomous research workspace powered by AI")

    selected_mode = st.radio(
        "Workspace",
        ["Research Agent", "Knowledge Base", "Admin"],
        index=["Research Agent", "Knowledge Base", "Admin"].index(
            st.session_state.page_mode
        ),
        label_visibility="collapsed",
    )
    st.session_state.page_mode = selected_mode

    st.markdown("---")

    # Primary CTA with gradient
    st.markdown("<div class='primary-action'>", unsafe_allow_html=True)
    if st.button("✨ New conversation", use_container_width=True, key="new_conversation"):
        st.session_state.active_chat_id = None
        st.session_state.working_messages = []
        st.session_state.page_mode = "Research Agent"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="history-header">RECENT CONVERSATIONS</div>', unsafe_allow_html=True)

    if not st.session_state.conversations:
        st.caption("No conversations yet. Start one to begin!")
    else:
        for conv in reversed(st.session_state.conversations):
            label = conv["title"][:32] + ("…" if len(conv["title"]) > 32 else "")
            key = f"conv_{conv['id']}"

            with st.container():
                st.markdown("<div class='sidebar-btn'>", unsafe_allow_html=True)
                # NOTE: no emoji here
                if st.button(label, key=key, use_container_width=True):
                    st.session_state.active_chat_id = conv["id"]
                    st.session_state.working_messages = conv["messages"]
                    st.session_state.page_mode = "Research Agent"
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)



# ----------------------------------------------------------
# 5. MAIN CONTENT
# ----------------------------------------------------------

# ==========================================================
# VIEW 1: RESEARCH AGENT
# ==========================================================
if st.session_state.page_mode == "Research Agent":
    st.markdown(
        '<div class="section-title">🔬 Research Agent</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Ask research questions and get comprehensive, citation-backed answers powered by autonomous AI agents.</div>',
        unsafe_allow_html=True,
    )

    col_main, col_meta = st.columns([2.8, 1.2], gap="large")

    # ---------- MAIN CHAT AREA ----------
    with col_main:
        messages = st.session_state.working_messages

        if not messages:
            # Empty state hero
            st.markdown(
                """
                <div class="hero-container">
                    <div class="hero-title">GraphScholar</div>
                    <div class="hero-subtitle">
                        Your AI research assistant for retrieval-augmented generation.
                        It plans queries, retrieves from your vector database, and synthesizes
                        literature-style answers grounded in real sources.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("### Quick RAG prompts")

            qcol1, qcol2 = st.columns(2, gap="medium")

            with qcol1:
                if st.button(
                    "🔍 Compare Qdrant, Pinecone, and Weaviate as vector databases for RAG workloads",
                    use_container_width=True,
                ):
                    handle_user_query(
                        "Compare Qdrant, Pinecone, and Weaviate as vector databases for RAG workloads. Cover indexing, filtering, scalability, and cost trade-offs."
                    )

                if st.button(
                    "🧱 Design a retrieval-augmented generation pipeline for legal documents",
                    use_container_width=True,
                ):
                    handle_user_query(
                        "Design a retrieval-augmented generation (RAG) pipeline for long legal documents, including chunking strategy, embedding model choice, and vector database design."
                    )

            with qcol2:
                if st.button(
                    "📊 How do we evaluate RAG systems (retrieval vs generation metrics)?",
                    use_container_width=True,
                ):
                    handle_user_query(
                        "Explain how to evaluate retrieval-augmented generation systems, including retrieval metrics, generation metrics, and end-to-end evaluation strategies."
                    )

                if st.button(
                    "🧠 Best practices for embeddings, chunking, and metadata in production RAG",
                    use_container_width=True,
                ):
                    handle_user_query(
                        "Summarize best practices for embeddings, chunking, and metadata design when deploying a production RAG system."
                    )

        # Render existing conversation
        for msg in messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if (
                    msg["role"] == "assistant"
                    and msg.get("queries")
                    and isinstance(msg.get("queries"), list)
                ):
                    with st.expander("📚 View search queries used"):
                        for i, query in enumerate(msg["queries"], 1):
                            st.markdown(f"**{i}.** {query}")

    # ---------- RUN DETAILS ----------
    with col_meta:
        st.markdown(
            '<div class="meta-section-title">🔍 Run Details</div>',
            unsafe_allow_html=True,
        )

        last_assistant = None
        for msg in reversed(st.session_state.working_messages):
            if msg["role"] == "assistant":
                last_assistant = msg
                break

        if last_assistant is None:
            st.markdown(
                """
                <div class="meta-card">
                    <div class="meta-label">Status</div>
                    <div class="meta-content">
                        <span class="status-badge status-idle">Idle</span>
                        <p style="margin-top: 0.8rem; color: var(--text-secondary); font-size: 0.85rem;">
                            No active research session. Submit a query to begin.
                        </p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            first_user = next(
                (
                    m
                    for m in st.session_state.working_messages
                    if m["role"] == "user"
                ),
                None,
            )
            query_text = first_user["content"] if first_user else "Current query"

            st.markdown(
                f"""
                <div class="meta-card">
                    <div class="meta-label">Research Query</div>
                    <div class="meta-content">{query_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            queries = last_assistant.get("queries") or []
            if queries:
                queries_html = "<br>".join(
                    f"<span style='color: var(--accent-secondary);'>•</span> {q}"
                    for q in queries
                )
            else:
                queries_html = "<em>No structured search plan available</em>"

            st.markdown(
                f"""
                <div class="meta-card">
                    <div class="meta-label">Search Strategy</div>
                    <div class="meta-content">{queries_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            critique = (last_assistant.get("critique") or "").strip()
            if not critique:
                critique = "<em>No quality review available for this response</em>"

            st.markdown(
                f"""
                <div class="meta-card">
                    <div class="meta-label">Quality Review</div>
                    <div class="meta-content">{critique}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # --- NEW: LLM vs retrieved token stats ---
            stats = last_assistant.get("stats") or {}
            llm_tokens = int(stats.get("llm_tokens", 0) or 0)
            retrieved_tokens = int(stats.get("retrieved_tokens", 0) or 0)
            total_tokens = llm_tokens + retrieved_tokens

            if total_tokens > 0:
                llm_pct = int(round(llm_tokens / total_tokens * 100))
                retrieved_pct = 100 - llm_pct

                st.markdown(
                    f"""
                    <div class="meta-card">
                        <div class="meta-label">Content Mix</div>
                        <div class="meta-content">
                            <strong>LLM tokens:</strong> {llm_tokens} ({llm_pct}%)<br>
                            <strong>Retrieved tokens:</strong> {retrieved_tokens} ({retrieved_pct}%)
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # --- NEW: Clickable references ---
            citations = last_assistant.get("citations") or []
            citations_items = ""
            for c in citations:
                title = c.get("title", "Source")
                url = c.get("url", "")
                snippet = c.get("snippet", "")

                if url:
                    link = f'<a href="{url}" target="_blank" style="color: var(--accent-secondary); text-decoration: none;">{title}</a>'
                else:
                    link = f'<span style="color: var(--accent-secondary);">{title}</span>'

                citations_items += "<li>" + link
                if snippet:
                    citations_items += (
                        "<br><span style='color: var(--text-secondary); "
                        "font-size: 0.85rem;'>"
                        + snippet
                        + "</span>"
                    )
                citations_items += "</li>"

            if not citations_items:
                citations_items = (
                    "<li><em>No references returned for this answer.</em></li>"
                )

            st.markdown(
                f"""
                <div class="meta-card">
                    <div class="meta-label">References</div>
                    <div class="meta-content">
                        <ul style="padding-left: 1.1rem; margin: 0;">
                            {citations_items}
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div class="meta-card">
                    <div class="meta-label">Status</div>
                    <div class="meta-content">
                        <span class="status-badge status-finished">Completed</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Chat input
    user_prompt = st.chat_input(
        "Ask a research question or request clarification..."
    )
    if user_prompt:
        handle_user_query(user_prompt)

# ==========================================================
# VIEW 2: KNOWLEDGE BASE
# ==========================================================
elif st.session_state.page_mode == "Knowledge Base":
    st.markdown(
        '<div class="section-title">📚 Knowledge Base</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Upload and manage research papers to expand the corpus used for intelligent retrieval.</div>',
        unsafe_allow_html=True,
    )

    col_upload, col_info = st.columns([2.2, 1.8], gap="large")

    with col_upload:
        st.markdown(
            """
            <div class="upload-area">
                <div style="position: relative; z-index: 1;">
                    <div class="upload-title">📄 Upload Research Documents</div>
                    <div class="upload-description">
                        PDFs will be parsed, chunked, embedded with state-of-the-art models, 
                        and indexed in the vector database for semantic retrieval.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload academic papers, research articles, or technical documents",
            label_visibility="collapsed",
        )

        if uploaded_file:
            st.markdown(
                f"""
                <div class="info-box">
                    <h4>📎 Selected File</h4>
                    <ul>
                        <li><strong>Name:</strong> {uploaded_file.name}</li>
                        <li><strong>Size:</strong> {uploaded_file.size / 1024:.1f} KB</li>
                        <li><strong>Type:</strong> {uploaded_file.type}</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_btn1, col_btn2 = st.columns([1, 1])

            with col_btn1:
                if st.button(
                    "🚀 Ingest Document",
                    use_container_width=True,
                    type="primary",
                ):
                    with st.spinner(
                        "Processing document... This may take a minute."
                    ):
                        try:
                            files = {
                                "file": (
                                    uploaded_file.name,
                                    uploaded_file.getvalue(),
                                    "application/pdf",
                                )
                            }
                            response = requests.post(
                                "http://localhost:8000/upload",
                                files=files,
                                timeout=120,
                            )

                            if response.status_code == 200:
                                metadata = response.json()
                                st.success(
                                    f"✅ Successfully indexed: **{metadata.get('title', uploaded_file.name)}**"
                                )
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(
                                    f"❌ Ingestion failed with status {response.status_code}"
                                )

                        except requests.exceptions.Timeout:
                            st.error(
                                "⏱️ Upload timed out. Try a smaller file or check server status."
                            )
                        except requests.exceptions.ConnectionError:
                            st.error(
                                "🔌 Cannot connect to backend. Ensure the API server is running."
                            )
                        except Exception as e:
                            st.error(f"❌ Upload error: {str(e)}")

            with col_btn2:
                if st.button(
                    "🔄 Clear Selection", use_container_width=True
                ):
                    st.rerun()

        # Corpus stats
        try:
            stats_response = requests.get(
                "http://localhost:8000/admin/stats", timeout=5
            )
            if stats_response.status_code == 200:
                stats = stats_response.json()

                st.markdown("---")
                st.markdown("### 📊 Corpus Statistics")

                stat_cols = st.columns(3)

                with stat_cols[0]:
                    st.markdown(
                        f"""
                        <div class="stat-container">
                            <div class="stat-label">Documents</div>
                            <div class="stat-value">{stats.get('documents', 0)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with stat_cols[1]:
                    st.markdown(
                        f"""
                        <div class="stat-container">
                            <div class="stat-label">Passages</div>
                            <div class="stat-value">{stats.get('passages', 0)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with stat_cols[2]:
                    st.markdown(
                        f"""
                        <div class="stat-container">
                            <div class="stat-label">Embeddings</div>
                            <div class="stat-value">{stats.get('embeddings', 0)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        except Exception:
            pass

    with col_info:
        st.markdown("### 🔧 How It Works")

        st.markdown(
            """
            <div class="info-box">
                <h4>Document Processing Pipeline</h4>
                <ul>
                    <li><strong>Extraction:</strong> Text is extracted from PDF with metadata preservation.</li>
                    <li><strong>Chunking:</strong> Content is split into semantic passages (~500 tokens).</li>
                    <li><strong>Embedding:</strong> Each passage is encoded using transformer models.</li>
                    <li><strong>Indexing:</strong> Vectors are stored in Qdrant for fast similarity search.</li>
                    <li><strong>Retrieval:</strong> Hybrid search (dense + sparse) finds relevant passages.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### 💡 Best Practices")

        st.markdown(
            """
            <div class="info-box">
                <ul>
                    <li>Upload high-quality PDFs with selectable text (not scanned images).</li>
                    <li>Include diverse papers to cover different perspectives.</li>
                    <li>Use recent publications for cutting-edge research questions.</li>
                    <li>Organize documents by topic for better retrieval accuracy.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ==========================================================
# VIEW 3: ADMIN
# ==========================================================
elif st.session_state.page_mode == "Admin":
    st.markdown(
        '<div class="section-title">⚙️ System Administration</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Monitor system health, manage background processes, and maintain the vector database.</div>',
        unsafe_allow_html=True,
    )

    try:
        status_response = requests.get(
            "http://localhost:8000/admin/migration_status", timeout=10
        )
        status = (
            status_response.json()
            if status_response.status_code == 200
            else None
        )
    except Exception:
        status = None

    if status is None:
        st.error(
            "🔌 Cannot connect to backend API. Please ensure the server is running on http://localhost:8000"
        )
        st.stop()

    st.markdown("### 📈 System Status")

    status_cols = st.columns(4)

    with status_cols[0]:
        if status.get("running"):
            badge_class = "status-running"
            badge_text = "Running"
            icon = "🟢"
        elif status.get("finished"):
            badge_class = "status-finished"
            badge_text = "Finished"
            icon = "🔵"
        else:
            badge_class = "status-idle"
            badge_text = "Idle"
            icon = "⚪"

        st.markdown(
            f"""
            <div class="stat-container">
                <div class="stat-label">Process State</div>
                <div style="font-size: 2rem; margin: 0.5rem 0;">{icon}</div>
                <span class="status-badge {badge_class}">{badge_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with status_cols[1]:
        st.markdown(
            f"""
            <div class="stat-container">
                <div class="stat-label">Migrated</div>
                <div class="stat-value">{status.get('migrated', 0)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with status_cols[2]:
        st.markdown(
            f"""
            <div class="stat-container">
                <div class="stat-label">Errors</div>
                <div class="stat-value" style="color: {'var(--error)' if status.get('errors', 0) > 0 else 'var(--success)'};">
                    {status.get('errors', 0)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with status_cols[3]:
        uptime = status.get("uptime", "N/A")
        st.markdown(
            f"""
            <div class="stat-container">
                <div class="stat-label">Uptime</div>
                <div class="stat-value" style="font-size: 1.5rem;">{uptime}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col_maint, col_logs = st.columns([1.5, 1.5], gap="large")

    with col_maint:
        st.markdown("### 🔧 Database Maintenance")

        st.markdown(
            """
            <div class="info-box">
                <h4>⚠️ Warning</h4>
                <ul>
                    <li>Clearing the vector database will permanently delete all indexed documents and embeddings.</li>
                    <li>This action cannot be undone.</li>
                    <li>You will need to re-upload all documents after clearing.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        confirm = st.checkbox(
            "I understand the consequences of clearing the database"
        )

        if st.button(
            "🗑️ Clear Vector Database",
            use_container_width=True,
            disabled=not confirm,
            type="primary" if confirm else "secondary",
        ):
            with st.spinner("Clearing vector database..."):
                try:
                    clear_response = requests.post(
                        "http://localhost:8000/admin/clear_vector_db",
                        timeout=30,
                    )

                    if clear_response.status_code == 200:
                        st.success(
                            "✅ Vector database has been successfully cleared!"
                        )
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(
                            f"❌ Clear operation failed with status {clear_response.status_code}"
                        )

                except requests.exceptions.Timeout:
                    st.error(
                        "⏱️ Clear operation timed out. The database may be large."
                    )
                except requests.exceptions.ConnectionError:
                    st.error("🔌 Cannot connect to backend server.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

        st.markdown("### 🔄 Background Jobs")

        if st.button(
            "🔃 Restart Migration Process", use_container_width=True
        ):
            try:
                restart_response = requests.post(
                    "http://localhost:8000/admin/restart_migration",
                    timeout=10,
                )
                if restart_response.status_code == 200:
                    st.success("✅ Migration process restarted")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Failed to restart migration")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    with col_logs:
        st.markdown("### 📋 Recent Activity")

        try:
            logs_response = requests.get(
                "http://localhost:8000/admin/logs", timeout=5
            )
            if logs_response.status_code == 200:
                logs = logs_response.json().get("logs", [])

                if logs:
                    for log in logs[-10:]:
                        timestamp = log.get("timestamp", "Unknown")
                        message = log.get("message", "")
                        level = log.get("level", "info")

                        if level == "error":
                            icon = "❌"
                            color = "var(--error)"
                        elif level == "warning":
                            icon = "⚠️"
                            color = "var(--warning)"
                        else:
                            icon = "ℹ️"
                            color = "var(--text-secondary)"

                        st.markdown(
                            f"""
                            <div class="meta-card" style="margin-bottom: 0.5rem;">
                                <div style="display: flex; align-items: start; gap: 0.5rem;">
                                    <span style="font-size: 1.2rem;">{icon}</span>
                                    <div style="flex: 1;">
                                        <div style="color: {color}; font-size: 0.85rem; font-weight: 500;">
                                            {message}
                                        </div>
                                        <div style="color: var(--text-tertiary); font-size: 0.75rem; margin-top: 0.2rem;">
                                            {timestamp}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("No recent activity to display")
            else:
                st.warning("Could not fetch activity logs")
        except Exception:
            st.warning("Activity logs unavailable")

        st.markdown("### 🔍 System Info")

        try:
            info_response = requests.get(
                "http://localhost:8000/admin/system_info", timeout=5
            )
            if info_response.status_code == 200:
                info = info_response.json()

                st.markdown(
                    f"""
                    <div class="meta-card">
                        <div class="meta-label">Backend Version</div>
                        <div class="meta-content">{info.get('version', 'Unknown')}</div>
                    </div>
                    <div class="meta-card">
                        <div class="meta-label">Vector DB</div>
                        <div class="meta-content">{info.get('vector_db', 'Qdrant')}</div>
                    </div>
                    <div class="meta-card">
                        <div class="meta-label">Embedding Model</div>
                        <div class="meta-content">{info.get('embedding_model', 'Unknown')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        except Exception:
            st.info("System information unavailable")
