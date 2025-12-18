# Lian-MCP-LLM Agent 系统

##### 本地多专家智能体调度系统 + 工具调用协议管理 + 可扩展知识库

By - Lian - 2025

[![DeepWiki](https://img.shields.io/badge/DeepWiki-Project%20Docs-blueviolet?logo=bookstack&logoColor=white)](https://deepwiki.com/Yueosa/Lian-MCP-LLM-Agent)


---

## 🚀 快速开始 (Quick Start)

### 1. 环境初始化

本项目推荐使用 `uv` 进行依赖管理和环境配置。

```bash
# 1. 安装依赖
uv sync

# 2. 锁定依赖版本 (可选)
uv lock
```

### 2. 运行项目

使用 `main.py` 作为统一入口，支持多种运行模式。

```bash
uv run ./main.py [MODE] [ARGS...]
```

#### 支持的模式 (MODE)

| 模式     | 描述                                     | 示例命令                                             |
| :------- | :--------------------------------------- | :--------------------------------------------------- |
| `agent`  | **[推荐]** 启动新版多专家智能体 Web 界面 | `uv run ./main.py agent`                             |
| `server` | 启动 MCP 工具服务器                      | `uv run ./main.py server --host 0.0.0.0 --port 8000` |
| `web`    | 启动旧版 LLM 客户端 Web 界面             | `uv run ./main.py web`                               |
| `client` | 启动终端交互式 LLM 客户端                | `uv run ./main.py client`                            |

#### 参数说明

*   **server 模式参数**:
    *   `--host`: 指定监听地址 (默认: 127.0.0.1)
    *   `--port`: 指定监听端口 (默认: 8000)
*   **通用参数**:
    *   `message`: 可选的初始消息 (部分模式支持)

---

## 🌟 项目核心

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

## 🚀 开发进度

### 💾 (1) 数据库层: LianORM --done--

> 完全自研的轻量级 ORM 系统，采用分层架构设计。

**核心架构**:
- **Schema**: 基于 FSM 的 SQL 解析器，脱离数据库提取元数据
- **Mapper**: 智能类型转换系统，支持 JSON/Vector 自动映射
- **Repository**: 业务对象 CRUD 的具体实现
- **Database**: 封装连接池与原子操作客户端
- **ORM**: 统一入口与资源管理

**📚 文档中心**:
- [LianORM 模块使用文档](mylib/lian_orm/docs/README.md)
- [数据模型 (Models)](mylib/lian_orm/docs/models.md) | [元数据 (Schema)](mylib/lian_orm/docs/schema.md) | [类型映射 (Mapper)](mylib/lian_orm/docs/mapper.md)
- [仓储层 (Repository)](mylib/lian_orm/docs/repository.md) | [数据库层 (Database)](mylib/lian_orm/docs/database.md) | [顶层接口 (ORM)](mylib/lian_orm/docs/orm.md)
- [配置说明 (Config)](mylib/lian_orm/docs/config.md)

### 🔌 (2) 工具层: MCP Server --done--

> 基于 FastAPI 实现的工具聚合服务器，提供统一的工具发现与调用接口

##### 核心功能

- **工具管理**: 自动发现和加载工具模块，支持热重载
- **RESTful API**: 提供完整的工具查询、调用接口

- **元数据提取**: 自动从工具代码中提取函数签名、参数类型、文档说明
- **工具分类**:
  - `file_tool`: 文件读写、复制、移动、删除等操作
  - `dir_tool`: 目录创建、列表、树形展示、统计信息
  - `web_tool`: HTTP 请求、网页内容提取、HTML/JSON 解析

##### 启动方式

**生产模式**:

```bash
uv run ./main.py server
# 自定义地址和端口
uv run ./main.py server --host 127.0.0.1 --port 8888
```

文档: [MCP Server API 文档](mylib/mcp/README.md) (点击跳转)

### 🤖 (3) 交互层: LLM Client --done--

> LLM 客户端封装，支持多种模型提供商与工具调用 (目前测试使用 deepseek-chat)

##### 核心功能

- **统一接口**: 封装了 `LLMClient`，屏蔽了底层 API 差异
- **Web UI**: 基于 Streamlit 的交互式界面 (`agent_web.py`)，是目前系统的主要入口
- **工具集成**: 自动对接 MCP Server，支持 Function Calling

##### 使用方式

**启动 Web 界面**:

```bash
uv run ./main.py web
```

### ⚙️ (4) 配置层: Config --done--

用于配置加载, 已经完备

测试: `uv run python ./tests/config.test.py`

文档 [UserGuide.md](mylib/config/docs/UserGuide.md) (点击跳转)

### 🧠 (5) 智能体层: Agent --done--

> **[毕设核心模块]** 多专家智能体协作系统的具体实现。

本模块实现了基于 **RAG -> Planning -> Execution -> Summarization** 架构的四类专家智能体：

1.  **RAGAgent (全知魔导书)**: 负责从数据库检索历史记忆，提供上下文支持。
2.  **PlannerAgent (星盘占卜师)**: 负责将用户请求拆解为结构化的执行步骤 (JSON)。
3.  **ExecutorAgent (魔力执行官)**: 负责调用 MCP 工具执行具体步骤，并反馈结果。
4.  **SummaryAgent (傲娇魔女)**: 负责汇总所有信息，以特定人设生成最终回复。

**📚 文档**: [Agent 详细设计文档](mylib/agent/agent.md) (点击跳转)

### 🕹️ (6) 核心层: Core --done--

> **[毕设演示模块]** 系统的核心枢纽与编排层。

目前主要由 `agent_web.py` 承载，它充当了 **Admin Agent** 的角色：
- **流程编排**: 串联 RAG、Planner、Executor、Summary 四个阶段。
- **状态管理**: 维护 Streamlit 的 Session State，管理对话历史。
- **UI 呈现**: 提供可视化的多智能体协作界面。

### 🌰 (7) 内核层: Kernel --new--

> 系统内核，定义了全局通用的基础类型。

- **Lenum**: 统一的枚举定义 (如 `MemoryLogRole`, `TasksStatus`)。
- **Ltypevar**: 通用泛型定义。
- **Lerror**: (规划中) 统一错误处理系统。

### 🚀 (8) 新一代平台: LianAgent --dev--

> `mylib/lian_agent/`

正在孵化中的下一代智能体平台，旨在提供更强的通用性和可扩展性，目前处于早期开发阶段。

### 🛠️ (9) 工具库: Kit (原 Utils)

> 包含了一系列自研的基础工具库，为上层模块提供支持。

#### 🔍 向量检索
- **Lfind**: 轻量级 Embedding 生成与检索工具。封装了向量化接口和相似度计算，是 RAGAgent 的核心依赖。
    - [Lfind 使用文档](mylib/kit/Lfind/docs/Lfind.md) (点击跳转)

#### 🎨 终端美化
- **Printer**: 基础彩色打印工具。简单轻量，开箱即用。
- **Loutput**: 高级终端输出库，支持 ANSI/256色/真彩色 (RGB 24bit)，提供色彩降级兼容。
    - [Loutput 使用文档](mylib/kit/Loutput/docs/Loutput.md) | [终端颜色指南](mylib/kit/Loutput/docs/ColorGuide.md) | [RGBColor 指南](mylib/kit/Loutput/docs/RGBColor.md)

#### 🧩 算法与数据结构
- **Lstack**: 封装的标准栈结构。
    - [Lstack 设计文档](mylib/kit/Lstack/docs/Lstack.md) (点击跳转)
- **Lfsm**: 通用有限状态机 (Finite State Machine) 基类。
    - [Lfsm 设计文档](mylib/kit/Lfsm/docs/Lfsm.md) (点击跳转)
- **Lpda**: 下推自动机 (Pushdown Automaton)。
    - [Lpda 设计文档](mylib/kit/Lpda/docs/Lpda.md) (点击跳转)

#### 📝 文本处理
- **Ltokenizer**: 基于状态机的通用分词器基类。
    - [Ltokenizer 设计文档](mylib/kit/Ltokenizer/docs/Ltokenizer.md) (点击跳转)
- **Lparser**: 基于 LPDA 的通用解析器基类。
    - [Lparser 设计文档](mylib/kit/Lparser/docs/Lparser.md) (点击跳转)

---

## 🎓 学术使用声明

**本项目为 2025 届毕业设计作品**

⚠️ **重要提醒**：

- 保护期：2025 年 11 月 10 日 - 2026 年 1 月 19 日
- 在此期间，禁止同校同学使用本项目进行毕业设计
- 禁止任何形式的学术作业提交
- 详细条款请参阅 LICENSE 文件

---

## 🧪 测试与示例

项目包含完整的测试用例，位于 `tests/` 目录下。

### 运行方式

使用 `uv` 运行测试文件：

```bash
uv run python tests/{TEST_FILE_NAME}
```

### 测试文件列表

| 文件名                           | 描述                                                                                              | 运行命令                                             |
| :------------------------------- | :------------------------------------------------------------------------------------------------ | :--------------------------------------------------- |
| `config_loader.test.py`          | **配置加载测试**<br>测试配置文件的读取、解析和默认值处理。                                        | `uv run python tests/config_loader.test.py`          |
| `lian_orm_schema_parser.test.py` | **SQL 解析器测试**<br>测试 SQL 文件解析功能，验证 Schema 提取的正确性。                           | `uv run python tests/lian_orm_schema_parser.test.py` |
| `lian_orm.test.py`               | **ORM 完整功能测试**<br>包含 CRUD、关联查询、事务、批量操作等全功能测试，**也是最佳的使用教程**。 | `uv run python tests/lian_orm.test.py`               |
| `Loutput.test.py`                | **终端输出测试**<br>展示 Loutput 库的各种颜色、样式和特效输出能力。                               | `uv run python tests/Loutput.test.py`                |
| `psql_connect.test.py`           | **数据库连接测试**<br>测试 PostgreSQL 数据库的连接状态，并列出所有公共表。                        | `uv run python tests/psql_connect.test.py`           |
| `rgb_demo.py`                    | **RGB 颜色演示**<br>展示 RGBColor 和 ANSItoRGB 工具的高级色彩处理能力。                           | `uv run python tests/rgb_demo.py`                    |

---

## 🐷 小猪话

> 开发过程中留下的感悟, 其实一直都没有记录... ...丢掉了好多有趣的想法

#### 📅 2025-11-24 

- 完了完了我的开发习惯疑似有点太极端了，再这么下去开发不完了呀！

#### 📅 2025-12-02

- 整个项目的规模已经达到 48 个目录 144 个文件了...有时候我自己都记不清哪些文件是干嘛的
- `lian_orm` 我是真喜欢, 但目前时间不够了...只能暂时留着等以后重构

#### 📅 2025-12-18

- 咳咳好久没写这个了, 补一条
- 目前开发进度慢得很啊, 不过我们还是先做了一个`agent/`把毕设敷衍过去吧!
