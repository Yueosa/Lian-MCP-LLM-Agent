"""描述可用 File 工具操作的声明式元数据"""

TOOL_METADATA = [
    {
        "name": "file_read",
        "description": "读取文件内容，支持按行范围读取",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
                "start_line": {"type": "integer", "description": "起始行号（1-indexed）"},
                "end_line": {"type": "integer", "description": "结束行号（1-indexed，包含）"},
                "encoding": {"type": "string", "description": "文件编码，默认 utf-8"},
            },
            "required": ["file_path"],
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "read",
        "async_method": True,
    },
    {
        "name": "file_write",
        "description": "写入/创建文件（覆盖模式）",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "要写入的内容"},
                "create_dirs": {"type": "boolean", "description": "是否自动创建父目录"},
                "encoding": {"type": "string", "description": "文件编码，默认 utf-8"},
            },
            "required": ["file_path", "content"],
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "write",
        "async_method": True,
    },
    {
        "name": "file_append",
        "description": "追加内容到文件末尾",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "要追加的内容"},
                "encoding": {"type": "string", "description": "文件编码，默认 utf-8"},
            },
            "required": ["file_path", "content"],
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "append",
        "async_method": True,
    },
    {
        "name": "file_delete",
        "description": "删除文件",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
            },
            "required": ["file_path"],
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "delete",
        "async_method": True,
    },
    {
        "name": "file_exists",
        "description": "检查文件是否存在",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
            },
            "required": ["file_path"],
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "exists",
        "async_method": True,
    },
    {
        "name": "file_info",
        "description": "获取文件详细信息（大小、创建时间、修改时间等）",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
            },
            "required": ["file_path"],
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "info",
        "async_method": True,
    },
    {
        "name": "file_copy",
        "description": "复制文件到新位置",
        "parameters": {
            "type": "object",
            "properties": {
                "src_path": {"type": "string", "description": "源文件路径"},
                "dest_path": {"type": "string", "description": "目标文件路径"},
                "overwrite": {"type": "boolean", "description": "是否覆盖已存在的目标文件"},
            },
            "required": ["src_path", "dest_path"],
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "copy",
        "async_method": True,
    },
    {
        "name": "file_move",
        "description": "移动/重命名文件",
        "parameters": {
            "type": "object",
            "properties": {
                "src_path": {"type": "string", "description": "源文件路径"},
                "dest_path": {"type": "string", "description": "目标文件路径"},
                "overwrite": {"type": "boolean", "description": "是否覆盖已存在的目标文件"},
            },
            "required": ["src_path", "dest_path"],
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "move",
        "async_method": True,
    },
]

__all__ = ["TOOL_METADATA"]
