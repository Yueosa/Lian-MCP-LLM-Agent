from enum import Enum


# ========================
# 数据表 日志表 memory_log
# ========================
class MemoryLogRole(Enum):
    """
    user: 用户
    assistant: 管理员
    system: 系统
    llm: 大模型
    """
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'
    LLM = 'llm'

class MemoryLogMemoryType(Enum):
    """
    conversation: 对话
    summary: 总结
    reflection: 反思
    preference: 偏好
    plan: 计划
    """
    CONVERSATION = 'conversation'
    SUMMARY = 'summary'
    REFLECTION = 'reflection'
    PREFERENCE = 'preference'
    PLAN = 'plan'


# ===================
# 数据表 任务表 tasks
# ===================
class TasksStatus(Enum):
    """
    pending: 待处理
    running: 运行中
    done: 已完成
    failed: 失败
    """
    PENDING = 'pending'
    RUNNING = 'running'
    DONE = 'done'
    FAILED = 'failed'


# ===========================
# 数据表 任务步骤表 task_steps
# ===========================
class TaskStepsStatus(Enum):
    """
    pending: 待处理
    running: 运行中
    done: 已完成
    failed: 失败
    """
    PENDING = 'pending'
    RUNNING = 'running'
    DONE = 'done'
    FAILED = 'failed'


# ===========================
# 数据表 工具调用表 tool_calls
# ===========================
class ToolCallsStatus(Enum):
    """
    success: 成功
    failed: 失败
    """
    SUCCESS = 'success'
    FAILED = 'failed'


# =====================
# 外键更新策略 on_update
# =====================
class OnUpdate(Enum):
    """
    CASCADE: 跟随更新
    SET_NULL: 置为空值
    RESTRICT: 禁止更新
    NO_ACTION: 没有操作
    """
    CASCADE = 'CASCADE'
    SET_NULL = 'SET NULL'
    RESTRICT = 'RESTRICT'
    NO_ACTION = 'NO ACTION'


# =====================
# 外键删除策略 on_delete
# =====================
class OnDelete(Enum):
    """
    CASCADE: 跟随删除
    SET_NULL: 置为空值
    RESTRICT: 禁止删除
    NO_ACTION: 没有操作
    """
    CASCADE = 'CASCADE'
    SET_NULL = 'SET NULL'
    RESTRICT = 'RESTRICT'
    NO_ACTION = 'NO ACTION'


# ==========================
# 外键关系 relationship_type
# ==========================
class Relationship(Enum):
    """
    one_to_one: 一对一
    one_to_mant: 一对多
    many_to_one: 多对一
    """
    ONE_TO_ONE = 'one_to_one'
    ONE_TO_MANY = 'one_to_many'
    MANY_TO_ONE = 'many_to_one'
