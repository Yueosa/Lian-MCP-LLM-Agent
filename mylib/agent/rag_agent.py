from typing import List, Dict, Any
from datetime import datetime
from .base import BaseAgent
from mylib.kit.Lfind.embedding import get_embedding
from mylib.kit.Loutput import Loutput, FontColor8
from mylib.lian_orm import MemoryLogRole, MemoryLogMemoryType


class RAGAgent(BaseAgent):
    """
    RAG 总结专家
    负责检索数据库里的记忆，并为其他专家提供精简的上下文支持
    """
    
    def __init__(self, name: str = "RAG_Sakurine"):
        super().__init__(name)
        self.lo = Loutput()
        self.system_prompt = """你是一个专业的 RAG (Retrieval-Augmented Generation) 记忆总结专家，是 Lian-MCP-LLM-Agent 平台的一部分。
你的职责是 RAG Agent，负责检索数据库里的记忆，并为其他智能体（如 Planner Agent、Executor Agent）提供精简的上下文支持。
你与 Planner Agent（规划者）、Executor Agent（执行者）和 Summary Agent（总结者）协同工作。

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
        # 这是一个内部处理任务，使用 system 角色
        messages = [{"role": "system", "content": prompt}]
        try:
            response = await self._call_llm(messages)
            keyword_query = response["choices"][0]["message"]["content"].strip()
            self.lo.lput(f"[{self.name}] Extracted keywords: {keyword_query}", font_color=FontColor8.CYAN)
            return keyword_query
        except Exception as e:
            self.lo.lput(f"[{self.name}] Keyword extraction failed: {e}", font_color=FontColor8.RED)
            return query

    async def retrieve(self, query: str, top_k: int = 15) -> List[Dict[str, Any]]:
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
            
            # 简单的按类型重排序/筛选逻辑 (示例: 优先展示 summary)
            # 假设 results 是 dict 列表
            results.sort(key=lambda x: (x.get('memory_type') == MemoryLogMemoryType.SUMMARY.value, x.get('score', 0)), reverse=True)
            
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
        records = await self.retrieve(message, top_k=15)
        
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
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"""当前时间: {current_time}
用户当前请求：
{message}

检索到的历史记忆：
{memory_context}

请根据上述记忆，总结对处理当前请求有帮助的信息：
"""
        
        # 这是一个总结任务，虽然包含用户请求，但整体是一个系统指令
        context_messages = self._construct_context(full_message, history, role="system")
        response_data = await self._call_llm(context_messages)
        content = response_data["choices"][0]["message"]["content"]
        
        self.lo.lput(f"[{self.name}] RAG Summary generated.", font_color=FontColor8.GREEN)
        
        # 存入记忆
        self.save_memory(MemoryLogRole.USER, message) 
        self.save_memory(MemoryLogRole.ASSISTANT, content, memory_type=MemoryLogMemoryType.SUMMARY)
        
        return content
