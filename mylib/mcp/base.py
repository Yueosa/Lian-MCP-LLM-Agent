from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]

class ToolCallRequest(BaseModel):
    tool_calls: List[ToolCall]

class ToolResponse(BaseModel):
    result: Any
    success: bool
    error: Optional[str] = None
