import json
from typing import List, Dict
from .base import BaseAgent
from mylib.lian_orm.models import Task, TaskStep, TasksStatus, TaskStepsStatus, MemoryLogMemoryType
from mylib.kit.Loutput import Loutput, FontColor8

class PlannerAgent(BaseAgent):
    """
    任务步骤规划专家
    负责将用户请求拆解为可执行的步骤
    """
    
    def __init__(self, name: str = "Planner_Lian"):
        super().__init__(name)
        self.lo = Loutput()
        self.system_prompt = """你是一个专业的任务规划专家。
你的任务是将用户的复杂请求拆解为一系列逻辑严密、可执行的步骤。

【输入说明】
你将接收到用户的请求以及 RAG 提供的背景信息。
请务必利用 RAG 中的背景信息（如过往经验、偏好、相关知识）来优化你的计划。

重要原则：
1. 你的计划将由一个自动化的执行器（Executor）执行，它无法与用户进行交互。
2. 严禁生成需要"询问用户"、"等待用户输入"或"确认用户意图"的步骤。
3. 如果信息不足，请在计划的第一步尝试使用工具获取信息，或者直接生成一个步骤说明"由于缺少XX信息，无法继续执行"。
4. 步骤应当具体、明确，可以直接映射到工具调用或代码执行。
5. 绝对不要输出任何闲聊、问候或解释性文字。只输出 JSON。

输出必须是严格的 JSON 格式，包含一个 steps 数组，每个 step 包含：
- step_index: 步骤序号
- instruction: 具体指令
- expected_output: 预期输出

示例格式：
{
    "steps": [
        {
            "step_index": 1,
            "instruction": "搜索关于 Python 3.13 的新特性",
            "expected_output": "Python 3.13 特性列表"
        },
        {
            "step_index": 2,
            "instruction": "总结这些特性",
            "expected_output": "特性总结文本"
        }
    ]
}
"""

    async def a_chat(self, message: str, history: List[Dict]) -> Dict:
        """
        规划任务
        返回解析后的 JSON 对象
        """
        self.lo.lput(f"[{self.name}] Generating plan...", font_color=FontColor8.MAGENTA)
        content = await super().a_chat(message, history, memory_type=MemoryLogMemoryType.PLAN)
        
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
