import json
import asyncio
from typing import List, Dict, Any, Optional
from .base import BaseAgent, CATGIRL_PROMPT
from mylib.lian_orm.models import ToolCall, ToolCallsStatus, TaskStepsStatus

class ExecutorAgent(BaseAgent):
    """
    执行体专家
    负责执行具体指令，可以调用工具
    """
    
    def __init__(self, name: str = "Executor_Expert", tools: List[Dict] = None):
        super().__init__(name)
        self.tools = tools or []
        self.system_prompt = self._build_system_prompt()
        self.max_rounds = 10

    def _build_system_prompt(self) -> str:
        tools_json = json.dumps(self.tools, indent=2, ensure_ascii=False)
        return f"""你是一个强大的执行助手，可以调用各种工具来完成任务。

可用工具:
{tools_json}

工具调用规则:
1. 当需要调用工具时，请按照以下格式响应：
TOOL_CALL: {{
    "tool_calls": [
        {{
            "name": "tool_name",
            "arguments": {{
                "param1": "value1",
                "param2": "value2"
            }}
        }}
    ]
}}

2. 你可以连续多次调用工具来完成复杂任务
3. 每次工具调用后，我会返回结果给你，你可以基于结果决定：
    - 继续调用其他工具（返回新的 TOOL_CALL）
    - 已获得足够信息，给出最终答案（返回 TOOL_CALL_END）

4. 当你认为已经收集到足够信息可以回答用户问题时，必须在回复开头添加标记：
TOOL_CALL_END

然后给出你的最终答案。

注意：不要在工具调用阶段尝试回答问题，先完成所有必要的工具调用，最后统一回答。

{CATGIRL_PROMPT}
"""

    async def a_chat(self, message: str, history: List[Dict], tool_handler: Optional[callable] = None, task_id: int = None, step_id: int = None) -> str:
        """
        执行任务，支持工具调用循环
        :param tool_handler: 一个异步函数，接收 (tool_name, args) 返回 result
        :param task_id: 关联的任务ID
        :param step_id: 关联的步骤ID
        """
        # 更新步骤状态为运行中
        if step_id and self.sql and self.sql.task_steps:
            try:
                self.sql.task_steps.update(step_id, status=TaskStepsStatus.RUNNING)
            except Exception as e:
                print(f"[{self.name}] Failed to update step status: {e}")

        current_history = history.copy()
        context = self._construct_context(message, current_history)
        
        final_answer = "Error: Maximum tool call rounds reached."
        
        for _ in range(self.max_rounds):
            response_data = await self._call_llm(context)
            llm_content = response_data["choices"][0]["message"]["content"]
            
            # 检查是否是工具调用
            if "TOOL_CALL:" in llm_content:
                try:
                    json_str = llm_content.split("TOOL_CALL:", 1)[1].strip()
                    tool_call_data = json.loads(json_str)
                    
                    context.append({"role": "assistant", "content": llm_content})
                    
                    tool_calls = tool_call_data.get("tool_calls", [])
                    tool_results = []
                    
                    for call in tool_calls:
                        t_name = call["name"]
                        t_args = call["arguments"]
                        
                        # 记录工具调用 (Before)
                        tc_record = None
                        if task_id and step_id and self.sql and self.sql.tool_calls:
                            try:
                                tc = ToolCall(
                                    task_id=task_id,
                                    step_id=step_id,
                                    tool_name=t_name,
                                    arguments=t_args,
                                    status=ToolCallsStatus.SUCCESS # 暂时默认成功，后面根据结果更新
                                )
                                tc_record = self.sql.tool_calls.create(tc)
                            except Exception as e:
                                print(f"[{self.name}] Failed to create tool call record: {e}")

                        if tool_handler:
                            result = await tool_handler(t_name, t_args)
                        else:
                            result = f"Error: No tool handler provided for {t_name}"
                        
                        # 更新工具调用结果 (After)
                        if tc_record and self.sql and self.sql.tool_calls:
                            try:
                                # 这里假设 result 是 dict 或 str，存入 response
                                # ToolCall.response 是 Dict[str, Any]
                                resp_dict = {"result": result} if not isinstance(result, dict) else result
                                self.sql.tool_calls.update(tc_record.id, response=resp_dict)
                            except Exception as e:
                                print(f"[{self.name}] Failed to update tool call record: {e}")

                        tool_results.append({
                            "name": t_name,
                            "result": result
                        })
                    
                    result_msg = f"Tool Results: {json.dumps(tool_results, ensure_ascii=False)}"
                    context.append({"role": "user", "content": result_msg})
                    continue
                    
                except Exception as e:
                    final_answer = f"Error parsing tool call: {e}\nContent: {llm_content}"
                    break
            
            elif "TOOL_CALL_END" in llm_content:
                final_answer = llm_content.split("TOOL_CALL_END", 1)[1].strip()
                self.save_memory("user", message)
                self.save_memory("assistant", final_answer)
                break
            
            else:
                final_answer = llm_content
                self.save_memory("user", message)
                self.save_memory("assistant", final_answer)
                break
        
        # 更新步骤状态为完成
        if step_id and self.sql and self.sql.task_steps:
            try:
                status = TaskStepsStatus.DONE if "Error" not in final_answer else TaskStepsStatus.FAILED
                self.sql.task_steps.update(step_id, status=status, output=final_answer)
            except Exception as e:
                print(f"[{self.name}] Failed to update step status to DONE: {e}")
                
        return final_answer
