# 📦 `lian_orm` 模块完整介绍

> 此文档面向 **模块开发者**，全面介绍模块架构、实现细节与使用方法

###### By - Lian 2025 | Updated 2025-11-29

---

## 一、项目概述

`lian_orm` 是一个基于 **PostgreSQL + pgvector** 的轻量级 ORM 抽象层，专为 LLM Agent 系统设计，用于管理对话记录、任务流程、工具调用等数据。

### 核心技术栈
- **数据库**: PostgreSQL 16 + pgvector 扩展
- **Python ORM**: 基于 Pydantic 的自定义实现
- **连接管理**: psycopg2 连接池

---

## 二、目录结构与职责

```
lian_orm/
├── __init__.py          # 顶层暴露接口
├── orm.py               # 🔥 核心入口类 Sql
├── config/              # 配置管理
│   ├── loader.py
│   └── sql_config.toml
├── database/            # 数据库连接层
│   ├── pool.py          # 连接池管理
│   └── client.py        # SQL 执行客户端
├── models/              # 数据模型
│   ├── core/            # 基础模型类
│   │   ├── BaseModel.py # RelationalModel 支持关系
│   │   ├── Enum.py      # 状态枚举定义
│   │   └── Type.py      # 类型定义
│   └── entities/        # 实体模型
│       ├── Tasks.py
│       ├── TaskSteps.py
│       ├── ToolCalls.py
│       └── MemoryLogs.py
├── repository/          # 仓库层 (CRUD)
│   ├── BaseRepo.py      # 基础仓库抽象类
│   ├── TasksRepo.py
│   ├── TaskStepsRepo.py
│   ├── ToolCallsRepo.py
│   └── MemoryLogRepo.py
├── schema/              # Schema 管理
│   ├── manager.py       # Schema 管理器
│   ├── localfile/       # 本地 SQL 文件解析
│   │   ├── LML_SQL.sql  # DDL 定义
│   │   ├── parser.py
│   │   └── tokenizer.py
│   └── metadata/        # 元数据模型
└── mapper/              # 数据转换层
    ├── converter.py     # Python <-> SQL 转换
    └── types.py         # 类型映射
```

---

## 三、顶层暴露 API (`__init__.py`)

```python
from mylib.lian_orm import (
    # 🔥 核心入口
    Sql,                        # ORM 主类
    
    # 📋 实体模型
    Task,                       # 任务模型
    TaskStep,                   # 任务步骤模型
    ToolCall,                   # 工具调用模型
    MemoryLog,                  # 记忆日志模型
    
    # 🏷️ 状态枚举
    tasks_status,               # pending/running/done/failed
    task_steps_status,          # pending/running/done/failed
    tool_calls_status,          # success/failed
    memory_log_role,            # user/assistant/system/llm
    memory_log_memory_type,     # conversation/summary/reflection/...
    
    # 🔗 关系枚举
    relationship,               # one_to_one/one_to_many/many_to_one
    on_update,                  # CASCADE/SET_NULL/RESTRICT/NO_ACTION
    on_delete                   # CASCADE/SET_NULL/RESTRICT/NO_ACTION
)
```

---

## 四、核心类详解

### 1️⃣ `Sql` 类 - 顶层入口 (`orm.py`)

这是整个模块的**唯一入口点**，提供动态的 CRUD 操作。

#### 初始化方式
```python
# 方式1: 使用默认配置文件
sql = Sql()

# 方式2: 指定配置文件
sql = Sql(config_path="/path/to/config.toml")

# 方式3: 直接传参
sql = Sql(
    host="localhost",
    port=5432,
    dbname="lml_sql",
    user="admin",
    passwd="password"
)
```

#### 动态方法 (通过 `__getattr__` 实现)
```python
# ✅ CRUD 操作 - 格式: {操作}_{表名}
sql.Create_tasks(task_instance)     # 创建
sql.Read_tasks(id=1)                # 读取
sql.Update_tasks(id=1, status=...)  # 更新
sql.Delete_tasks(id=1)              # 删除

# ✅ 关联查询
sql.Read_tasks_With_Relations(relations=["task_steps"])

# ✅ JOIN 查询
sql.Join_tasks_task_steps(
    join_condition="tasks.id = task_steps.task_id",
    select_fields=["tasks.title", "task_steps.instruction"],
    join_type="LEFT"
)
```

#### 工具方法
```python
sql.test_connect()                   # 测试连接
sql.get_supported_tables()           # 获取所有表名
sql.get_table_fields("tasks")        # 获取表字段信息
sql.get_table_create_sql("tasks")    # 获取建表 SQL
```

---

### 2️⃣ 数据库连接层

#### `PostgreSQLConnectionPool` (pool.py)
```python
# 封装 psycopg2.pool.ThreadedConnectionPool
pool = PostgreSQLConnectionPool(minconn=1, maxconn=10, host=..., ...)
conn = pool.get_connection()
pool.release_connection(conn)
pool.clear_connections()
```

#### `DatabaseClient` (client.py)
```python
# 提供上下文管理的 SQL 执行接口
client = DatabaseClient(pool)

client.execute(sql, params)              # INSERT/UPDATE/DELETE
client.execute_returning(sql, params)    # INSERT ... RETURNING id
client.fetch_all(sql, params)            # SELECT 返回 List[Dict]
client.fetch_one(sql, params)            # SELECT 返回单个 Dict
```

---

### 3️⃣ 模型层

#### `RelationalModel` (BaseModel.py)
所有实体的基类，继承自 Pydantic `BaseModel`：

```python
class Task(RelationalModel):
    __table_name__ = "tasks"
    
    id: Optional[int] = Field(None)
    title: str = Field(default="")
    status: tasks_status = Field(default=tasks_status.pending)
    
    # 关系定义
    task_steps: Optional[List["TaskStep"]] = Field(
        default=None, exclude=True,
        description=RelationshipField("TaskStep", "one_to_many", back_populates="task")
    )
```

**关键方法**:
```python
task.get_related_object("task_steps")      # 获取已加载的关联对象
task.set_related_object("task_steps", [...])
task.has_related_object("task_steps")
task.get_relationships()                    # 获取所有关系定义
```

---

### 4️⃣ 仓库层 (`BaseRepo`)

所有 Repo 的基类，提供统一 CRUD 接口：

```python
class BaseRepo(ABC, Generic[T]):
    _model_class: Type[T]           # 对应的模型类
    _allowed_get_fields = []        # 允许查询的字段
    CREATE_TABLE_SQL = None         # 建表 SQL
    
    # 权限控制
    _can_create = True
    _can_read = True
    _can_update = True
    _can_delete = True
    
    # CRUD 方法
    def create(self, model_instance: T) -> T
    def read(self, **kwargs) -> List[T]
    def update(self, id: int, **kwargs) -> bool
    def delete(self, id: int) -> bool
    def get_by_id(self, id: int) -> Optional[T]
    
    # 关联查询
    def read_with_relations(self, relations=None, **kwargs) -> List[T]
    def join_query(self, join_table, join_condition, ...) -> List[Dict]
```

---

## 五、数据表结构

[README.md (点击跳转)](./README.md)

---

## 六、完整工作流程图

```
用户代码调用
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│                        Sql 类                              │
│   __getattr__ 动态路由: Create_tasks → TasksRepo.create     │
└────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│                     BaseRepo.create()                      │
│   1. model_instance.model_dump() 导出数据                   │
│   2. DataConverter.python_to_sql() 类型转换                 │
│   3. 构建 INSERT SQL                                       │
└────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│                    DatabaseClient                          │
│   execute_returning(sql, params)                           │
└────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│               PostgreSQLConnectionPool                     │
│   get_connection() → cursor.execute() → release()          │
└────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│                   PostgreSQL 数据库                         │
└────────────────────────────────────────────────────────────┘
```

```Mermaid
flowchart LR

    A[用户代码调用] --> B["Sql 类
    `__getattr__ 动态路由`
Create_tasks → TasksRepo.create"]

    B --> C["BaseRepo.create()
1. model_dump()
2. python_to_sql()
3. 构建 INSERT SQL"]

    C --> D["DatabaseClient
execute_returning(sql, params)"]

    D --> E["PostgreSQLConnectionPool
get_connection() → execute() → release()"]

    E --> F[PostgreSQL 数据库]

```

---

## 七、使用示例

### 基本 CRUD
```python
from mylib.lian_orm import Sql, Task, tasks_status

# 初始化
sql = Sql()

# 创建任务
task = Task(title="完成报告", description="年度总结", user_id="user_001")
created_task = sql.Create_tasks(task)
print(f"Created task ID: {created_task.id}")

# 读取任务
tasks = sql.Read_tasks(user_id="user_001")
for t in tasks:
    print(t.title, t.status)

# 更新状态
sql.Update_tasks(id=created_task.id, status=tasks_status.running)

# 删除
sql.Delete_tasks(id=created_task.id)
```

### 关联查询
```python
# 读取任务并加载关联的步骤
tasks = sql.Read_tasks_With_Relations(
    relations=["task_steps"],
    user_id="user_001"
)

for task in tasks:
    steps = task.get_related_object("task_steps")
    print(f"Task: {task.title}, Steps: {len(steps) if steps else 0}")
```

### JOIN 查询
```python
results = sql.Join_tasks_task_steps(
    join_condition="tasks.id = task_steps.task_id",
    select_fields=["tasks.title", "task_steps.instruction", "task_steps.status"],
    join_type="INNER",
    **{"tasks.status": "running"}
)
```

---

## 八、配置说明

配置文件 `sql_config.toml`:
```toml
[Postgresql]
host = "localhost"
port = 5432
dbname = "sql"
user = "admin"
password = "your_password"
```

---

## 九、扩展指南

### 添加新表
1. 在 `LML_SQL.sql` 添加 DDL
2. 在 `models/entities/` 创建新模型类
3. 在 `repository/` 创建新 Repo 类
4. 在 `orm.py` 的 `_load_repos()` 中注册

---

> 此模块设计遵循 **分层架构**: 连接池 → 客户端 → 仓库 → 模型，职责清晰，便于维护和扩展。
