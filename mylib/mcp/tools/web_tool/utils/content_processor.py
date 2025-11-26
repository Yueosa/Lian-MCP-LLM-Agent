"""内容处理算法模块"""

from typing import Optional, Tuple


def clip_content(text: str, max_length: int) -> str:
    """
    裁剪内容到最大长度
    
    参数:
        text: 原始文本
        max_length: 最大长度
        
    返回:
        裁剪后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length]


def slice_lines_from_content(
    content: str,
    start_idx: Optional[int] = None,
    end_idx: Optional[int] = None,
) -> str:
    """
    按行切片内容（使用 0-based 索引）
    
    参数:
        content: 原始内容
        start_idx: 起始行索引（0-based），None 表示从头开始
        end_idx: 结束行索引（0-based，不包含），None 表示到末尾
        
    返回:
        切片后的内容
    """
    lines = content.split("\n")
    selected = lines[start_idx:end_idx]
    return "\n".join(selected)
