import asyncio
import aiohttp
import numpy as np
from abc import ABC, abstractmethod
from typing import List, Dict, Any


from mylib.kernel.Lenum import LLMRole, LLMStatus
from mylib.lian_orm import Sql, MemoryLog, Task, TaskStep, ToolCall
from mylib.lian_orm import MemoryLogRole, MemoryLogMemoryType, TasksStatus, TaskStepsStatus, ToolCallsStatus
from mylib.kit.Lfind import get_embedding


# =============================================================================
# 4. 🗄 记忆系统接口 (MemoryInterface)
# =============================================================================
class MemoryInterface(ABC):
    @abstractmethod
    async def save_message(self, user_msg: str, reply: str, role: str = "user") -> None:
        """保存对话消息"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """计算文本嵌入"""
        pass
    
    @abstractmethod
    async def search(self, embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """检索相似记忆"""
        pass
    
    @abstractmethod
    async def insert_summary(self, text: str) -> None:
        """插入摘要"""
        pass

# =============================================================================
# 5. 🧰 任务系统接口 (TaskInterface)
# =============================================================================
class TaskInterface(ABC):
    @abstractmethod
    async def create_task(self, title: str, desc: str) -> int:
        """创建新任务"""
        pass
    
    @abstractmethod
    async def add_step(self, task_id: int, instruction: str) -> int:
        """添加任务步骤"""
        pass
    
    @abstractmethod
    async def update_step(self, step_id: int, output: str, status: str) -> None:
        """更新步骤状态"""
        pass

# =============================================================================
# 2. 🧠 基类：LLMBaseAgent
# =============================================================================
class LLMBaseAgent:
    # === 类变量（全局共享） ===
    api_key: str = ""                       # 远程LLM API Key
    api_url: str = ""                       # Base URL
    embedding_url: str = ""                 # Embedding URL（可选）
    model_name: str = "deepseek-chat"       # 主模型名
    embed_model_name: str = "text-embedding-v4" # embedding 使用的模型

    request_timeout: int = 30               # 网络超时
    max_context_tokens: int = 131072        # 上下文最大token裁剪

    def __init__(
        self,
        agent_id: str,
        identity_prompt: str,
        memory_interface: MemoryInterface,
        task_interface: TaskInterface
    ):
        # === 实例变量 ===
        self.agent_id = agent_id                  # 代理身份ID
        self.identity_prompt = identity_prompt    # 自我认知提示词
        self.memory = memory_interface            # 记忆系统
        self.tasks = task_interface               # 任务系统
        self.message_cache: List[Dict[str, str]] = [] # 当前上下文消息缓存
        self.loop = asyncio.get_event_loop()      # 异步事件循环

    # 3.3.1 注入自我认知
    def build_self_identity_block(self) -> dict:
        """
        构建一个 system 消息，作为“我是谁”注入上下文顶端。
        """
        return {
            "role": "system",
            "content": self.identity_prompt
        }

    # 3.3.2 查询长期记忆（本地 RAG）
    async def query_memory(self, query: str, top_k: int = 5) -> List[dict]:
        """
        调用 PGVector 数据库检索相似记忆。
        返回 {content, score} 列表。
        """
        query_embed = await self.memory.embed(query)
        return await self.memory.search(query_embed, top_k)

    # 3.3.3 构建完整上下文
    async def build_context(self, user_msg: str) -> List[dict]:
        """
        构建发送给 LLM 的完整上下文：
        1. 自我认知
        2. 检索到的长期记忆（经过裁剪）
        3. 当前缓存消息
        4. 新的用户消息
        """
        memory_hits = await self.query_memory(user_msg)
        memory_block_content = self.format_memory_block(memory_hits)
        
        memory_block = {
            "role": "system",
            "content": memory_block_content,
        }

        return [
            self.build_self_identity_block(),
            memory_block,
            *self.message_cache,
            {"role": "user", "content": user_msg}
        ]

    def format_memory_block(self, memory_hits: List[dict]) -> str:
        """格式化检索到的记忆"""
        if not memory_hits:
            return "No relevant memories found."
        
        lines = ["Relevant Memories:"]
        for hit in memory_hits:
            content = hit.get('content', '')
            lines.append(f"- {content}")
        return "\n".join(lines)

    # 3.3.4 调用远程 LLM（异步）
    async def call_llm(self, messages: List[dict]) -> str:
        """
        异步调用远程 LLM API。
        """
        payload = {
            "model": self.model_name,
            "messages": messages,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=self.request_timeout
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"LLM API Error: {resp.status} - {error_text}")
                data = await resp.json()
                return data["choices"][0]["message"]["content"]

    # 3.3.5 外部入口：处理消息
    async def handle(self, user_msg: str) -> str:
        """
        处理单条用户输入：
        1. 构建上下文
        2. 调用LLM
        3. 保存消息
        4. 更新缓存
        """
        messages = await self.build_context(user_msg)
        assistant_reply = await self.call_llm(messages)

        await self.memory.save_message(user_msg, assistant_reply)
        self.message_cache.append({"role": "user", "content": user_msg})
        self.message_cache.append({"role": "assistant", "content": assistant_reply})

        return assistant_reply
    
    # 7. 🚦 异步事件调度（并行执行）
    async def background_task(self, coro):
        self.loop.create_task(coro)

# =============================================================================
# Implementations
# =============================================================================

class MemoryImpl(MemoryInterface):
    def __init__(self):
        self.sql = Sql()

    async def embed(self, text: str) -> List[float]:
        """历史消息向量化 (Async wrapper)"""
        return await asyncio.to_thread(get_embedding, text)

    async def save_message(self, user_msg: str, reply: str, role: str = "user") -> None:
        """保存消息到数据库"""
        user_id = "default"
        
        # Embedding user message
        emb = await self.embed(user_msg)
        
        log = MemoryLog(
            user_id=user_id, 
            role=MemoryLogRole.USER,
            content=user_msg, 
            embedding=emb,
            memory_type=MemoryLogMemoryType.SHORT_TERM,
            importance=1.0
        )
        await asyncio.to_thread(self.sql.memory_log.create, log)
        
        # Embedding assistant reply
        emb_reply = await self.embed(reply)
        log_reply = MemoryLog(
            user_id=user_id,
            role=MemoryLogRole.ASSISTANT,
            content=reply,
            embedding=emb_reply,
            memory_type=MemoryLogMemoryType.SHORT_TERM,
            importance=1.0
        )
        await asyncio.to_thread(self.sql.memory_log.create, log_reply)

    async def search(self, embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """检索相似记忆"""
        results = await asyncio.to_thread(self.sql.memory_log.search_by_embedding, embedding, top_k)
        
        return [
            {
                "content": item["content"],
                "score": item["score"],
                "role": item["role"]
            }
            for item in results
        ]

    def top_n_similar_np(self, target, candidates, n):
        target = np.array(target)
        scores = []

        for item in candidates:
            emb = np.array(item["embedding"])
            if np.linalg.norm(emb) == 0: continue
            sim = np.dot(target, emb) / (np.linalg.norm(target) * np.linalg.norm(emb))
            scores.append((sim, item))

        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:n]

    async def insert_summary(self, text: str) -> None:
        user_id = "default"
        emb = await self.embed(text)
        log = MemoryLog(
            user_id=user_id,
            role=MemoryLogRole.SYSTEM,
            content=text,
            embedding=emb,
            memory_type=MemoryLogMemoryType.SUMMARY,
            importance=1.0
        )
        await asyncio.to_thread(self.sql.memory_log.create, log)

class TaskImpl(TaskInterface):
    def __init__(self):
        self.sql = Sql()

    async def create_task(self, title: str, desc: str) -> int:
        task = Task(
            title=title,
            description=desc,
            status=TasksStatus.PENDING
        )
        created_task = await asyncio.to_thread(self.sql.tasks.create, task)
        return created_task.id if created_task else -1

    async def add_step(self, task_id: int, instruction: str) -> int:
        step = TaskStep(
            task_id=task_id,
            instruction=instruction,
            status=TaskStepsStatus.PENDING
        )
        created_step = await asyncio.to_thread(self.sql.task_steps.create, step)
        return created_step.id if created_step else -1

    async def update_step(self, step_id: int, output: str, status: str) -> None:
        await asyncio.to_thread(
            self.sql.task_steps.update,
            id=step_id,
            output=output,
            status=status
        )

    async def search(self, embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """检索相似记忆"""
        results = await asyncio.to_thread(self.sql.Search_memory_log, embedding, top_k)
        
        return [
            {
                "content": item["content"],
                "score": item["score"],
                "role": item["role"]
            }
            for item in results
        ]

    async def insert_summary(self, text: str) -> None:
        user_id = "default"
        emb = await self.embed(text)
        log = MemoryLog(
            user_id=user_id,
            role=MemoryLogRole.SYSTEM,
            content=text,
            embedding=emb,
            memory_type=MemoryLogMemoryType.SUMMARY,
            importance=1.0
        )
        await asyncio.to_thread(self.sql.Create_memory_log, log)

class TaskImpl(TaskInterface):
    def __init__(self):
        self.sql = Sql()

    async def create_task(self, title: str, desc: str) -> int:
        task = Task(
            title=title,
            description=desc,
            status=TasksStatus.PENDING
        )
        created_task = await asyncio.to_thread(self.sql.Create_tasks, task)
        return created_task.id if created_task else -1

    async def add_step(self, task_id: int, instruction: str) -> int:
        step = TaskStep(
            task_id=task_id,
            instruction=instruction,
            status=TaskStepsStatus.PENDING
        )
        created_step = await asyncio.to_thread(self.sql.Create_task_steps, step)
        return created_step.id if created_step else -1

    async def update_step(self, step_id: int, output: str, status: str) -> None:
        await asyncio.to_thread(
            self.sql.Update_task_steps,
            id=step_id,
            output=output,
            status=status
        )

# =============================================================================
# 6. 🪄 子类扩展示例
# =============================================================================

class PlannerAgent(LLMBaseAgent):
    async def plan(self, goal: str) -> List[str]:
        # 调用 LLM 生成步骤列表
        prompt = f"Goal: {goal}\nCreate a step-by-step plan."
        response = await self.handle(prompt)
        # Parse response to list
        return response.split('\\n')

class WorkerAgent(LLMBaseAgent):
    async def execute(self, instruction: str) -> str:
        prompt = f"Execute this instruction: {instruction}"
        return await self.handle(prompt)

class ReflectorAgent(LLMBaseAgent):
    async def reflect(self) -> str:
        prompt = "Reflect on the recent interactions and summarize key insights."
        return await self.handle(prompt)
