"""文件信息查询算法模块"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def get_file_info(path: Path) -> Dict[str, Any]:
    """
    获取文件详细信息
    
    参数:
        path: 文件路径对象
        
    返回:
        包含文件名、大小、扩展名、时间戳等信息的字典
    """
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    
    if not path.is_file():
        raise ValueError(f"路径不是文件: {path}")
    
    stat = path.stat()
    return {
        "name": path.name,
        "size": stat.st_size,
        "extension": path.suffix,
        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "is_readable": os.access(path, os.R_OK),
        "is_writable": os.access(path, os.W_OK),
    }


def check_file_exists(path: Path) -> Dict[str, Any]:
    """
    检查文件是否存在
    
    参数:
        path: 文件路径对象
        
    返回:
        包含 exists、is_file 的字典
    """
    return {
        "exists": path.exists(),
        "is_file": path.is_file() if path.exists() else False,
    }
