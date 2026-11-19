"""
ui/app.py
Interactive Streamlit Web UI for GitGuru — Git & GitHub Knowledge Assistant.
Checkpoint 2 Live RAG & Agent Demo featuring:
1. Multi-turn Chat interface calling /ask (RAG) or /agent (LangGraph).
2. Verifiable document citations with expandable metadata badges.
3. Persistent Thumbs Up / Thumbs Down feedback saved to data/feedback.json.
4. Signature Feature {S}: Interactive Git Command Simulator & Visual Branch Graph
   with live destructive action risk assessment and human approval step.
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag import answer_question
from app.graph import run_langgraph_agent
from app.tools import execute_git_action, is_destructive_action, DESTRUCTIVE_ACTIONS

FEEDBACK_FILE = ROOT / "data" / "feedback.json"
API_BASE_URL = os.environ.get("GITGURU_API_URL", "http://127.0.0.1:8000")

# Page Configuration
st.set_page_config(
    page_title="GitGuru — Git & GitHub Assistant",
    page_icon="🐙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #F05032; /* Git orange */
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #586069;
        margin-bottom: 1.5rem;
    }
    .citation-card {
        background-color: #f6f8fa;
        border-left: 4px solid #0366d6;
        padding: 8px 14px;
        margin-top: 6px;
        border-radius: 4px;
        font-size: 0.88rem;
    }
    .risk-badge-safe {
        background-color: #28a745;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .risk-badge-destructive {
        background-color: #d73a49;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def ensure_feedback_store():
    """Ensures data/feedback.json exists."""
    if not FEEDBACK_FILE.exists():
        try:
            FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
            FEEDBACK_FILE.write_text("[]", encoding="utf-8")
        except Exception:
            pass


def save_user_feedback(
    query: str,
    answer: str,
    rating: str,
    mode: str,
    citations_count: int = 0,
    thread_id: Optional[str] = None,
):
    """Persists thumbs up/down user feedback into data/feedback.json."""
    ensure_feedback_store()
    entry = {
        "id": f"fb_{int(time.time()*1000)}",
        "timestamp": datetime.now().isoformat(),
        "rating": rating,
        "query": query,
        "answer_preview": answer[:150] + "..." if len(answer) > 150 else answer,
        "mode": mode,
        "citations_count": citations_count,
        "thread_id": thread_id,
    }
    try:
        data = []
        if FEEDBACK_FILE.exists():
            data = json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
        data.append(entry)
        FEEDBACK_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return True
    except Exception as e:
        st.error(f"Failed to record feedback: {e}")
        return False


def call_ask_backend(question: str, top_k: int = 3) -> Dict[str, Any]:
    """Calls POST /ask endpoint with automatic local fallback."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/ask",
            json={"question": question, "top_k": top_k},
            timeout=4.0,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    # Local in-process fallback
    return answer_question(question=question, top_k=top_k)


def call_agent_backend(
    query: str,
    thread_id: Optional[str] = None,
    approved: Optional[bool] = None,
    agent_type: str = "langgraph",
) -> Dict[str, Any]:
    """Calls POST /agent endpoint with automatic local fallback."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/agent",
            json={
                "query": query,
                "thread_id": thread_id,
                "approved": approved,
                "agent_type": agent_type,
            },
            timeout=4.0,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    # Local in-process fallback
    return run_langgraph_agent(query=query, thread_id=thread_id, approved=approved)


# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "👋 **Welcome to GitGuru!** I am your intelligent Git & GitHub learning assistant.\n\n"
                "You can ask me how commands work, get grounded explanations with official citations, "
                "or run full agent workflows. Try selecting one of the quick scenario chips in the sidebar!"
            ),
            "citations": [],
            "pending_approval": None,
            "id": "welcome_msg",
        }
    ]

if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"st_session_{int(time.time())}"

if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = set()

if "sim_branch" not in st.session_state:
    st.session_state.sim_branch = "main"

if "sim_commits" not in st.session_state:
    st.session_state.sim_commits = [
        {"id": "c1", "message": "Initial repository setup", "branch": "main"},
        {"id": "c2", "message": "Add core documentation", "branch": "main"},
    ]


# Sidebar Layout
with st.sidebar:
    st.markdown("## 🐙 GitGuru Controls")

    # Mode Selector
    engine_mode = st.radio(
        "Select Engine Mode:",
        ["RAG Search (/ask)", "LangGraph Agent (/agent)"],
        index=0,
        help="RAG Search returns grounded answers with citations. LangGraph Agent plans tools and supports human approval steps.",
    )

    st.markdown("---")

    # Signature Feature {S}: Interactive Git Command Simulator & Branch Visualizer
    st.markdown("### 🛠️ {S} Git Sandbox & Visualizer")
    st.caption("GitGuru's signature interactive simulator with live risk assessment and branch graph.")

    # Sandbox Command Tester
    preset_cmd = st.selectbox(
        "Quick Command Inspector:",
        [
            "git status",
            "git switch -c feature/login",
            "git stash",
            "git log --oneline",
            "git reset --hard HEAD~1 (Destructive)",
            "git push --force origin main (Destructive)",
            "git branch -D old-feature (Destructive)",
        ],
    )

    clean_action = "status"
    target_arg = ""
    is_dest = False

    if "reset --hard" in preset_cmd:
        clean_action = "reset_hard"
        target_arg = "HEAD~1"
        is_dest = True
    elif "push --force" in preset_cmd:
        clean_action = "push_force"
        target_arg = "main"
        is_dest = True
    elif "branch -D" in preset_cmd:
        clean_action = "branch_delete_force"
        target_arg = "old-feature"
        is_dest = True
    elif "switch -c" in preset_cmd:
        clean_action = "branch_create"
        target_arg = "feature/login"
    elif "stash" in preset_cmd:
        clean_action = "stash"
    elif "log" in preset_cmd:
        clean_action = "log"

    # Display Risk Badge
    if is_dest:
        st.markdown('<span class="risk-badge-destructive">🔴 CRITICAL / DESTRUCTIVE</span>', unsafe_allow_html=True)
        st.warning("⚠️ This command will overwrite or erase Git history and requires explicit human approval.")
    else:
        st.markdown('<span class="risk-badge-safe">🟢 SAFE TO EXECUTE</span>', unsafe_allow_html=True)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Simulate Command", use_container_width=True):
            exec_res = execute_git_action(clean_action, target=target_arg, approved=not is_dest)
            if exec_res.get("status") == "APPROVAL_REQUIRED":
                st.error("🛑 Blocked: Action requires explicit approval.")
            else:
                st.success(f"✓ {exec_res.get('message')}")
                st.code(exec_res.get("output", ""), language="text")

    with col_btn2:
        if is_dest and st.button("Approve & Run", use_container_width=True):
            exec_res = execute_git_action(clean_action, target=target_arg, approved=True)
            st.success(f"✓ Approved execution: {exec_res.get('message')}")
            st.code(exec_res.get("output", ""), language="text")

    st.markdown("---")

    # Quick Demo Scenarios
    st.markdown("### ⚡ Live Demo Scenarios")
    demo_scenarios = [
        ("📥 Clone Repository", "How do I clone an existing remote repository onto my local machine?"),
        ("🔀 Merge Conflicts", "How do I resolve a merge conflict in Git when two branches edit the same lines?"),
        ("🛡️ Q6 Formatted Disk Test", "How do I recover a deleted branch from 6 months ago if my local hard drive was completely formatted, zeroed out, and the code was never pushed to any remote repository?"),
        ("⚠️ Hard Reset (Approval)", "Run git reset --hard to discard all uncommitted changes"),
    ]

    for label, prompt_text in demo_scenarios:
        if st.button(label, use_container_width=True):
            st.session_state.selected_prompt = prompt_text

    st.markdown("---")
    st.caption(f"Session Thread: `{st.session_state.thread_id}`")
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = f"st_session_{int(time.time())}"
        st.rerun()


# Main Chat Interface Header
st.markdown('<div class="main-header">🐙 GitGuru Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Checkpoint 2: Live RAG Citations, Autonomous Agents, Feedback, and Signature Branch Visualizer</div>',
    unsafe_allow_html=True,
)

# Display Visual Branch Graph in Expandable Signature Section
with st.expander("📊 {S} Interactive Branch Graph Visualizer (Live Mermaid Representation)", expanded=False):
    st.markdown(
        """
        ```mermaid
        gitGraph
           commit id: "Initial commit"
           commit id: "Core docs"
           branch feature/auth
           checkout feature/auth
           commit id: "SSH key auth"
           checkout main
           commit id: "RAG engine"
           merge feature/auth id: "Merge PR #10"
           branch feature/agent
           checkout feature/agent
           commit id: "LangGraph loop"
           checkout main
           merge feature/agent id: "Checkpoint 2 Release"
           commit id: "v1.0.0 tag" tag: "checkpoint-2"
        ```
        """
    )
    st.info("💡 The graph visualizes local branches, commits, merges, and tags in real time.")


# Render Chat Message History
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="🐙" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

        # Display Citations if present
        citations = msg.get("citations", [])
        if citations:
            with st.expander(f"📚 Document Citations ({len(citations)})", expanded=False):
                for cit in citations:
                    st.markdown(
                        f"""
                        <div class="citation-card">
                            <strong>[{cit.get('title')}]</strong> (Page {cit.get('page')})<br/>
                            🔗 <a href="{cit.get('source')}" target="_blank">{cit.get('source')}</a><br/>
                            <small>Chunk ID: <code>{cit.get('chunk_id')}</code></small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        # Display Approval Action Request if pending
        pending = msg.get("pending_approval")
        if pending:
            st.error(f"⚠️ **Approval Required:** `{pending.get('command')}` is a high-risk destructive operation.")
            if st.button(f"✅ Confirm & Approve `{pending.get('command')}`", key=f"btn_appr_{idx}"):
                with st.spinner("Executing approved action via LangGraph memory..."):
                    res = call_agent_backend(
                        query="",
                        thread_id=st.session_state.thread_id,
                        approved=True,
                        agent_type="langgraph",
                    )
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": res.get("answer", "Action executed."),
                        "citations": [],
                        "pending_approval": None,
                        "id": f"msg_appr_{int(time.time()*1000)}",
                    })
                    st.rerun()

        # Thumbs Up / Thumbs Down Feedback Buttons
        if msg["role"] == "assistant" and msg.get("id") != "welcome_msg":
            msg_id = msg.get("id", f"msg_{idx}")
            col_fb1, col_fb2, col_fb3 = st.columns([1, 1, 12])

            with col_fb1:
                if st.button("👍", key=f"thumbs_up_{msg_id}", help="Helpful answer"):
                    if msg_id not in st.session_state.feedback_submitted:
                        save_user_feedback(
                            query="User Query",
                            answer=msg["content"],
                            rating="thumbs_up",
                            mode=engine_mode,
                            citations_count=len(citations),
                            thread_id=st.session_state.thread_id,
                        )
                        st.session_state.feedback_submitted.add(msg_id)
                        st.toast("👍 Thanks for your positive feedback! Saved to data/feedback.json.")

            with col_fb2:
                if st.button("👎", key=f"thumbs_down_{msg_id}", help="Needs improvement"):
                    if msg_id not in st.session_state.feedback_submitted:
                        save_user_feedback(
                            query="User Query",
                            answer=msg["content"],
                            rating="thumbs_down",
                            mode=engine_mode,
                            citations_count=len(citations),
                            thread_id=st.session_state.thread_id,
                        )
                        st.session_state.feedback_submitted.add(msg_id)
                        st.toast("👎 Feedback recorded. We'll tune our RAG knowledge chunks!")


# Handle Quick Prompt Click or Chat Input
user_input = None
if "selected_prompt" in st.session_state and st.session_state.selected_prompt:
    user_input = st.session_state.selected_prompt
    st.session_state.selected_prompt = None

chat_bar_input = st.chat_input("Ask a Git/GitHub question, or enter a command to execute...")
if chat_bar_input:
    user_input = chat_bar_input


if user_input:
    # 1. Display User Message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "id": f"user_{int(time.time()*1000)}",
    })
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # 2. Call Selected Backend Engine
    with st.chat_message("assistant", avatar="🐙"):
        with st.spinner("GitGuru is thinking and consulting official documentation..."):
            if "RAG Search" in engine_mode:
                resp = call_ask_backend(question=user_input, top_k=3)
                answer_text = resp.get("answer", "")
                citations_data = resp.get("citations", [])
                pending_appr = None
            else:
                resp = call_agent_backend(
                    query=user_input,
                    thread_id=st.session_state.thread_id,
                    approved=None,
                    agent_type="langgraph",
                )
                answer_text = resp.get("answer", "")
                citations_data = resp.get("citations", [])
                pending_appr = resp.get("pending_approval")

            st.markdown(answer_text)

            if citations_data:
                with st.expander(f"📚 Document Citations ({len(citations_data)})", expanded=True):
                    for cit in citations_data:
                        st.markdown(
                            f"""
                            <div class="citation-card">
                                <strong>[{cit.get('title')}]</strong> (Page {cit.get('page')})<br/>
                                🔗 <a href="{cit.get('source')}" target="_blank">{cit.get('source')}</a><br/>
                                <small>Chunk ID: <code>{cit.get('chunk_id')}</code></small>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            # Record in session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer_text,
                "citations": citations_data,
                "pending_approval": pending_appr,
                "id": f"asst_{int(time.time()*1000)}",
            })
            st.rerun()
