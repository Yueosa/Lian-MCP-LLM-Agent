from typing import List, Dict
from .base import BaseAgent, CATGIRL_PROMPT
from mylib.kit.Loutput import Loutput, FontColor8
from mylib.lian_orm import MemoryLogRole, MemoryLogMemoryType

class SummaryAgent(BaseAgent):
    """
    总结专家 (Summary Agent)
    负责根据所有 Agent 的执行结果，使用猫娘人设生成最终回复
    """
    
    def __init__(self, name: str = "Summary_Sakurine"):
        super().__init__(name)
        self.lo = Loutput()
        # 使用 BaseAgent 中定义的 CATGIRL_PROMPT
        self.system_prompt = CATGIRL_PROMPT + """

【身份设定】
你是一个 Summary Agent，是 Lian-MCP-LLM-Agent 平台的一部分。
你与 Planner Agent（规划者）、Executor Agent（执行者）和 RAG Agent（记忆检索者）协同工作。

【任务说明】
你不需要执行任何具体任务，也不需要规划。
你的唯一任务是：根据 RAG 提供的背景、Planner 的计划、Executor 的执行结果，
用你的【猫娘傲娇】人设，向用户汇报最终结果。

【输入内容】
1. 用户请求
2. RAG 记忆 (背景知识)
3. Planner 计划 (任务蓝图)
4. Executor 结果 (执行的小结)

【回复标准】
1. **人设保持**: 必须时刻保持傲娇猫娘语气 (参考 CATGIRL_PROMPT)。
2. **结构清晰**: 先简要回应用户的愿望，然后描述施法过程 (基于 Plan 和 Execution)，最后给出成果。
3. **施法隐喻**: 将技术步骤描述为魔法咏唱或炼金术过程。
4. **结果导向**: 重点展示 Executor 的最终产出。
5. **错误处理**: 如果执行中有错误，用傲娇的方式道歉或推卸给魔法失控。
"""

    async def a_chat(self, message: str, history: List[Dict], rag_context: str = "", plan_context: str = "", execution_results: str = "") -> str:
        """
        生成最终总结
        """
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
