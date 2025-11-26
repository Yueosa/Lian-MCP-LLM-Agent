"""描述可用 Dir 工具操作的声明式元数据"""

TOOL_METADATA = [
    {
        "name": "dir_create",
        "description": "创建目录（支持递归创建）",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "目录路径"},
                "exist_ok": {"type": "boolean", "description": "如果目录已存在是否视为成功"},
            },
            "required": ["dir_path"],
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "create",
        "async_method": True,
    },
    {
        "name": "dir_delete",
        "description": "删除目录",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "目录路径"},
                "recursive": {"type": "boolean", "description": "是否递归删除（包含子目录和文件）"},
            },
            "required": ["dir_path"],
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "delete",
        "async_method": True,
    },
    {
        "name": "dir_list",
        "description": "列出目录内容",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "目录路径"},
                "pattern": {"type": "string", "description": "文件名匹配模式（glob 语法），如 *.py"},
                "include_hidden": {"type": "boolean", "description": "是否包含隐藏文件/目录"},
                "files_only": {"type": "boolean", "description": "只列出文件"},
                "dirs_only": {"type": "boolean", "description": "只列出目录"},
            },
            "required": ["dir_path"],
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "list",
        "async_method": True,
    },
    {
        "name": "dir_exists",
        "description": "检查目录是否存在",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "目录路径"},
            },
            "required": ["dir_path"],
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "exists",
        "async_method": True,
    },
    {
        "name": "dir_info",
        "description": "获取目录详细信息（文件数、子目录数、总大小等）",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "目录路径"},
            },
            "required": ["dir_path"],
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "info",
        "async_method": True,
    },
    {
        "name": "dir_tree",
        "description": "获取目录树结构",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "目录路径"},
                "max_depth": {"type": "integer", "description": "最大递归深度，默认 3"},
                "include_hidden": {"type": "boolean", "description": "是否包含隐藏文件/目录"},
            },
            "required": ["dir_path"],
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "tree",
        "async_method": True,
    },
    {
        "name": "dir_copy",
        "description": "复制目录到新位置",
        "parameters": {
            "type": "object",
            "properties": {
                "src_path": {"type": "string", "description": "源目录路径"},
                "dest_path": {"type": "string", "description": "目标目录路径"},
                "overwrite": {"type": "boolean", "description": "是否覆盖已存在的目标目录"},
            },
            "required": ["src_path", "dest_path"],
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "copy",
        "async_method": True,
    },
    {
        "name": "dir_move",
        "description": "移动/重命名目录",
        "parameters": {
            "type": "object",
            "properties": {
                "src_path": {"type": "string", "description": "源目录路径"},
                "dest_path": {"type": "string", "description": "目标目录路径"},
                "overwrite": {"type": "boolean", "description": "是否覆盖已存在的目标目录"},
            },
            "required": ["src_path", "dest_path"],
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "move",
        "async_method": True,
    },
]

__all__ = ["TOOL_METADATA"]
