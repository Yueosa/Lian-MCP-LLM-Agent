"""目录树构建算法模块"""

from pathlib import Path
from typing import Dict, Any


def build_directory_tree(
    path: Path,
    max_depth: int,
    include_hidden: bool,
    current_depth: int = 0,
) -> Dict[str, Any]:
    """
    递归构建目录树结构
    
    参数:
        path: 当前路径对象
        max_depth: 最大递归深度
        include_hidden: 是否包含隐藏文件/目录
        current_depth: 当前深度（内部递归使用）
        
    返回:
        树形结构字典，包含 name、type、children 等字段
    """
    node: Dict[str, Any] = {
        "name": path.name,
        "type": "directory",
        "children": [],
    }
    
    # 达到最大深度，标记截断
    if current_depth >= max_depth:
        node["truncated"] = True
        return node
    
    try:
        # 遍历子项，按类型和名称排序
        for item in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            # 跳过隐藏项
            if not include_hidden and item.name.startswith('.'):
                continue
            
            if item.is_dir():
                # 递归处理子目录
                child_node = build_directory_tree(
                    item,
                    max_depth,
                    include_hidden,
                    current_depth + 1,
                )
                node["children"].append(child_node)
            else:
                # 添加文件节点
                node["children"].append({
                    "name": item.name,
                    "type": "file",
                    "size": item.stat().st_size,
                })
    except PermissionError:
        # 权限不足时标记错误
        node["error"] = "Permission denied"
    
    return node
