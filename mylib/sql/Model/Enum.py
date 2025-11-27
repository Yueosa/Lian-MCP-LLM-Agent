from enum import Enum


# ========================
# 数据表 日志表 memory_log
# ========================
class memory_log_role(Enum):
    """
    user: 用户
    assistant: 管理员
    system: 系统
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
