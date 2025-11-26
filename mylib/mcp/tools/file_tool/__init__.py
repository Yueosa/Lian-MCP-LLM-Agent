"""
file_tool - 文件操作工具

提供文件的增删改查接口：
- read: 读取文件内容
- write: 写入/创建文件
- delete: 删除文件
- exists: 检查文件是否存在
- info: 获取文件信息
- append: 追加内容到文件
"""

from .file_tool import FileTool, TOOL_METADATA

__all__ = ["FileTool", "TOOL_METADATA"]
