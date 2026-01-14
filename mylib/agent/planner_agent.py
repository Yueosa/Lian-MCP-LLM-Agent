import json
from typing import List, Dict, Optional
from .base import BaseAgent
from .prompts import PLANNER_SYSTEM_PROMPT
from mylib.lian_orm.models import Task, TaskStep, TasksStatus, TaskStepsStatus, MemoryLogMemoryType
from mylib.kit.Loutput import Loutput, FontColor8


class PlannerAgent(BaseAgent):
    """
    任务步骤规划专家 (星盘占卜师)
    负责将用户请求拆解为可执行的步骤
    """
    
    def __init__(self, name: str = "Planner_Lian", tools: Optional[List[Dict]] = None):
        super().__init__(name)
        self.lo = Loutput()
        self.tools = tools or []
        # 使用新的增强提示词
        self.system_prompt = PLANNER_SYSTEM_PROMPT

    async def a_chat(self, message: str, history: List[Dict]) -> Dict:
        """
        规划任务
        返回解析后的 JSON 对象
        """
        self.lo.lput(f"[{self.name}] Generating plan...", font_color=FontColor8.MAGENTA)
        
        # 构建包含工具列表的请求
        tools_info = ""
        if self.tools:
            tool_names = [t.get("name", "unknown") for t in self.tools]
            tools_info = f"\n\n【重要】可用工具列表（你的规划必须只使用这些工具）:\n{', '.join(tool_names)}\n\n工具详情:\n"
            for tool in self.tools:
                tools_info += f"- {tool.get('name')}: {tool.get('description', 'No description')[:100]}\n"
        else:
            tools_info = "\n\n【注意】未检测到可用工具，请生成纯文本回答或建议用户启动 MCP Server。\n"
        
        enriched_message = message + tools_info
        # 【修复】Planner 不使用对话历史，避免被其他 Agent 的人设污染
        # Planner 只负责生成 JSON 格式的执行计划，应保持客观中立
        content = await super().a_chat(enriched_message, [], memory_type=MemoryLogMemoryType.PLAN)
        
        result = {}
        # 尝试解析 JSON
        try:
            # 提取 JSON 部分 (防止 LLM 输出多余文本)
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = content[start:end]
                result = json.loads(json_str)
                self.lo.lput(f"[{self.name}] Plan generated successfully.", font_color=FontColor8.GREEN)
            else:
                result = {"error": "No JSON found", "raw_content": content}
                self.lo.lput(f"[{self.name}] No JSON found in response.", font_color=FontColor8.RED)
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON", "raw_content": content}
            self.lo.lput(f"[{self.name}] Invalid JSON response.", font_color=FontColor8.RED)

        # 如果解析成功且有 steps，保存到数据库
        if "steps" in result and self.sql and self.sql.tasks:
            try:
                # 1. 创建任务
                task = Task(
                    title=message[:50], 
                    description=message, 
                    status=TasksStatus.PENDING
                )
                created_task = self.sql.tasks.create(task)
                result['task_id'] = created_task.id
                
                # 2. 创建步骤
                for step in result['steps']:
                    ts = TaskStep(
                        task_id=created_task.id,
                        step_index=step.get('step_index', 0),
                        instruction=step.get('instruction', ''),
                        status=TaskStepsStatus.PENDING
                    )
                    created_step = self.sql.task_steps.create(ts)
                    step['step_id'] = created_step.id # 回填 ID 供执行器使用
                
                self.lo.lput(f"[{self.name}] Plan saved to DB (Task ID: {created_task.id}).", font_color=FontColor8.GREEN)
                    
            except Exception as e:
                self.lo.lput(f"[{self.name}] Failed to save task plan: {e}", font_color=FontColor8.RED)
                
        return result
