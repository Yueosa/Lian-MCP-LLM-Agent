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

__all__ = [
    # 加载器
    "ToolLoader",
    "ToolMetaData",
    "get_tool_loader",
    "get_tools_list",
    "get_tool_meta",
    "call_tool",
]

"""
工具规范：
(1) 每个工具模块需在 mylib.mcp.tools 包下创建子模块。
(2) 每个工具模块需定义 TOOL_METADATA 列表，包含工具元数据字典。
(3) 每个工具模块需实现对应的类和方法，类名与 TOOL_METADATA 中的 class_name 一致，方法名与 method 一致。
(4) 工具方法可为同步或异步，需在 TOOL_METADATA 中通过 async_method 指定。
(5) 工具方法需接受参数字典，并返回结果字典。
"""
