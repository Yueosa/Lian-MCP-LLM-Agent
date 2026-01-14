from enum import Enum, auto


class LLMRole(Enum):
    """大模型角色枚举"""
    RULER = "Ruler"  
    # 管理所有流程、调度其他Agent、拥有最高权限
    # 对应：系统中枢 / Orchestrator / Supervisor

    CASTER = "Caster"
    # 负责 RAG 检索、知识整合、总结记忆供其他Agent使用
    # 对应：记忆检索 / RAG Summarizer / Knowledge Provider

    FORETELLER = "Foreteller"  
    # 负责任务规划、分解步骤、产生执行计划
    # 对应：Planner / Task Decomposer

    ASSASSIN = "Assassin"
    # 执行任务步骤、调用工具、处理结果、最终回答用户
    # 对应：Executor / Tool User / Worker Agent

    SHIELDER = "Shielder"
    # 责总结整个对话、输出最终报告或总结
    # 对应：Summarizer / Dialog Review / Safety Layer

    ARCHIVER = "Archiver"
    # 负责将关键信息、长期记忆、结构化数据保存到数据库
    # 对应：Memory Writer / Persistence Agent / Data Archivist


class LLMStatus(Enum):
    """大模型状态枚举"""
    IDLE = "idle"
    # 空闲状态：刚创建 / 等待任务

    RUNNING = "running"
    # 工作状态：正在处理中（RAG检索、规划、执行等）

    FINISHED = "finished"
    # 任务结束，可进入下一个任务或销毁


class LLMContextType(str, Enum):
    """上下文角色类型"""
    SYSTEM = "system"        
    # 系统规则 / 人设 / 行为约束
    USER = "user"            
    # 用户输入
    ASSISTANT = "assistant"  
    # 模型输出


# ============================================================
#  Agent FSM 状态机相关枚举
# ============================================================

class AgentState(Enum):
    """
    Agent 状态机状态
    用于约束 Agent 的操作流程，确保每一步都在可控范围内
    """
    IDLE = auto()              # 空闲，等待任务
    INITIALIZING = auto()      # 初始化中
    PROCESSING = auto()        # 处理用户输入/中间数据
    WAITING_LLM = auto()       # 等待 LLM 响应
    PARSING_RESPONSE = auto()  # 解析 LLM 响应
    WAITING_TOOL = auto()      # 等待工具执行结果
    CALLBACK_PENDING = auto()  # 发起回调，等待其他 Agent 响应
    SUMMARIZING = auto()       # 生成总结
    COMPLETED = auto()         # 任务完成
    ERROR = auto()             # 错误状态
    TERMINATED = auto()        # 已终止


class AgentTransition(Enum):
    """
    状态转换触发事件
    定义了从一个状态转换到另一个状态的触发条件
    """
    START = auto()             # 开始任务
    INIT_COMPLETE = auto()     # 初始化完成
    LLM_REQUEST = auto()       # 发起 LLM 请求
    LLM_RESPONSE = auto()      # 收到 LLM 响应
    LLM_CALL = auto()          # 发起 LLM 调用（别名）
    LLM_DONE = auto()          # LLM 调用完成（别名）
    PARSE_COMPLETE = auto()    # 解析完成
    TOOL_CALL = auto()         # 发起工具调用
    TOOL_RESULT = auto()       # 收到工具结果
    CALLBACK_REQUEST = auto()  # 发起回调请求
    CALLBACK_RESPONSE = auto() # 收到回调响应
    SUMMARIZE = auto()         # 开始总结
    COMPLETE = auto()          # 任务完成
    FAIL = auto()              # 任务失败
    ERROR = auto()             # 错误（别名）
    RESET = auto()             # 重置状态
    TERMINATE = auto()         # 终止
    RETRY = auto()             # 重试（从 ERROR 状态恢复）


class CallbackAction(Enum):
    """
    回调动作类型
    定义了 Agent 间回调请求的类型
    """
    REPLAN = "REPLAN"                # 请求重新规划 (Executor → Planner)
    MORE_CONTEXT = "MORE_CONTEXT"    # 请求更多上下文 (Summary → RAG)
    CLARIFY = "CLARIFY"              # 请求澄清结果 (Summary → Executor)
    RETRY = "RETRY"                  # 请求重试
    ABORT = "ABORT"                  # 请求终止任务


class TaskType(Enum):
    """
    任务类型
    定义了 Planner 生成的任务执行方式
    """
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行
    MIXED = "mixed"            # 混合执行（部分并行）


class RetryPolicy(Enum):
    """
    重试策略
    定义了步骤失败时的处理方式
    """
    NO_RETRY = "no_retry"         # 不重试
    RETRY_ONCE = "retry_once"     # 重试一次
    RETRY_TWICE = "retry_twice"   # 重试两次
    RETRY_INFINITE = "retry_infinite"  # 无限重试（有上限）
    SKIP = "skip"                 # 跳过继续
    CALLBACK = "callback"         # 回调上游 Agent
    # 工具返回（可选，未来用）