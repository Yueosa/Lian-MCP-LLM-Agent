"""
用于网页抓取的 MCP 工具包

提供以下功能:
- fetch: 获取并返回 URL 的 HTML 内容
- check_status: 检查 URL 的 HTTP 状态和元数据
- extract_elements: 使用 CSS 选择器从 HTML 中提取元素

支持超时控制、内容裁剪、URL 重定向和属性解析
"""

from .metadata import TOOL_METADATA
from .web import WebTool


__all__ = [
    "WebTool",
    "TOOL_METADATA",
]
