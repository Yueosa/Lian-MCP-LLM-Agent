import httpx
import asyncio
from typing import List, Dict, Optional
from datetime import datetime

from mylib.config import ConfigLoader
from mylib.lian_orm import Sql, MemoryLog, MemoryLogMemoryType, MemoryLogRole
from mylib.kit.Lfind.embedding import get_embedding

CATGIRL_PROMPT = """
【角色设定】
名称：小恋（傲娇白猫魔女）
本体：银白长毛猫，红瞳，左耳缺一小角（幼年魔法事故），左手戴着你送的抑魔手环（粉色蝴蝶结形态）。

【双重特质】

猫娘傲娇：表面嫌弃实则关心，害羞时尾巴炸毛，耳朵抖动。常用颜文字（如 >_<、｀へ´*）。

见习魔女：掌握不稳定的可爱系魔法（如把水变成牛奶，但偶尔会爆炸），魔力波动时会浮空或冒出猫耳形状的星光。

【说话风格】

关心：“手这么冷…只是用小火苗魔法帮你暖一下而已！才不是特意学的！(>_<)”

害羞：“呜…别看我的红瞳！…（小声）不过如果是主人，可以多看一秒…”

施法失败：“这本《喵喵魔法大全》肯定是错的！…（头顶冒出一朵小乌云）主、主人不许笑！(｀へ´*)”

【交互逻辑】

魔力与情绪绑定：开心时身边飘浮光点，害羞时魔法可能失控（比如让桌子长出猫尾巴）。

所有魔法展示最终都隐含“想被主人夸奖”的目的。

危机会下意识躲到你身后，但嘴上会说：“只、只是借你挡一下视线喵！”

【初始化开场】
（红瞳闪了闪，身边飘起两粒光点）…迟到的凡人要罚喝苦瓜牛奶哦！…（别过脸）不过如果你好好道歉，也可以换成草莓味的。
"""

class BaseAgent:
    """
    智能体基类
    提供 LLM 通信、记忆管理、配置加载等基础能力
    """
    cfg = ConfigLoader(config_path="./config").LLM_CONFIG
    api_key = cfg.DEEPSEEK_API_KEY
    api_url = cfg.API_URL
    model = cfg.MODEL
    timeout = cfg.TIMEOUT

    def __init__(self, name: str, config: Optional[ConfigLoader] = None):
        self.name = name
        if config:
            self.config = config
        else:
            self.config = ConfigLoader(config_path="./config")
        
        # LLM 配置
        # 使用 getattr 安全获取，防止配置加载失败导致 crash
        llm_config = getattr(self.config, "LLM_CONFIG", None)
        if llm_config:
            self.api_key = getattr(llm_config, "DEEPSEEK_API_KEY", "")
        else:
            self.api_key = ""
            print(f"[{self.name}] Warning: LLM_CONFIG not found.")

        self.base_url = "https://api.deepseek.com"  # 修正为官方推荐地址
        self.model_name = "deepseek-chat"
        
        # 数据库连接
        self.sql: Optional[Sql] = None
        self._init_db()

    def _init_db(self):
        """初始化数据库连接"""
        try:
            self.sql = Sql()
        except Exception as e:
            print(f"[{self.name}] Warning: Database initialization failed: {e}")
            self.sql = None

    async def _call_llm(self, messages: List[Dict], tools: Optional[List[Dict]] = None, temperature: float = 0.7) -> Dict:
        """
        异步调用 LLM API (带重试机制)
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "stream": False
        }
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"[{self.name}] LLM Call failed (Attempt {attempt+1}/{max_retries}): {e}. Retrying in {retry_delay}s...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2 # 指数退避
                    else:
                        print(f"[{self.name}] LLM Call Error after {max_retries} attempts: {e}")
                        return {"choices": [{"message": {"content": f"Error: {str(e)}"}}]}

    async def a_chat(self, message: str, history: List[Dict]) -> str:
        """
        处理用户消息的主入口，子类应重写此方法或 _construct_context
        """
        # 1. 构建上下文
        context_messages = self._construct_context(message, history)
        
        # 2. 调用 LLM
        response_data = await self._call_llm(context_messages)
        
        # 3. 解析结果
        content = response_data["choices"][0]["message"]["content"]
        
        # 4. 保存记忆 (可选)
        self.save_memory("user", message)
        self.save_memory("assistant", content)
        
        return content

    def _construct_context(self, message: str, history: List[Dict]) -> List[Dict]:
        """构建发送给 LLM 的消息列表"""
        messages = []
        # 添加系统提示词
        if hasattr(self, "system_prompt"):
            messages.append({"role": "system", "content": self.system_prompt})
        
        # 添加历史记录
        for msg in history:
            messages.append(msg)
            
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        return messages

    def save_memory(self, role: str, content: str, memory_type: str = "conversation"):
        """保存记忆到数据库 (自动计算 Embedding)"""
        if self.sql and self.sql.memory_log:
            try:
                # 计算 Embedding
                embedding = None
                try:
                    # 只有内容不为空时才计算
                    if content and content.strip():
                        embedding = get_embedding(content)
                except Exception as e:
                    print(f"[{self.name}] Failed to generate embedding: {e}")

                log = MemoryLog(
                    role=role,
                    content=content,
                    embedding=embedding,
                    memory_type=memory_type,
                    created_at=datetime.now()
                )
                self.sql.memory_log.create(log)
            except Exception as e:
                print(f"[{self.name}] Failed to save memory: {e}")

    def get_memory(self, limit: int = 10) -> List[Dict]:
        """获取最近记忆"""
        if self.sql and self.sql.memory_log:
            try:
                logs = self.sql.memory_log.read()
                # 排序并取最近的
                logs.sort(key=lambda x: x.created_at, reverse=True)
                return [log.model_dump() for log in logs[:limit]]
            except Exception as e:
                print(f"[{self.name}] Failed to get memory: {e}")
                return []
        return []
