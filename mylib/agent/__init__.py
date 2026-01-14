"""
Agent 模块

包含四种专业智能体及其支持组件：
- RAGAgent: 记忆检索智能体
- PlannerAgent: 任务规划智能体  
- ExecutorAgent: 工具执行智能体
- SummaryAgent: 结果总结智能体

支持组件：
- AgentFSM: 状态机控制
- AgentLogger: 日志记录
- CallbackManager: 回调机制
- ContextBackup: 上下文备份
- ExecutorPool: 并行执行器池
"""

# 核心 Agent
from .base import BaseAgent
from .rag_agent import RAGAgent
from .planner_agent import PlannerAgent
from .executor_agent import ExecutorAgent
from .summary_agent import SummaryAgent

# FSM 状态机
from .fsm import AgentFSM, fsm_manager

# Logger 日志
from .logger import AgentLogger, LogLevel, logger_manager

# Callback 回调
from .callback import (
    CallbackManager, 
    CallbackRequest, 
    CallbackResponse, 
    CallbackBuilder,
    callback_manager
)

# Backup 备份
from .backup import ContextBackup, context_backup

# StateStore 状态存储（跨进程共享）
from .state_store import StateStore, state_store

# Monitor API（监控服务）
from .monitor_api import run_monitor_server

# ExecutorPool 执行器池
from .executor_pool import (
    ExecutorPool, 
    ExecutorTask, 
    TaskStatus,
    executor_pool_manager
)

# Prompts 提示词
from .prompts import (
    SYSTEM_AWARENESS,
    RAG_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    build_executor_prompt,
    SUMMARY_SYSTEM_PROMPT,
    CATGIRL_PERSONA
)

__all__ = [
    # Agents
    "BaseAgent",
    "RAGAgent",
    "PlannerAgent", 
    "ExecutorAgent",
    "SummaryAgent",
    
    # FSM
    "AgentFSM",
    "fsm_manager",
    
    # Logger
    "AgentLogger",
    "LogLevel",
    "logger_manager",
    
    # Callback
    "CallbackManager",
    "CallbackRequest",
    "CallbackResponse",
    "CallbackBuilder",
    "callback_manager",
    
    # Backup
    "ContextBackup",
    "context_backup",
    
    # StateStore
    "StateStore",
    "state_store",
    
    # ExecutorPool
    "ExecutorPool",
    "ExecutorTask",
    "TaskStatus",
    "executor_pool_manager",
    
    # Prompts
    "SYSTEM_AWARENESS",
    "RAG_SYSTEM_PROMPT",
    "PLANNER_SYSTEM_PROMPT",
    "build_executor_prompt",
    "SUMMARY_SYSTEM_PROMPT",
    "CATGIRL_PERSONA",
]
