"""目录列表算法模块"""

from pathlib import Path
from typing import Dict, List, Optional, Any


def list_directory_contents(
    dir_path: Path,
    pattern: Optional[str] = None,
    include_hidden: bool = False,
    files_only: bool = False,
    dirs_only: bool = False,
) -> List[Dict[str, Any]]:
    """
    列出目录内容
    
    参数:
        dir_path: 目录路径对象
        pattern: 文件名匹配模式（glob 语法），如 "*.py"
        include_hidden: 是否包含隐藏文件/目录（以 . 开头）
        files_only: 只列出文件
        dirs_only: 只列出目录
        
    返回:
        包含目录项信息的列表，每项包含 name、type、size
    """
    items = []
    
    # 获取目录内容（支持 glob 模式）
    if pattern:
        entries = dir_path.glob(pattern)
    else:
        entries = dir_path.iterdir()
    
    # 遍历并过滤
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
        
        # 构建项信息
        item_info = {
            "name": item.name,
            "type": "directory" if is_dir else "file",
            "size": item.stat().st_size if is_file else 0,
        }
        items.append(item_info)
    
    # 按类型和名称排序（目录在前）
    items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
    
    return items
