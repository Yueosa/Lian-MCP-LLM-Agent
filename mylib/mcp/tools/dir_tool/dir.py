"""目录操作工具核心实现模块"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from .utils import build_directory_tree, get_directory_info, list_directory_contents


def get_user_home() -> Path:
    """
    获取用户家目录（跨平台兼容）
    
    返回:
        用户家目录路径对象
    """
    return Path.home()


class DirTool:
    """目录操作工具类"""

    def __init__(self, default_base_path: Optional[str] = None):
        """
        初始化目录工具
        
        参数:
            default_base_path: 默认基础路径，None 则使用用户家目录
        """
        if default_base_path:
            self.default_base = Path(default_base_path)
        else:
            self.default_base = get_user_home()

    def _resolve_path(self, dir_path: str) -> Path:
        """
        解析路径，相对路径基于默认基础路径
        
        参数:
            dir_path: 用户输入的路径字符串
            
        返回:
            解析后的绝对路径对象
        """
        path = Path(dir_path)
        if not path.is_absolute():
            # 相对路径时，基于默认基础路径解析
            path = self.default_base / path
        return path.resolve()

    async def create(self, dir_path: str, exist_ok: bool = True) -> Dict[str, Any]:
        """
        创建目录（支持递归创建）
        
        参数:
            dir_path: 目录路径（相对于用户家目录或绝对路径）
            exist_ok: 如果目录已存在是否视为成功
            
        返回:
            包含 success、path、created 的字典
        """
        try:
            path = self._resolve_path(dir_path)
            already_exists = path.exists()
            if already_exists and not exist_ok:
                return {"success": False, "error": f"目录已存在: {path}"}
            path.mkdir(parents=True, exist_ok=exist_ok)
            return {"success": True, "path": str(path), "created": not already_exists}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"创建目录错误: {str(e)}"}

    async def delete(self, dir_path: str, recursive: bool = False) -> Dict[str, Any]:
        """
        删除目录
        
        参数:
            dir_path: 目录路径
            recursive: 是否递归删除（包含子目录和文件）
            
        返回:
            包含 success、path 的字典
        """
        try:
            path = self._resolve_path(dir_path)
            if not path.exists():
                return {"success": False, "error": f"目录不存在: {path}"}
            if not path.is_dir():
                return {"success": False, "error": f"路径不是目录: {path}"}
            if recursive:
                shutil.rmtree(path)
            else:
                try:
                    path.rmdir()
                except OSError:
                    return {"success": False, "error": f"目录非空，请使用 recursive=True: {path}"}
            return {"success": True, "path": str(path)}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"删除目录错误: {str(e)}"}

    async def list(
        self,
        dir_path: str,
        pattern: Optional[str] = None,
        include_hidden: bool = False,
        files_only: bool = False,
        dirs_only: bool = False,
    ) -> Dict[str, Any]:
        """
        列出目录内容
        
        参数:
            dir_path: 目录路径
            pattern: 文件名匹配模式（glob 语法），如 "*.py"
            include_hidden: 是否包含隐藏文件/目录
            files_only: 只列出文件
            dirs_only: 只列出目录
            
        返回:
            包含 success、path、items、total 的字典
        """
        try:
            path = self._resolve_path(dir_path)
            if not path.exists():
                return {"success": False, "error": f"目录不存在: {path}"}
            if not path.is_dir():
                return {"success": False, "error": f"路径不是目录: {path}"}

            items = list_directory_contents(path, pattern, include_hidden, files_only, dirs_only)
            return {"success": True, "path": str(path), "items": items, "total": len(items)}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"列出目录错误: {str(e)}"}

    async def exists(self, dir_path: str) -> Dict[str, Any]:
        """
        检查目录是否存在
        
        参数:
            dir_path: 目录路径
            
        返回:
            包含 exists、is_dir、path 的字典
        """
        path = self._resolve_path(dir_path)
        return {
            "exists": path.exists(),
            "is_dir": path.is_dir() if path.exists() else False,
            "path": str(path),
        }

    async def info(self, dir_path: str) -> Dict[str, Any]:
        """
        获取目录详细信息
        
        参数:
            dir_path: 目录路径
            
        返回:
            包含 success、name、path、created_at、modified_at、file_count、dir_count、total_size 的字典
        """
        try:
            path = self._resolve_path(dir_path)
            if not path.exists():
                return {"success": False, "error": f"目录不存在: {path}"}
            if not path.is_dir():
                return {"success": False, "error": f"路径不是目录: {path}"}

            stat = path.stat()
            stats = get_directory_info(path)

            return {
                "success": True,
                "name": path.name,
                "path": str(path),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "file_count": stats["file_count"],
                "dir_count": stats["dir_count"],
                "total_size": stats["total_size"],
            }
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"获取目录信息错误: {str(e)}"}

    async def tree(self, dir_path: str, max_depth: int = 3, include_hidden: bool = False) -> Dict[str, Any]:
        """
        获取目录树结构
        
        参数:
            dir_path: 目录路径
            max_depth: 最大递归深度
            include_hidden: 是否包含隐藏文件/目录
            
        返回:
            包含 success、path、tree 的字典
        """
        try:
            path = self._resolve_path(dir_path)
            if not path.exists():
                return {"success": False, "error": f"目录不存在: {path}"}
            if not path.is_dir():
                return {"success": False, "error": f"路径不是目录: {path}"}

            tree = build_directory_tree(path, max_depth, include_hidden)
            return {"success": True, "path": str(path), "tree": tree}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"获取目录树错误: {str(e)}"}

    async def copy(self, src_path: str, dest_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        复制目录
        
        参数:
            src_path: 源目录路径
            dest_path: 目标目录路径
            overwrite: 是否覆盖已存在的目标目录
            
        返回:
            包含 success、src、dest 的字典
        """
        try:
            src = self._resolve_path(src_path)
            dest = self._resolve_path(dest_path)
            if not src.exists():
                return {"success": False, "error": f"源目录不存在: {src}"}
            if not src.is_dir():
                return {"success": False, "error": f"源路径不是目录: {src}"}
            if dest.exists():
                if not overwrite:
                    return {"success": False, "error": f"目标目录已存在: {dest}"}
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            return {"success": True, "src": str(src), "dest": str(dest)}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"复制目录错误: {str(e)}"}

    async def move(self, src_path: str, dest_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        移动/重命名目录
        
        参数:
            src_path: 源目录路径
            dest_path: 目标目录路径
            overwrite: 是否覆盖已存在的目标目录
            
        返回:
            包含 success、src、dest 的字典
        """
        try:
            src = self._resolve_path(src_path)
            dest = self._resolve_path(dest_path)
            if not src.exists():
                return {"success": False, "error": f"源目录不存在: {src}"}
            if not src.is_dir():
                return {"success": False, "error": f"源路径不是目录: {src}"}
            if dest.exists():
                if not overwrite:
                    return {"success": False, "error": f"目标目录已存在: {dest}"}
                shutil.rmtree(dest)
            shutil.move(str(src), str(dest))
            return {"success": True, "src": str(src), "dest": str(dest)}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"移动目录错误: {str(e)}"}

