from pydantic import BaseModel, Field
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

class RuntimeConfig(BaseModel):
    MCP_SERVER_HOST: str
    MCP_SERVER_PORT: int
    
    LLM_API_KEY: str
    LLM_API_URL: str

class ToolConfig(BaseModel):
    # 使用带默认值的注解，保证可以在没有显式传参时安全实例化
    MAX_FILE_SIZE: int = Field(10 * 1024 * 1024, description="最大文件大小（字节）")
    REQUEST_TIMEOUT: int = Field(30, description="工具请求超时时间（秒）")

    model_config = {
        "extra": "allow",
        "populate_by_name": True,
    }


# ---------- 新增模型: 规范工具元数据 ----------
class ToolMetaData(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    module: Optional[str] = None
    class_name: Optional[str] = None
    method: Optional[str] = None
    async_method: Optional[bool] = False


# ---------- 运行时状态模型: MCP Server & LLM Client ----------
class MCPServerState(BaseModel):
    host: str
    port: int
    running: bool = False


class LLMClientState(BaseModel):
    provider: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    initialized: bool = False


# 兼容旧命名：暴露简短别名
RuntimeToolConfig = ToolConfig
