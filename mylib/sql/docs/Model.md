# SQL Model 模型系统文档

###### By - Lian 2025 | Updated 2025-11-24

---

## 概述

`Model` 基于 `Pydantic` 实现，定义了数据表的结构和Python对象的映射关系。新版本引入了 `RelationalModel` 基类，支持外键关系定义和关联对象管理。

## 核心概念

### 1. 模型继承体系

```
BaseModel (Pydantic)
    ↓
RelationalModel (mylib.sql)
    ↓
Task, TaskStep, ToolCall, MemoryLog (业务模型)
```

### 2. 关系类型

- **one_to_many**: 一对多（如 Task → TaskStep）
- **many_to_one**: 多对一（如 TaskStep → Task）
- **one_to_one**: 一对一

## 基础模型模板

### 简单模型（不需要关系）

```python
from pydantic import Field
from mylib.sql.Model.BaseModel import RelationalModel
from datetime import datetime

class SimpleModel(RelationalModel):
    """简单模型示例"""
    
    __table_name__ = "simple_table"  # 可选，默认使用类名小写
    
    # 字段定义
    id: int = Field(None, description="主键 ID")
    name: str = Field(..., description="名称", max_length=100)
    status: str = Field(default="active", description="状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def __repr__(self) -> str:
        """自定义表示"""
        return f"<SimpleModel(id={self.id}, name='{self.name}')>"
```

### 带关系的模型

```python
from typing import Optional, List, TYPE_CHECKING
from pydantic import Field
from mylib.sql.Model.BaseModel import RelationalModel, Relationship

# 避免循环导入
if TYPE_CHECKING:
    from .RelatedModel import RelatedModel

class ComplexModel(RelationalModel):
    """带关系的复杂模型"""
    
    __table_name__ = "complex_table"
    
    # 基本字段
    id: int = Field(None, description="主键 ID")
    name: str = Field(..., description="名称")
    related_id: int = Field(..., description="关联ID（外键）")
    
    # 关系定义
    related_items: Optional[List["RelatedModel"]] = Relationship(
        "RelatedModel",           # 目标模型名称
        "one_to_many",           # 关系类型
        back_populates="parent"  # 反向关系字段
    )
    
    parent: Optional["ParentModel"] = Relationship(
        "ParentModel",
        "many_to_one",
        foreign_key="related_id",  # 外键字段
        back_populates="children"
    )
```

## 实际示例: Task 模型

```python
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pydantic import Field
from .Enum import tasks_status
from .BaseModel import RelationalModel, Relationship

if TYPE_CHECKING:
    from .TaskSteps import TaskStep
    from .ToolCalls import ToolCall


class Task(RelationalModel):
    """任务数据模型 - 支持关系的 Pydantic BaseModel"""
    
    __table_name__ = "tasks"
    
    # 基本字段
    id: int = Field(None, description="主键 ID")
    user_id: str = Field(default="default", description="用户 ID")
    title: str = Field(default="", description="任务标题")
    description: str = Field(default="", description="任务描述")
    status: tasks_status = Field(default=tasks_status.pending, description="任务状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    # 关系定义
    task_steps: Optional[List["TaskStep"]] = Relationship(
        "TaskStep", "one_to_many", back_populates="task"
    )
    tool_calls: Optional[List["ToolCall"]] = Relationship(
        "ToolCall", "one_to_many", back_populates="task"
    )
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = False
        json_encoders = {
            tasks_status: lambda v: v.value,
            datetime: lambda v: v.isoformat()
        }
    
    def __repr__(self) -> str:
        """自定义表示"""
        title_preview = self.title[:50] + "..." if len(self.title) > 50 else self.title
        return (
            f"<Task(id={self.id}, user_id='{self.user_id}', "
            f"status={self.status.value}, title='{title_preview}')>"
        )
```

## 模型字段类型

### 常用字段类型

```python
from pydantic import Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ExampleModel(RelationalModel):
    # 整数
    id: int = Field(None, description="主键")
    count: int = Field(default=0, ge=0, description="计数（非负）")
    
    # 字符串
    name: str = Field(..., description="必填字符串")
    title: str = Field(default="", max_length=200, description="标题")
    
    # 可选字段
    optional_field: Optional[str] = Field(None, description="可选字符串")
    
    # 枚举
    status: MyEnum = Field(default=MyEnum.pending, description="状态枚举")
    
    # 日期时间
    created_at: datetime = Field(default_factory=datetime.now)
    
    # 浮点数
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="评分 0-1")
    
    # JSON/字典
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    # 列表
    tags: List[str] = Field(default_factory=list, description="标签列表")
    embedding: Optional[List[float]] = Field(None, description="向量")
```

### Field 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `default` | 默认值 | `default="pending"` |
| `default_factory` | 默认值工厂函数 | `default_factory=datetime.now` |
| `description` | 字段描述 | `description="用户ID"` |
| `...` | 必填字段 | `Field(...)` |
| `None` | 可选字段 | `Field(None)` |
| `max_length` | 最大长度 | `max_length=100` |
| `min_length` | 最小长度 | `min_length=1` |
| `ge` | 大于等于 | `ge=0` |
| `le` | 小于等于 | `le=100` |
| `gt` | 大于 | `gt=0` |
| `lt` | 小于 | `lt=100` |

## RelationalModel 特性

### 1. 关系定义

```python
# 一对多关系
children: Optional[List["ChildModel"]] = Relationship(
    "ChildModel",              # 目标模型
    "one_to_many",            # 关系类型
    back_populates="parent"   # 反向字段
)

# 多对一关系
parent: Optional["ParentModel"] = Relationship(
    "ParentModel",
    "many_to_one",
    foreign_key="parent_id",  # 当前模型中的外键字段
    back_populates="children"
)

# 一对一关系
profile: Optional["ProfileModel"] = Relationship(
    "ProfileModel",
    "one_to_one",
    foreign_key="profile_id"
)
```

### 2. 访问关联对象

```python
# 创建任务
task = sql.Create_tasks(task_obj)

# 查询任务并加载关联对象
tasks = sql.Read_tasks_With_Relations(id=task.id)
task = tasks[0]

# 访问关联的步骤
steps = task.get_related_object("task_steps")
if steps:
    for step in steps:
        print(step.instruction)

# 访问所有关联对象
related_objects = task.get_related_objects()
# 返回: {"task_steps": [...], "tool_calls": [...]}

# 检查是否已加载
if task.has_related_object("task_steps"):
    print("步骤已加载")
```

### 3. 导出数据

```python
# 基本导出（不含关系）
task_dict = task.model_dump()

# 导出包含所有关联对象
task_with_relations = task.to_dict_with_relations()
# {
#     "id": 1,
#     "title": "任务",
#     "task_steps": [
#         {"id": 1, "instruction": "步骤1"},
#         {"id": 2, "instruction": "步骤2"}
#     ],
#     "tool_calls": [...]
# }

# 排除关联对象
task_only = task.to_dict_with_relations(exclude_relations=True)

# 只包含特定关系
task_partial = task.to_dict_with_relations(
    include_relations=["task_steps"]
)
```

### 4. 手动设置关联对象

```python
# 查询任务
task = sql.Read_tasks(id=1)[0]

# 手动查询步骤
steps = sql.Read_task_steps(task_id=task.id)

# 设置关联对象
task.set_related_object("task_steps", steps)

# 清除关联对象
task.clear_related_objects()
```

## 枚举类型

### 定义枚举

```python
from enum import Enum

class tasks_status(str, Enum):
    """任务状态枚举"""
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"

class task_steps_status(str, Enum):
    """步骤状态枚举"""
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"
```

### 使用枚举

```python
# 创建模型时使用枚举
task = Task(
    title="测试任务",
    status=tasks_status.pending  # 使用枚举值
)

# 更新时可以使用枚举或字符串
sql.Update_tasks(task.id, status=tasks_status.running)
sql.Update_tasks(task.id, status="done")  # 也支持字符串

# 访问枚举值
print(task.status.value)  # 输出: "pending"
print(task.status)        # 输出: tasks_status.pending
```

## Config 配置

### 常用配置项

```python
class Config:
    """Pydantic 配置"""
    
    # 是否使用枚举的值而不是枚举对象
    use_enum_values = False  # 推荐 False，保留枚举类型
    
    # JSON 序列化器
    json_encoders = {
        datetime: lambda v: v.isoformat(),
        tasks_status: lambda v: v.value,
    }
    
    # 允许任意类型（用于关系字段）
    arbitrary_types_allowed = True
    
    # 验证赋值
    validate_assignment = True
    
    # 额外字段策略
    extra = "forbid"  # 禁止额外字段
```

## 最佳实践

### 1. 使用 TYPE_CHECKING 避免循环导入

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .OtherModel import OtherModel

class MyModel(RelationalModel):
    other: Optional["OtherModel"] = Relationship(...)
```

### 2. 合理使用默认值

```python
# ✅ 推荐
created_at: datetime = Field(default_factory=datetime.now)
tags: List[str] = Field(default_factory=list)

# ❌ 避免（可变默认值）
tags: List[str] = Field(default=[])  # 危险！所有实例共享同一个列表
```

### 3. 字段验证

```python
from pydantic import validator, Field

class Task(RelationalModel):
    priority: int = Field(..., ge=1, le=5, description="优先级 1-5")
    
    @validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('标题不能为空')
        return v.strip()
```

### 4. 关系命名约定

```python
# 一对多：使用复数
task_steps: Optional[List["TaskStep"]] = ...

# 多对一：使用单数
task: Optional["Task"] = ...

# 反向关系名称保持一致
# Task.task_steps ←→ TaskStep.task (back_populates)
```

## 完整示例

```python
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pydantic import Field, validator
from mylib.sql.Model.BaseModel import RelationalModel, Relationship
from mylib.sql.Model.Enum import project_status

if TYPE_CHECKING:
    from .Task import Task
    from .User import User


class Project(RelationalModel):
    """项目模型 - 完整示例"""
    
    __table_name__ = "projects"
    
    # 基本字段
    id: int = Field(None, description="主键 ID")
    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    description: str = Field(default="", description="项目描述")
    owner_id: str = Field(..., description="项目负责人ID（外键）")
    status: project_status = Field(default=project_status.planning)
    priority: int = Field(default=3, ge=1, le=5, description="优先级 1-5")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # 关系定义
    tasks: Optional[List["Task"]] = Relationship(
        "Task", "one_to_many", back_populates="project"
    )
    owner: Optional["User"] = Relationship(
        "User", "many_to_one", foreign_key="owner_id"
    )
    
    # 验证器
    @validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('项目名称不能为空')
        return v.strip()
    
    @validator('priority')
    def validate_priority(cls, v):
        if v < 1 or v > 5:
            raise ValueError('优先级必须在 1-5 之间')
        return v
    
    class Config:
        use_enum_values = False
        json_encoders = {
            project_status: lambda v: v.value,
            datetime: lambda v: v.isoformat()
        }
        arbitrary_types_allowed = True
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', status={self.status.value})>"
    
    # 自定义方法
    def get_active_tasks(self):
        """获取活动任务"""
        tasks = self.get_related_object("tasks")
        if tasks:
            return [t for t in tasks if t.status != "completed"]
        return []
```

## 参考

- [sql.md](sql.md) - SQL 模块使用文档
- [DBRepo.md](DBRepo.md) - 仓库层文档
- [Pydantic 官方文档](https://docs.pydantic.dev/)
