"""描述可用 Web 工具操作的声明式元数据"""

TOOL_METADATA = [
    {
        "name": "web_fetch",
        "description": "获取网页内容（支持按行切片）",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "网页 URL"},
                "start_line": {"type": "integer", "description": "起始行号 (1-indexed)"},
                "end_line": {"type": "integer", "description": "结束行号 (1-indexed，包含)"},
                "timeout": {"type": "integer", "description": "请求超时时间（秒）"},
            },
            "required": ["url"],
        },
        "module": "mylib.mcp.tools.web_tool",
        "class_name": "WebTool",
        "method": "fetch",
        "async_method": True,
    },
    {
        "name": "web_check_status",
        "description": "检查 URL 状态（状态码、重定向等）",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "网页 URL"},
                "timeout": {"type": "integer", "description": "请求超时时间（秒）"},
            },
            "required": ["url"],
        },
        "module": "mylib.mcp.tools.web_tool",
        "class_name": "WebTool",
        "method": "check_status",
        "async_method": True,
    },
    {
        "name": "web_extract_elements",
        "description": "根据 CSS 选择器提取特定标签内容（可指定属性、文本、HTML）",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "网页 URL"},
                "selector": {"type": "string", "description": "CSS 选择器，如 div.info 或 meta[name='description']"},
                "attributes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "需要提取的属性列表，例如 ['href', 'src']"
                },
                "include_text": {
                    "type": "boolean",
                    "description": "是否返回元素的纯文本内容",
                    "default": True,
                },
                "include_html": {
                    "type": "boolean",
                    "description": "是否返回元素的原始 HTML",
                    "default": False,
                },
                "limit": {"type": "integer", "description": "最大提取数量"},
                "resolve_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "需要根据页面基础 URL 转换为绝对路径的属性名"
                },
                "timeout": {"type": "integer", "description": "请求超时时间（秒）"},
            },
            "required": ["url", "selector"],
        },
        "module": "mylib.mcp.tools.web_tool",
        "class_name": "WebTool",
        "method": "extract_elements",
        "async_method": True,
    },
]

__all__ = ["TOOL_METADATA"]
