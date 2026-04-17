# -*- coding: utf-8 -*-
"""
TravelBuddy Agent — LangGraph + Gemini

Agentic travel assistant với tool calling.
Quản lý hội thoại multi-turn qua session_id.
"""
import os
import time
import logging
from typing import Annotated
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from tools import search_flights, search_hotels, calculate_budget

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# System Prompt
# ─────────────────────────────────────────────────────────
_PROMPT_PATH = Path(__file__).parent / "system_prompt.txt"
with open(_PROMPT_PATH, "r", encoding="utf-8") as _f:
    SYSTEM_PROMPT = _f.read()

TOOLS_LIST = [search_flights, search_hotels, calculate_budget]

# ─────────────────────────────────────────────────────────
# Agent State
# ─────────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# ─────────────────────────────────────────────────────────
# Graph Builder
# ─────────────────────────────────────────────────────────
def _build_graph(api_key: str, model: str):
    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.7,
    )
    llm_with_tools = llm.bind_tools(TOOLS_LIST)

    def agent_node(state: AgentState):
        messages = list(state["messages"])
        # Prepend system prompt if not already present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    builder = StateGraph(AgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS_LIST))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder.compile()


# ─────────────────────────────────────────────────────────
# Session Store (in-memory)
# ─────────────────────────────────────────────────────────
_MAX_SESSIONS = 500
_SESSION_TTL_SECONDS = 3600  # 1 hour

class _SessionStore:
    def __init__(self):
        self._sessions: dict[str, dict] = {}  # {session_id: {"messages": [...], "last_access": float}}

    def get(self, session_id: str) -> list:
        entry = self._sessions.get(session_id)
        if entry is None:
            return []
        entry["last_access"] = time.time()
        return list(entry["messages"])

    def save(self, session_id: str, messages: list) -> None:
        self._evict_stale()
        self._sessions[session_id] = {
            "messages": messages,
            "last_access": time.time(),
        }

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def _evict_stale(self):
        now = time.time()
        stale = [k for k, v in self._sessions.items()
                 if now - v["last_access"] > _SESSION_TTL_SECONDS]
        for k in stale:
            del self._sessions[k]
        # If still over limit, evict oldest
        if len(self._sessions) >= _MAX_SESSIONS:
            oldest = sorted(self._sessions, key=lambda k: self._sessions[k]["last_access"])
            for k in oldest[:len(self._sessions) - _MAX_SESSIONS + 1]:
                del self._sessions[k]


_store = _SessionStore()


# ─────────────────────────────────────────────────────────
# Public Interface
# ─────────────────────────────────────────────────────────
_graph = None

def init_agent(api_key: str, model: str = "gemini-2.5-flash-lite") -> None:
    """Initialize the LangGraph agent. Call once at startup."""
    global _graph
    logger.info(f"Initializing TravelBuddy agent with model: {model}")
    _graph = _build_graph(api_key, model)
    logger.info("TravelBuddy agent ready.")


def ask_travel(question: str, session_id: str) -> str:
    """
    Ask the travel agent a question, maintaining conversation history by session_id.
    Returns the agent's answer as a string.
    """
    global _graph
    if _graph is None:
        # Lazy init — pick up from environment variables
        api_key = os.environ.get("GEMINI_API_KEY", "")
        model = os.environ.get("LLM_MODEL", "gemini-2.5-flash-lite")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set. Cannot initialize travel agent.")
        init_agent(api_key, model)

    history = _store.get(session_id)
    result = _graph.invoke({"messages": history + [HumanMessage(content=question)]})
    _store.save(session_id, result["messages"])

    last = result["messages"][-1]
    return last.content if hasattr(last, "content") else str(last)


def clear_session(session_id: str) -> None:
    """Clear conversation history for a session."""
    _store.clear(session_id)
