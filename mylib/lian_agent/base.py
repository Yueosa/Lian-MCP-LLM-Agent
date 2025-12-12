import httpx

from uuid import uuid4, UUID
from typing import List, Dict, Union, Any

from mylib.config import ConfigLoader
from mylib.kernel.Lenum import LLMRole, LLMStatus
from mylib.lian_orm import Sql, MemoryLog, Task, TaskStep, ToolCall


class LLMBaseAgent:
    cfg = ConfigLoader(config_path="./config").LLM
    schema = ConfigLoader(config_path="./schema")
    # ----------- 类变量（所有 Agent 共用）-----------
    provider: str = cfg.MODEL           # 模型供应商（deepseek/openai）
    api_key: str = cfg.API_KEY          # API key
    api_url: str = cfg.API_URL          # HTTP 地址
    max_tokens: int = cfg.MAXTOKENS     # 模型最大 tokens
    api_timeout: float = cfg.TIMEOUT    # 模型超时
    request_schema: dict                # 发往 LLM 的消息格式
    response_schema: dict               # LLM 必须按此格式返回

    # ----------- 实例变量（每个 Agent 独立）-----------
    agent_id: UUID                      # 唯一 ID
    role: LLMRole                       # 角色名（Programmer、Analyst…）
    description: str                    # 自我认知的内容（System Prompt）
    goals: list[str]                    # 当前目标列表
    memory: list[dict]                  # 短期上下文（部分）
    long_memory_ids: list[str]          # 长期记忆在 DB 的存储引用
    parent_id: str | None               # 创建这个 agent 的“父代理”
    status: LLMStatus                   # {idle, running, finished}

    def __init_subclasses__(self):
        self.agent_id = uuid4()
        self.db = Sql()

    # ----------- 必须实现的方法（抽象方法）-----------
    def think(self, user_input: str) -> dict:
        """发起一次LLM请求的完整过程"""
    def _receive(self, message: dict) -> None:
        """处理消息拼接/tokens计算..."""

    # ----------- 工具与系统方法（基类统一实现）-----------
    def call_tool(self, name: str, args: dict) -> dict:
        """调用MCP工具的能力"""
    def spawn_agent(self, role: str, description: str, goals: list[str]):
        """创建子代理的工具"""
    def save_data(self, data: Union[MemoryLog, Task, TaskStep, ToolCall]) -> Any:
        """对数据库的 Create 操作"""

        table = self._model_to_table(data)

        table_obj = getattr(self.db, table)
        return table_obj.create(data)

    def update_data(self, data: Union[MemoryLog, Task, TaskStep, ToolCall]) -> bool:
        """对数据库的 Update 操作"""

        table = self._model_to_table(data)
        
        self.db.memory_log.update()

    def retrieve_memory(self, query: str): ...
    def log(self, event): ...

    # ----------- 底层统一封装（基类统一实现）-----------
    def _model_to_table(self, model: Union[MemoryLog, Task, TaskStep, ToolCall]) -> str:
        if isinstance(model, MemoryLog):
            return "memory_log"
        elif isinstance(model, Task):
            return "tasks"
        elif isinstance(model, TaskStep):
            return "task_steps"
        elif isinstance(model, ToolCall):
            return "tool_calls"
        else:
            raise TypeError(f"Unsupported data type: {type(model)}")

    async def _call_llm(self, message: List[Dict], temperature: float = 0.7, stream: bool = False) -> Dict:
        """发起一个LLM会话"""
        header = {
            "Content-Type": "application/json",
            "Suthorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.provider,
            "message": message,
            "temperature": temperature,
            "stream": stream
        }

        async with httpx.AsyncClient(timeout=self.api_timeout) as client:
            try:
                response = await client.post(
                    {self.api_url},
                    headers=header,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"[{self.agent_id}] LLM Call Error: {e}")
                return {"choices": [{"message": {"content": f"Error: {str(e)}"}}]}

    def _construct_context(self, user_input: str):
        """维护memory, 拼接上下文"""
        ...

    def _tokens(self):
        """计算, 维护, 截断 memory 的 token"""
        ...
