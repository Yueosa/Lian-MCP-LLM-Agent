# Lian-MCP-LLM Agent 系统

##### 本地多专家智能体调度系统 + 工具调用协议管理 + 可扩展知识库

By - Lian - 2025

---

- [Lian-MCP-LLM Agent 系统](#lian-mcp-llm-agent-系统) - [本地多专家智能体调度系统 + 工具调用协议管理 + 可扩展知识库](#本地多专家智能体调度系统--工具调用协议管理--可扩展知识库)
  - [项目核心](#项目核心)
    - [| 顶层：多专家协作与调度 (论文亮点)](#-顶层多专家协作与调度-论文亮点)
  - [开发进度](#开发进度)
    - [| 数据库 --done--](#-数据库---done--)
      - [SQL 模块 --done--](#sql-模块---done--)
      - [测试套件](#测试套件)
    - [| mcp 包 --done--](#-mcp-包---done--)
      - [核心功能](#核心功能)
      - [API 端点](#api-端点)
      - [启动方式](#启动方式)
    - [| llm 包 --done-- (等待 Core 完成后进行重构)](#-llm-包---done---等待-core-完成后进行重构)
      - [核心功能](#核心功能-1)
      - [使用方式](#使用方式)
    - [| Config 包 --done--](#-config-包---done--)
    - [| utils 包](#-utils-包)
      - [目前实现的包](#目前实现的包)
      - [Printer --done--](#printer---done--)
      - [Loutput --done--](#loutput---done--)
  - [🎓 学术使用声明](#-学术使用声明)

---

## 项目核心

#### | 顶层：多专家协作与调度 (论文亮点)

包括：

1. **专家自动生成（Auto-spawn agents）**

   管理员 LLM 会根据任务自动生成 n 个专家 -> 专家拥有角色标签（Role） -> 专家有生命周期（create → run → exit）

2. **管理员 LLM 的职责**

   管理员不是执行者，它是调度中心：

   接收用户输入 -> 分解任务 -> 调度不同专家 -> 路由消息 -> 控制哪些专家被杀死、哪些被创建 -> 最后收敛所有专家的输出，返回结果

3. **专家间的通信协议（Agent → Agent, Agent → Admin）**

   “需要一个明确的路由、管理规则”

   例如：

   - 请求类型：询问、协作、评估

   - 数据格式：JSON schema

   - ID 标识：session_id、agent_id

   - 管理员决定每次迭代的动作

---

## 开发进度

#### | 数据库 --done--

使用 `PostgreSQL`, 基于 `Pydantic` 的 ORM 封装已完成

##### SQL 模块 --done--

完全自研的轻量级 ORM 系统, 目前已经支持:

- 基于 Pydantic 的模型定义和数据验证
- 完整的 CRUD 操作 (Create, Read, Update, Delete)
- Python 端外键关系抽象 (一对多、多对一、一对一)
- 关系查询 (批量加载关联对象, 避免 N+1 问题)
- JOIN 多表联合查询 (INNER, LEFT, RIGHT, FULL)
- 连接池管理, 自动重连机制
- SQL 文件解析, 自动提取表结构元数据
- 枚举类型支持, JSON/JSONB 字段处理
- 级联删除, 事务支持

##### 测试套件

连接测试: `uv run python ./tests/sql_connect.test.py`
关系功能测试: `uv run python ./tests/test_relations.py`
完整功能测试 (学习文档): `uv run python ./tests/test_sql_complete.py`

**文档**

[SQL 模块使用文档](mylib/sql/docs/sql.md) (点击跳转)

[数据模型系统文档](mylib/sql/docs/Model.md) (点击跳转)

[仓库层 API 文档](mylib/sql/docs/DBRepo.md) (点击跳转)

[配置说明](mylib/sql/docs/Config.md) (点击跳转)

#### | mcp 包 --done--

基于 FastAPI 实现的工具聚合服务器，提供统一的工具发现与调用接口

##### 核心功能

- **工具管理**: 自动发现和加载工具模块，支持热重载
- **RESTful API**: 提供完整的工具查询、调用接口- [Lian-MCP-LLM Agent 系统](#lian-mcp-llm-agent-系统) - [本地多专家智能体调度系统 + 工具调用协议管理 + 可扩展知识库](#本地多专家智能体调度系统--工具调用协议管理--可扩展知识库)

  - [项目核心](#项目核心)
    - [| 顶层：多专家协作与调度 (论文亮点)](#-顶层多专家协作与调度-论文亮点)
  - [开发进度](#开发进度)
    - [| 数据库 --done--](#-数据库---done--)
      - [SQL 模块 --done--](#sql-模块---done--)
      - [测试套件](#测试套件)
    - [| mcp 包 --done--](#-mcp-包---done--)
      - [核心功能](#核心功能)
      - [API 端点](#api-端点)
      - [启动方式](#启动方式)
    - [| llm 包 --done-- (等待 Core 完成后进行重构)](#-llm-包---done---等待-core-完成后进行重构)
      - [核心功能](#核心功能-1)
      - [使用方式](#使用方式)
    - [| Config 包 --done--](#-config-包---done--)
    - [| utils 包](#-utils-包)
      - [目前实现的包](#目前实现的包)
      - [Printer --done--](#printer---done--)
      - [Loutput --done--](#loutput---done--)
  - [🎓 学术使用声明](#-学术使用声明)

- **元数据提取**: 自动从工具代码中提取函数签名、参数类型、文档说明
- **工具分类**:
  - `file_tool`: 文件读写、复制、移动、删除等操作
  - `dir_tool`: 目录创建、列表、树形展示、统计信息
  - `web_tool`: HTTP 请求、网页内容提取、HTML/JSON 解析

##### API 端点

- `GET /`: 服务状态
- `GET /tools`: 获取所有可用工具列表
- `GET /tools/{tool_name}`: 获取工具详细信息
- `POST /tools/{tool_name}/call`: 调用指定工具
- `POST /tools/reload`: 热重载工具元数据

##### 启动方式

**生产模式**（普通启动）:

```bash
uv run python ./main.py server
# 自定义地址和端口
uv run python ./main.py server --host 127.0.0.1 --port 8888
```

**开发模式**（支持热重载，代码修改自动生效）:

```bash
./start_server_dev.sh
# 或自定义参数
./start_server_dev.sh 127.0.0.1 8888
```

文档: [MCP Server API 文档](mylib/mcp/README.md) (点击跳转)

#### | llm 包 --done-- (等待 Core 完成后进行重构)

LLM 客户端封装，支持多种模型提供商与工具调用 (目前测试使用 deepseek-chat)

##### 核心功能

- **工具调用**: 自动集成 MCP Server 工具，支持 function calling
- **连续调用**: 支持工具的多轮连续调用，直到 LLM 返回 `TOOL_CALL_END`
- **对话管理**: 完整的对话上下文管理和历史记录
- **双界面**: 终端交互式界面 + Streamlit Web UI

##### 使用方式

**终端客户端**（交互式命令行）:

```bash
uv run python ./main.py client
```

**Web UI**（Streamlit 网页界面）:

```bash
uv run python ./main.py web
```

Web UI 特性:

- 📱 左右分栏布局：左侧对话，右侧实时日志
- 🎨 美观的消息气泡样式
- 📊 可视化工具调用流程
- 🔄 实时显示工具执行进度
- 📚 侧边栏显示所有可用工具

环境配置: 需要在 `mylib/llm/llm_config.toml` 填入 `DEEPSEEK_API_KEY` 和 MCP Server 地址

#### | Config 包 --done--

用于配置加载, 已经完备

测试: `uv run python ./tests/config.test.py`

文档 [UserGuide.md](mylib/config/docs/UserGuide.md) (点击跳转)

#### | utils 包

###### 目前实现的包

##### Printer --done--

提供了一个彩色打印方法

##### Loutput --done--

基于 `Printer` 完全重构, 目前已经支持:

- 基于 ANSI 的文字效果, 文字色彩, 背景色彩显示
- 支持 256 色, rgb 24bit 色彩
- 支持将 ANSI 代码转换为 rgb 真彩色显示

效果预览: `uv run python ./tests/utils_Loutput/Loutput.test.py`
对比终端颜色与真彩色: `uv run python ./tests/utils_Loutput/color_comparison.py`
测试`RGBColor`: `uv run python .tests/utils_Loutput/rgb_quick.py`

文档

[Loutput 使用文档](mylib/utils/Loutput/docs/Loutput.md) (点击跳转)

[终端颜色显示指南](mylib/utils/Loutput/docs/ColorGuide.md) (点击跳转)

[RGBColor 使用指南](mylib/utils/Loutput/docs/RGBColor.md) (点击跳转)

---

## 🎓 学术使用声明

**本项目为 2025 届毕业设计作品**

⚠️ **重要提醒**：

- 保护期：2025 年 11 月 10 日 - 2026 年 1 月 19 日
- 在此期间，禁止同校同学使用本项目进行毕业设计
- 禁止任何形式的学术作业提交
- 详细条款请参阅 LICENSE 文件

---
