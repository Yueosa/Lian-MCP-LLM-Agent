# SQL 模块使用文档

## 概述

`mylib.sql` 是一个轻量级的 ORM（对象关系映射）抽象层，基于 PostgreSQL 数据库和 Pydantic 模型。它提供了：

- 🎯 **简洁的 API**: 通过 `Create_`, `Read_`, `Update_`, `Delete_` 动态方法操作数据库
- 🔗 **关系支持**: Python 端的外键关系定义和自动加载关联对象
- 🚀 **类型安全**: 基于 Pydantic 的数据验证和类型提示
- 🔧 **连接池**: 内置数据库连接池管理
- 📊 **JOIN 查询**: 支持多表联合查询

## 快速开始

### 1. 安装依赖

```bash
pip install psycopg2-binary pydantic
```

### 2. 配置数据库连接

在 `mylib/sql/config/config.toml` 中配置：

```toml
[Postgresql]
host = "localhost"
port = 5432
dbname = "your_database"
user = "your_user"
password = "your_password"
```

### 3. 基本使用

```python
from mylib.sql import Sql
from mylib.sql.Model import Task
from mylib.sql.Model.Enum import tasks_status

# 创建 SQL 实例
sql = Sql()

# 创建任务
task = Task(
    user_id="lian",
    title="完成项目文档",
    description="编写完整的 API 文档",
    status=tasks_status.pending
)
created_task = sql.Create_tasks(task)
print(f"创建的任务 ID: {created_task.id}")

# 查询任务
tasks = sql.Read_tasks(user_id="lian")
for task in tasks:
    print(f"任务: {task.title}, 状态: {task.status.value}")

# 更新任务
success = sql.Update_tasks(created_task.id, status=tasks_status.done)
print(f"更新成功: {success}")

# 删除任务
success = sql.Delete_tasks(created_task.id)
print(f"删除成功: {success}")
```

## 核心功能

### 1. CRUD 操作

#### Create - 创建记录

```python
from mylib.sql.Model import Task, TaskStep
from mylib.sql.Model.Enum import tasks_status, task_steps_status

# 创建任务
task = Task(
    user_id="user123",
    title="数据分析任务",
    description="分析用户行为数据",
    status=tasks_status.pending
)
created_task = sql.Create_tasks(task)

# 创建任务步骤
step = TaskStep(
    task_id=created_task.id,
    step_index=1,
    instruction="加载数据",
    status=task_steps_status.pending
)
created_step = sql.Create_task_steps(step)
```

#### Read - 查询记录

```python
# 查询所有任务
all_tasks = sql.Read_tasks()

# 根据条件查询
pending_tasks = sql.Read_tasks(status=tasks_status.pending)
user_tasks = sql.Read_tasks(user_id="user123")

# 根据 ID 查询单条记录
tasks = sql.Read_tasks(id=1)
if tasks:
    task = tasks[0]
    print(task.title)
```

#### Update - 更新记录

```python
# 更新单个字段
success = sql.Update_tasks(task_id, status=tasks_status.running)

# 更新多个字段
success = sql.Update_tasks(
    task_id,
    status=tasks_status.done,
    description="任务已完成"
)
```

#### Delete - 删除记录

```python
# 根据 ID 删除
success = sql.Delete_tasks(task_id)
if success:
    print("删除成功")
```

### 2. 关系查询

#### 定义模型关系

模型之间的关系在 Model 类中定义：

```python
from mylib.sql.Model.BaseModel import RelationalModel, Relationship
from typing import Optional, List

class Task(RelationalModel):
    __table_name__ = "tasks"

    # ... 字段定义 ...

    # 关系定义: 一个任务有多个步骤
    task_steps: Optional[List["TaskStep"]] = Relationship(
        "TaskStep", "one_to_many", back_populates="task"
    )
    tool_calls: Optional[List["ToolCall"]] = Relationship(
        "ToolCall", "one_to_many", back_populates="task"
    )

class TaskStep(RelationalModel):
    __table_name__ = "task_steps"

    # ... 字段定义 ...

    # 关系定义: 多个步骤属于一个任务
    task: Optional["Task"] = Relationship(
        "Task", "many_to_one", back_populates="task_steps", foreign_key="task_id"
    )
```

#### 加载关联对象

```python
# 查询任务并自动加载所有关联的步骤和工具调用
tasks_with_relations = sql.Read_tasks_With_Relations(user_id="user123")

for task in tasks_with_relations:
    print(f"任务: {task.title}")

    # 访问关联的步骤
    steps = task.get_related_object("task_steps")
    if steps:
        for step in steps:
            print(f"  步骤 {step.step_index}: {step.instruction}")

    # 访问关联的工具调用
    tool_calls = task.get_related_object("tool_calls")
    if tool_calls:
        for tool_call in tool_calls:
            print(f"  工具: {tool_call.tool_name}")

# 只加载特定关系
tasks = sql.Read_tasks_With_Relations(
    relations=["task_steps"],  # 只加载步骤，不加载工具调用
    user_id="user123"
)

# 反向查询: 查询步骤并加载关联的任务
steps = sql.Read_task_steps_With_Relations(relations=["task"])
for step in steps:
    task = step.get_related_object("task")
    if task:
        print(f"步骤属于任务: {task.title}")
```

#### 导出包含关联对象的数据

```python
# 查询并加载关联对象
tasks = sql.Read_tasks_With_Relations(user_id="user123")

# 转换为字典（包含关联对象）
for task in tasks:
    task_dict = task.to_dict_with_relations()
    # task_dict 包含嵌套的 task_steps 和 tool_calls 列表
    print(task_dict)

# 排除关联对象
task_dict_only = task.to_dict_with_relations(exclude_relations=True)

# 只包含特定关系
task_dict_partial = task.to_dict_with_relations(
    include_relations=["task_steps"]
)
```

### 3. JOIN 查询

```python
# 简单的 INNER JOIN
results = sql.Join_tasks_task_steps(
    join_condition="tasks.id = task_steps.task_id",
    select_fields=["tasks.title", "tasks.status", "task_steps.instruction"],
    **{"tasks.user_id": "user123"}
)

for result in results:
    print(f"任务: {result['title']}, 步骤: {result['instruction']}")

# LEFT JOIN
results = sql.Join_tasks_task_steps(
    join_condition="tasks.id = task_steps.task_id",
    join_type="LEFT",
    select_fields=["tasks.*", "task_steps.step_index"]
)

# 复杂条件
results = sql.Join_tasks_task_steps(
    join_condition="tasks.id = task_steps.task_id",
    **{
        "tasks.status": "done",
        "task_steps.status": "completed"
    }
)
```

## 更多文档

- [Model 模型系统详解](Model.md)
- [DBRepo 仓库层详解](DBRepo.md)
- [配置说明](Config.md)

_(完整文档见原文件，此处为简化版本)_
