# RAG Agent
# 负责查询记忆库, 并返回总结
from typing import List, Dict, Any

from .base import BaseAgent

from mylib.config import ConfigLoader
from mylib.kit.Loutput import FontColor8
from mylib.kernel.Lenum import LLMRole


class Caster(BaseAgent):
    cfg = ConfigLoader(config_path="./config/response_schema.toml")
    USER_INPUT = cfg.PROMPT.USER_INPUT  # 用户请求
    RAG_MEMORY = cfg.PROMPT.RAG_MEMORY  # 检索到的历史记忆
    RAG_PROMPT = cfg.PROMPT.RAG_SUMMARY # 总结历史记录提示词

    def __init__(self):
        super().__init__()
        self.role = LLMRole.CASTER
        self.description = self.cfg.Caster.Response.SYSTEM_PROMPT   # 自我认知
        self.goals = self.cfg.Caster.Response.KEY_PROMPT            # 关键词任务

    def think(self, user_input):
        """检索 -> 总结"""
        self.lo.lput(f"[{self.agent_id}](Caster) Starting RAG flow...", font_color=FontColor8.BLUE)
        records = self._retrieve(user_input, top_k=5)

        if not records:
            self.lo.lput(f"[{self.agent_id}](Caster) No records found.", font_color=FontColor8.YELLOW)
            return "无相关历史记忆"
        
        # TODO#1: 统一格式化数据库返回的结构信息, 后续需要撰写专门的处理算法
        memory_context = ""
        for i, record in enumerate(records):
            m_type = record.get("memory_type", "unknown")
            content = record.get("content", '')
            score = record.get("score", 0)

            memory_context += f"--- 记忆片段 {i+1} (类型: {m_type}, 相关度: {score:.2f}) ---\n{content}\n\n"

        # 最终总结
        self.lo.lput(f"[{self.agent_id}](Caster) Summarizing context...", font_color=FontColor8.CYAN)

        # TODO#2: 期望实现一个build方法可以正确处理参数
        #       是否需要添加Enum规范?
        #       build 需要的参数类型是一个List[LLMContext]
        #       LLMContext应该是一个{LLMContextType: Any}
        #       Any非常广泛, 既可以是一个实例/局部变量, 也可以是他们的字符串拼接
        #           除Caster之外的子类通常只维护一个memory, 也许keyword可以手动维护?
        #           思路: 选择将fields作为类元数据维护? 验证对于其余子类是否可行并进行泛化
        #           
        #       保持了硬编码, 睡一觉有思路了再来补吧
        #   都怪恋没有提前封装好数据协议!
        msg = [
            {
                "system": self.description
            },
            {
                "user": self.USER_INPUT + user_input + self.RAG_MEMORY + memory_context + self.RAG_PROMPT
            }
        ]

        fly_content = self._call_llm(msg)["choices"][0]["message"]["content"]

        self.lo.lput(f"[{self.agent_id}](Caster) RAG Summary generated.", font_color=FontColor8.GREEN)

        return fly_content

    def _retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """根据用户输入获取RAG记录"""
        if not self.db or not self.db.memory_log:
            self.lo.lput(f"[{self.agent_id}](Caster) Memory log not initialized.", font_color=FontColor8.YELLOW)
            return []
        
        try:
            self.lo.lput(f"[{self.agent_id}](Caster) Generating embedding...", font_color=FontColor8.CYAN)
            embedding = self._get_emb(self._extract_keywords(query))

            self.lo.lput(f"[{self.agent_id}](Caster) Searching database...", font_color=FontColor8.CYAN)
            results = self.db.memory_log.search_by_embedding(embedding, top_k)
            self.lo.lput(f"[{self.agent_id}](Caster) Found {len(results)} memory fragments.", font_color=FontColor8.CYAN)
            return results
        except Exception as e:
                self.lo.lput(f"[{self.agent_id}](Caster) Retrieval failed: {e}", font_color=FontColor8.RED)
                return []

    def _extract_keywords(self, query: str) -> str:
        """将用户输入解析为关键词语句"""
        self.lo.lput(f"[{self.agent_id}](Caster) Extract keywords ...", font_color=FontColor8.CYAN)
        
        # msg = self._new_build("self.goals", "self.USER_INPUT", query)

        msg = [
            {
                "user": self.goals + self.USER_INPUT + query
            }
        ]

        try:
            keyworkd_query = self._call_llm(msg)["choices"][0]["message"]["content"].strip()
            self.lo.lput(f"[{self.agent_id}](Caster) Extracted keywords: {keyworkd_query}", font_color=FontColor8.CYAN)
            return keyworkd_query
        except Exception as e:
            self.lo.lput(f"[{self.agent_id}](Caster) Keyword extraction failed: {e}", font_color=FontColor8.RED)
            return query
