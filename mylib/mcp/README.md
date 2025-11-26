# MCP Server

FastAPI 实现的工具聚合服务，提供统一的工具发现与调用接口。

---

## API 文档

### GET `/`

**描述**：获取服务状态

**响应**：

```json
{
  "message": "MCP Server is running",
  "version": "1.0.0",
  "tools_count": 19
}
```

---

### GET `/help`

**描述**: 获取服务帮助

**响应**:

```json
{
  "message": "欢迎使用 MCP Server !",
  "endpoints": {
    "/tools": "获取所有可用工具列表",
    "/tools/{tool_name}": "获取指定工具的详细信息",
    "/tools/{tool_name}/call": "调用单个工具",
    "/tools/reload": "热重载工具元数据与绑定"
  }
}
```

---

### GET `/health`

**描述**：健康检查

**响应**：

```json
{
  "status": "healthy",
  "service": "mcp-server"
}
```

---

### GET `/tools`

**描述**：获取所有可用工具列表

**响应**：

```json
{
  "tools": [
    {
      "name": "file_read",
      "description": "读取文件内容，支持按行范围读取",
      "parameters": {
        "type": "object",
        "properties": {
          "file_path": { "type": "string", "description": "文件路径" },
          "start_line": {
            "type": "integer",
            "description": "起始行号（1-indexed）"
          },
          "end_line": {
            "type": "integer",
            "description": "结束行号（1-indexed，包含）"
          },
          "encoding": {
            "type": "string",
            "description": "文件编码，默认 utf-8"
          }
        },
        "required": ["file_path"]
      }
    }
    // ... 更多工具
  ]
}
```

---

### GET `/tools/{tool_name}`

**描述**：获取指定工具的详细元数据

**路径参数**：

- `tool_name`：工具名称（如 `file_read`）

**响应示例**：

```json
{
  "tool": {
    "name": "file_read",
    "description": "读取文件内容，支持按行范围读取",
    "parameters": {
      /* ... */
    },
    "module": "mylib.mcp.tools.file_tool",
    "class_name": "FileTool",
    "method": "read",
    "async_method": true
  }
}
```

**错误响应**（404）：

```json
{
  "detail": "工具不存在: invalid_tool"
}
```

---

### POST `/tools/{tool_name}/call`

**描述**：调用单个工具

**路径参数**：

- `tool_name`：工具名称

**请求体**：

```json
{
  "file_path": "README.md",
  "start_line": 1,
  "end_line": 20
}
```

**响应格式**（统一）：

```json
{
  "result": {
    /* 工具返回的结果 */
  },
  "success": true,
  "error": null
}
```

**成功示例**（`file_read`）：

```json
{
  "result": {
    "success": true,
    "content": "# MCP Server\n...",
    "lines_read": 20,
    "total_lines": 100
  },
  "success": true,
  "error": null
}
```

**失败示例**（工具不存在）：

```json
{
  "result": null,
  "success": false,
  "error": "工具不存在: invalid_tool"
}
```

**失败示例**（工具执行错误）：

```json
{
  "result": null,
  "success": false,
  "error": "读取文件错误: [Errno 2] No such file or directory: 'missing.txt'"
}
```

---

### POST `/tools/reload`

**描述**：热重载工具（无需重启服务）

**请求体**：无

**响应**：

```json
{
  "success": true,
  "tools_count": 19,
  "tools": [
    /* 工具列表 */
  ]
}
```

**错误响应**：

```json
{
  "success": false,
  "error": "重载失败原因"
}
```

## 运行

### 使用 venv / pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m mylib.mcp.mcp
```

### 使用 uv（可选）

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
python -m mylib.mcp.mcp
```

## 示例

```bash
# 健康检查
curl http://127.0.0.1:8080/health

# 列出工具
curl http://127.0.0.1:8080/tools

# 调用文件读取
curl -X POST http://127.0.0.1:8080/tools/file_read/call \
  -H 'Content-Type: application/json' \
  -d '{"file_path":"README.md","start_line":1,"end_line":20}'

# 调用目录列表
curl -X POST http://127.0.0.1:8080/tools/dir_list/call \
  -H 'Content-Type: application/json' \
  -d '{"dir_path":".","pattern":"*.py"}'

# 检查文件是否存在
curl -X POST http://127.0.0.1:8080/tools/file_exists/call \
  -H 'Content-Type: application/json' \
  -d '{"file_path":"README.md"}'

# 热重载（新增/修改工具后）
curl -X POST http://127.0.0.1:8080/tools/reload
```

## 配置

`mylib/mcp/config/mcp_config.toml`

```toml
[fastapi]
host = "0.0.0.0"
port = 8080
debug = true
```

当前 CORS 全开放，若需限制域名或添加鉴权，可在后续加入。
