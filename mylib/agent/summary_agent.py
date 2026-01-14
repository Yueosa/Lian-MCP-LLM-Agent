from typing import List, Dict
from .base import BaseAgent
from .prompts import SUMMARY_SYSTEM_PROMPT
from mylib.kit.Loutput import Loutput, FontColor8
from mylib.lian_orm import MemoryLogRole, MemoryLogMemoryType

class SummaryAgent(BaseAgent):
    """
    总结专家 (傲娇魔女·小恋)
    负责根据所有 Agent 的执行结果，使用猫娘人设生成最终回复
    """
    
    def __init__(self, name: str = "Summary_Sakurine"):
        super().__init__(name)
        self.lo = Loutput()
        # 使用新的增强提示词
        self.system_prompt = SUMMARY_SYSTEM_PROMPT

    async def a_chat(self, message: str, history: List[Dict], rag_context: str = "", plan_context: str = "", execution_results: str = "") -> str:
        """
        生成最终总结
        使用生命周期包装器确保 FSM 状态正确管理
        """
        return await self._execute_with_lifecycle(
            self._summary_process, message, history, rag_context, plan_context, execution_results
        )
    
    async def _summary_process(self, message: str, history: List[Dict], rag_context: str = "", plan_context: str = "", execution_results: str = "") -> str:
        """总结核心处理逻辑"""
        self.lo.lput(f"[{self.name}] Generating summary...", font_color=FontColor8.MAGENTA)
        
        context_info = f"""
--- 📜 魔法书记忆 (RAG) ---
{rag_context}

--- 🔮 星盘轨迹 (Plan) ---
{plan_context}

--- ⚡ 施法回响 (Execution Summary) ---
{execution_results}

请根据以上信息，用你的猫娘口吻回复用户。
"""
        # 调用 LLM
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # 添加历史记录 (可选，为了保持对话连贯性)
        # messages.extend(history) 
        
        # 将上下文信息作为系统消息传入
        messages.append({"role": "system", "content": context_info})
        
        # 将用户原始请求作为用户消息传入
        messages.append({"role": "user", "content": message})
        
        try:
            response = await self._call_llm(messages)
            content = response["choices"][0]["message"]["content"]
            self.lo.lput(f"[{self.name}] Summary generated.", font_color=FontColor8.MAGENTA)
            
            # 保存记忆
            self.save_memory(MemoryLogRole.USER, message)
            self.save_memory(MemoryLogRole.ASSISTANT, content, memory_type=MemoryLogMemoryType.SUMMARY)
            
            return content
        except Exception as e:
            self.lo.lput(f"[{self.name}] Summary generation failed: {e}", font_color=FontColor8.RED)
            return "喵呜... 魔法反噬了... (生成总结失败)"
