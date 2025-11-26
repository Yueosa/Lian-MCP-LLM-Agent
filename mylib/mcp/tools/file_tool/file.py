"""文件操作工具核心实现模块"""

from pathlib import Path
from typing import Optional, Dict, Any

from .utils import (
    append_file_content,
    check_file_exists,
    copy_file,
    delete_file,
    get_file_info,
    move_file,
    read_file_content,
    write_file_content,
)


def get_user_home() -> Path:
    """
    获取用户家目录（跨平台兼容）
    
    返回:
        用户家目录路径对象
    """
    return Path.home()


class FileTool:
    """文件操作工具类"""

    def __init__(self, default_base_path: Optional[str] = None):
        """
        初始化文件工具
        
        参数:
            default_base_path: 默认基础路径，None 则使用用户家目录
        """
        if default_base_path:
            self.default_base = Path(default_base_path)
        else:
            self.default_base = get_user_home()

    def _resolve_path(self, file_path: str) -> Path:
        """
        解析路径，相对路径基于默认基础路径
        
        参数:
            file_path: 用户输入的路径字符串
            
        返回:
            解析后的绝对路径对象
        """
        path = Path(file_path)
        if not path.is_absolute():
            # 相对路径时，基于默认基础路径解析
            path = self.default_base / path
        return path.resolve()

    async def read(
        self,
        file_path: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """
        读取文件内容
        
        参数:
            file_path: 文件路径（相对于用户家目录或绝对路径）
            start_line: 起始行号（1-indexed），None 表示从头开始
            end_line: 结束行号（1-indexed，包含），None 表示读到末尾
            encoding: 文件编码，默认 utf-8
            
        返回:
            包含 success、content、lines_read、total_lines 的字典
        """
        try:
            path = self._resolve_path(file_path)
            if not path.exists():
                return {"success": False, "error": f"文件不存在: {path}"}
            if not path.is_file():
                return {"success": False, "error": f"路径不是文件: {path}"}

            result = await read_file_content(path, start_line, end_line, encoding)
            return {"success": True, **result}
        except ValueError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"读取文件错误: {str(e)}"}

    async def write(
        self,
        file_path: str,
        content: str,
        create_dirs: bool = True,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """
        写入/创建文件（覆盖模式）
        
        参数:
            file_path: 文件路径
            content: 要写入的内容
            create_dirs: 是否自动创建父目录
            encoding: 文件编码
            
        返回:
            包含 success、path、bytes_written 的字典
        """
        try:
            path = self._resolve_path(file_path)
            bytes_written = await write_file_content(path, content, create_dirs, encoding)
            return {"success": True, "path": str(path), "bytes_written": bytes_written}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"写入文件错误: {str(e)}"}

    async def append(
        self,
        file_path: str,
        content: str,
        encoding: str = "utf-8",
    ) -> Dict[str, Any]:
        """
        追加内容到文件末尾
        
        参数:
            file_path: 文件路径
            content: 要追加的内容
            encoding: 文件编码
            
        返回:
            包含 success、path、bytes_appended 的字典
        """
        try:
            path = self._resolve_path(file_path)
            bytes_appended = await append_file_content(path, content, encoding)
            return {"success": True, "path": str(path), "bytes_appended": bytes_appended}
        except FileNotFoundError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"追加文件错误: {str(e)}"}

    async def delete(self, file_path: str) -> Dict[str, Any]:
        """
        删除文件
        
        参数:
            file_path: 文件路径
            
        返回:
            包含 success、path 的字典
        """
        try:
            path = self._resolve_path(file_path)
            await delete_file(path)
            return {"success": True, "path": str(path)}
        except (FileNotFoundError, ValueError) as e:
            return {"success": False, "error": str(e)}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"删除文件错误: {str(e)}"}

    async def exists(self, file_path: str) -> Dict[str, Any]:
        """
        检查文件是否存在
        
        参数:
            file_path: 文件路径
            
        返回:
            包含 exists、is_file、path 的字典
        """
        path = self._resolve_path(file_path)
        result = check_file_exists(path)
        return {**result, "path": str(path)}

    async def info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件详细信息
        
        参数:
            file_path: 文件路径
            
        返回:
            包含 success、name、path、size、extension、时间戳等的字典
        """
        try:
            path = self._resolve_path(file_path)
            info = get_file_info(path)
            return {"success": True, "path": str(path), **info}
        except (FileNotFoundError, ValueError) as e:
            return {"success": False, "error": str(e)}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"获取文件信息错误: {str(e)}"}

    async def copy(
        self,
        src_path: str,
        dest_path: str,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """
        复制文件
        
        参数:
            src_path: 源文件路径
            dest_path: 目标文件路径
            overwrite: 是否覆盖已存在的目标文件
            
        返回:
            包含 success、src、dest 的字典
        """
        try:
            src = self._resolve_path(src_path)
            dest = self._resolve_path(dest_path)
            await copy_file(src, dest, overwrite)
            return {"success": True, "src": str(src), "dest": str(dest)}
        except (FileNotFoundError, FileExistsError) as e:
            return {"success": False, "error": str(e)}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"复制文件错误: {str(e)}"}

    async def move(
        self,
        src_path: str,
        dest_path: str,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """
        移动/重命名文件
        
        参数:
            src_path: 源文件路径
            dest_path: 目标文件路径
            overwrite: 是否覆盖已存在的目标文件
            
        返回:
            包含 success、src、dest 的字典
        """
        try:
            src = self._resolve_path(src_path)
            dest = self._resolve_path(dest_path)
            await move_file(src, dest, overwrite)
            return {"success": True, "src": str(src), "dest": str(dest)}
        except (FileNotFoundError, FileExistsError) as e:
            return {"success": False, "error": str(e)}
        except Exception as e:  # noqa: BLE001
            return {"success": False, "error": f"移动文件错误: {str(e)}"}

