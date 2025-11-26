"""
目录操作工具模块

提供目录的增删改查接口：
- create: 创建目录
- delete: 删除目录
- list: 列出目录内容
- exists: 检查目录是否存在
- info: 获取目录信息
- tree: 获取目录树结构
- copy: 复制目录
- move: 移动/重命名目录

默认路径基于用户家目录，支持相对路径和绝对路径。

# 默认基于用户家目录
tool = DirTool()
await tool.list("Documents")  # 列出 ~/Documents

# 自定义基础路径
tool = DirTool(default_base_path="/var/log")
await tool.list("nginx")  # 列出 /var/log/nginx
"""

from .dir import DirTool
from .metadata import TOOL_METADATA

__all__ = ["DirTool", "TOOL_METADATA"]

