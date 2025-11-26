"""
DirTool - 目录操作工具

提供目录的完整 CRUD 操作接口。
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List


class DirTool:
    """目录操作工具类"""
    
    async def create(
        self, 
        dir_path: str, 
        exist_ok: bool = True
    ) -> Dict[str, Any]:
        """
        创建目录（支持递归创建）
        
        Args:
            dir_path: 目录路径
            exist_ok: 如果目录已存在是否视为成功
            
        Returns:
            {"success": bool, "path": str, "created": bool, "error": str}
        """
        try:
            path = Path(dir_path)
            already_exists = path.exists()
            
            if already_exists and not exist_ok:
                return {"success": False, "error": f"目录已存在: {dir_path}"}
            
            path.mkdir(parents=True, exist_ok=exist_ok)
            return {
                "success": True,
                "path": str(path.absolute()),
                "created": not already_exists
            }
        except Exception as e:
            return {"success": False, "error": f"创建目录错误: {str(e)}"}
    
    async def delete(
        self, 
        dir_path: str, 
        recursive: bool = False
    ) -> Dict[str, Any]:
        """
        删除目录
        
        Args:
            dir_path: 目录路径
            recursive: 是否递归删除（包含子目录和文件）
            
        Returns:
            {"success": bool, "path": str, "error": str}
        """
        try:
            path = Path(dir_path)
            
            if not path.exists():
                return {"success": False, "error": f"目录不存在: {dir_path}"}
            
            if not path.is_dir():
                return {"success": False, "error": f"路径不是目录: {dir_path}"}
            
            if recursive:
                shutil.rmtree(path)
            else:
                # 非递归删除，目录必须为空
                try:
                    path.rmdir()
                except OSError:
                    return {"success": False, "error": f"目录非空，请使用 recursive=True: {dir_path}"}
            
            return {"success": True, "path": str(path.absolute())}
        except Exception as e:
            return {"success": False, "error": f"删除目录错误: {str(e)}"}
    
    async def list(
        self, 
        dir_path: str,
        pattern: Optional[str] = None,
        include_hidden: bool = False,
        files_only: bool = False,
        dirs_only: bool = False
    ) -> Dict[str, Any]:
        """
        列出目录内容
        
        Args:
            dir_path: 目录路径
            pattern: 文件名匹配模式（glob 语法），如 "*.py"
            include_hidden: 是否包含隐藏文件/目录（以 . 开头）
            files_only: 只列出文件
            dirs_only: 只列出目录
            
        Returns:
            {
                "success": bool,
                "path": str,
                "items": [{"name": str, "type": str, "size": int}],
                "total": int,
                "error": str
            }
        """
        try:
            path = Path(dir_path)
            
            if not path.exists():
                return {"success": False, "error": f"目录不存在: {dir_path}"}
            
            if not path.is_dir():
                return {"success": False, "error": f"路径不是目录: {dir_path}"}
            
            items = []
            
            # 获取目录内容
            if pattern:
                entries = path.glob(pattern)
            else:
                entries = path.iterdir()
            
            for item in entries:
                # 过滤隐藏文件
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                is_dir = item.is_dir()
                is_file = item.is_file()
                
                # 过滤类型
                if files_only and not is_file:
                    continue
                if dirs_only and not is_dir:
                    continue
                
                item_info = {
                    "name": item.name,
                    "type": "directory" if is_dir else "file",
                    "size": item.stat().st_size if is_file else 0
                }
                items.append(item_info)
            
            # 按类型和名称排序（目录在前）
            items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
            
            return {
                "success": True,
                "path": str(path.absolute()),
                "items": items,
                "total": len(items)
            }
        except Exception as e:
            return {"success": False, "error": f"列出目录错误: {str(e)}"}
    
    async def exists(self, dir_path: str) -> Dict[str, Any]:
        """
        检查目录是否存在
        
        Args:
            dir_path: 目录路径
            
        Returns:
            {"exists": bool, "is_dir": bool, "path": str}
        """
        path = Path(dir_path)
        return {
            "exists": path.exists(),
            "is_dir": path.is_dir() if path.exists() else False,
            "path": str(path.absolute())
        }
    
    async def info(self, dir_path: str) -> Dict[str, Any]:
        """
        获取目录详细信息
        
        Args:
            dir_path: 目录路径
            
        Returns:
            {
                "success": bool,
                "name": str,
                "path": str,
                "created_at": str,
                "modified_at": str,
                "file_count": int,
                "dir_count": int,
                "total_size": int,
                "error": str
            }
        """
        try:
            path = Path(dir_path)
            
            if not path.exists():
                return {"success": False, "error": f"目录不存在: {dir_path}"}
            
            if not path.is_dir():
                return {"success": False, "error": f"路径不是目录: {dir_path}"}
            
            stat = path.stat()
            
            # 统计文件和子目录数量
            file_count = 0
            dir_count = 0
            total_size = 0
            
            for item in path.iterdir():
                if item.is_file():
                    file_count += 1
                    total_size += item.stat().st_size
                elif item.is_dir():
                    dir_count += 1
            
            return {
                "success": True,
                "name": path.name,
                "path": str(path.absolute()),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "file_count": file_count,
                "dir_count": dir_count,
                "total_size": total_size
            }
        except Exception as e:
            return {"success": False, "error": f"获取目录信息错误: {str(e)}"}
    
    async def tree(
        self, 
        dir_path: str,
        max_depth: int = 3,
        include_hidden: bool = False
    ) -> Dict[str, Any]:
        """
        获取目录树结构
        
        Args:
            dir_path: 目录路径
            max_depth: 最大递归深度
            include_hidden: 是否包含隐藏文件/目录
            
        Returns:
            {
                "success": bool,
                "path": str,
                "tree": {...},  # 树形结构
                "error": str
            }
        """
        try:
            path = Path(dir_path)
            
            if not path.exists():
                return {"success": False, "error": f"目录不存在: {dir_path}"}
            
            if not path.is_dir():
                return {"success": False, "error": f"路径不是目录: {dir_path}"}
            
            def build_tree(p: Path, depth: int) -> Dict:
                node = {
                    "name": p.name,
                    "type": "directory",
                    "children": []
                }
                
                if depth >= max_depth:
                    node["truncated"] = True
                    return node
                
                try:
                    for item in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                        if not include_hidden and item.name.startswith('.'):
                            continue
                        
                        if item.is_dir():
                            node["children"].append(build_tree(item, depth + 1))
                        else:
                            node["children"].append({
                                "name": item.name,
                                "type": "file",
                                "size": item.stat().st_size
                            })
                except PermissionError:
                    node["error"] = "Permission denied"
                
                return node
            
            tree = build_tree(path, 0)
            
            return {
                "success": True,
                "path": str(path.absolute()),
                "tree": tree
            }
        except Exception as e:
            return {"success": False, "error": f"获取目录树错误: {str(e)}"}
    
    async def copy(
        self, 
        src_path: str, 
        dest_path: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        复制目录
        
        Args:
            src_path: 源目录路径
            dest_path: 目标目录路径
            overwrite: 是否覆盖已存在的目标目录
            
        Returns:
            {"success": bool, "src": str, "dest": str, "error": str}
        """
        try:
            src = Path(src_path)
            dest = Path(dest_path)
            
            if not src.exists():
                return {"success": False, "error": f"源目录不存在: {src_path}"}
            
            if not src.is_dir():
                return {"success": False, "error": f"源路径不是目录: {src_path}"}
            
            if dest.exists():
                if not overwrite:
                    return {"success": False, "error": f"目标目录已存在: {dest_path}"}
                shutil.rmtree(dest)
            
            shutil.copytree(src, dest)
            
            return {
                "success": True,
                "src": str(src.absolute()),
                "dest": str(dest.absolute())
            }
        except Exception as e:
            return {"success": False, "error": f"复制目录错误: {str(e)}"}
    
    async def move(
        self, 
        src_path: str, 
        dest_path: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        移动/重命名目录
        
        Args:
            src_path: 源目录路径
            dest_path: 目标目录路径
            overwrite: 是否覆盖已存在的目标目录
            
        Returns:
            {"success": bool, "src": str, "dest": str, "error": str}
        """
        try:
            src = Path(src_path)
            dest = Path(dest_path)
            
            if not src.exists():
                return {"success": False, "error": f"源目录不存在: {src_path}"}
            
            if not src.is_dir():
                return {"success": False, "error": f"源路径不是目录: {src_path}"}
            
            if dest.exists():
                if not overwrite:
                    return {"success": False, "error": f"目标目录已存在: {dest_path}"}
                shutil.rmtree(dest)
            
            shutil.move(str(src), str(dest))
            
            return {
                "success": True,
                "src": str(src.absolute()),
                "dest": str(dest.absolute())
            }
        except Exception as e:
            return {"success": False, "error": f"移动目录错误: {str(e)}"}


# 工具元数据（供 MCP 动态发现）
TOOL_METADATA = [
    {
        "name": "dir_create",
        "description": "创建目录（支持递归创建）",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "目录路径"},
                "exist_ok": {"type": "boolean", "description": "如果目录已存在是否视为成功"}
            },
            "required": ["dir_path"]
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "create",
        "async_method": True
    },
    {
        "name": "dir_delete",
        "description": "删除目录",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "目录路径"},
                "recursive": {"type": "boolean", "description": "是否递归删除（包含子目录和文件）"}
            },
            "required": ["dir_path"]
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "delete",
        "async_method": True
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
                "dirs_only": {"type": "boolean", "description": "只列出目录"}
            },
            "required": ["dir_path"]
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "list",
        "async_method": True
    },
    {
        "name": "dir_exists",
        "description": "检查目录是否存在",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "目录路径"}
            },
            "required": ["dir_path"]
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "exists",
        "async_method": True
    },
    {
        "name": "dir_info",
        "description": "获取目录详细信息（文件数、子目录数、总大小等）",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "目录路径"}
            },
            "required": ["dir_path"]
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "info",
        "async_method": True
    },
    {
        "name": "dir_tree",
        "description": "获取目录树结构",
        "parameters": {
            "type": "object",
            "properties": {
                "dir_path": {"type": "string", "description": "目录路径"},
                "max_depth": {"type": "integer", "description": "最大递归深度，默认 3"},
                "include_hidden": {"type": "boolean", "description": "是否包含隐藏文件/目录"}
            },
            "required": ["dir_path"]
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "tree",
        "async_method": True
    },
    {
        "name": "dir_copy",
        "description": "复制目录到新位置",
        "parameters": {
            "type": "object",
            "properties": {
                "src_path": {"type": "string", "description": "源目录路径"},
                "dest_path": {"type": "string", "description": "目标目录路径"},
                "overwrite": {"type": "boolean", "description": "是否覆盖已存在的目标目录"}
            },
            "required": ["src_path", "dest_path"]
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "copy",
        "async_method": True
    },
    {
        "name": "dir_move",
        "description": "移动/重命名目录",
        "parameters": {
            "type": "object",
            "properties": {
                "src_path": {"type": "string", "description": "源目录路径"},
                "dest_path": {"type": "string", "description": "目标目录路径"},
                "overwrite": {"type": "boolean", "description": "是否覆盖已存在的目标目录"}
            },
            "required": ["src_path", "dest_path"]
        },
        "module": "mylib.mcp.tools.dir_tool",
        "class_name": "DirTool",
        "method": "move",
        "async_method": True
    }
]
