from typing import List, Dict, Any
from datetime import datetime
from .base import BaseAgent
from .prompts import RAG_SYSTEM_PROMPT
from .prompts.rag_prompt import KEYWORD_EXTRACTION_PROMPT
from mylib.kit.Lfind.embedding import get_embedding
from mylib.kit.Loutput import Loutput, FontColor8
from mylib.lian_orm import MemoryLogRole, MemoryLogMemoryType


class RAGAgent(BaseAgent):
    """
    RAG 总结专家 (全知魔导书)
    负责检索数据库里的记忆，并为其他专家提供精简的上下文支持
    """
    
    def __init__(self, name: str = "RAG_Sakurine"):
        super().__init__(name)
        self.lo = Loutput()
        # 使用新的增强提示词
        self.system_prompt = RAG_SYSTEM_PROMPT

    async def extract_keywords(self, query: str) -> str:
        """使用 LLM 提取搜索关键词"""
        self.lo.lput(f"[{self.name}] Step 1: Extracting keywords...", font_color=FontColor8.CYAN)
        prompt = KEYWORD_EXTRACTION_PROMPT.format(query=query)
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
        使用生命周期包装器确保 FSM 状态正确管理
        """
        return await self._execute_with_lifecycle(
            self._rag_process, message, history
        )
    
    async def _rag_process(self, message: str, history: List[Dict]) -> str:
        """RAG 核心处理逻辑"""
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
        # 【重要】RAG Agent 不使用对话历史，避免被其他 Agent 的人设污染
        # 只使用系统提示词 + 当前检索任务，保持客观中立
        self.lo.lput(f"[{self.name}] Step 4: Summarizing context...", font_color=FontColor8.CYAN)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"""当前时间: {current_time}
用户当前请求：
{message}

检索到的历史记忆：
{memory_context}

请根据上述记忆，总结对处理当前请求有帮助的信息：
"""
        
        # 【修复】不传入 history，避免被其他 Agent 的回复风格污染
        # RAG 只负责检索和摘要，应保持客观中立
        context_messages = self._construct_context(full_message, [], role="system")
        response_data = await self._call_llm(context_messages)
        content = response_data["choices"][0]["message"]["content"]
        
        self.lo.lput(f"[{self.name}] RAG Summary generated.", font_color=FontColor8.GREEN)
        
        # 存入记忆
        self.save_memory(MemoryLogRole.USER, message) 
        self.save_memory(MemoryLogRole.ASSISTANT, content, memory_type=MemoryLogMemoryType.SUMMARY)
        
        return content
