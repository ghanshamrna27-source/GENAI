"""
app/tools.py
Agent tools for GitGuru:
1. rag_search: Semantic RAG search over GitGuru documentation chunks with citations.
2. execute_git_action: Safe & destructive Git action executor/simulator with risk detection.
3. generate_git_workflow: Step-by-step Git workflow planner for developer tasks.
Includes LangChain @tool decorators and JSON schemas for LLM function calling.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag import answer_question

# Actions classified as destructive / irreversible requiring human approval
DESTRUCTIVE_ACTIONS = {
    "reset_hard": {
        "command": "git reset --hard",
        "risk": "Destroys all uncommitted local modifications and moves HEAD backwards.",
    },
    "push_force": {
        "command": "git push --force origin",
        "risk": "Overwrites remote branch commit history on GitHub, potentially erasing team commits.",
    },
    "branch_delete_force": {
        "command": "git branch -D",
        "risk": "Deletes local branch even if commits have not been merged into main.",
    },
    "clean_force": {
        "command": "git clean -fd",
        "risk": "Permanently deletes untracked files and directories from the working tree.",
    },
}

# Standard safe actions
SAFE_ACTIONS = {
    "status": "git status",
    "branch_list": "git branch",
    "branch_create": "git switch -c",
    "log": "git log --oneline -n 5",
    "diff": "git diff",
    "clone": "git clone",
    "stash": "git stash",
    "stash_pop": "git stash pop",
    "commit": "git commit -m",
    "pull": "git pull origin",
    "tag": "git tag -a",
}


def is_destructive_action(action: str, command_str: str = "", force: bool = False) -> bool:
    """Detects whether an action or command string is high-risk/destructive."""
    act_lower = action.lower()
    cmd_lower = command_str.lower()

    if force:
        return True
    if act_lower in DESTRUCTIVE_ACTIONS:
        return True
    if "--force" in cmd_lower or "-f" in cmd_lower and "clean" in cmd_lower:
        return True
    if "--hard" in cmd_lower:
        return True
    if "-d" in cmd_lower and "branch" in cmd_lower:
        return True

    return False


def rag_search(query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Searches the GitGuru knowledge base using dense vector embeddings
    and returns grounded documentation chunks and citations.
    """
    res = answer_question(question=query, top_k=top_k)
    return {
        "tool": "rag_search",
        "query": query,
        "answer": res.get("answer", ""),
        "citations": res.get("citations", []),
        "chunks_retrieved": len(res.get("retrieved_chunks", [])),
        "is_grounded": res.get("is_grounded", False),
        "confidence": res.get("confidence", "low"),
    }


def execute_git_action(
    action: str,
    target: Optional[str] = None,
    force: bool = False,
    approved: bool = False,
) -> Dict[str, Any]:
    """
    Domain Tool {T} for GitGuru:
    Simulates or executes Git commands with safety boundaries and approval checks.
    Destructive actions (e.g. reset --hard, push --force, branch -D, clean -fd)
    strictly require human approval (approved=True) before execution.
    """
    act_key = action.strip().lower()
    tgt = (target or "").strip()

    # Determine command representation
    if act_key in DESTRUCTIVE_ACTIONS:
        base_cmd = DESTRUCTIVE_ACTIONS[act_key]["command"]
        cmd_str = f"{base_cmd} {tgt}".strip()
        destructive = True
        risk_desc = DESTRUCTIVE_ACTIONS[act_key]["risk"]
    elif force or "--force" in tgt or "--hard" in tgt:
        destructive = True
        cmd_str = f"git {act_key} {tgt}".strip()
        risk_desc = "Operation requested with --force or --hard flag."
    else:
        destructive = False
        base_cmd = SAFE_ACTIONS.get(act_key, f"git {act_key}")
        cmd_str = f"{base_cmd} {tgt}".strip()
        risk_desc = ""

    # Human-in-the-loop approval guardrail
    if destructive and not approved:
        return {
            "tool": "execute_git_action",
            "status": "APPROVAL_REQUIRED",
            "action": act_key,
            "target": tgt,
            "command": cmd_str,
            "risk_level": "HIGH",
            "warning": (
                f"Action '{act_key}' ({cmd_str}) is destructive and could result in permanent data loss. "
                f"Details: {risk_desc} Explicit human approval is required to execute."
            ),
            "requires_approval": True,
            "approved": False,
        }

    # Successful simulated execution
    output_map = {
        "status": "On branch main\nYour branch is up to date with 'origin/main'.\nnothing to commit, working tree clean",
        "branch_list": "* main\n  feature/auth\n  dev",
        "branch_create": f"Switched to a new branch '{tgt or 'feature/new-branch'}'",
        "log": "2ea9277 Day 8: RAG Grounded Answering\na0030f0 Day 7: Document chunking & Chroma\n52479e0 Day 6: LLM Provider wrapper",
        "diff": "diff --git a/app/main.py b/app/main.py\n--- a/app/main.py\n+++ b/app/main.py",
        "clone": f"Cloning into '{tgt or 'my-repo'}'...\nremote: Enumerating objects: 42, done.\nReceiving objects: 100%",
        "stash": "Saved working directory and index state WIP on main: 2ea9277 Day 8",
        "stash_pop": "On branch main\nChanges not staged for commit:\n  modified: app/main.py\nDropped refs/stash@{0}",
        "commit": f"[main a1b2c3d] {tgt or 'Updated documentation'}\n 1 file changed, 10 insertions(+)",
        "pull": f"From https://github.com/example/repo\n * branch {tgt or 'main'} -> FETCH_HEAD\nAlready up to date.",
        "tag": f"Created annotated tag '{tgt or 'v1.0.0'}'",
        "reset_hard": f"HEAD is now at 2ea9277 (Hard reset executed to '{tgt or 'HEAD~1'}')",
        "push_force": f"Force pushed to origin/{tgt or 'main'} (remote history overwritten)",
        "branch_delete_force": f"Deleted branch '{tgt or 'feature'}' (was 2ea9277)",
        "clean_force": "Removing untracked/build/ output files",
    }

    mock_output = output_map.get(act_key, f"Executed command: '{cmd_str}' successfully.")

    return {
        "tool": "execute_git_action",
        "status": "SUCCESS",
        "action": act_key,
        "target": tgt,
        "command": cmd_str,
        "requires_approval": False,
        "approved": approved if destructive else True,
        "output": mock_output,
        "message": f"Successfully executed: {cmd_str}",
    }


def generate_git_workflow(task_description: str) -> Dict[str, Any]:
    """
    Plans and generates a structured Git command sequence for a developer goal.
    """
    t_lower = task_description.lower()
    commands = []
    has_destructive = False

    if "feature" in t_lower or "create branch" in t_lower:
        commands = [
            "git switch main",
            "git pull origin main",
            "git switch -c feature/new-capability",
            "# Make file edits",
            "git add .",
            "git commit -m 'Implement feature capability'",
            "git push -u origin feature/new-capability",
        ]
    elif "conflict" in t_lower:
        commands = [
            "git status",
            "# Open conflicted files and remove <<<<<<<, =======, >>>>>>> markers",
            "git add <resolved-files>",
            "git commit -m 'Resolve merge conflicts'",
            "git push origin <branch>",
        ]
    elif "undo" in t_lower or "revert" in t_lower:
        if "hard" in t_lower or "discard" in t_lower:
            commands = ["git status", "git reset --hard HEAD~1"]
            has_destructive = True
        else:
            commands = ["git revert HEAD", "git push origin main"]
    elif "tag" in t_lower or "release" in t_lower:
        commands = [
            "git tag -a v1.0.0 -m 'Release version 1.0.0'",
            "git push origin v1.0.0",
        ]
    elif "stash" in t_lower:
        commands = [
            "git stash",
            "git switch <other-branch>",
            "# ... work on other branch ...",
            "git switch <original-branch>",
            "git stash pop",
        ]
    else:
        commands = [
            "git status",
            "git add .",
            "git commit -m 'Update project files'",
            "git push origin main",
        ]

    return {
        "tool": "generate_git_workflow",
        "task": task_description,
        "commands": commands,
        "steps_count": len(commands),
        "contains_destructive_step": has_destructive,
        "guidance": (
            "Caution: Review commands carefully before executing in production repositories."
            if has_destructive
            else "Standard safe Git workflow sequence."
        ),
    }


# JSON Schemas for Function Calling
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "rag_search",
            "description": "Searches the GitGuru documentation knowledge base for official Git and GitHub explanations, commands, and citations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or concept to look up in documentation.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of documentation chunks to retrieve (default: 3).",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_git_action",
            "description": "Executes or simulates a Git command. Destructive actions (reset_hard, push_force, branch_delete_force, clean_force) require human approval (approved=True).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "status",
                            "branch_list",
                            "branch_create",
                            "log",
                            "diff",
                            "clone",
                            "stash",
                            "stash_pop",
                            "commit",
                            "pull",
                            "tag",
                            "reset_hard",
                            "push_force",
                            "branch_delete_force",
                            "clean_force",
                        ],
                        "description": "The Git action to execute or simulate.",
                    },
                    "target": {
                        "type": "string",
                        "description": "Optional branch name, file path, commit hash, or URL parameter.",
                    },
                    "force": {
                        "type": "boolean",
                        "description": "Whether the action uses --force or --hard.",
                    },
                    "approved": {
                        "type": "boolean",
                        "description": "True if human confirmation has been granted for destructive actions.",
                    },
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_git_workflow",
            "description": "Plans a complete step-by-step Git command sequence for a user's development workflow goal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "The development goal or scenario (e.g. 'feature branch', 'resolve conflict', 'undo commit').",
                    }
                },
                "required": ["task_description"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "rag_search": rag_search,
    "execute_git_action": execute_git_action,
    "generate_git_workflow": generate_git_workflow,
}


def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Unified entry point to execute an agent tool by name with arguments."""
    func = TOOL_REGISTRY.get(name)
    if not func:
        return {
            "error": f"Tool '{name}' not found. Available tools: {list(TOOL_REGISTRY.keys())}"
        }
    try:
        return func(**arguments)
    except Exception as e:
        return {"error": f"Tool execution failed for '{name}': {str(e)}"}


# LangChain Tool Decorators for LangGraph
try:
    from langchain_core.tools import tool

    @tool
    def rag_search_tool(query: str, top_k: int = 3) -> str:
        """Search GitGuru knowledge base documentation chunks with citations."""
        res = rag_search(query=query, top_k=top_k)
        return json.dumps(res, indent=2)

    @tool
    def execute_git_action_tool(
        action: str,
        target: str = "",
        force: bool = False,
        approved: bool = False,
    ) -> str:
        """Execute or simulate a Git command. Destructive actions require approved=True."""
        res = execute_git_action(
            action=action,
            target=target,
            force=force,
            approved=approved,
        )
        return json.dumps(res, indent=2)

    @tool
    def generate_git_workflow_tool(task_description: str) -> str:
        """Plan a complete step-by-step Git workflow for a developer goal."""
        res = generate_git_workflow(task_description=task_description)
        return json.dumps(res, indent=2)

    LANGCHAIN_TOOLS = [rag_search_tool, execute_git_action_tool, generate_git_workflow_tool]
except ImportError:
    LANGCHAIN_TOOLS = []


if __name__ == "__main__":
    print("=" * 65)
    print("         GitGuru Agent Tools Diagnostic (app/tools.py)")
    print("=" * 65)

    print("\n1. Testing RAG Search Tool:")
    rag_res = rag_search("How do I clone a repository?", top_k=1)
    print(f"   Answer preview: {rag_res['answer'][:90]}...")
    print(f"   Citations: {len(rag_res['citations'])}")

    print("\n2. Testing Safe Git Action Tool (branch_create):")
    safe_res = execute_git_action("branch_create", target="feature/rag-agent")
    print(f"   Status: {safe_res['status']} | Output: {safe_res['output']}")

    print("\n3. Testing Destructive Git Action (reset_hard) WITHOUT approval:")
    dest_res = execute_git_action("reset_hard", target="HEAD~1", approved=False)
    print(f"   Status: {dest_res['status']} | Requires Approval: {dest_res['requires_approval']}")
    print(f"   Warning: {dest_res['warning']}")

    print("\n4. Testing Destructive Git Action (reset_hard) WITH approval:")
    appr_res = execute_git_action("reset_hard", target="HEAD~1", approved=True)
    print(f"   Status: {appr_res['status']} | Output: {appr_res['output']}")

    print("\n" + "=" * 65)
