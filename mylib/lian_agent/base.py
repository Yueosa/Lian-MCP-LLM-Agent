import httpx
import datetime
import time
import tiktoken


from uuid import uuid4, UUID
from typing import List, Dict, Union, Any

from mylib.config import ConfigLoader
from mylib.kernel.Lenum import LLMRole, LLMStatus, MemoryLogMemoryType, MemoryLogRole, LLMContextType
from mylib.lian_orm import Sql, MemoryLog, Task, TaskStep, ToolCall
from mylib.kit.Lfind import get_embedding
from mylib.kit.Loutput import Loutput


class BaseAgent:
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
    memory_tokens: list[int]            # 短期上下文的token

    # === 实例变量 === 子类可选实现 ===
    long_memory_ids: list[str]          # 长期记忆在 DB 的存储引用
    parent_id: str | None               # 创建这个 agent 的“父代理”


    def __init__(self):
        self.agent_id = uuid4()
        self.db = Sql()
        self.lo = Loutput()
        self.status = LLMStatus.IDLE
        self.memory = []
        self.memory_tokens = []
        self.tokenizer = tiktoken.get_encoding("cl100k_base")


        # === 子类必须实例化的变量 ===
        # {role, descriptopn, goals}

    def _tokens(self, content: str) -> int:
        """计算一个content的tokens"""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(content))
            except Exception:
                return len(content) // 4
        return len(content) // 4

    def _append_memory(self, role: LLMContextType, content: str):
        """将一条role: content加入memory"""
        self.memory.append({"role": role, "content": content})
        self.memory_tokens.append(self._tokens(content))


    # === 必须实现的方法 === think = save_memory ===
    def think(self, user_input: str) -> dict:
        """发起一次LLM请求的完整过程"""
        contexts = self._build(user_input=user_input)
        response = self._call_llm(contexts)
        
        if "choices" in response and len(response["choices"]) > 0:
            try:
                content = response["choices"][0]["message"]["content"]
                self._append_memory(LLMContextType.ASSISTANT, content)
            except KeyError:
                pass
            
        return response

    def _build(self, user_input: str) -> List[Dict[LLMContextType, str]]:
        """构造请求消息"""
        self._append_memory(LLMContextType.USER, user_input)

        contexts: list[Dict[LLMContextType, str]] = [{
            "role": LLMContextType.SYSTEM,
            "content": self.description,
        }]

        remaining_tokens = self.max_tokens - self._tokens(self.description)
        start = len(self.memory)

        for i in range(len(self.memory) - 1, -1, -1):
            tokens = self.memory_tokens[i]
            if remaining_tokens < tokens:
                break
            remaining_tokens -= tokens
            start = i

        if start > 0:
            contexts.append({
                "role": LLMContextType.SYSTEM,
                "content": "[History Truncated]"
            })

        contexts.extend(self.memory[start:])

        return contexts


    def _call_llm(self, contexts: List[Dict[LLMContextType, str]]) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        payload = {
            "model": self.provider,
            "messages": contexts,
            "temperature": 0.7,
            "stream": False,
        }

        for attempt in range(self.max_retries):
            try:
                with httpx.Client(timeout=self.api_timeout) as client:
                    response = client.post(
                        self.api_url,
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    print(f"[{self.agent_id}] LLM Call Error: {e}")
                    return {"choices": [{"message": {"content": f"Error: {str(e)}"}}]}
        return {"choices": [{"message": {"content": "Error: Max retries reached"}}]}

    def save_memory(self, role: MemoryLogRole, content: str, memmory_type: MemoryLogMemoryType = MemoryLogMemoryType.CONVERSATION):
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
                    role=role,
                    content=content,
                    embedding=embedding,
                    memory_type=memmory_type,
                    created_at=datetime.datetime.now()
                )
                self._save_data(data=log)
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
    def _get_emb(self, query: str) -> List[float]:
        return get_embedding(query)

    def _new_state(self, state: LLMStatus):
        if isinstance(state, LLMStatus):
            self.status = state

    def _save_data(self, data: Union[MemoryLog, Task, TaskStep, ToolCall]) -> Any:
        """对数据库的 Create 操作"""
        table = self._model_to_table(data)
        return table.create(data)

    def _update_data(self, data: Union[MemoryLog, Task, TaskStep, ToolCall]) -> bool:
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
