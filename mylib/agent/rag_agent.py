import json
from typing import List, Dict, Any
from .base import BaseAgent
from mylib.kit.Lfind.embedding import get_embedding
from mylib.kernel.Lenum.lian_orm import MemoryLogMemoryType
from mylib.kit.Loutput import Loutput, FontColor8

import asyncio

class RAGAgent(BaseAgent):
    """
    RAG 总结专家
    负责检索数据库里的记忆，并为其他专家提供精简的上下文支持
    """
    
    def __init__(self, name: str = "RAG_Expert"):
        super().__init__(name)
        self.lo = Loutput()
        self.system_prompt = """你是一个专业的 RAG (Retrieval-Augmented Generation) 记忆总结专家。
你的职责不是直接回答用户问题，而是根据检索到的历史记忆片段，为其他智能体（如规划专家、执行专家）提供有价值的背景信息。

请分析检索到的记忆片段（包含对话、总结、反思、计划等），提取与当前用户请求相关的关键信息。
如果记忆中包含过往的成功经验、偏好设置或相关计划，请重点强调。
如果检索到的内容与当前请求无关，请忽略。

输出格式：
请输出一段简洁的背景信息摘要，不需要引用来源，直接陈述事实。
如果没有相关信息，请输出 "无相关历史记忆"。
不要输出任何多余的寒暄或解释。
"""

    async def extract_keywords(self, query: str) -> str:
        """使用 LLM 提取搜索关键词"""
        self.lo.lput(f"[{self.name}] Step 1: Extracting keywords...", font_color=FontColor8.CYAN)
        prompt = f"""请分析以下用户请求，提取出用于数据库向量检索的关键信息。
用户请求: "{query}"

请忽略语气词和无关信息，只提取核心实体、概念或意图。
将提取的关键词组合成一个简洁的搜索语句。
直接输出搜索语句，不要包含任何解释。
"""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self._call_llm(messages)
            keyword_query = response["choices"][0]["message"]["content"].strip()
            self.lo.lput(f"[{self.name}] Extracted keywords: {keyword_query}", font_color=FontColor8.CYAN)
            return keyword_query
        except Exception as e:
            self.lo.lput(f"[{self.name}] Keyword extraction failed: {e}", font_color=FontColor8.RED)
            return query

    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """检索相关记忆"""
        if not self.sql or not self.sql.memory_log:
            self.lo.lput(f"[{self.name}] Memory log not initialized.", font_color=FontColor8.YELLOW)
            return []
            
        try:
            # 1. 提取关键词
            search_query = await self.extract_keywords(query)
            
            # 2. 获取查询向量 (直接调用，不使用 ThreadPoolExecutor，按用户要求一步一步来)
            self.lo.lput(f"[{self.name}] Step 2: Generating embedding...", font_color=FontColor8.CYAN)
            # 注意：如果 get_embedding 是同步的，这里会阻塞。但为了满足用户"不使用async流程"的要求(或者理解为简化流程)，直接调用。
            embedding = get_embedding(search_query)
            
            # 3. 数据库向量检索
            self.lo.lput(f"[{self.name}] Step 3: Searching database...", font_color=FontColor8.CYAN)
            results = self.sql.memory_log.search_by_embedding(embedding, top_k)
            self.lo.lput(f"[{self.name}] Found {len(results)} memory fragments.", font_color=FontColor8.CYAN)
            return results
        except Exception as e:
            self.lo.lput(f"[{self.name}] Retrieval failed: {e}", font_color=FontColor8.RED)
            return []

    async def a_chat(self, message: str, history: List[Dict]) -> str:
        """
        执行 RAG 流程：检索 -> 总结
        """
        self.lo.lput(f"[{self.name}] Starting RAG flow...", font_color=FontColor8.BLUE)
        
        # 1. 检索
        records = await self.retrieve(message, top_k=5)
        
        if not records:
            self.lo.lput(f"[{self.name}] No records found.", font_color=FontColor8.YELLOW)
            return "无相关历史记忆"
            
        # 2. 格式化记忆上下文
        memory_context = ""
        for i, record in enumerate(records):
            # 解析类型
            m_type = record.get('memory_type', 'unknown')
            content = record.get('content', '')
            score = record.get('score', 0)
            
            memory_context += f"--- 记忆片段 {i+1} (类型: {m_type}, 相关度: {score:.2f}) ---\n{content}\n\n"
            
        # 3. 构建 Prompt 让 LLM 总结
        self.lo.lput(f"[{self.name}] Step 4: Summarizing context...", font_color=FontColor8.CYAN)
        full_message = f"""用户当前请求：
{message}

检索到的历史记忆：
{memory_context}

请根据上述记忆，总结对处理当前请求有帮助的信息：
"""
        
        context_messages = self._construct_context(full_message, history)
        response_data = await self._call_llm(context_messages)
        content = response_data["choices"][0]["message"]["content"]
        
        self.lo.lput(f"[{self.name}] RAG Summary generated.", font_color=FontColor8.GREEN)
        
        # 存入记忆
        self.save_memory("user", message) 
        self.save_memory("assistant", content, memory_type="summary")
        
        return content
