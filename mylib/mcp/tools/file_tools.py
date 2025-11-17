import aiofiles
from pathlib import Path

class FileTools:
    async def read_file(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return content
        except Exception as e:
            return f"读取文件错误: {str(e)}"
    
    async def write_file(self, file_path: str, content: str) -> str:
        """写入文件内容"""
        try:
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            return f"文件已成功写入: {file_path}"
        except Exception as e:
            return f"写入文件错误: {str(e)}"
    
    async def list_directory(self, directory: str) -> list:
        """列出目录内容"""
        try:
            path = Path(directory)
            if not path.exists():
                return f"目录不存在: {directory}"
            
            items = []
            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            return items
        except Exception as e:
            return f"列出目录错误: {str(e)}"

    async def create_directory(self, directory: str, exist_ok: bool = True) -> str:
        """创建目录，如果已存在则根据 exist_ok 决定行为"""
        try:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=bool(exist_ok))
            return f"目录已创建或已存在: {str(path)}"
        except Exception as e:
            return f"创建目录错误: {str(e)}"


# 元数据描述（供 MCP 动态发现）
TOOL_METADATA = [
    {
        "name": "read_file",
        "description": "读取文件内容",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"}
            },
            "required": ["file_path"]
        },
        "module": "mylib.mcp.tools.file_tools",
        "class": "FileTools",
        "method": "read_file",
        "async": True
    },
    {
        "name": "write_file",
        "description": "写入文件内容",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "文件内容"}
            },
            "required": ["file_path", "content"]
        },
        "module": "mylib.mcp.tools.file_tools",
        "class": "FileTools",
        "method": "write_file",
        "async": True
    },
    {
        "name": "list_directory",
        "description": "列出目录内容",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "目录路径"}
            },
            "required": ["directory"]
        },
        "module": "mylib.mcp.tools.file_tools",
        "class": "FileTools",
        "method": "list_directory",
        "async": True
    }
    ,
    {
        "name": "create_directory",
        "description": "创建目录（支持递归）",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "要创建的目录路径"},
                "exist_ok": {"type": "boolean", "description": "如果目录存在是否视为成功"}
            },
            "required": ["directory"]
        },
        "module": "mylib.mcp.tools.file_tools",
        "class": "FileTools",
        "method": "create_directory",
        "async": True
    }
]
