"""
MCP Tools 模块

提供文件、目录、网页操作等工具。

工具列表：
- file_tool: 文件操作（读/写/删/查/复制/移动）
- dir_tool: 目录操作（创建/删除/列表/树形结构）
- web_tool: 网页操作（获取/解析/提取内容）

使用方式：
    from mylib.mcp.tools import get_tools_list, call_tool, get_tool_meta
    
    # 获取所有工具列表
    tools = get_tools_list()
    
    # 获取单个工具的元数据
    meta = get_tool_meta("file_read")
    
    # 调用工具
    result = await call_tool("file_read", file_path="/path/to/file")
"""

from .Tool import (
    ToolLoader,
    ToolMetaData,
    get_tool_loader,
    get_tools_list,
    get_tool_meta,
    call_tool
)

from .file_tool import FileTool, TOOL_METADATA as FILE_TOOL_METADATA
from .dir_tool import DirTool, TOOL_METADATA as DIR_TOOL_METADATA
from .web_tool import WebTool, TOOL_METADATA as WEB_TOOL_METADATA

__all__ = [
    # 加载器
    "ToolLoader",
    "ToolMetaData",
    "get_tool_loader",
    "get_tools_list",
    "get_tool_meta",
    "call_tool",
    
    # 工具类
    "FileTool",
    "DirTool", 
    "WebTool",
    
    # 元数据
    "FILE_TOOL_METADATA",
    "DIR_TOOL_METADATA",
    "WEB_TOOL_METADATA"
]
