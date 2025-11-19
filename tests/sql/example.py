from .sql import Sql
from .Model import Task, TaskStep
from .Model.Enum import TaskStatus, StepStatus # type: ignore


# 创建ORM实例
sql = Sql(config_path="path/to/config.toml")

# 创建任务
task = Task(
    user_id=1,
    content="完成ORM系统实现",
    status=TaskStatus.TODO
)
created_task = sql.Create_tasks(task)

# 创建任务步骤
step = TaskStep(
    task_id=created_task.id,
    content="实现外键关系映射",
    status=StepStatus.TODO
)
created_step = sql.Create_tasksteps(step)

# 查询任务并加载关联的步骤
tasks_with_steps = sql.Read_tasks_With_Relations(relations=["steps"], user_id=1)
for task in tasks_with_steps:
    print(f"任务: {task.content}")
    steps = task.get_related_object("steps")
    if steps:
        for step in steps:
            print(f"  步骤: {step.content}")

# 查询任务步骤并加载关联的任务
steps_with_task = sql.Read_tasksteps_With_Relations(relations=["task"])
for step in steps_with_task:
    task = step.get_related_object("task")
    if task:
        print(f"步骤: {step.content}, 所属任务: {task.content}")
