import asyncio
from typing import Iterable, List, Optional

from mylib.lian_orm import Sql, Task, TaskStep, TasksStatus, TaskStepsStatus


class TaskPipeline:
    """轻量任务流封装，用于 Agent 模式的 Task/TaskStep 管理。"""

    def __init__(self, sql: Optional[Sql] = None) -> None:
        self.sql = sql or Sql()

    async def create_task(self, title: str, description: str = "") -> int:
        task = Task(title=title, description=description, status=TasksStatus.PENDING)
        created = await asyncio.to_thread(self.sql.tasks.create, task)
        return created.id if created else -1

    async def add_steps(self, task_id: int, instructions: Iterable[str]) -> List[int]:
        step_ids: List[int] = []
        for idx, instr in enumerate(instructions, start=1):
            step = TaskStep(task_id=task_id, instruction=instr, status=TaskStepsStatus.PENDING, step_index=idx)
            created = await asyncio.to_thread(self.sql.task_steps.create, step)
            if created:
                step_ids.append(created.id)
        return step_ids

    async def mark_step(self, step_id: int, output: str, status: TaskStepsStatus = TaskStepsStatus.DONE) -> None:
        await asyncio.to_thread(self.sql.task_steps.update, id=step_id, output=output, status=status)

    async def mark_task(self, task_id: int, status: TasksStatus) -> None:
        await asyncio.to_thread(self.sql.tasks.update, id=task_id, status=status)
