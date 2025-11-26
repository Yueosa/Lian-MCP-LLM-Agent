# Web Tool 模块文档

## 概述

`web_tool` 是 MCP (Model Context Protocol) 工具集的网页操作模块，提供异步网页获取、状态检查和元素提取功能。该模块采用统一的选择器驱动架构，简化了网页内容抽取流程。

## 架构设计

### 模块结构

```
web_tool/
├── __init__.py          # 包入口，导出 WebTool 和 TOOL_METADATA
├── metadata.py          # 工具元数据声明（供 Tool.py 发现）
├── web.py               # 核心 WebTool 类实现
├── web.config.toml      # 本地配置文件
├── web.md               # 本文档
└── utils/
    ├── __init__.py      # 工具函数导出
    └── extractors.py    # 通用元素提取助手
```

### 与 Tool.py 的集成

#### 兼容性分析

✅ **完全兼容** - web_tool 遵循 Tool.py 要求的所有约定：

1. **元数据格式**：`metadata.py` 中的 `TOOL_METADATA` 列表完全符合 `ToolMetaData` 数据类规范
2. **异步方法标识**：所有工具方法正确标记 `"async_method": True`
3. **模块/类/方法引用**：元数据中的 `module`, `class_name`, `method` 字段准确指向实际实现
4. **参数契约**：所有方法签名与元数据声明的参数类型一致

#### 发现流程

```python
# Tool.py 工作流程
1. ToolLoader._iter_package_modules()
   → 发现 mylib.mcp.tools.web_tool 包

2. 导入 web_tool.__init__
   → 获取 TOOL_METADATA 列表

3. ToolLoader._build_callables()
   → 实例化 WebTool()
   → 绑定方法：fetch, check_status, extract_elements

4. ToolLoader.call("web_fetch", url="...")
   → 检测 async_method=True
   → 执行 await fn(**kwargs)
```

## 功能特性

### 1. 配置管理

使用本地 `web.config.toml` 实现模块级配置隔离：

```toml
[http]
user_agent = "MCP-WebTool/1.0"
timeout = 30
max_content_length = 5242880  # 5 MB

[extraction]
default_limit = 50
resolve_url_attributes = ["href", "src"]
```

**优势**：

- 避免跨模块配置污染
- 通过 `ConfigLoader` 实现统一配置发现
- 支持类级缓存以提升性能

### 2. 核心工具方法

#### (1) web_fetch - 网页内容获取

获取完整或部分网页内容，支持行范围切片。

**方法签名**：

```python
async def fetch(
    self,
    url: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    timeout: Optional[int] = None,
) -> Dict[str, object]
```

**返回结构**：

```python
{
    "success": True,
    "url": "https://example.com",
    "final_url": "https://example.com/",  # 重定向后的最终 URL
    "status_code": 200,
    "content": "页面内容...",
    "lines_returned": 42,      # 返回的行数
    "total_lines": 150,        # 页面总行数
    "content_type": "text/html; charset=utf-8",
    "truncated": False         # 是否因长度限制被截断
}
```

**使用示例**：

```python
from mylib.mcp.tools import call_tool

# 获取完整页面
result = await call_tool("web_fetch", url="https://example.com")

# 获取特定行范围（第 10-50 行）
result = await call_tool(
    "web_fetch",
    url="https://example.com",
    start_line=10,
    end_line=50
)
```

**特性**：

- 自动处理重定向
- 内容长度限制（默认 5MB）
- 支持行级切片（1-indexed，包含边界）
- 异常安全（返回包含错误信息的字典）

#### (2) web_check_status - URL 状态检查

快速检查 URL 可达性和响应状态，不下载完整内容。

**方法签名**：

```python
async def check_status(
    self,
    url: str,
    timeout: Optional[int] = None,
) -> Dict[str, object]
```

**返回结构**：

```python
{
    "success": True,
    "url": "https://example.com",
    "status_code": 200,
    "content_type": "text/html",
    "content_length": 12345,
    "final_url": "https://www.example.com/",
    "is_redirect": True
}
```

**使用示例**：

```python
# 检查链接有效性
result = await call_tool("web_check_status", url="https://example.com")
if result["success"] and result["status_code"] == 200:
    print("链接有效")
```

**特性**：

- 不消费响应体（节省带宽）
- 自动跟随重定向
- 检测重定向状态
- 超时可配置

#### (3) web_extract_elements - 元素提取

基于 CSS 选择器提取特定页面元素及其属性、文本或 HTML。

**方法签名**：

```python
async def extract_elements(
    self,
    url: str,
    selector: str,
    *,
    attributes: Optional[Sequence[str]] = None,
    include_text: bool = True,
    include_html: bool = False,
    limit: Optional[int] = None,
    resolve_urls: Optional[Sequence[str]] = None,
    timeout: Optional[int] = None,
) -> Dict[str, object]
```

**参数说明**：

- `selector`: CSS 选择器（如 `"a.link"`, `"div#content > p"`, `"meta[property='og:title']"`）
- `attributes`: 需要提取的 HTML 属性列表（如 `["href", "src", "alt"]`）
- `include_text`: 是否包含元素的纯文本内容
- `include_html`: 是否包含元素的原始 HTML
- `limit`: 最大提取数量（默认 50）
- `resolve_urls`: 需要转换为绝对路径的属性（默认 `["href", "src"]`）
- `timeout`: 请求超时（默认 30 秒）

**返回结构**：

```python
{
    "success": True,
    "url": "https://example.com",
    "final_url": "https://example.com/",
    "selector": "a.external",
    "total": 12,
    "results": [
        {
            "index": 0,
            "tag": "a",
            "text": "Example Link",
            "attributes": {
                "href": "https://example.org",  # 已解析为绝对 URL
                "class": "external"
            },
            "html": "<a href=\"/link\" class=\"external\">Example Link</a>"
        },
        # ... 更多元素
    ],
    "truncated": False
}
```

**使用示例**：

```python
# 示例 1: 提取所有链接
result = await call_tool(
    "web_extract_elements",
    url="https://example.com",
    selector="a",
    attributes=["href", "title"]
)

# 示例 2: 提取元数据标签
result = await call_tool(
    "web_extract_elements",
    url="https://example.com",
    selector="meta[property^='og:']",  # OpenGraph 标签
    attributes=["property", "content"]
)

# 示例 3: 提取图片信息（包含 HTML）
result = await call_tool(
    "web_extract_elements",
    url="https://example.com/gallery",
    selector="img.photo",
    attributes=["src", "alt", "width", "height"],
    include_html=True,
    limit=10
)

# 示例 4: 提取文章段落
result = await call_tool(
    "web_extract_elements",
    url="https://blog.example.com/post",
    selector="article.content p",
    include_text=True,
    include_html=False
)
```

**特性**：

- 基于 BeautifulSoup 的强大 CSS 选择器支持
- 自动将相对 URL 解析为绝对路径
- 灵活控制输出内容（文本/属性/HTML）
- 结果数量限制（防止过载）
- 异常安全（解析失败返回错误信息）

### 3. 内部实现亮点

#### 配置缓存机制

```python
class WebTool:
    _CONFIG_CACHE: Dict[Tuple[str, bool], ConfigLoader] = {}

    @classmethod
    def _get_config_loader(cls, config_path, search_subdirs):
        cache_key = (config_path or str(DEFAULT_CONFIG_PATH), search_subdirs)
        if cache_key not in cls._CONFIG_CACHE:
            cls._CONFIG_CACHE[cache_key] = ConfigLoader(...)
        return cls._CONFIG_CACHE[cache_key]
```

**优势**：避免重复解析 TOML 文件，提升初始化性能。

#### 统一文档获取接口

```python
async def _retrieve_document(
    self,
    url: str,
    *,
    timeout: Optional[int] = None,
    allow_redirects: bool = True,
    consume_body: bool = True,  # check_status 时设为 False
) -> Dict[str, object]
```

**设计理由**：

- 代码复用（fetch 和 check_status 共享逻辑）
- 精细控制响应体处理（节省资源）
- 统一错误处理

#### 安全的内容长度限制

```python
def _clip_content(self, text: str) -> Tuple[str, bool]:
    if len(text) <= self._max_content_length:
        return text, False
    return text[: self._max_content_length], True
```

**防护**：防止超大页面导致内存溢出，并通过 `truncated` 标志告知调用者。

## 元数据契约

### 元数据定义（metadata.py）

所有工具必须在 `TOOL_METADATA` 中声明以下字段：

| 字段           | 类型 | 必需 | 说明                                                    |
| -------------- | ---- | ---- | ------------------------------------------------------- |
| `name`         | str  | ✅   | 工具唯一标识符（如 `web_fetch`）                        |
| `description`  | str  | ✅   | 工具功能描述                                            |
| `parameters`   | dict | ✅   | JSON Schema 格式的参数定义                              |
| `module`       | str  | ✅   | 完整模块路径（`mylib.mcp.tools.web_tool`）              |
| `class_name`   | str  | ✅   | 实现类名（`WebTool`）                                   |
| `method`       | str  | ✅   | 方法名（`fetch` / `check_status` / `extract_elements`） |
| `async_method` | bool | ✅   | 是否为异步方法（必须为 `True`）                         |

### 参数 Schema 规范

遵循 [JSON Schema Draft-07](https://json-schema.org/) 标准：

```python
{
    "type": "object",
    "properties": {
        "url": {
            "type": "string",
            "description": "网页 URL"
        },
        "selector": {
            "type": "string",
            "description": "CSS 选择器"
        }
    },
    "required": ["url", "selector"]
}
```

## 错误处理

### 错误返回格式

所有方法在失败时返回统一结构：

```python
{
    "success": False,
    "url": "https://example.com",
    "error": "HTTP 错误: 404",
    "status_code": 404  # 如适用
}
```

### 常见错误类型

| 错误类型     | 原因                         | 示例                                     |
| ------------ | ---------------------------- | ---------------------------------------- |
| 网络请求错误 | 连接失败、DNS 解析失败、超时 | `"网络请求错误: Cannot connect to host"` |
| HTTP 错误    | 服务器返回非 200 状态码      | `"HTTP 错误: 404"`                       |
| 解析错误     | HTML 解析失败、选择器无效    | `"获取网页错误: Invalid selector"`       |

### 异常安全保证

- **无泄漏**：所有异常在方法内部捕获并转换为字典返回
- **资源清理**：使用 `async with` 确保连接正确关闭
- **上下文保留**：错误信息包含原始 URL 和请求参数

## 配置指南

### 配置文件位置

默认：`mylib/mcp/tools/web_tool/web.config.toml`

### 配置项说明

#### [http] 部分

```toml
[http]
# HTTP 请求的 User-Agent 头
user_agent = "MCP-WebTool/1.0"

# 默认超时时间（秒）
timeout = 30

# 单次请求最大内容长度（字节）
max_content_length = 5242880  # 5 MB
```

#### [extraction] 部分

```toml
[extraction]
# extract_elements 的默认结果数量限制
default_limit = 50

# 需要自动解析为绝对路径的 HTML 属性
resolve_url_attributes = ["href", "src"]
```

### 覆盖配置

通过构造函数传递自定义配置路径：

```python
tool = WebTool(config_path="/path/to/custom.toml")
```

## 依赖项

### 必需依赖

```toml
[dependencies]
aiohttp = ">=3.13.2"       # 异步 HTTP 客户端
beautifulsoup4 = ">=4.14.2"  # HTML 解析
```

### 内部依赖

- `mylib.config.ConfigLoader` - 配置加载器
- `.utils.extractors` - 元素提取助手

## 性能考量

### 优化策略

1. **连接复用**：每次请求使用新 session（aiohttp 管理连接池）
2. **内容限制**：截断超大响应防止内存溢出
3. **按需下载**：`check_status` 不下载响应体
4. **配置缓存**：类级缓存避免重复解析配置文件

### 性能指标（参考）

| 操作                   | 平均耗时  | 备注                     |
| ---------------------- | --------- | ------------------------ |
| `web_fetch`            | 200-500ms | 取决于网络延迟和页面大小 |
| `web_check_status`     | 50-150ms  | 仅发送 HEAD 请求         |
| `web_extract_elements` | 300-800ms | 包含下载和 HTML 解析     |

## 测试建议

### 单元测试示例

```python
import pytest
from mylib.mcp.tools.web_tool import WebTool

@pytest.mark.asyncio
async def test_fetch_success():
    tool = WebTool()
    result = await tool.fetch("https://httpbin.org/html")
    assert result["success"] is True
    assert result["status_code"] == 200
    assert "content" in result

@pytest.mark.asyncio
async def test_check_status_redirect():
    tool = WebTool()
    result = await tool.check_status("http://httpbin.org/redirect/1")
    assert result["success"] is True
    assert result["is_redirect"] is True

@pytest.mark.asyncio
async def test_extract_elements():
    tool = WebTool()
    result = await tool.extract_elements(
        url="https://httpbin.org/html",
        selector="h1",
        include_text=True
    )
    assert result["success"] is True
    assert result["total"] >= 1
    assert result["results"][0]["tag"] == "h1"
```

### 集成测试

通过 `Tool.py` 测试完整调用链：

```python
from mylib.mcp.tools import get_tool_loader

@pytest.mark.asyncio
async def test_tool_loader_integration():
    loader = get_tool_loader()

    # 验证工具已注册
    tools = loader.get_tools_list()
    tool_names = [t["name"] for t in tools]
    assert "web_fetch" in tool_names
    assert "web_check_status" in tool_names
    assert "web_extract_elements" in tool_names

    # 通过加载器调用
    result = await loader.call("web_fetch", url="https://httpbin.org/html")
    assert result["success"] is True
```

## 最佳实践

### 1. 选择器编写建议

✅ **推荐**：

```python
# 精确选择器
"article.main-content p"
"div#header > nav > ul > li.active"
"meta[property='og:title']"

# 属性存在性检查
"a[href]"
"img[src][alt]"
```

❌ **不推荐**：

```python
# 过于宽泛（可能匹配大量无关元素）
"div"
"*"

# 性能较差的后代选择器
"body div span a"  # 优化为更精确的选择器
```

### 2. 错误处理模式

```python
result = await call_tool("web_fetch", url=user_provided_url)

if not result.get("success"):
    # 总是检查 success 字段
    logger.error(f"获取失败: {result.get('error')}")
    return None

# 继续处理成功结果
content = result["content"]
```

### 3. 超时配置

根据目标网站特性调整超时：

```python
# 快速 API 端点
result = await call_tool("web_fetch", url=api_url, timeout=10)

# 慢速或不稳定的站点
result = await call_tool("web_fetch", url=slow_site, timeout=60)
```

### 4. 结果限制

防止过度抓取：

```python
# 总是设置合理的 limit
result = await call_tool(
    "web_extract_elements",
    url=url,
    selector="a",
    limit=100  # 避免提取数千个链接
)
```

## 常见问题 (FAQ)

### Q1: 为什么 `extract_elements` 返回空数组？

**原因**：

- 选择器不匹配任何元素
- 页面使用 JavaScript 动态渲染（本工具不执行 JS）

**解决方案**：

```python
# 1. 验证选择器（在浏览器开发者工具中测试）
# 2. 检查返回的 HTML 内容
result = await call_tool("web_fetch", url=url)
print(result["content"])  # 查看实际 HTML 结构
```

### Q2: 如何处理需要认证的网页？

目前不直接支持。可通过以下方式实现：

```python
# 方案 1: 扩展 WebTool 添加自定义 headers
# 方案 2: 使用代理服务处理认证
# 方案 3: 直接修改 _session_kwargs 方法添加认证头
```

### Q3: 能否提取 JavaScript 渲染的内容？

**不能**。本工具基于静态 HTML 解析（BeautifulSoup），不执行 JavaScript。

**替代方案**：

- 考虑集成 Playwright/Selenium（需大幅增加依赖）
- 分析网站 API 直接调用数据接口
- 检查页面初始 HTML 中是否包含数据（部分 SSR 网站）

### Q4: 如何提取嵌套很深的元素？

使用后代选择器或多步提取：

```python
# 方法 1: 精确选择器
result = await call_tool(
    "web_extract_elements",
    url=url,
    selector="div.article > section.content > p.summary"
)

# 方法 2: 先提取父容器，再手动解析
# （如果需要复杂逻辑处理）
```

### Q5: `truncated=True` 时如何获取完整内容？

```python
# 方案 1: 使用行切片分段获取
total_lines = 1000  # 从第一次请求获取
chunk_size = 100
for start in range(1, total_lines, chunk_size):
    result = await call_tool(
        "web_fetch",
        url=url,
        start_line=start,
        end_line=start + chunk_size - 1
    )
    process(result["content"])

# 方案 2: 增加 max_content_length 配置
```

## 扩展开发

### 添加新工具方法

1. **在 `web.py` 中实现方法**：

```python
async def extract_tables(
    self,
    url: str,
    timeout: Optional[int] = None,
) -> Dict[str, object]:
    # 实现逻辑
    pass
```

2. **在 `metadata.py` 中注册**：

```python
{
    "name": "web_extract_tables",
    "description": "提取页面中的所有表格",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "网页 URL"}
        },
        "required": ["url"]
    },
    "module": "mylib.mcp.tools.web_tool",
    "class_name": "WebTool",
    "method": "extract_tables",
    "async_method": True
}
```

3. **更新 `__all__` 导出**（如需要）

### 自定义提取助手

在 `utils/` 下添加新模块：

```python
# utils/table_parser.py
from bs4 import BeautifulSoup
from typing import List, Dict

def parse_tables(soup: BeautifulSoup) -> List[Dict]:
    """提取并结构化所有表格"""
    tables = []
    for table in soup.find_all("table"):
        # 解析表头和行
        pass
    return tables
```

然后在 `web.py` 中导入使用。

## 版本历史

### v1.0.0 (当前)

- 初始版本
- 实现 `fetch`, `check_status`, `extract_elements` 三大核心功能
- 基于 ConfigLoader 的本地配置支持
- 完整的 Tool.py 集成

## 相关文档

- [Tool.py 工具加载器文档](../Tool.py)
- [ConfigLoader 配置管理文档](../../../config/docs/)
- [MCP 服务器架构文档](../../docs/)

## 许可证

MIT License - 参见项目根目录的 LICENSE 文件

---

**维护者**: Lian  
**创建日期**: 2025-01-26  
**最后更新**: 2025-01-26
