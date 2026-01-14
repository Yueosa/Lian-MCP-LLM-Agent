"""
Lian-MCP-LLM-Agent 提示词模块

提供统一的、增强的系统提示词，让每个 Agent 对整个系统架构有清晰认知。

模块结构:
- system_awareness: 系统架构认知（所有 Agent 共享）
- rag_prompt: RAG Agent 专用提示词
- planner_prompt: Planner Agent 专用提示词
- executor_prompt: Executor Agent 专用提示词
- summary_prompt: Summary Agent 专用提示词
"""

from .system_awareness import SYSTEM_AWARENESS
from .rag_prompt import RAG_SYSTEM_PROMPT
from .planner_prompt import PLANNER_SYSTEM_PROMPT
from .executor_prompt import build_executor_prompt
from .summary_prompt import SUMMARY_SYSTEM_PROMPT, CATGIRL_PERSONA

__all__ = [
    "SYSTEM_AWARENESS",
    "RAG_SYSTEM_PROMPT",
    "PLANNER_SYSTEM_PROMPT",
    "build_executor_prompt",
    "SUMMARY_SYSTEM_PROMPT",
    "CATGIRL_PERSONA",
]
