import httpx
import datetime
import time

from uuid import uuid4, UUID
from typing import List, Dict, Union, Any

from mylib.config import ConfigLoader
from mylib.kernel.Lenum import LLMRole, LLMStatus, MemoryLogMemoryType
from mylib.lian_orm import Sql, MemoryLog, Task, TaskStep, ToolCall
from mylib.kit.Lfind import get_embedding


class LLMBaseAgent:
    # === 配置区 ===
    cfg = ConfigLoader(config_path="./config").LLM
    schema = ConfigLoader(config_path="./schema")

    # === 类变量 === 所有 Agent 公用 === 可被实例级覆盖 ===
    provider: str = cfg.MODEL           # 模型供应商（deepseek/openai）
    api_key: str = cfg.API_KEY          # API key
    api_url: str = cfg.API_URL          # HTTP 地址
    max_tokens: int = cfg.MAX_TOKENS    # 模型最大 tokens
    max_retries: int = cfg.MAX_RETRIES  # 最大尝试次数
    api_timeout: float = cfg.TIMEOUT    # 模型超时
    retry_delay: int = cfg.DELAY        # 指数退缩

    # === 实例变量 === 从配置文件加载 === 可为空
    request_schema: dict                # 发往 LLM 的消息格式
    response_schema: dict               # LLM 必须按此格式返回

    # === 实例变量 === 要求子类必须实现 ===
    agent_id: UUID                      # 唯一 ID
    status: LLMStatus                   # {idle, running, finished}
    role: LLMRole                       # {ruler, caster, foreteller, assassin, shielder}
    description: str                    # 自我认知的内容（System Prompt）
    goals: list[str]                    # 当前目标列表
    memory: list[dict]                  # 短期上下文（部分）

    # === 实例变量 === 子类可选实现 ===
    long_memory_ids: list[str]          # 长期记忆在 DB 的存储引用
    parent_id: str | None               # 创建这个 agent 的“父代理”


    def __init_subclasses__(self):
        self.agent_id = uuid4()
        self.db = Sql()
        self.status = LLMStatus.IDLE

        # === 子类必须实例化的变量 ===
        # {role, descriptopn, goals}


    # === 必须实现的方法 === think = save_memory ===
    def think(self, user_input: str) -> dict:
        """发起一次LLM请求的完整过程"""
        content = self._construct_context(user_input=user_input)
        return self._call_llm(content)

    def save_memory(self, content: str, memmory_type: MemoryLogMemoryType = MemoryLogMemoryType.CONVERSATION):
        """保存一条对话历史到数据库"""
        if self.db and self.db.memory_log:
            try:
                embedding = None
                try:
                    if content and content.strip():
                        embedding = get_embedding(content)
                except Exception as e:
                    print(f"[{self.name}] Failed to generate embedding: {e}")

                log = MemoryLog(
                    role=self.role,
                    content=content,
                    embedding=embedding,
                    memory_type=memmory_type,
                    created_at=datetime.datetime.now()
                )
                self.save_data(data=log)
            except Exception as e:
                print(f"[{self.name}] Failed to save memory: {e}")


    # === 工具方法 === 子类可选实现 ===
    def call_tool(self, name: str, args: dict) -> dict:
        """调用MCP工具的能力"""
    def spawn_agent(self, role: str, description: str, goals: list[str]):
        """创建子代理的工具"""
    def up_task(self, data: Union[Task, TaskStep]) -> bool:
        """更新数据库任务条目"""


    # === 统一子函数封装 === 为主要函数提供底层算法 ===
    def save_data(self, data: Union[MemoryLog, Task, TaskStep, ToolCall]) -> Any:
        """对数据库的 Create 操作"""
        table = self._model_to_table(data)
        return table.create(data)

    def update_data(self, data: Union[MemoryLog, Task, TaskStep, ToolCall]) -> bool:
        """对数据库的 Update 操作"""
        table = self._model_to_table(data)
        return table.update(data)

    def _model_to_table(self, model: Union[MemoryLog, Task, TaskStep, ToolCall]) -> object:
        """根据数据模型返回可操作的数据库对象"""
        if isinstance(model, MemoryLog):
            return getattr(self.db, "memory_log")
        elif isinstance(model, Task):
            return getattr(self.db, "tasks")
        elif isinstance(model, TaskStep):
            return getattr(self.db, "task_steps")
        elif isinstance(model, ToolCall):
            return getattr(self.db, "tool_calls")
        else:
            raise TypeError(f"Unsupported data type: {type(model)}")

    def _call_llm(self, message: List[Dict], temperature: float = 0.7, stream: bool = False) -> Dict:
        """发起一个LLM会话"""
        delay = self.retry_delay
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

        for attempt in range(self.max_retries):
            with httpx.AsyncClient(timeout=self.api_timeout) as client:
                try:
                    response = client.post(
                        {self.api_url},
                        headers=header,
                        json=payload
                    )
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    if attempt < self.max_retries -1:
                        print(f"[{self.name}] LLM Call failed (Attempt {attempt+1}/{self.max_retries}): {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2 # 指数退避
                    else:
                        print(f"[{self.name}] LLM Call Error after {self.max_retries} attempts: {e}")
                        return {"choices": [{"message": {"content": f"Error: {str(e)}"}}]}


    def _construct_context(self, user_input: str):
        """维护memory, 拼接上下文"""
        message = []
        # 自我认知
        if hasattr(self, "description"):
            message.append({"role": "system", "content": self.description})

        # 任务列表
        if hasattr(self, "goals"):
            message.append({"role": "system", "content": self.goals})
        
        # 发送/回复格式
        if hasattr(self, "request_schema"):
            message.append
        
        # 短期历史记录
        if hasattr(self, "memory"):
            message.append(self.memory)
        
        # 当前消息
        message.append({"role": "user", "content": user_input})
        
        return message

    def build(self, user_input: str, fields=None):
        """上下文构造器"""
        if fields is None:
            fields = ["description", "goals", "request_schema", "response_schema"]

        msg = []
        for f in fields:
            if hasattr(self, f):
                msg.append({"role": "system", "content": getattr(self, f)})

        if hasattr(self, "memory"):
            msg.append(self.memory)

        msg.append({"role": "user", "content": user_input})
        return msg
