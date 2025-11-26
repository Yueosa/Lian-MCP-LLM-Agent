"""
文件操作工具模块

提供文件的增删改查接口：
- read: 读取文件内容
- write: 写入/创建文件
- append: 追加内容到文件
- delete: 删除文件
- exists: 检查文件是否存在
- info: 获取文件信息
- copy: 复制文件
- move: 移动/重命名文件

默认路径基于用户家目录，支持相对路径和绝对路径。

# 默认基于用户家目录
tool = FileTool()
await tool.read("Documents/note.txt")  # 读取 ~/Documents/note.txt

# 自定义基础路径
tool = FileTool(default_base_path="/tmp")
await tool.write("test.txt", "content")  # 写入 /tmp/test.txt
"""

from .file import FileTool
from .metadata import TOOL_METADATA

__all__ = ["FileTool", "TOOL_METADATA"]

