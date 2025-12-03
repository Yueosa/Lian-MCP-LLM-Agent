"""Pydantic 数据模型：MCP 工具调用响应"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class ToolResponse(BaseModel):
    """统一的工具调用响应"""
    result: Optional[Any] = None
    success: bool
    error: Optional[str] = None


__all__ = [
    "ToolResponse",
]
