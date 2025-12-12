from enum import Enum


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


class LLMStatus(Enum):
    """大模型状态枚举"""
    IDLE = "idle"
    # 空闲状态：刚创建 / 等待任务

    RUNNING = "running"
    # 工作状态：正在处理中（RAG检索、规划、执行等）

    FINISHED = "finished"
    # 任务结束，可进入下一个任务或销毁
