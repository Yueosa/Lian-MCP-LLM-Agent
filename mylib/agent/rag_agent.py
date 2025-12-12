import json
from typing import List, Dict, Any
from .base import BaseAgent
from mylib.kit.Lfind.embedding import get_embedding
from mylib.kernel.Lenum.lian_orm import MemoryLogMemoryType

class RAGAgent(BaseAgent):
    """
    RAG 总结专家
    负责检索数据库里的记忆，并为其他专家提供精简的上下文支持
    """
    
    def __init__(self, name: str = "RAG_Expert"):
        super().__init__(name)
        self.system_prompt = """你是一个专业的 RAG (Retrieval-Augmented Generation) 记忆总结专家。
你的职责不是直接回答用户问题，而是根据检索到的历史记忆片段，为其他智能体（如规划专家、执行专家）提供有价值的背景信息。

请分析检索到的记忆片段（包含对话、总结、反思、计划等），提取与当前用户请求相关的关键信息。
如果记忆中包含过往的成功经验、偏好设置或相关计划，请重点强调。
如果检索到的内容与当前请求无关，请忽略。

输出格式：
请输出一段简洁的背景信息摘要，不需要引用来源，直接陈述事实。
如果没有相关信息，请输出 "无相关历史记忆"。
"""

    async def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """检索相关记忆"""
        if not self.sql or not self.sql.memory_log:
            return []
            
        try:
            # 获取查询向量
            # 注意：get_embedding 是同步的，如果需要异步可能需要 run_in_executor，这里暂时直接调用
            # 实际生产中建议将其放入线程池
            embedding = get_embedding(query)
            
            # 数据库向量检索
            results = self.sql.memory_log.search_by_embedding(embedding, top_k)
            return results
        except Exception as e:
            print(f"[{self.name}] Retrieval failed: {e}")
            return []

    async def a_chat(self, message: str, history: List[Dict]) -> str:
        """
        执行 RAG 流程：检索 -> 总结
        """
        # 1. 检索
        records = await self.retrieve(message, top_k=5)
        
        if not records:
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
        full_message = f"""用户当前请求：
{message}

检索到的历史记忆：
{memory_context}

请根据上述记忆，总结对处理当前请求有帮助的信息：
"""
        # 调用父类方法请求 LLM
        # 注意：这里我们不把检索过程产生的 prompt 加入到长期记忆中，
        # 而是只返回总结结果。父类 a_chat 会保存 (user_msg, response)
        # 但这里的 user_msg 是 full_message，这可能导致记忆污染。
        # 我们应该重写 a_chat 避免将 full_message 存入 user 记忆，或者只存原始 message。
        
        # 复用父类的 _call_llm 和 _construct_context，但不调用父类 a_chat 以控制记忆存储
        
        context_messages = self._construct_context(full_message, history)
        response_data = await self._call_llm(context_messages)
        content = response_data["choices"][0]["message"]["content"]
        
        # RAG 的结果通常作为中间结果，是否需要存入 memory_log 取决于设计
        # 这里我们选择存入，类型可以标记为 SUMMARY 或 REFLECTION ?
        # 或者保持默认 CONVERSATION
        self.save_memory("user", message) # 存原始请求
        self.save_memory("assistant", content, memory_type="summary") # 存总结结果
        
        return content
