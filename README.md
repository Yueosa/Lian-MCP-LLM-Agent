# Lian-MCP-LLM Agent 系统

##### 本地多专家智能体调度系统 + 工具调用协议管理 + 可扩展知识库

By - Lian - 2025

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

**功能特性**:
- 完整的 CRUD 操作与事务支持
- 自动化的关联对象加载 (解决 N+1 问题)
- 复杂的 JOIN 查询支持
- 完善的类型提示与 Pydantic 集成

**📚 文档中心**:
- [LianORM 模块使用文档](mylib/lian_orm/docs/README.md)
- [数据模型 (Models)](mylib/lian_orm/docs/models.md) | [元数据 (Schema)](mylib/lian_orm/docs/schema.md) | [类型映射 (Mapper)](mylib/lian_orm/docs/mapper.md)
- [仓储层 (Repository)](mylib/lian_orm/docs/repository.md) | [数据库层 (Database)](mylib/lian_orm/docs/database.md) | [顶层接口 (ORM)](mylib/lian_orm/docs/orm.md)
- [配置说明 (Config)](mylib/lian_orm/docs/config.md)

### 🔌 (2) 工具层: MCP Server --done--

基于 FastAPI 实现的工具聚合服务器，提供统一的工具发现与调用接口

##### 核心功能

- **工具管理**: 自动发现和加载工具模块，支持热重载
- **RESTful API**: 提供完整的工具查询、调用接口

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

文档: [MCP Server API 文档](mylib/mcp/README.md) (点击跳转)

### 🤖 (3) 交互层: LLM Client --done-- (等待 Core 完成后进行重构)

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

### ⚙️ (4) 配置层: Config --done--

用于配置加载, 已经完备

测试: `uv run python ./tests/config.test.py`

文档 [UserGuide.md](mylib/config/docs/UserGuide.md) (点击跳转)

### 🧠 (5) 智能体层: Agent --pedding--

定义了智能体的基类与核心行为模式。

##### 设计哲学

> 自我认知是一切的起点

每个 Agent 都必须拥有三个核心要素：

1.  **身份 (Identity)**: 明确角色定位与能力边界
2.  **目标 (Objectives)**: 当前任务目标与工作范围
3.  **记忆 (Memory)**: 短期操作记录、长期经验积累与元认知反思

**文档**

[Agent 设计文档](mylib/agent/agent.md) (点击跳转)

### 🕹️ (6) 核心层: Core --pedding--

系统的核心枢纽，负责多专家智能体的调度与协作管理。

##### 核心职责 (Admin Agent)

- **任务编排**: 接收用户输入，分解为可执行的子任务序列
- **专家调度**: 根据任务需求自动生成 (Spawn) 或唤醒特定角色的专家 Agent
- **生命周期管理**: 控制 Agent 的创建、运行与销毁
- **消息路由**: 管理 Agent 之间以及 Agent 与 Admin 之间的通信协议
- **结果收敛**: 汇总各专家的输出，生成最终响应

这是整个系统的"大脑"，实现了论文中提到的多专家协作架构。

### 🛠️ (7) 工具库: Kit (原 Utils)

> 包含了一系列自研的基础工具库，为上层模块提供支持。

#### 🎨 终端美化
- **Printer**: 基础彩色打印工具。简单轻量，开箱即用，适合快速输出带颜色的调试信息或日志，无需复杂配置。
- **Loutput**: 高级终端输出库，支持 ANSI/256色/真彩色 (RGB 24bit)，提供色彩降级兼容。内置了丰富的颜色映射表和样式处理器，能够自动检测终端色彩支持能力并进行适配，让终端界面开发像前端一样优雅。
    - [Loutput 使用文档](mylib/kit/Loutput/docs/Loutput.md) | [终端颜色指南](mylib/kit/Loutput/docs/ColorGuide.md) | [RGBColor 指南](mylib/kit/Loutput/docs/RGBColor.md)

#### 🧩 算法与数据结构
- **Lstack**: 封装的标准栈结构。提供了严谨的压栈、出栈接口，支持迭代器模式，是实现下推自动机和递归算法的基础容器。
    - [Lstack 设计文档](mylib/kit/Lstack/docs/Lstack.md) (点击跳转)
- **Lfsm**: 通用有限状态机 (Finite State Machine) 基类。通过继承方式定义状态与转换规则，逻辑清晰且易于维护，广泛应用于协议解析和流程控制场景。
    - [Lfsm 设计文档](mylib/kit/Lfsm/docs/Lfsm.md) (点击跳转)
- **Lpda**: 下推自动机 (Pushdown Automaton)，支持嵌套结构解析。结合了有限状态机与栈的特性，专门用于处理括号匹配、代码块解析等具有递归特性的语法结构。
    - [Lpda 设计文档](mylib/kit/Lpda/docs/Lpda.md) (点击跳转)

#### 📝 文本处理
- **Ltokenizer**: 基于状态机的通用分词器基类。支持流式处理和位置追踪（行号/列号），能够高效地将原始文本转换为结构化的 Token 序列，为解析器提供标准输入。
    - [Ltokenizer 设计文档](mylib/kit/Ltokenizer/docs/Ltokenizer.md) (点击跳转)
- **Lparser**: 基于 LPDA 的通用解析器基类，用于构建复杂的语法分析器。提供了灵活的解析钩子和上下文管理机制，开发者只需关注语法规则的定义，即可快速构建出功能强大的自定义语言解析器。
    - [Lparser 设计文档](mylib/kit/Lparser/docs/Lparser.md) (点击跳转)
- **Lfind**: 向量嵌入 (Embedding) 工具封装，用于知识库检索。集成了主流的 Embedding 模型接口，提供了开箱即用的文本向量化和相似度匹配功能，是实现 RAG（检索增强生成）系统的核心组件。

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
| `test_sql_complete.py`           | **ORM 完整功能测试**<br>包含 CRUD、关联查询、事务、批量操作等全功能测试，**也是最佳的使用教程**。 | `uv run python tests/test_sql_complete.py`           |
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
