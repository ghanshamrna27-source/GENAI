"""
app/graph.py
LangGraph Agent for GitGuru with Memory and Human-in-the-Loop Approval Step.
Rebuilds the ReAct agent into a stateful LangGraph StateGraph equipped with:
1. MemorySaver checkpointer for multi-turn conversational session memory across thread_id.
2. A dedicated Human-in-the-Loop Approval Step intercepting destructive Git operations.
3. Coordination of RAG semantic search and Git action tool {T}.
"""

import sys
import os
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, TypedDict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.tools import (
    rag_search,
    execute_git_action,
    generate_git_workflow,
    is_destructive_action,
    DESTRUCTIVE_ACTIONS,
)


class AgentGraphState(TypedDict):
    """LangGraph state schema preserving messages, memory, and approval flags."""
    query: str
    thread_id: str
    messages: List[Dict[str, Any]]
    steps: List[Dict[str, Any]]
    tools_called: List[str]
    pending_tool_call: Optional[Dict[str, Any]]
    pending_approval: Optional[Dict[str, Any]]
    approved: Optional[bool]
    rag_result: Optional[Dict[str, Any]]
    tool_result: Optional[Dict[str, Any]]
    final_answer: str
    next_step: str


def agent_planner_node(state: AgentGraphState) -> Dict[str, Any]:
    """
    Reasoning / Planning Node:
    Determines next action based on query, previous tool observations, and approval state.
    """
    query = state.get("query", "").strip()
    q_lower = query.lower()
    tools_called = list(state.get("tools_called", []))
    steps = list(state.get("steps", []))
    rag_result = state.get("rag_result")
    approved = state.get("approved")

    # If an approval was already pending and user provided approved=True, proceed to execute the pending tool!
    if state.get("pending_approval") and approved is True:
        pending = state["pending_approval"]
        return {
            "pending_tool_call": {
                "name": "execute_git_action",
                "args": {"action": pending["action"], "target": pending.get("target", ""), "approved": True},
            },
            "pending_approval": None,
            "next_step": "approval_check",
        }

    # 1. First step: Always consult RAG knowledge base if not already retrieved
    if "rag_search" not in tools_called:
        return {
            "pending_tool_call": {
                "name": "rag_search",
                "args": {"query": query, "top_k": 3},
            },
            "next_step": "approval_check",
        }

    # 2. Check if RAG indicates an unanswerable question (e.g. Q6 formatted drive)
    if rag_result and "i don't know" in rag_result.get("answer", "").lower():
        return {
            "pending_tool_call": None,
            "next_step": "respond",
        }

    # 3. Second step: Execute or plan the relevant Git action tool {T}
    if "execute_git_action" not in tools_called and "generate_git_workflow" not in tools_called:
        # Detect intended action
        if "reset --hard" in q_lower or "hard reset" in q_lower or ("discard" in q_lower and "all" in q_lower):
            action_args = {"action": "reset_hard", "target": "HEAD~1", "approved": approved is True}
        elif "force push" in q_lower or "push --force" in q_lower or "overwrite remote" in q_lower:
            action_args = {"action": "push_force", "target": "main", "approved": approved is True}
        elif "delete branch" in q_lower and ("force" in q_lower or "-d" in q_lower):
            action_args = {"action": "branch_delete_force", "target": "feature-branch", "approved": approved is True}
        elif "clean" in q_lower and ("force" in q_lower or "-fd" in q_lower):
            action_args = {"action": "clean_force", "target": "", "approved": approved is True}
        elif "status" in q_lower:
            action_args = {"action": "status", "target": "", "approved": True}
        elif "branch" in q_lower and ("create" in q_lower or "new" in q_lower or "switch" in q_lower):
            action_args = {"action": "branch_create", "target": "feature/new-feature", "approved": True}
        elif "clone" in q_lower:
            action_args = {"action": "clone", "target": "https://github.com/example/repo.git", "approved": True}
        elif "commit" in q_lower:
            action_args = {"action": "commit", "target": "feat: update codebase", "approved": True}
        elif "stash" in q_lower:
            action_args = {"action": "stash", "target": "", "approved": True}
        elif "tag" in q_lower or "release" in q_lower:
            action_args = {"action": "tag", "target": "v1.0.0", "approved": True}
        else:
            action_args = None

        if action_args:
            return {
                "pending_tool_call": {
                    "name": "execute_git_action",
                    "args": action_args,
                },
                "next_step": "approval_check",
            }
        else:
            return {
                "pending_tool_call": {
                    "name": "generate_git_workflow",
                    "args": {"task_description": query},
                },
                "next_step": "approval_check",
            }

    # Ready to respond
    return {
        "pending_tool_call": None,
        "next_step": "respond",
    }


def approval_step_node(state: AgentGraphState) -> Dict[str, Any]:
    """
    Human-in-the-Loop Approval Step Node:
    Intercepts destructive actions and pauses for explicit human confirmation.
    """
    pending = state.get("pending_tool_call")
    if not pending:
        return {"next_step": "respond"}

    tool_name = pending.get("name")
    args = pending.get("args", {})
    approved = state.get("approved")

    # Only execute_git_action with destructive actions needs approval
    if tool_name == "execute_git_action":
        action_name = args.get("action", "")
        force = args.get("force", False)

        if is_destructive_action(action_name, force=force):
            if approved is not True:
                # Trigger Approval Interruption!
                risk_info = DESTRUCTIVE_ACTIONS.get(
                    action_name,
                    {"command": f"git {action_name}", "risk": "Destructive repository modification"}
                )
                approval_payload = {
                    "action": action_name,
                    "target": args.get("target", ""),
                    "command": risk_info["command"],
                    "risk": risk_info["risk"],
                    "warning": (
                        f"Action '{action_name}' ({risk_info['command']}) is destructive and could result in permanent data loss. "
                        f"Explicit human approval is required before execution."
                    ),
                    "requires_approval": True,
                }
                step_record = {
                    "node": "approval_step",
                    "status": "APPROVAL_REQUIRED",
                    "details": approval_payload,
                }
                return {
                    "pending_approval": approval_payload,
                    "steps": state.get("steps", []) + [step_record],
                    "next_step": "pause_for_approval",
                }

    # Safe tool or approved: proceed to tool execution
    return {
        "pending_approval": None,
        "next_step": "execute_tool",
    }


def tool_execution_node(state: AgentGraphState) -> Dict[str, Any]:
    """Executes the approved or safe tool and updates state and messages."""
    pending = state.get("pending_tool_call")
    if not pending:
        return {"next_step": "respond"}

    tool_name = pending["name"]
    args = pending["args"]
    steps = list(state.get("steps", []))
    tools_called = list(state.get("tools_called", []))
    messages = list(state.get("messages", []))

    if tool_name == "rag_search":
        obs = rag_search(**args)
        tools_called.append("rag_search")
        steps.append({
            "node": "tool_execution",
            "tool": "rag_search",
            "args": args,
            "observation_summary": f"Retrieved {obs['chunks_retrieved']} chunks with {len(obs['citations'])} citations.",
        })
        messages.append({
            "role": "tool",
            "tool": "rag_search",
            "content": obs.get("answer", ""),
        })
        return {
            "rag_result": obs,
            "tools_called": tools_called,
            "steps": steps,
            "messages": messages,
            "pending_tool_call": None,
            "next_step": "plan",
        }

    elif tool_name == "execute_git_action":
        obs = execute_git_action(**args)
        tools_called.append("execute_git_action")
        steps.append({
            "node": "tool_execution",
            "tool": "execute_git_action",
            "args": args,
            "status": obs.get("status"),
            "observation_summary": obs.get("output", ""),
        })
        messages.append({
            "role": "tool",
            "tool": "execute_git_action",
            "content": obs.get("output", ""),
        })
        return {
            "tool_result": obs,
            "tools_called": tools_called,
            "steps": steps,
            "messages": messages,
            "pending_tool_call": None,
            "next_step": "plan",
        }

    elif tool_name == "generate_git_workflow":
        obs = generate_git_workflow(**args)
        tools_called.append("generate_git_workflow")
        steps.append({
            "node": "tool_execution",
            "tool": "generate_git_workflow",
            "args": args,
            "observation_summary": f"Generated {obs['steps_count']} workflow commands.",
        })
        messages.append({
            "role": "tool",
            "tool": "generate_git_workflow",
            "content": json.dumps(obs.get("commands", [])),
        })
        return {
            "tool_result": obs,
            "tools_called": tools_called,
            "steps": steps,
            "messages": messages,
            "pending_tool_call": None,
            "next_step": "plan",
        }

    return {"next_step": "respond"}


def response_synthesizer_node(state: AgentGraphState) -> Dict[str, Any]:
    """
    Response Node:
    Synthesizes the final answer incorporating retrieved knowledge,
    tool observations, and human approval status.
    """
    pending_approval = state.get("pending_approval")
    rag_result = state.get("rag_result", {})
    tool_result = state.get("tool_result", {})
    messages = list(state.get("messages", []))

    if pending_approval:
        final_answer = (
            f"### Action Requires Confirmation\n"
            f"⚠️ **Warning:** The requested action `{pending_approval['command']}` is destructive and could result in permanent data loss.\n\n"
            f"{pending_approval['warning']}\n\n"
            f"**To execute this action, please resend your request with `approved=True` and `thread_id='{state.get('thread_id')}'`.**"
        )
    else:
        rag_answer = rag_result.get("answer", "") if rag_result else ""
        citations = rag_result.get("citations", []) if rag_result else []

        # If unanswerable question:
        if "i don't know" in rag_answer.lower():
            final_answer = rag_answer
        else:
            action_section = ""
            if tool_result:
                if "output" in tool_result:
                    action_section = f"\n\n**Executed Git Action:** `{tool_result.get('command')}`\n```\n{tool_result.get('output')}\n```"
                elif "commands" in tool_result:
                    cmds = "\n".join(f"{i}. `{c}`" for i, c in enumerate(tool_result.get("commands", []), 1))
                    action_section = f"\n\n**Recommended Git Workflow:**\n{cmds}"

            citations_text = ""
            if citations:
                citations_text = "\n\n**Sources & Citations:**\n" + "\n".join(
                    f"- [{c['title']}] (Page {c['page']}) <{c['source']}> [{c['chunk_id']}]"
                    for c in citations
                )

            final_answer = f"{rag_answer}{action_section}{citations_text}"

    messages.append({"role": "assistant", "content": final_answer})

    return {
        "final_answer": final_answer,
        "messages": messages,
        "next_step": "end",
    }


# Routing functions
def route_from_planner(state: AgentGraphState) -> str:
    """Routes from planner node to approval check or response synthesizer."""
    next_s = state.get("next_step")
    if next_s == "approval_check":
        return "approval_step"
    return "response_synthesizer"


def route_from_approval(state: AgentGraphState) -> str:
    """Routes from approval node: pause for human input or execute tool."""
    next_s = state.get("next_step")
    if next_s == "pause_for_approval":
        return "response_synthesizer"
    return "tool_execution"


# Build and Compile the LangGraph
def build_agent_graph(checkpointer: Optional[Any] = None) -> Any:
    """Constructs the LangGraph StateGraph with nodes, edges, and memory checkpointer."""
    workflow = StateGraph(AgentGraphState)

    # Add Nodes
    workflow.add_node("agent_planner", agent_planner_node)
    workflow.add_node("approval_step", approval_step_node)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("response_synthesizer", response_synthesizer_node)

    # Add Edges
    workflow.add_edge(START, "agent_planner")

    workflow.add_conditional_edges(
        "agent_planner",
        route_from_planner,
        {
            "approval_step": "approval_step",
            "response_synthesizer": "response_synthesizer",
        },
    )

    workflow.add_conditional_edges(
        "approval_step",
        route_from_approval,
        {
            "response_synthesizer": "response_synthesizer",
            "tool_execution": "tool_execution",
        },
    )

    # After tool execution, loop back to planner
    workflow.add_edge("tool_execution", "agent_planner")

    # Synthesizer finishes the graph turn
    workflow.add_edge("response_synthesizer", END)

    # Attach Memory Checkpointer
    saver = checkpointer if checkpointer is not None else MemorySaver()
    return workflow.compile(checkpointer=saver)


# Singleton Graph & Memory Instance
_GLOBAL_CHECKPOINTER = MemorySaver()
_COMPILED_GRAPH = build_agent_graph(checkpointer=_GLOBAL_CHECKPOINTER)


def run_langgraph_agent(
    query: str,
    thread_id: Optional[str] = None,
    approved: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Main LangGraph Agent execution interface.
    Preserves state and thread memory across calls for the same thread_id.
    """
    session_id = thread_id or f"session_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": session_id}}

    # Check if there is existing state for this thread in memory
    existing_checkpoint = _GLOBAL_CHECKPOINTER.get(config)
    initial_state: AgentGraphState

    if existing_checkpoint and "channel_values" in existing_checkpoint:
        # Resume conversation from memory
        saved_state = existing_checkpoint["channel_values"]
        initial_state = {
            "query": query if query else saved_state.get("query", ""),
            "thread_id": session_id,
            "messages": list(saved_state.get("messages", [])),
            "steps": list(saved_state.get("steps", [])),
            "tools_called": list(saved_state.get("tools_called", [])),
            "pending_tool_call": saved_state.get("pending_tool_call"),
            "pending_approval": saved_state.get("pending_approval"),
            "approved": approved if approved is not None else saved_state.get("approved"),
            "rag_result": saved_state.get("rag_result"),
            "tool_result": saved_state.get("tool_result"),
            "final_answer": "",
            "next_step": "plan",
        }
        if query:
            initial_state["messages"].append({"role": "user", "content": query})
    else:
        # Fresh conversation thread
        initial_state = {
            "query": query,
            "thread_id": session_id,
            "messages": [{"role": "user", "content": query}],
            "steps": [],
            "tools_called": [],
            "pending_tool_call": None,
            "pending_approval": None,
            "approved": approved,
            "rag_result": None,
            "tool_result": None,
            "final_answer": "",
            "next_step": "plan",
        }

    # Execute graph
    final_output = _COMPILED_GRAPH.invoke(initial_state, config=config)

    return {
        "query": final_output.get("query", query),
        "answer": final_output.get("final_answer", ""),
        "thread_id": session_id,
        "pending_approval": final_output.get("pending_approval"),
        "tools_called": final_output.get("tools_called", []),
        "steps": final_output.get("steps", []),
        "is_approved": final_output.get("approved"),
        "messages_count": len(final_output.get("messages", [])),
    }


if __name__ == "__main__":
    print("=" * 70)
    print("      GitGuru LangGraph Agent with Memory & Approval Step (app/graph.py)")
    print("=" * 70)

    # Test 1: Safe Query
    print("\n[Test 1: Safe Git Query]")
    res1 = run_langgraph_agent("How do I clone a repository and check status?")
    print(f"Thread ID:     {res1['thread_id']}")
    print(f"Tools Called:  {res1['tools_called']}")
    print(f"Approval Req:  {res1['pending_approval'] is not None}")
    print(f"Answer:\n{res1['answer'][:180]}...\n")

    # Test 2: Destructive Query - Turn 1 (Requires Approval)
    test_thread = "test_thread_destructive"
    print("\n[Test 2: Destructive Action - Turn 1]")
    res2 = run_langgraph_agent("Run git reset --hard to discard local changes", thread_id=test_thread)
    print(f"Thread ID:     {res2['thread_id']}")
    print(f"Approval Req:  {res2['pending_approval'] is not None}")
    if res2['pending_approval']:
        print(f"Warning:       {res2['pending_approval']['warning']}")

    # Test 3: Destructive Query - Turn 2 (Human Approval Granted)
    print("\n[Test 3: Destructive Action - Turn 2: User Confirms approved=True]")
    res3 = run_langgraph_agent("", thread_id=test_thread, approved=True)
    print(f"Thread ID:     {res3['thread_id']}")
    print(f"Approval Req:  {res3['pending_approval'] is not None}")
    print(f"Approved:      {res3['is_approved']}")
    print(f"Answer:\n{res3['answer']}")

    print("=" * 70)
