"""
FileTool - 文件操作工具

提供文件的完整 CRUD 操作接口。
"""

import os
import aiofiles
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Union


class FileTool:
    """文件操作工具类"""
    
    async def read(
        self, 
        file_path: str, 
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            start_line: 起始行号（1-indexed），None 表示从头开始
            end_line: 结束行号（1-indexed，包含），None 表示读到末尾
            encoding: 文件编码，默认 utf-8
            
        Returns:
            {
                "success": bool,
                "content": str,  # 文件内容
                "lines_read": int,  # 读取的行数
                "total_lines": int,  # 文件总行数
                "error": str  # 错误信息（如有）
            }
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": f"文件不存在: {file_path}"}
            
            if not path.is_file():
                return {"success": False, "error": f"路径不是文件: {file_path}"}
            
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                lines = await f.readlines()
            
            total_lines = len(lines)
            
            # 处理行范围
            if start_line is not None or end_line is not None:
                start_idx = (start_line - 1) if start_line else 0
                end_idx = end_line if end_line else total_lines
                
                # 边界检查
                start_idx = max(0, start_idx)
                end_idx = min(total_lines, end_idx)
                
                selected_lines = lines[start_idx:end_idx]
                content = ''.join(selected_lines)
                lines_read = len(selected_lines)
            else:
                content = ''.join(lines)
                lines_read = total_lines
            
            return {
                "success": True,
                "content": content,
                "lines_read": lines_read,
                "total_lines": total_lines
            }
        except UnicodeDecodeError as e:
            return {"success": False, "error": f"编码错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"读取文件错误: {str(e)}"}
    
    async def write(
        self, 
        file_path: str, 
        content: str,
        create_dirs: bool = True,
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        写入/创建文件（覆盖模式）
        
        Args:
            file_path: 文件路径
            content: 要写入的内容
            create_dirs: 是否自动创建父目录
            encoding: 文件编码
            
        Returns:
            {"success": bool, "path": str, "bytes_written": int, "error": str}
        """
        try:
            path = Path(file_path)
            
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
                await f.write(content)
            
            return {
                "success": True,
                "path": str(path.absolute()),
                "bytes_written": len(content.encode(encoding))
            }
        except Exception as e:
            return {"success": False, "error": f"写入文件错误: {str(e)}"}
    
    async def append(
        self, 
        file_path: str, 
        content: str,
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        追加内容到文件末尾
        
        Args:
            file_path: 文件路径
            content: 要追加的内容
            encoding: 文件编码
            
        Returns:
            {"success": bool, "path": str, "bytes_appended": int, "error": str}
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": f"文件不存在: {file_path}"}
            
            async with aiofiles.open(file_path, 'a', encoding=encoding) as f:
                await f.write(content)
            
            return {
                "success": True,
                "path": str(path.absolute()),
                "bytes_appended": len(content.encode(encoding))
            }
        except Exception as e:
            return {"success": False, "error": f"追加文件错误: {str(e)}"}
    
    async def delete(self, file_path: str) -> Dict[str, Any]:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            {"success": bool, "path": str, "error": str}
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": f"文件不存在: {file_path}"}
            
            if not path.is_file():
                return {"success": False, "error": f"路径不是文件: {file_path}"}
            
            path.unlink()
            return {"success": True, "path": str(path.absolute())}
        except Exception as e:
            return {"success": False, "error": f"删除文件错误: {str(e)}"}
    
    async def exists(self, file_path: str) -> Dict[str, Any]:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            {"exists": bool, "is_file": bool, "path": str}
        """
        path = Path(file_path)
        return {
            "exists": path.exists(),
            "is_file": path.is_file() if path.exists() else False,
            "path": str(path.absolute())
        }
    
    async def info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件详细信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            {
                "success": bool,
                "name": str,
                "path": str,
                "size": int,  # 字节
                "extension": str,
                "created_at": str,
                "modified_at": str,
                "is_readable": bool,
                "is_writable": bool,
                "error": str
            }
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": f"文件不存在: {file_path}"}
            
            if not path.is_file():
                return {"success": False, "error": f"路径不是文件: {file_path}"}
            
            stat = path.stat()
            return {
                "success": True,
                "name": path.name,
                "path": str(path.absolute()),
                "size": stat.st_size,
                "extension": path.suffix,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_readable": os.access(path, os.R_OK),
                "is_writable": os.access(path, os.W_OK)
            }
        except Exception as e:
            return {"success": False, "error": f"获取文件信息错误: {str(e)}"}
    
    async def copy(
        self, 
        src_path: str, 
        dest_path: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        复制文件
        
        Args:
            src_path: 源文件路径
            dest_path: 目标文件路径
            overwrite: 是否覆盖已存在的目标文件
            
        Returns:
            {"success": bool, "src": str, "dest": str, "error": str}
        """
        try:
            src = Path(src_path)
            dest = Path(dest_path)
            
            if not src.exists():
                return {"success": False, "error": f"源文件不存在: {src_path}"}
            
            if dest.exists() and not overwrite:
                return {"success": False, "error": f"目标文件已存在: {dest_path}"}
            
            # 确保目标目录存在
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # 读取源文件
            async with aiofiles.open(src, 'rb') as f:
                content = await f.read()
            
            # 写入目标文件
            async with aiofiles.open(dest, 'wb') as f:
                await f.write(content)
            
            return {
                "success": True,
                "src": str(src.absolute()),
                "dest": str(dest.absolute())
            }
        except Exception as e:
            return {"success": False, "error": f"复制文件错误: {str(e)}"}
    
    async def move(
        self, 
        src_path: str, 
        dest_path: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        移动/重命名文件
        
        Args:
            src_path: 源文件路径
            dest_path: 目标文件路径
            overwrite: 是否覆盖已存在的目标文件
            
        Returns:
            {"success": bool, "src": str, "dest": str, "error": str}
        """
        try:
            src = Path(src_path)
            dest = Path(dest_path)
            
            if not src.exists():
                return {"success": False, "error": f"源文件不存在: {src_path}"}
            
            if dest.exists() and not overwrite:
                return {"success": False, "error": f"目标文件已存在: {dest_path}"}
            
            # 确保目标目录存在
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            src.rename(dest)
            return {
                "success": True,
                "src": str(src.absolute()),
                "dest": str(dest.absolute())
            }
        except Exception as e:
            return {"success": False, "error": f"移动文件错误: {str(e)}"}


# 工具元数据（供 MCP 动态发现）
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
                "encoding": {"type": "string", "description": "文件编码，默认 utf-8"}
            },
            "required": ["file_path"]
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "read",
        "async_method": True
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
                "encoding": {"type": "string", "description": "文件编码，默认 utf-8"}
            },
            "required": ["file_path", "content"]
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "write",
        "async_method": True
    },
    {
        "name": "file_append",
        "description": "追加内容到文件末尾",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "要追加的内容"},
                "encoding": {"type": "string", "description": "文件编码，默认 utf-8"}
            },
            "required": ["file_path", "content"]
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "append",
        "async_method": True
    },
    {
        "name": "file_delete",
        "description": "删除文件",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"}
            },
            "required": ["file_path"]
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "delete",
        "async_method": True
    },
    {
        "name": "file_exists",
        "description": "检查文件是否存在",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"}
            },
            "required": ["file_path"]
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "exists",
        "async_method": True
    },
    {
        "name": "file_info",
        "description": "获取文件详细信息（大小、创建时间、修改时间等）",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"}
            },
            "required": ["file_path"]
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "info",
        "async_method": True
    },
    {
        "name": "file_copy",
        "description": "复制文件到新位置",
        "parameters": {
            "type": "object",
            "properties": {
                "src_path": {"type": "string", "description": "源文件路径"},
                "dest_path": {"type": "string", "description": "目标文件路径"},
                "overwrite": {"type": "boolean", "description": "是否覆盖已存在的目标文件"}
            },
            "required": ["src_path", "dest_path"]
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "copy",
        "async_method": True
    },
    {
        "name": "file_move",
        "description": "移动/重命名文件",
        "parameters": {
            "type": "object",
            "properties": {
                "src_path": {"type": "string", "description": "源文件路径"},
                "dest_path": {"type": "string", "description": "目标文件路径"},
                "overwrite": {"type": "boolean", "description": "是否覆盖已存在的目标文件"}
            },
            "required": ["src_path", "dest_path"]
        },
        "module": "mylib.mcp.tools.file_tool",
        "class_name": "FileTool",
        "method": "move",
        "async_method": True
    }
]
