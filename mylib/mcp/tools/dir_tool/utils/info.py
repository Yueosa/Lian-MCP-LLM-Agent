"""目录信息统计算法模块"""

from pathlib import Path
from typing import Dict, Any


def get_directory_info(path: Path) -> Dict[str, Any]:
    """
    统计目录的文件数、子目录数和总大小
    
    参数:
        path: 目录路径对象
        
    返回:
        包含 file_count、dir_count、total_size 的字典
    """
    file_count = 0
    dir_count = 0
    total_size = 0
    
    # 遍历直接子项（不递归）
    for item in path.iterdir():
        if item.is_file():
            file_count += 1
            total_size += item.stat().st_size
        elif item.is_dir():
            dir_count += 1
    
    return {
        "file_count": file_count,
        "dir_count": dir_count,
        "total_size": total_size,
    }
