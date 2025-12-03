# 所有 LLM 的基类
from typing import List, Dict, Generic, TypeVar, Type

from .Enum import LLMRole, LLMStatus


ReqT = TypeVar("ReqT")
ResT = TypeVar("ResT")


class LLMBaseAgent(Generic[ReqT, ResT]):
    # ----------- 类变量（所有 Agent 共用）------------------------
    # 大模型访问
    provider: str                     # 模型供应商（deepseek）
    api_key: str                      # API key
    api_url: str                      # HTTP 地址
    # 通信协议 Local - Origin
    request_schema: Type[ReqT]        # 发往 LLM 的消息格式
    response_schema: Type[ResT]       # LLM 必须按此格式返回

    # ----------- 实例变量（每个 Agent 需要独立实现的方法）-----------
    # 身份
    agent_id: str                     # 唯一 ID
    role: LLMRole                     # 角色名 枚举
    description: str                  # 完整提示词 (System Prompt）
    # 目的
    goals: List[str]                  # 当前职责
    # 记忆
    memory: List[Dict[str, str]]      # 短期上下文
    long_memory_ids: Dict[str, str]   # 长期记忆在 DB 的存储引用
    # 状态
    parent_id: str | None             # 创建这个 agent 的“父代理”
    status: LLMStatus                 # 当前状态 枚举
    # 固定字段
    identity_prompt: str              # 自我认知的内容（System Prompt）

    # ----------- 必须实现的方法（抽象方法）-------------------------
    def think(self, user_input: str) -> dict:
        """
        Args:
            user_input: 用户输入
        Return:
            dict: LLM返回的标准结构
        """
    def receive(self, message: dict) -> None: 
        """
        Args:
            message: 需要加入memory的消息
        """
    def respond(self) -> dict:
        """
        Return:
            根据memory给出回答
        """

    # ----------- 工具与系统方法（基类统一实现）----------------------
    def call_tool(self, args: dict) -> Dict:
        """
        Args:
            args: 调用MCP工具的json格式
        Return:
            dict: MCP工具的应答
        """
    def spawn_agent(self, role: LLMRole, description: str, goals: List[str]) -> object:
        """
        Args:
            role: 子代理的权限
            description: 子代理的自我认知
            goals: 子代理的职责
        Retrun: 
            object: 子代理
        """
    def save_memory(self, text: str) -> Dict:
        """
        Args: 
            text: 需要保存的内容
        Return:
            Dict: 状态信息
        """
    def retrieve_memory(self, query: str):
        """
        Args:
            query: 向量记忆检索
        """
    def log(self, event):
        """
        日志
        """
