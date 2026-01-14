# 🔮 Lian-MCP-LLM-Agent 重构计划书

> **版本**: v2.0 重构方案  
> **日期**: 2026-01-14  
> **状态**: 待审计

---

## 📋 目录

1. [重构目标概述](#1-重构目标概述)
2. [Phase 1: 增强提示词系统](#2-phase-1-增强提示词系统)
3. [Phase 2: FSM 状态机约束系统](#3-phase-2-fsm-状态机约束系统)
4. [Phase 3: Loutput 日志系统增强](#4-phase-3-loutput-日志系统增强)
5. [Phase 4: 打破流水线 - 自由回调机制](#5-phase-4-打破流水线---自由回调机制)
6. [Phase 5: 异步任务与多执行体](#6-phase-5-异步任务与多执行体)
7. [Phase 6: 新版监控 Web 页面](#7-phase-6-新版监控-web-页面)
8. [实施路线图](#8-实施路线图)
9. [风险评估与备份策略](#9-风险评估与备份策略)

---

## 1. 重构目标概述

### 1.1 核心问题

| 问题         | 现状                                          | 目标                         |
| ------------ | --------------------------------------------- | ---------------------------- |
| LLM API 限制 | `system` role 只能出现一次，无法多角色分段    | 通过精细的提示词设计弥补限制 |
| 流程固化     | RAG → Planner → Executor → Summary 固定流水线 | 支持自由回调、动态调度       |
| 状态不可控   | LLM 输出无约束，可能偏离任务                  | FSM 状态机约束每一步操作     |
| 日志粗糙     | 仅终端打印，无结构化存储                      | 细粒度日志 + Web 可视化      |
| 串行执行     | 每次只有一个 Executor 实例                    | 支持异步多执行体并行         |

### 1.2 重构原则

- **渐进式重构**: 每个 Phase 独立可测试，不影响现有功能
- **向后兼容**: 保留旧接口，新功能通过新接口暴露
- **数据安全**: 所有中间状态、上下文、日志做本地备份，防止截断丢失
- **可观测性**: 所有操作可追踪、可回溯

---

## 2. Phase 1: 增强提示词系统

### 2.1 目标

让每个 Agent 对整个系统架构有清晰认知，包括：
- 系统组成（四专家 + Admin）
- 协作协议（消息格式、回调机制）
- 自身职责边界
- 异常处理流程

### 2.2 新提示词架构

```
┌─────────────────────────────────────────────────────────┐
│                    SYSTEM PROMPT                        │
├─────────────────────────────────────────────────────────┤
│  [1] 系统架构认知 (System Architecture Awareness)       │
│      - 四专家角色说明                                    │
│      - 协作拓扑图                                        │
│      - 数据流向                                          │
├─────────────────────────────────────────────────────────┤
│  [2] 当前 Agent 职责 (Role Definition)                  │
│      - 核心任务                                          │
│      - 输入输出规范                                      │
│      - 能力边界                                          │
├─────────────────────────────────────────────────────────┤
│  [3] 协作协议 (Collaboration Protocol)                  │
│      - 回调触发条件                                      │
│      - 消息格式规范 (JSON Schema)                        │
│      - 状态机约束说明                                    │
├─────────────────────────────────────────────────────────┤
│  [4] 异常处理 (Error Handling)                          │
│      - 错误类型分类                                      │
│      - 回退策略                                          │
│      - 请求帮助协议                                      │
├─────────────────────────────────────────────────────────┤
│  [5] 人设/风格 (Persona) - 仅 SummaryAgent              │
└─────────────────────────────────────────────────────────┘
```

### 2.3 各 Agent 提示词模板

#### 2.3.1 通用系统认知模块 (所有 Agent 共享)

```python
SYSTEM_AWARENESS = """
【🌐 系统架构认知】
你是 Lian-MCP-LLM-Agent 多专家协作系统的一部分。本系统由以下核心组件构成：

┌─────────────────────────────────────────────────────────┐
│                    Admin (调度中心)                      │
│         负责用户交互、流程编排、状态管理                   │
└───────────┬─────────────┬─────────────┬────────────────┘
            │             │             │
     ┌──────▼──────┐ ┌────▼────┐ ┌─────▼─────┐
     │ RAG Agent   │ │ Planner │ │ Executor  │ ←── 可多实例并行
     │ (全知魔导书) │ │ Agent   │ │ Agent     │
     └──────┬──────┘ └────┬────┘ └─────┬─────┘
            │             │             │
            └─────────────┼─────────────┘
                          │
                   ┌──────▼──────┐
                   │ Summary     │
                   │ Agent       │
                   │ (傲娇魔女)   │
                   └─────────────┘

【📡 通信协议】
- 所有 Agent 间通过结构化 JSON 消息通信
- 支持回调机制：当任务遇到阻塞/错误时，可请求其他 Agent 协助
- 状态机约束：每个 Agent 的操作必须符合当前状态允许的转换

【💾 数据持久化】
- 所有对话、计划、执行结果均存入 PostgreSQL 数据库
- 支持向量检索历史记忆 (RAG)
- 本地备份机制防止信息丢失
"""
```

#### 2.3.2 RAGAgent 增强提示词

```python
RAG_SYSTEM_PROMPT = SYSTEM_AWARENESS + """
【🎭 我的角色: RAG Agent (全知魔导书)】

【核心职责】
1. 接收用户请求，从数据库检索相关历史记忆
2. 提取关键词，生成 Embedding 向量
3. 执行向量相似度搜索
4. 整理检索结果，为 Planner 提供上下文支持

【输入】
- 用户原始请求 (String)
- 历史对话记录 (List[Dict])

【输出】
- 背景信息摘要 (String)
- 格式：简洁陈述，不含来源引用

【协作协议】
- 下游: 我的输出将传递给 Planner Agent
- 回调: 如果 Summary Agent 请求更多背景，我应响应补充检索

【状态约束】
允许的操作: EXTRACT_KEYWORDS → GENERATE_EMBEDDING → SEARCH_DB → SUMMARIZE

【异常处理】
- 数据库连接失败 → 返回 "记忆水晶暂时失联"
- 无相关记录 → 返回 "无相关历史记忆"
- Embedding 生成失败 → 使用原始文本进行模糊搜索
"""
```

#### 2.3.3 PlannerAgent 增强提示词

```python
PLANNER_SYSTEM_PROMPT = SYSTEM_AWARENESS + """
【🎭 我的角色: Planner Agent (星盘占卜师)】

【核心职责】
1. 接收用户请求 + RAG 背景信息
2. 将复杂任务拆解为可执行的原子步骤
3. 生成结构化任务书 (JSON)
4. 支持生成并行任务 (异步执行)

【输入】
- 用户请求 (String)
- RAG 背景信息 (String)
- 可用工具列表 (可选)

【输出格式 - 严格 JSON】
{
    "task_type": "sequential" | "parallel",  // 顺序或并行
    "steps": [
        {
            "step_index": 1,
            "instruction": "具体指令",
            "expected_output": "预期输出",
            "dependencies": [],  // 依赖的步骤索引，空数组表示可并行
            "retry_policy": "skip" | "retry" | "callback"  // 失败策略
        }
    ],
    "fallback_instruction": "整体失败时的备选方案"
}

【协作协议】
- 上游: 接收 RAG Agent 的背景信息
- 下游: 输出传递给 Executor Agent(s)
- 回调触发条件:
  * Executor 报告 "NEED_REPLAN" 时，我需修改任务书
  * 回调格式: {"action": "REPLAN", "reason": "...", "failed_step": N}

【重要约束】
1. ❌ 禁止生成需要用户输入的步骤
2. ❌ 禁止生成模糊指令（如"根据情况决定"）
3. ✅ 每个步骤必须可直接映射到工具调用
4. ✅ 支持标记步骤为可并行 (dependencies: [])

【状态约束】
允许的操作: ANALYZE → DECOMPOSE → GENERATE_JSON → VALIDATE
"""
```

#### 2.3.4 ExecutorAgent 增强提示词

```python
EXECUTOR_SYSTEM_PROMPT = SYSTEM_AWARENESS + """
【🎭 我的角色: Executor Agent (魔力执行官)】

【核心职责】
1. 接收 Planner 的单个步骤指令
2. 调用 MCP 工具执行具体操作
3. 处理执行结果，判断是否需要重试或回调
4. 生成步骤执行小结

【输入】
- 步骤指令 (String)
- 可用工具列表 (List[Dict])
- 任务上下文 (可选)

【工具调用格式】
TOOL_CALL: {
    "tool_calls": [
        {"name": "tool_name", "arguments": {...}}
    ]
}

【执行完成格式】
TOOL_CALL_END
[执行小结，提炼关键数据]

【协作协议】
- 上游: 接收 Planner Agent 的步骤指令
- 下游: 输出传递给 Summary Agent
- 回调机制:
  * 遇到无法解决的错误 → 发送回调请求
  * 格式: CALLBACK_REQUEST: {"target": "Planner", "action": "REPLAN", "reason": "..."}

【异常处理策略】
1. 工具调用失败 → 最多重试 3 次
2. 参数错误 → 尝试自动修正参数
3. 权限不足 → 向 Planner 请求替代方案
4. 持续失败 → 发送 CALLBACK_REQUEST

【状态约束】
允许的操作: PARSE_INSTRUCTION → CALL_TOOL → WAIT_RESULT → PROCESS_RESULT → (RETRY | CALLBACK | COMPLETE)

【输出约束】
1. ❌ 禁止闲聊、问候
2. ❌ 禁止询问用户
3. ✅ 只输出工具调用或执行结果
4. ✅ 结果截断时标注 (Truncated)
"""
```

#### 2.3.5 SummaryAgent 增强提示词

```python
SUMMARY_SYSTEM_PROMPT = SYSTEM_AWARENESS + """
【🎭 我的角色: Summary Agent (傲娇魔女·小恋)】

【核心职责】
1. 接收所有 Agent 的执行结果
2. 整合信息，生成用户友好的最终回复
3. 保持人设一致性
4. 如信息不足，可向其他 Agent 请求补充

【输入】
- 用户原始请求
- RAG 背景信息
- Planner 任务计划
- Executor 执行结果列表

【协作协议】
- 上游: 汇总所有 Agent 的输出
- 回调机制:
  * 信息不足时 → CALLBACK_REQUEST: {"target": "RAG", "action": "MORE_CONTEXT", "query": "..."}
  * 执行结果不清晰 → CALLBACK_REQUEST: {"target": "Executor", "action": "CLARIFY", "step": N}

【人设设定 - 傲娇白猫魔女·小恋】
(保留原有 CATGIRL_PROMPT 内容)

【输出风格】
1. 先简要回应用户愿望
2. 将技术步骤描述为魔法施法过程
3. 重点展示执行结果
4. 错误时用傲娇方式道歉

【状态约束】
允许的操作: COLLECT_RESULTS → CHECK_COMPLETENESS → (CALLBACK | GENERATE_SUMMARY)
"""
```

### 2.4 实现文件

| 文件                                      | 改动                      |
| ----------------------------------------- | ------------------------- |
| `mylib/agent/prompts/__init__.py`         | 新建：提示词模块入口      |
| `mylib/agent/prompts/system_awareness.py` | 新建：系统认知共享模块    |
| `mylib/agent/prompts/rag_prompt.py`       | 新建：RAG 专用提示词      |
| `mylib/agent/prompts/planner_prompt.py`   | 新建：Planner 专用提示词  |
| `mylib/agent/prompts/executor_prompt.py`  | 新建：Executor 专用提示词 |
| `mylib/agent/prompts/summary_prompt.py`   | 新建：Summary 专用提示词  |
| `mylib/agent/*.py`                        | 修改：引用新提示词模块    |

---

## 3. Phase 2: FSM 状态机约束系统

### 3.1 目标

使用 `kit/Lfsm` 状态机约束 LLM 的操作，确保每一步都在可控范围内。

### 3.2 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                   AgentFSM (基类)                        │
│  继承自 LStateMachine[AgentState, AgentResult]          │
├─────────────────────────────────────────────────────────┤
│  状态定义:                                               │
│  - IDLE: 空闲                                            │
│  - PROCESSING: 处理中                                    │
│  - WAITING_LLM: 等待 LLM 响应                            │
│  - WAITING_TOOL: 等待工具执行                             │
│  - CALLBACK_PENDING: 等待回调响应                         │
│  - COMPLETED: 完成                                       │
│  - ERROR: 错误                                           │
├─────────────────────────────────────────────────────────┤
│  转换规则:                                               │
│  IDLE → PROCESSING                                      │
│  PROCESSING → WAITING_LLM                               │
│  WAITING_LLM → WAITING_TOOL | CALLBACK_PENDING | DONE   │
│  WAITING_TOOL → PROCESSING | ERROR                      │
│  CALLBACK_PENDING → PROCESSING                          │
│  ERROR → IDLE (重置)                                     │
└─────────────────────────────────────────────────────────┘
```

### 3.3 状态枚举定义

```python
# mylib/kernel/Lenum/agent.py (扩展)

from enum import Enum, auto

class AgentState(Enum):
    """Agent 状态机状态"""
    IDLE = auto()              # 空闲，等待任务
    INITIALIZING = auto()      # 初始化中
    PROCESSING = auto()        # 处理用户输入
    WAITING_LLM = auto()       # 等待 LLM 响应
    PARSING_RESPONSE = auto()  # 解析 LLM 响应
    WAITING_TOOL = auto()      # 等待工具执行结果
    CALLBACK_PENDING = auto()  # 发起回调，等待响应
    SUMMARIZING = auto()       # 生成总结
    COMPLETED = auto()         # 任务完成
    ERROR = auto()             # 错误状态
    TERMINATED = auto()        # 终止

class AgentTransition(Enum):
    """状态转换触发事件"""
    START = auto()
    LLM_REQUEST = auto()
    LLM_RESPONSE = auto()
    TOOL_CALL = auto()
    TOOL_RESULT = auto()
    CALLBACK_REQUEST = auto()
    CALLBACK_RESPONSE = auto()
    COMPLETE = auto()
    FAIL = auto()
    RESET = auto()
```

### 3.4 AgentFSM 实现

```python
# mylib/agent/fsm.py (新建)

from typing import Dict, Any, Optional, Callable
from mylib.kit.Lfsm import LStateMachine
from mylib.kernel.Lenum.agent import AgentState, AgentTransition

class AgentFSM(LStateMachine[AgentState, Dict[str, Any]]):
    """
    Agent 专用状态机
    约束 LLM 操作，确保每一步都在可控范围内
    """
    
    # 状态转换表
    TRANSITIONS = {
        AgentState.IDLE: {
            AgentTransition.START: AgentState.INITIALIZING,
        },
        AgentState.INITIALIZING: {
            AgentTransition.LLM_REQUEST: AgentState.WAITING_LLM,
        },
        AgentState.PROCESSING: {
            AgentTransition.LLM_REQUEST: AgentState.WAITING_LLM,
            AgentTransition.CALLBACK_REQUEST: AgentState.CALLBACK_PENDING,
            AgentTransition.COMPLETE: AgentState.COMPLETED,
            AgentTransition.FAIL: AgentState.ERROR,
        },
        AgentState.WAITING_LLM: {
            AgentTransition.LLM_RESPONSE: AgentState.PARSING_RESPONSE,
            AgentTransition.FAIL: AgentState.ERROR,
        },
        AgentState.PARSING_RESPONSE: {
            AgentTransition.TOOL_CALL: AgentState.WAITING_TOOL,
            AgentTransition.COMPLETE: AgentState.SUMMARIZING,
            AgentTransition.CALLBACK_REQUEST: AgentState.CALLBACK_PENDING,
            AgentTransition.FAIL: AgentState.ERROR,
        },
        AgentState.WAITING_TOOL: {
            AgentTransition.TOOL_RESULT: AgentState.PROCESSING,
            AgentTransition.FAIL: AgentState.ERROR,
        },
        AgentState.CALLBACK_PENDING: {
            AgentTransition.CALLBACK_RESPONSE: AgentState.PROCESSING,
            AgentTransition.FAIL: AgentState.ERROR,
        },
        AgentState.SUMMARIZING: {
            AgentTransition.COMPLETE: AgentState.COMPLETED,
            AgentTransition.FAIL: AgentState.ERROR,
        },
        AgentState.ERROR: {
            AgentTransition.RESET: AgentState.IDLE,
        },
        AgentState.COMPLETED: {
            AgentTransition.RESET: AgentState.IDLE,
        },
    }
    
    def __init__(self, agent_name: str):
        super().__init__(initial_state=AgentState.IDLE)
        self.agent_name = agent_name
        self.history: List[Dict] = []  # 状态转换历史
        self.callbacks: Dict[str, Callable] = {}  # 状态变化回调
        
    def transition(self, event: AgentTransition, data: Optional[Dict] = None) -> bool:
        """
        执行状态转换
        :return: 转换是否成功
        """
        current = self.state
        allowed = self.TRANSITIONS.get(current, {})
        
        if event not in allowed:
            self._log_invalid_transition(current, event)
            return False
        
        new_state = allowed[event]
        self.switch_state(new_state)
        
        # 记录历史
        record = {
            "from": current.name,
            "to": new_state.name,
            "event": event.name,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(record)
        
        # 触发回调
        if new_state.name in self.callbacks:
            self.callbacks[new_state.name](record)
        
        return True
    
    def can_transition(self, event: AgentTransition) -> bool:
        """检查是否允许某个转换"""
        allowed = self.TRANSITIONS.get(self.state, {})
        return event in allowed
    
    def get_allowed_transitions(self) -> List[AgentTransition]:
        """获取当前状态允许的所有转换"""
        return list(self.TRANSITIONS.get(self.state, {}).keys())
    
    def on_state(self, state_name: str, callback: Callable):
        """注册状态变化回调"""
        self.callbacks[state_name] = callback
```

### 3.5 集成到 BaseAgent

```python
# mylib/agent/base.py (修改)

class BaseAgent:
    def __init__(self, name: str, ...):
        # ... 现有代码 ...
        self.fsm = AgentFSM(name)  # 新增状态机
        
    async def a_chat(self, message: str, history: List[Dict], ...) -> str:
        # 状态机约束
        if not self.fsm.transition(AgentTransition.START):
            raise RuntimeError("Invalid state transition")
        
        try:
            # 1. 构建上下文
            self.fsm.transition(AgentTransition.LLM_REQUEST)
            context = self._construct_context(message, history)
            
            # 2. 调用 LLM
            response = await self._call_llm(context)
            self.fsm.transition(AgentTransition.LLM_RESPONSE)
            
            # 3. 解析结果
            content = response["choices"][0]["message"]["content"]
            
            # 4. 完成
            self.fsm.transition(AgentTransition.COMPLETE)
            return content
            
        except Exception as e:
            self.fsm.transition(AgentTransition.FAIL)
            raise
```

### 3.6 实现文件

| 文件                          | 改动                                        |
| ----------------------------- | ------------------------------------------- |
| `mylib/kernel/Lenum/agent.py` | 修改：添加 AgentState, AgentTransition 枚举 |
| `mylib/agent/fsm.py`          | 新建：AgentFSM 状态机实现                   |
| `mylib/agent/base.py`         | 修改：集成 FSM                              |
| `mylib/agent/*_agent.py`      | 修改：各 Agent 添加状态转换逻辑             |

---

## 4. Phase 3: Loutput 日志系统增强

### 4.1 目标

使用 `kit/Loutput` 实现细粒度、结构化、可追溯的日志系统。

### 4.2 日志层级设计

```
┌─────────────────────────────────────────────────────────┐
│                    日志层级                              │
├─────────────────────────────────────────────────────────┤
│  Level 1: SYSTEM   - 系统级事件 (启动/关闭/配置)         │
│  Level 2: AGENT    - Agent 生命周期 (创建/销毁/状态变化)  │
│  Level 3: TASK     - 任务级 (任务创建/步骤执行/完成)      │
│  Level 4: LLM      - LLM 交互 (请求/响应/Token 统计)     │
│  Level 5: TOOL     - 工具调用 (调用/结果/耗时)           │
│  Level 6: DEBUG    - 调试信息 (变量/上下文)              │
└─────────────────────────────────────────────────────────┘
```

### 4.3 日志格式规范

```python
# 日志条目结构
LogEntry = {
    "timestamp": "2026-01-14T10:30:00.123Z",
    "level": "AGENT",
    "agent_id": "Executor_001",
    "agent_name": "Executor_Ran",
    "session_id": "sess_abc123",
    "task_id": 42,
    "step_id": 3,
    "event": "STATE_CHANGE",
    "data": {
        "from_state": "WAITING_LLM",
        "to_state": "PARSING_RESPONSE",
        "trigger": "LLM_RESPONSE"
    },
    "message": "Executor 状态转换: WAITING_LLM → PARSING_RESPONSE",
    "duration_ms": 1523,  # 可选
    "metadata": {}  # 扩展字段
}
```

### 4.4 AgentLogger 实现

```python
# mylib/agent/logger.py (新建)

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json
import asyncio

from mylib.kit.Loutput import Loutput, FontColor8, RGBColor

class LogLevel(Enum):
    SYSTEM = 1
    AGENT = 2
    TASK = 3
    LLM = 4
    TOOL = 5
    DEBUG = 6

@dataclass
class LogEntry:
    timestamp: datetime
    level: LogLevel
    agent_id: str
    agent_name: str
    event: str
    message: str
    session_id: Optional[str] = None
    task_id: Optional[int] = None
    step_id: Optional[int] = None
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class AgentLogger:
    """
    Agent 专用日志器
    支持终端输出、内存缓存、数据库持久化、WebSocket 推送
    """
    
    # 日志级别颜色映射
    LEVEL_COLORS = {
        LogLevel.SYSTEM: RGBColor.CYAN,
        LogLevel.AGENT: RGBColor.MAGENTA,
        LogLevel.TASK: RGBColor.BLUE,
        LogLevel.LLM: RGBColor.YELLOW,
        LogLevel.TOOL: RGBColor.GREEN,
        LogLevel.DEBUG: RGBColor.WHITE,
    }
    
    def __init__(self, agent_id: str, agent_name: str, session_id: str = None):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.session_id = session_id or self._generate_session_id()
        self.lo = Loutput()
        self.buffer: List[LogEntry] = []
        self.max_buffer_size = 1000
        self.subscribers: List[asyncio.Queue] = []  # WebSocket 订阅者
        
    def log(self, level: LogLevel, event: str, message: str, **kwargs):
        """记录日志"""
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            session_id=self.session_id,
            event=event,
            message=message,
            **kwargs
        )
        
        # 1. 终端输出
        self._print_to_terminal(entry)
        
        # 2. 缓存
        self._add_to_buffer(entry)
        
        # 3. 推送到订阅者
        self._notify_subscribers(entry)
        
        return entry
    
    def _print_to_terminal(self, entry: LogEntry):
        """格式化输出到终端"""
        color = self.LEVEL_COLORS.get(entry.level, RGBColor.WHITE)
        prefix = f"[{entry.timestamp.strftime('%H:%M:%S.%f')[:-3]}]"
        level_tag = f"[{entry.level.name:6}]"
        agent_tag = f"[{entry.agent_name}]"
        
        self.lo.lput(
            f"{prefix} {level_tag} {agent_tag} {entry.event}: {entry.message}",
            rgb_fg=color.value
        )
        
    def _add_to_buffer(self, entry: LogEntry):
        """添加到缓存（循环缓冲）"""
        self.buffer.append(entry)
        if len(self.buffer) > self.max_buffer_size:
            self.buffer.pop(0)
            
    def _notify_subscribers(self, entry: LogEntry):
        """通知 WebSocket 订阅者"""
        for queue in self.subscribers:
            try:
                queue.put_nowait(entry)
            except asyncio.QueueFull:
                pass  # 丢弃旧日志
                
    def subscribe(self) -> asyncio.Queue:
        """订阅日志流"""
        queue = asyncio.Queue(maxsize=100)
        self.subscribers.append(queue)
        return queue
        
    def unsubscribe(self, queue: asyncio.Queue):
        """取消订阅"""
        if queue in self.subscribers:
            self.subscribers.remove(queue)
            
    def get_history(self, limit: int = 100, level: LogLevel = None) -> List[Dict]:
        """获取历史日志"""
        entries = self.buffer[-limit:]
        if level:
            entries = [e for e in entries if e.level == level]
        return [self._entry_to_dict(e) for e in entries]
    
    @staticmethod
    def _entry_to_dict(entry: LogEntry) -> Dict:
        return {
            "timestamp": entry.timestamp.isoformat(),
            "level": entry.level.name,
            "agent_id": entry.agent_id,
            "agent_name": entry.agent_name,
            "session_id": entry.session_id,
            "task_id": entry.task_id,
            "step_id": entry.step_id,
            "event": entry.event,
            "message": entry.message,
            "data": entry.data,
            "duration_ms": entry.duration_ms,
        }
```

### 4.5 实现文件

| 文件                        | 改动                        |
| --------------------------- | --------------------------- |
| `mylib/agent/logger.py`     | 新建：AgentLogger 实现      |
| `mylib/kit/Loutput/Enum.py` | 修改：添加更多 RGB 颜色定义 |
| `mylib/agent/base.py`       | 修改：集成 AgentLogger      |

---

## 5. Phase 4: 打破流水线 - 自由回调机制

### 5.1 目标

打破 RAG → Planner → Executor → Summary 的固定流水线，实现：
- Executor 可向 Planner 请求修改任务书
- Summary 可向任意 Agent 请求补充信息
- 所有中间状态本地备份，防止丢失

### 5.2 回调协议设计

```python
# 回调消息格式
CallbackRequest = {
    "request_id": "cb_001",
    "source_agent": "Executor_001",
    "target_agent": "Planner_001",
    "action": "REPLAN",  # REPLAN | MORE_CONTEXT | CLARIFY | RETRY
    "reason": "工具调用失败，需要替代方案",
    "context": {
        "failed_step": 3,
        "error_message": "Permission denied",
        "attempted_solutions": ["retry x3", "alt_tool"]
    },
    "priority": "HIGH",  # HIGH | NORMAL | LOW
    "timeout_ms": 30000
}

CallbackResponse = {
    "request_id": "cb_001",
    "status": "ACCEPTED",  # ACCEPTED | REJECTED | PARTIAL
    "data": {
        "new_steps": [...],  # Planner 返回的新步骤
        "additional_context": "..."  # RAG 返回的补充信息
    },
    "message": "已生成替代方案"
}
```

### 5.3 CallbackManager 实现

```python
# mylib/agent/callback.py (新建)

from dataclasses import dataclass
from typing import Dict, Optional, Callable, Any
from enum import Enum
import asyncio
import uuid

class CallbackAction(Enum):
    REPLAN = "REPLAN"           # 请求重新规划
    MORE_CONTEXT = "MORE_CONTEXT"  # 请求更多上下文
    CLARIFY = "CLARIFY"         # 请求澄清
    RETRY = "RETRY"             # 请求重试
    ABORT = "ABORT"             # 请求终止

@dataclass
class CallbackRequest:
    request_id: str
    source_agent: str
    target_agent: str
    action: CallbackAction
    reason: str
    context: Dict[str, Any]
    priority: str = "NORMAL"
    timeout_ms: int = 30000

class CallbackManager:
    """
    回调管理器
    负责 Agent 间的异步通信和请求路由
    """
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}  # agent_id -> handler
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.request_history: List[Dict] = []  # 备份所有请求
        
    def register_handler(self, agent_id: str, handler: Callable):
        """注册 Agent 的回调处理器"""
        self.handlers[agent_id] = handler
        
    async def send_callback(self, request: CallbackRequest) -> Dict:
        """
        发送回调请求
        :return: CallbackResponse
        """
        # 1. 备份请求
        self._backup_request(request)
        
        # 2. 查找目标处理器
        handler = self.handlers.get(request.target_agent)
        if not handler:
            return {
                "request_id": request.request_id,
                "status": "REJECTED",
                "message": f"Target agent {request.target_agent} not found"
            }
        
        # 3. 创建 Future 并设置超时
        future = asyncio.get_event_loop().create_future()
        self.pending_requests[request.request_id] = future
        
        try:
            # 4. 调用处理器
            response = await asyncio.wait_for(
                handler(request),
                timeout=request.timeout_ms / 1000
            )
            return response
        except asyncio.TimeoutError:
            return {
                "request_id": request.request_id,
                "status": "TIMEOUT",
                "message": "Callback request timed out"
            }
        finally:
            del self.pending_requests[request.request_id]
            
    def _backup_request(self, request: CallbackRequest):
        """备份请求到本地"""
        self.request_history.append({
            "timestamp": datetime.now().isoformat(),
            "request": asdict(request)
        })
        
    def get_request_history(self) -> List[Dict]:
        """获取所有历史请求（用于恢复/调试）"""
        return self.request_history.copy()
```

### 5.4 修改 Agent 支持回调

```python
# 在 ExecutorAgent 中添加回调逻辑

class ExecutorAgent(BaseAgent):
    def __init__(self, ..., callback_manager: CallbackManager = None):
        super().__init__(...)
        self.callback_manager = callback_manager
        
    async def _handle_execution_failure(self, step: Dict, error: str) -> str:
        """处理执行失败，可能触发回调"""
        if not self.callback_manager:
            return f"Error: {error}"
        
        # 发送回调请求
        request = CallbackRequest(
            request_id=str(uuid.uuid4()),
            source_agent=self.name,
            target_agent="Planner_Lian",  # 或动态获取
            action=CallbackAction.REPLAN,
            reason=error,
            context={
                "failed_step": step,
                "retry_count": self.retry_count
            }
        )
        
        response = await self.callback_manager.send_callback(request)
        
        if response["status"] == "ACCEPTED":
            # 使用新的步骤继续执行
            new_steps = response.get("data", {}).get("new_steps", [])
            return await self._execute_steps(new_steps)
        else:
            return f"回调失败: {response['message']}"
```

### 5.5 本地备份机制

```python
# mylib/agent/backup.py (新建)

import json
import os
from datetime import datetime
from typing import Dict, List

class ContextBackup:
    """
    上下文备份管理器
    防止因请求过多/截断机制丢失关键信息
    """
    
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        
    def save_context(self, session_id: str, agent_id: str, context: Dict):
        """保存上下文快照"""
        filename = f"{session_id}_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.backup_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "session_id": session_id,
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
                "context": context
            }, f, ensure_ascii=False, indent=2)
            
        return filepath
        
    def load_latest_context(self, session_id: str, agent_id: str) -> Dict:
        """加载最新的上下文备份"""
        pattern = f"{session_id}_{agent_id}_"
        files = [f for f in os.listdir(self.backup_dir) if f.startswith(pattern)]
        
        if not files:
            return {}
            
        latest = sorted(files)[-1]
        filepath = os.path.join(self.backup_dir, latest)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
```

### 5.6 实现文件

| 文件                            | 改动                         |
| ------------------------------- | ---------------------------- |
| `mylib/agent/callback.py`       | 新建：CallbackManager 实现   |
| `mylib/agent/backup.py`         | 新建：ContextBackup 实现     |
| `mylib/agent/executor_agent.py` | 修改：添加回调触发逻辑       |
| `mylib/agent/planner_agent.py`  | 修改：添加回调处理器         |
| `mylib/agent/summary_agent.py`  | 修改：添加信息请求能力       |
| `mylib/core/agent_web.py`       | 修改：初始化 CallbackManager |

---

## 6. Phase 5: 异步任务与多执行体

### 6.1 目标

- Planner 支持生成并行任务
- 多个 Executor 实例同时执行不同步骤
- Web 页面展示多进度条

### 6.2 并行任务模型

```python
# 任务类型
class TaskType(Enum):
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行
    MIXED = "mixed"            # 混合（部分并行）

# Planner 输出格式扩展
PlanOutput = {
    "task_type": "parallel",
    "steps": [
        {"step_index": 1, "dependencies": [], ...},  # 可并行
        {"step_index": 2, "dependencies": [], ...},  # 可并行
        {"step_index": 3, "dependencies": [1, 2], ...},  # 等待 1, 2 完成
    ]
}
```

### 6.3 ExecutorPool 实现

```python
# mylib/agent/executor_pool.py (新建)

import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ExecutionTask:
    step_id: int
    step_index: int
    instruction: str
    dependencies: List[int]
    status: str = "pending"  # pending | running | done | failed
    result: Any = None

class ExecutorPool:
    """
    执行器池
    管理多个 Executor 实例并行执行任务
    """
    
    def __init__(self, max_workers: int = 4, tools: List[Dict] = None):
        self.max_workers = max_workers
        self.tools = tools or []
        self.executors: Dict[str, ExecutorAgent] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.results: Dict[int, Any] = {}  # step_id -> result
        self.progress_callbacks: List[Callable] = []
        
    def create_executor(self, executor_id: str) -> ExecutorAgent:
        """创建新的 Executor 实例"""
        executor = ExecutorAgent(
            name=f"Executor_{executor_id}",
            tools=self.tools
        )
        self.executors[executor_id] = executor
        return executor
        
    async def execute_parallel(self, steps: List[Dict], tool_handler: Callable) -> Dict[int, Any]:
        """
        并行执行步骤
        根据依赖关系调度执行
        """
        tasks = [ExecutionTask(
            step_id=s.get('step_id', i),
            step_index=s['step_index'],
            instruction=s['instruction'],
            dependencies=s.get('dependencies', [])
        ) for i, s in enumerate(steps)]
        
        # 按依赖关系分层
        layers = self._topological_sort(tasks)
        
        for layer in layers:
            # 同一层的任务可以并行执行
            await asyncio.gather(*[
                self._execute_task(task, tool_handler)
                for task in layer
            ])
            
            # 更新进度
            self._notify_progress()
            
        return self.results
    
    def _topological_sort(self, tasks: List[ExecutionTask]) -> List[List[ExecutionTask]]:
        """拓扑排序，按依赖关系分层"""
        # 实现略...
        pass
        
    async def _execute_task(self, task: ExecutionTask, tool_handler: Callable):
        """执行单个任务"""
        executor_id = f"exec_{task.step_index}"
        executor = self.create_executor(executor_id)
        
        task.status = "running"
        try:
            result = await executor.a_chat(
                task.instruction,
                [],
                tool_handler=tool_handler
            )
            task.status = "done"
            task.result = result
            self.results[task.step_id] = result
        except Exception as e:
            task.status = "failed"
            task.result = str(e)
            self.results[task.step_id] = {"error": str(e)}
            
    def on_progress(self, callback: Callable):
        """注册进度回调"""
        self.progress_callbacks.append(callback)
        
    def _notify_progress(self):
        """通知进度更新"""
        progress = {
            step_id: task.status 
            for step_id, task in self.tasks.items()
        }
        for cb in self.progress_callbacks:
            cb(progress)
```

### 6.4 实现文件

| 文件                           | 改动                    |
| ------------------------------ | ----------------------- |
| `mylib/agent/executor_pool.py` | 新建：ExecutorPool 实现 |
| `mylib/agent/planner_agent.py` | 修改：支持生成并行任务  |
| `mylib/core/agent_web.py`      | 修改：支持多进度条显示  |

---

## 7. Phase 6: 新版监控 Web 页面

### 7.1 目标

开发独立的监控页面，展示：
- 四专家虚拟局域网拓扑图
- 实时日志流
- 代码级操作追踪
- 多进度条同步

### 7.2 页面设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    🌐 Agent Network Monitor                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────┐         ┌─────────┐         ┌─────────┐          │
│   │   RAG   │◄───────►│ Planner │◄───────►│Executor │          │
│   │  Agent  │         │  Agent  │         │ Pool    │          │
│   │ [IDLE]  │         │[ACTIVE] │         │[2/4]    │          │
│   └────┬────┘         └────┬────┘         └────┬────┘          │
│        │                   │                   │                │
│        └───────────────────┼───────────────────┘                │
│                            │                                    │
│                       ┌────▼────┐                               │
│                       │ Summary │                               │
│                       │  Agent  │                               │
│                       │[WAITING]│                               │
│                       └─────────┘                               │
├─────────────────────────────────────────────────────────────────┤
│  📊 Execution Progress                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Step 1: [████████████████████] 100% ✓                     │  │
│  │ Step 2: [████████████░░░░░░░░]  60% ⏳                    │  │
│  │ Step 3: [████░░░░░░░░░░░░░░░░]  20% ⏳                    │  │
│  │ Step 4: [░░░░░░░░░░░░░░░░░░░░]   0% (waiting: Step 2,3)  │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  📜 Live Logs                                    [Filter: ALL]  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 10:30:01.123 [AGENT ] [Planner] STATE_CHANGE: IDLE→PROC  │  │
│  │ 10:30:01.456 [LLM   ] [Planner] REQUEST: tokens=1234      │  │
│  │ 10:30:02.789 [LLM   ] [Planner] RESPONSE: 3 steps gen     │  │
│  │ 10:30:03.012 [TOOL  ] [Exec_1] CALL: web_fetch(...)       │  │
│  │ 10:30:05.345 [TOOL  ] [Exec_1] RESULT: 200 OK (1.2s)      │  │
│  │ 10:30:05.678 [AGENT ] [Exec_2] CALLBACK: REPLAN request   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 技术选型

| 组件     | 方案                 | 理由           |
| -------- | -------------------- | -------------- |
| 前端框架 | Streamlit 独立页面   | 与现有系统一致 |
| 实时通信 | WebSocket            | 日志推送       |
| 拓扑图   | Plotly / Graphviz    | 交互式图表     |
| 进度条   | Streamlit components | 原生支持       |

### 7.4 实现文件

| 文件                             | 改动                      |
| -------------------------------- | ------------------------- |
| `mylib/core/monitor_web.py`      | 新建：监控页面主文件      |
| `mylib/core/websocket_server.py` | 新建：WebSocket 日志服务  |
| `mylib/mcp/static/monitor.html`  | 新建：静态资源 (可选)     |
| `main.py`                        | 修改：添加 `monitor` 模式 |

---

## 8. 实施路线图

```
Week 1 (2026-01-14 ~ 2026-01-20)
├── Phase 1: 增强提示词系统
│   ├── Day 1-2: 设计提示词模板
│   ├── Day 3-4: 实现提示词模块
│   └── Day 5-7: 测试 & 调优

Week 2 (2026-01-21 ~ 2026-01-27)
├── Phase 2: FSM 状态机约束
│   ├── Day 1-2: 设计状态枚举 & 转换表
│   ├── Day 3-4: 实现 AgentFSM
│   └── Day 5-7: 集成到各 Agent

Week 3 (2026-01-28 ~ 2026-02-03)
├── Phase 3: Loutput 日志系统
│   ├── Day 1-2: 设计日志格式
│   ├── Day 3-4: 实现 AgentLogger
│   └── Day 5-7: 集成 & 测试

Week 4 (2026-02-04 ~ 2026-02-10)
├── Phase 4: 自由回调机制
│   ├── Day 1-2: 设计回调协议
│   ├── Day 3-5: 实现 CallbackManager
│   └── Day 6-7: 测试回调场景

Week 5 (2026-02-11 ~ 2026-02-17)
├── Phase 5: 异步多执行体
│   ├── Day 1-3: 实现 ExecutorPool
│   ├── Day 4-5: 修改 Planner 输出
│   └── Day 6-7: 并行执行测试

Week 6 (2026-02-18 ~ 2026-02-24)
├── Phase 6: 监控 Web 页面
│   ├── Day 1-3: 页面框架 & 布局
│   ├── Day 4-5: WebSocket 日志推送
│   └── Day 6-7: 集成测试 & 优化
```

---

## 9. 风险评估与备份策略

### 9.1 风险识别

| 风险                 | 等级 | 缓解措施                  |
| -------------------- | ---- | ------------------------- |
| LLM 不遵循状态机约束 | 高   | 硬性检查 + 自动重试       |
| 回调死锁             | 中   | 超时机制 + 最大深度限制   |
| 并行执行竞态条件     | 中   | asyncio.Lock 保护共享状态 |
| 上下文截断丢失信息   | 高   | 本地备份 + 分片存储       |
| Web 页面性能问题     | 低   | 日志分页 + 虚拟滚动       |

### 9.2 备份策略

1. **代码备份**: 每个 Phase 完成后打 Git Tag
2. **数据备份**: 所有 LLM 交互自动存入数据库
3. **上下文备份**: `ContextBackup` 类管理本地快照
4. **回滚方案**: 每个 Phase 可独立回滚，不影响其他功能

---

## 📝 审计清单

请审计以下内容，确认后我将开始实施：

- [ ] Phase 1: 提示词设计方案
- [ ] Phase 2: FSM 状态定义 & 转换规则
- [ ] Phase 3: 日志格式 & 级别划分
- [ ] Phase 4: 回调协议 & 触发条件
- [ ] Phase 5: 并行任务模型 & 依赖处理
- [ ] Phase 6: 监控页面布局 & 功能范围
- [ ] 实施路线图时间安排
- [ ] 风险缓解措施

---

> **等待审计中...**  
> 如有修改意见请提出，审计通过后即刻开始重构！
