"""文件读写操作算法模块"""

import aiofiles
from pathlib import Path
from typing import Optional, Tuple, Dict, Any


async def read_file_content(
    path: Path,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    encoding: str = "utf-8",
) -> Dict[str, Any]:
    """
    读取文件内容（支持按行范围读取）
    
    参数:
        path: 文件路径对象
        start_line: 起始行号（1-indexed），None 表示从头开始
        end_line: 结束行号（1-indexed，包含），None 表示读到末尾
        encoding: 文件编码
        
    返回:
        包含 content、lines_read、total_lines 的字典
    """
    try:
        async with aiofiles.open(path, "r", encoding=encoding) as f:
            lines = await f.readlines()
        
        total_lines = len(lines)
        
        # 处理行范围
        if start_line is not None or end_line is not None:
            start_idx = (start_line - 1) if start_line else 0
            end_idx = end_line if end_line else total_lines
            start_idx = max(0, start_idx)
            end_idx = min(total_lines, end_idx)
            selected_lines = lines[start_idx:end_idx]
            content = "".join(selected_lines)
            lines_read = len(selected_lines)
        else:
            content = "".join(lines)
            lines_read = total_lines
        
        return {
            "content": content,
            "lines_read": lines_read,
            "total_lines": total_lines,
        }
    except UnicodeDecodeError as e:
        raise ValueError(f"编码错误: {str(e)}")


async def write_file_content(
    path: Path,
    content: str,
    create_dirs: bool = True,
    encoding: str = "utf-8",
) -> int:
    """
    写入文件内容（覆盖模式）
    
    参数:
        path: 文件路径对象
        content: 要写入的内容
        create_dirs: 是否自动创建父目录
        encoding: 文件编码
        
    返回:
        写入的字节数
    """
    if create_dirs:
        path.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiofiles.open(path, "w", encoding=encoding) as f:
        await f.write(content)
    
    return len(content.encode(encoding))


async def append_file_content(
    path: Path,
    content: str,
    encoding: str = "utf-8",
) -> int:
    """
    追加内容到文件末尾
    
    参数:
        path: 文件路径对象
        content: 要追加的内容
        encoding: 文件编码
        
    返回:
        追加的字节数
    """
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    async with aiofiles.open(path, "a", encoding=encoding) as f:
        await f.write(content)
    
    return len(content.encode(encoding))
