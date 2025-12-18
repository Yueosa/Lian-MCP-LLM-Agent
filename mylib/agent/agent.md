# Lian Agent System Documentation

By Lian - 2025

---

## 1. 体系架构 (Architecture)

本系统采用多智能体协作模式 (Multi-Agent System)，将复杂任务拆解为四个阶段，由不同的专家智能体协作完成：

1.  **Context Retrieval (RAG)**: 检索历史记忆，提供背景信息。
2.  **Planning**: 将用户请求拆解为可执行的步骤。
3.  **Execution**: 调用工具执行具体步骤，并反馈结果。
4.  **Summarization**: 根据执行结果，使用特定人设（猫娘）生成最终回复。

---

## 2. 基类设计 (BaseAgent)

位于 `mylib/agent/base.py`，是所有智能体的父类。

### 核心职责
*   **LLM 通信**: 封装了异步的大模型 API 调用 (`_call_llm`)，包含重试机制。
*   **配置管理**: 自动加载 `config/` 下的 LLM 配置。
*   **数据库连接**: 初始化 `lian_orm` 连接，用于存取记忆和任务状态。
*   **记忆管理**: 提供统一的 `save_memory` 接口，支持自动计算 Embedding。

### 关键方法
*   `a_chat(message, history, memory_type)`: 智能体的主入口，处理用户消息并返回回复。
*   `save_memory(role, content, memory_type)`: 将对话或思考结果持久化到 `memory_log` 表。
*   `_construct_context(message, history)`: 构建发送给 LLM 的消息列表 (System Prompt + History + User Input)。

---

## 3. 专家智能体 (Specialized Agents)

### 3.1 全知魔导书 (RAGAgent)
*   **文件**: `mylib/agent/rag_agent.py`
*   **职责**: 记忆检索与上下文总结。
*   **工作流**:
    1.  **关键词提取**: 使用 LLM 从用户请求中提取搜索关键词。
    2.  **向量检索**: 计算关键词 Embedding，在 `memory_log` 中检索 Top-K (默认 15) 条相关记录。
    3.  **排序优化**: 优先展示 `summary` 类型的记忆，其次按相似度排序。
    4.  **总结生成**: 结合当前时间 (`datetime.now()`) 和检索到的记忆，生成对当前任务有帮助的背景摘要。

### 3.2 星盘占卜师 (PlannerAgent)
*   **文件**: `mylib/agent/planner_agent.py`
*   **职责**: 任务规划与拆解。
*   **输出格式**: 严格的 JSON 格式，包含 `steps` 数组。
*   **数据库交互**:
    *   创建 `Task` 记录 (状态: PENDING)。
    *   创建多个 `TaskStep` 记录 (状态: PENDING)，供 Executor 执行。
*   **记忆类型**: `MemoryLogMemoryType.PLAN`。

### 3.3 魔力执行官 (ExecutorAgent)
*   **文件**: `mylib/agent/executor_agent.py`
*   **职责**: 任务执行与工具调用。
*   **特性**:
    *   **工具循环**: 支持多轮工具调用 (`TOOL_CALL` -> `TOOL_CALL_END`)。
    *   **状态更新**: 将 `TaskStep` 状态更新为 `RUNNING` -> `DONE` / `FAILED`。
    *   **结果截断**: 防止工具返回过长数据导致 Context 溢出。
    *   **审计**: 记录所有的 `ToolCall` 到数据库。

### 3.4 傲娇魔女 (SummaryAgent)
*   **文件**: `mylib/agent/summary_agent.py`
*   **职责**: 最终回复生成与人设扮演。
*   **人设**: "小恋" (傲娇白猫魔女)。
*   **输入**: 用户请求 + RAG 背景 + Planner 计划 + Executor 结果。
*   **输出**: 带有情感色彩的最终总结。
*   **记忆类型**: `MemoryLogMemoryType.SUMMARY`。

---

## 4. 数据流与记忆 (Data Flow & Memory)

### 4.1 记忆模型 (MemoryLog)
系统使用 `memory_log` 表存储所有交互历史，字段包括：
*   `role`: `MemoryLogRole` (USER, ASSISTANT, SYSTEM, TOOL)
*   `content`: 文本内容
*   `embedding`: 向量数据 (用于检索)
*   `memory_type`: `MemoryLogMemoryType` (CONVERSATION, SUMMARY, PLAN, REFLECTION)

### 4.2 任务追踪 (Task System)
*   **Task**: 代表一次完整的用户请求。
*   **TaskStep**: 代表计划中的一个具体步骤。
*   **ToolCall**: 记录步骤执行过程中的工具调用详情。

---

## 5. 交互流程示例

1.  **用户输入**: "帮我查询 Python 3.13 的新特性并总结"
2.  **RAG**: 检索是否有关于 Python 3.13 的过往记忆，生成背景摘要。
3.  **Planner**: 生成计划 -> `[Step 1: Search Python 3.13 features, Step 2: Summarize]`。
4.  **Executor**:
    *   执行 Step 1: 调用搜索工具，获取结果。
    *   执行 Step 2: 调用总结工具 (或直接由 LLM 总结)。
5.  **Summary**: 结合所有信息，用猫娘语气回复: "哼，虽然很麻烦，但还是帮你查到了..."
