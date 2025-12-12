import json
from typing import List, Dict
from .base import BaseAgent
from mylib.lian_orm.models import Task, TaskStep, TasksStatus, TaskStepsStatus

class PlannerAgent(BaseAgent):
    """
    任务步骤规划专家
    负责将用户请求拆解为可执行的步骤
    """
    
    def __init__(self, name: str = "Planner_Expert"):
        super().__init__(name)
        self.system_prompt = """你是一个专业的任务规划专家。
你的任务是将用户的复杂请求拆解为一系列逻辑严密、可执行的步骤。

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
        content = await super().a_chat(message, history)
        
        result = {}
        # 尝试解析 JSON
        try:
            # 提取 JSON 部分 (防止 LLM 输出多余文本)
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = content[start:end]
                result = json.loads(json_str)
            else:
                result = {"error": "No JSON found", "raw_content": content}
        except json.JSONDecodeError:
            result = {"error": "Invalid JSON", "raw_content": content}

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
                    
            except Exception as e:
                print(f"[{self.name}] Failed to save task plan: {e}")
                
        return result
