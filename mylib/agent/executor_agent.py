import json
import asyncio
from typing import List, Dict, Any, Optional
from .base import BaseAgent
from .prompts import build_executor_prompt
from mylib.lian_orm.models import ToolCall, ToolCallsStatus, TaskStepsStatus, MemoryLogRole, MemoryLogMemoryType
from mylib.kit.Loutput import Loutput, FontColor8


class ExecutorAgent(BaseAgent):
    """
    执行体专家 (魔力执行官)
    负责执行具体指令，可以调用工具
    """
    
    def __init__(self, name: str = "Executor_Ran", tools: List[Dict] = None):
        super().__init__(name)
        self.lo = Loutput()
        self.tools = tools or []
        # 使用新的增强提示词构建器
        self.system_prompt = build_executor_prompt(self.tools)
        self.max_rounds = 100

    async def a_chat(self, message: str, history: List[Dict], tool_handler: Optional[callable] = None, task_id: int = None, step_id: int = None) -> str:
        """
        执行任务，支持工具调用循环
        :param tool_handler: 一个异步函数，接收 (tool_name, args) 返回 result
        :param task_id: 关联的任务ID
        :param step_id: 关联的步骤ID
        """
        return await self._execute_with_lifecycle(
            self._executor_process, message, history, tool_handler, task_id, step_id
        )
    
    async def _executor_process(self, message: str, history: List[Dict], tool_handler: Optional[callable] = None, task_id: int = None, step_id: int = None) -> str:
        """执行器核心处理逻辑"""
        # 更新步骤状态为运行中
        if step_id and self.sql and self.sql.task_steps:
            try:
                self.sql.task_steps.update(step_id, status=TaskStepsStatus.RUNNING)
            except Exception as e:
                self.lo.lput(f"[{self.name}] Failed to update step status: {e}", font_color="red")
        
        # Ensure message is not empty to avoid 400 Bad Request
        if not message or not message.strip():
            message = "Please execute the current step."
        
        # 【修复】Executor 不使用对话历史，避免被其他 Agent 的人设污染
        # Executor 只负责执行具体任务和调用工具，应保持客观中立
        current_history = []
        # Executor 接收的是系统下发的指令，虽然是系统指令，但为了符合 API 规范（避免多个 system 消息），这里 role 设为 user
        context = self._construct_context(message, current_history, role="user")
        
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
                                    status=ToolCallsStatus.SUCCESS
                                )
                                tc_record = self.sql.tool_calls.create(tc)
                            except Exception as e:
                                print(f"[{self.name}] Failed to create tool call record: {e}")

                        if tool_handler:
                            result = await tool_handler(t_name, t_args)
                        else:
                            result = f"Error: No tool handler provided for {t_name}"
                        
                        # --- 结果截断逻辑 ---
                        result_str = json.dumps(result, ensure_ascii=False)
                        max_len = 10000
                        if len(result_str) > max_len:
                            truncated_result = result_str[:max_len] + f"... (Truncated, total length: {len(result_str)})"
                            try:
                                result = json.loads(truncated_result)
                            except:
                                result = truncated_result
                            
                            self.lo.lput(f"[{self.name}] Tool output truncated ({len(result_str)} -> {max_len})", font_color=FontColor8.YELLOW)
                        # -------------------

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
                    # 工具执行结果，role 设为 user，模拟用户（或系统）反馈的 Observation，避免使用 API 不支持的 "tool" role
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
