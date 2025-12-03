from enum import Enum


# ========================
# 数据表 日志表 memory_log
# ========================
class memory_log_role(Enum):
    """
    user: 用户
    assistant: 管理员
    system: 系统
    llm: 大模型
    """
    user = 'user'
    assistant = 'assistant'
    system = 'system'
    llm = 'llm'

class memory_log_memory_type(Enum):
    """
    conversation: 对话
    summary: 总结
    reflection: 反思
    preference: 偏好
    plan: 计划
    """
    conversation = 'conversation'
    summary = 'summary'
    reflection = 'reflection'
    preference = 'preference'
    plan = 'plan'


# ===================
# 数据表 任务表 tasks
# ===================
class tasks_status(Enum):
    """
    pending: 待处理
    running: 运行中
    done: 已完成
    failed: 失败
    """
    pending = 'pending'
    running = 'running'
    done = 'done'
    failed = 'failed'


# ===========================
# 数据表 任务步骤表 task_steps
# ===========================
class task_steps_status(Enum):
    """
    pending: 待处理
    running: 运行中
    done: 已完成
    failed: 失败
    """
    pending = 'pending'
    running = 'running'
    done = 'done'
    failed = 'failed'


# ===========================
# 数据表 工具调用表 tool_calls
# ===========================
class tool_calls_status(Enum):
    """
    success: 成功
    failed: 失败
    """
    success = 'success'
    failed = 'failed'


# =====================
# 外键更新策略 on_update
# =====================
class on_update(Enum):
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
class on_delete(Enum):
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
class relationship(Enum):
    """
    one_to_one: 一对一
    one_to_mant: 一对多
    many_to_one: 多对一
    """
    one_to_one = 'one_to_one'
    one_to_many = 'one_to_many'
    many_to_one = 'many_to_one'
