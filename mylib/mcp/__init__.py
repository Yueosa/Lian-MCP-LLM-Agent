"""
MCP (Model Context Protocol) 模块

提供统一的工具调用接口和 FastAPI 服务器实现。

使用示例：
    # 方式 1: 直接运行服务器
    from mylib.mcp import MCPServer
    server = MCPServer()
    server.run()
    
    
    # 方式 3: 直接调用工具（无需 HTTP）
    from mylib.mcp.tools import call_tool
    result = await call_tool("file_read", file_path="/path/to/file")
"""

from .base import ToolResponse
from .mcp import MCPServer


__all__ = [
    # 服务器
    "MCPServer",
    # 数据模型
    "ToolResponse",
]
