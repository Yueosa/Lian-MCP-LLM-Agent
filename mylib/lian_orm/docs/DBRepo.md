# DBRepo 仓库层文档

###### By - Lian 2025 | Updated 2025-11-24

---

## 概述

`BaseRepo` 是数据库仓库层的抽象基类，为所有具体的数据表仓库提供统一的 CRUD（创建、读取、更新、删除）接口和关系查询功能。它封装了数据库操作的底层细节，提供了类型安全和易用的 API。

## 设计理念

### 分层架构

```
Sql (顶层接口)
    ↓
BaseRepo (仓库抽象层)
    ↓
具体 Repo (TasksRepo, TaskStepsRepo, etc.)
    ↓
DBPool (连接池)
    ↓
PostgreSQL (数据库)
```

### 职责分离

- **Sql 类**: 提供统一的入口和动态方法生成
- **BaseRepo**: 定义通用的数据库操作逻辑
- **具体 Repo**: 配置表特定的信息（表名、允许字段等）
- **Model**: 定义数据结构和验证规则

## BaseRepo 核心功能

### 1. 基本 CRUD 操作

#### create() - 创建记录

```python
def create(self, model_instance: Union[MemoryLog, Task, TaskStep, ToolCall]) -> Any:
    """创建记录
    
    Args:
        model_instance: Pydantic 模型实例
        
    Returns:
        创建后的模型实例（包含生成的 ID）
        
    Raises:
        ValueError: 如果不允许创建操作或参数错误
        Exception: 数据库操作异常
    """
```

**特性**:
- 自动排除 `id`、`created_at`、`updated_at` 等字段
- 自动转换枚举类型为值
- 返回包含新生成 ID 的模型实例
- 使用 RETURNING 子句获取 ID

**示例**:
```python
from mylib.sql.Model import Task
from mylib.sql.Model.Enum import tasks_status

task = Task(
    user_id="user123",
    title="新任务",
    status=tasks_status.pending
)

# 通过 Repo 创建
repo = TasksRepo(connection_pool)
created_task = repo.create(task)
print(f"创建的任务 ID: {created_task.id}")
```

#### read() - 查询记录

```python
def read(self, **kwargs) -> List[Any]:
    """读取记录，支持多字段查询
    
    Args:
        **kwargs: 查询条件，支持 _allowed_get_fields 中的字段
        
    Returns:
        符合条件的模型实例列表
        
    Raises:
        ValueError: 如果不允许读取操作或查询字段无效
    """
```

**特性**:
- 支持多字段组合查询（AND 条件）
- 返回 Pydantic 模型实例列表
- 自动验证查询字段合法性
- 空条件返回所有记录

**示例**:
```python
# 查询所有记录
all_tasks = repo.read()

# 单字段查询
user_tasks = repo.read(user_id="user123")

# 多字段查询
pending_tasks = repo.read(user_id="user123", status="pending")

# 根据 ID 查询
tasks = repo.read(id=1)
if tasks:
    task = tasks[0]
```

#### update() - 更新记录

```python
def update(self, id: int, **kwargs) -> bool:
    """根据 ID 更新记录
    
    Args:
        id: 记录 ID
        **kwargs: 要更新的字段和值
        
    Returns:
        更新是否成功
        
    Raises:
        ValueError: 如果不允许更新操作或参数错误
    """
```

**特性**:
- 只能更新 `_allowed_get_fields` 中的字段
- 自动验证枚举类型的值
- 不允许更新 ID 字段
- 自动转换枚举对象为值

**示例**:
```python
# 更新单个字段
success = repo.update(task_id, status="running")

# 更新多个字段
success = repo.update(
    task_id,
    status="done",
    description="任务已完成"
)

# 使用枚举
from mylib.sql.Model.Enum import tasks_status
success = repo.update(task_id, status=tasks_status.done)
```

#### delete() - 删除记录

```python
def delete(self, id: int) -> bool:
    """根据 ID 删除记录
    
    Args:
        id: 记录 ID
        
    Returns:
        删除是否成功
        
    Raises:
        ValueError: 如果不允许删除操作
    """
```

**特性**:
- 根据 ID 删除单条记录
- 数据库级联删除会自动处理外键关系
- 返回是否成功删除

**示例**:
```python
# 删除记录
success = repo.delete(task_id)
if success:
    print("删除成功")
else:
    print("记录不存在或删除失败")
```

### 2. 关系查询功能（新增）

#### read_with_relations() - 加载关联对象

```python
def read_with_relations(self, relations: Optional[List[str]] = None, **kwargs) -> List[Any]:
    """读取记录并加载关联对象
    
    Args:
        relations: 要加载的关系列表，None 表示加载所有关系
        **kwargs: 查询条件
        
    Returns:
        包含关联对象的模型实例列表
        
    Raises:
        ValueError: 如果不允许读取操作或查询字段无效
    """
```

**工作流程**:
1. 首先执行基本查询获取主记录
2. 检查模型是否继承自 `RelationalModel`
3. 根据模型定义的关系自动加载关联对象
4. 批量查询避免 N+1 问题
5. 将关联对象设置到模型实例中

**示例**:
```python
# 加载所有关系
tasks = repo.read_with_relations(user_id="user123")
for task in tasks:
    steps = task.get_related_object("task_steps")
    tools = task.get_related_object("tool_calls")

# 只加载特定关系
tasks = repo.read_with_relations(
    relations=["task_steps"],  # 只加载步骤
    user_id="user123"
)

# 无条件加载所有记录的所有关系
all_with_relations = repo.read_with_relations()
```

#### 关系加载方法

##### _load_one_to_many_relations() - 一对多关系

加载一个主记录对应的多个子记录（如 Task → TaskSteps）。

**工作原理**:
1. 收集所有主记录的 ID
2. 使用外键批量查询所有子记录
3. 按主记录 ID 分组
4. 设置到对应的主记录中

**示例场景**:
- Task → TaskSteps (一个任务有多个步骤)
- Task → ToolCalls (一个任务有多个工具调用)

##### _load_many_to_one_relations() - 多对一关系

加载多个子记录对应的父记录（如 TaskStep → Task）。

**工作原理**:
1. 收集所有子记录的外键值
2. 批量查询父记录
3. 建立外键到父记录的映射
4. 设置到对应的子记录中

**示例场景**:
- TaskStep → Task (多个步骤属于一个任务)
- ToolCall → Task (多个工具调用属于一个任务)

##### _load_one_to_one_relations() - 一对一关系

加载一对一的关联记录。

**示例场景**:
- User → UserProfile
- Task → TaskSummary

#### join_query() - SQL JOIN 查询

```python
def join_query(self, 
               join_table: str,
               join_condition: str,
               select_fields: Optional[List[str]] = None,
               join_type: str = "INNER",
               **where_conditions) -> List[Dict[str, Any]]:
    """执行 JOIN 查询
    
    Args:
        join_table: 要 JOIN 的表名
        join_condition: JOIN 条件，例如 "tasks.id = task_steps.task_id"
        select_fields: 要选择的字段列表，None 表示选择所有字段
        join_type: JOIN 类型 (INNER, LEFT, RIGHT, FULL)
        **where_conditions: WHERE 条件
        
    Returns:
        查询结果字典列表
    """
```

**特性**:
- 支持所有标准 JOIN 类型
- 灵活的字段选择
- 支持 WHERE 条件过滤
- 返回字典列表（不是模型实例）

**示例**:
```python
# INNER JOIN
results = repo.join_query(
    join_table="task_steps",
    join_condition="tasks.id = task_steps.task_id",
    select_fields=["tasks.title", "task_steps.instruction"]
)

# LEFT JOIN with WHERE
results = repo.join_query(
    join_table="task_steps",
    join_condition="tasks.id = task_steps.task_id",
    join_type="LEFT",
    **{"tasks.status": "done"}
)

# 选择所有字段
results = repo.join_query(
    join_table="task_steps",
    join_condition="tasks.id = task_steps.task_id"
)
```

### 3. 辅助方法

#### get_by_id() - 根据 ID 获取单条记录

```python
def get_by_id(self, id: int) -> Optional[Any]:
    """根据 ID 获取单条记录
    
    Args:
        id: 记录 ID
        
    Returns:
        模型实例或 None
    """
```

**示例**:
```python
task = repo.get_by_id(1)
if task:
    print(task.title)
else:
    print("任务不存在")
```

#### has_field() - 检查字段是否存在

```python
def has_field(self, field_name: str) -> bool:
    """检查表是否包含指定字段
    
    Args:
        field_name: 字段名
        
    Returns:
        是否包含该字段
    """
```

**用途**:
- 验证查询字段有效性
- 动态构建查询条件
- 关系加载时检查外键字段

#### create_table() - 创建数据表

```python
def create_table(self):
    """创建数据库表
    
    Raises:
        ValueError: 如果 CREATE_TABLE_SQL 未设置
        Exception: 数据库操作异常
    """
```

**示例**:
```python
# 初始化表
repo = TasksRepo(connection_pool)
repo.create_table()
```

## 创建自定义 Repo

### 1. 基本模板

```python
from typing import List
from ..Repo.BaseRepo import BaseRepo
from ..Model.YourModel import YourModel


class YourModelRepo(BaseRepo):
    """YourModel 数据仓库"""
    
    # 必须设置的类变量
    _model_class = YourModel
    _allowed_get_fields = [
        "id", "field1", "field2", "field3",
        "created_at", "updated_at"
    ]
    
    # 创建表的 SQL
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS your_table (
        id SERIAL PRIMARY KEY,
        field1 VARCHAR(100),
        field2 TEXT,
        field3 INTEGER,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    # 操作权限控制（可选）
    _can_create = True
    _can_read = True
    _can_update = True
    _can_delete = True
    
    def get_table_name(self) -> str:
        """获取表名"""
        return "your_table"
```

### 2. 实际示例: TasksRepo

```python
from typing import List
from ..Repo.BaseRepo import BaseRepo
from ..Model.Tasks import Task


class TasksRepo(BaseRepo):
    """Tasks 数据仓库"""
    
    _model_class = Task
    _allowed_get_fields = [
        "id", "user_id", "title", "description", 
        "status", "created_at", "updated_at"
    ]
    
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        user_id VARCHAR(64) DEFAULT 'default',
        title TEXT,
        description TEXT,
        status VARCHAR(32) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS tasks_user_id_idx ON tasks (user_id);
    """
    
    def get_table_name(self) -> str:
        return "tasks"
```

### 3. 带外键的 Repo

```python
class TaskStepsRepo(BaseRepo):
    """TaskSteps 数据仓库"""
    
    _model_class = TaskStep
    _allowed_get_fields = [
        "id", "task_id", "step_index", "instruction", 
        "output", "status", "created_at", "updated_at"
    ]
    
    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS task_steps (
        id SERIAL PRIMARY KEY,
        task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
        step_index INTEGER NOT NULL,
        instruction TEXT NOT NULL,
        output TEXT,
        status VARCHAR(32) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    CREATE INDEX IF NOT EXISTS task_steps_task_id_idx ON task_steps (task_id);
    """
    
    def get_table_name(self) -> str:
        return "task_steps"
```

## 配置说明

### 必须配置的类变量

| 变量 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `_model_class` | Type | Pydantic 模型类 | ✅ |
| `_allowed_get_fields` | List[str] | 允许查询/更新的字段列表 | ✅ |
| `CREATE_TABLE_SQL` | str | 创建表的 SQL 语句 | ⚠️ 推荐 |

### 可选配置的类变量

| 变量 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `_can_create` | bool | True | 是否允许创建操作 |
| `_can_read` | bool | True | 是否允许读取操作 |
| `_can_update` | bool | True | 是否允许更新操作 |
| `_can_delete` | bool | True | 是否允许删除操作 |

### _allowed_get_fields 说明

**包含的字段**:
- ✅ 可以用于查询条件的字段
- ✅ 可以用于更新的字段
- ✅ 业务相关的所有字段

**排除的字段**:
- ❌ 关系字段（如 `task_steps`）
- ❌ 不应该被查询/更新的内部字段

**示例**:
```python
_allowed_get_fields = [
    "id",           # 主键
    "user_id",      # 业务字段
    "title",        # 业务字段
    "status",       # 业务字段
    "created_at",   # 时间戳
    "updated_at"    # 时间戳
    # 不包含 "task_steps" 等关系字段
]
```

## 连接池管理

### 连接获取和释放

```python
def _get_cursor(self):
    """获取数据库游标和连接"""
    conn = self._connection_pool.get_connection()
    return conn.cursor(), conn

def _release_cursor(self, cursor, connection):
    """释放数据库游标和连接"""
    cursor.close()
    self._connection_pool.release_connection(connection)
```

**使用模式**:
```python
try:
    cursor, conn = self._get_cursor()
    cursor.execute(sql, params)
    results = cursor.fetchall()
    conn.commit()
    return results
except Exception as e:
    conn.rollback()
    raise e
finally:
    self._release_cursor(cursor, conn)
```

## 权限控制

### 操作权限

可以通过类变量控制每个操作的权限：

```python
class ReadOnlyRepo(BaseRepo):
    """只读仓库示例"""
    
    _can_create = False  # 禁止创建
    _can_update = False  # 禁止更新
    _can_delete = False  # 禁止删除
    _can_read = True     # 允许读取
```

**权限检查**:
```python
def create(self, model_instance):
    if not self._can_create:
        raise ValueError(f"表 '{self.get_table_name()}' 不允许创建操作")
    # ... 执行创建逻辑
```

## 错误处理

### 常见异常

```python
# ValueError - 参数验证错误
try:
    repo.read(invalid_field="value")
except ValueError as e:
    print(f"字段验证失败: {e}")

# Exception - 数据库错误
try:
    repo.create(task)
except Exception as e:
    print(f"数据库错误: {e}")
    # 事务已自动回滚
```

### 验证流程

1. **字段验证**: 检查查询/更新字段是否在 `_allowed_get_fields` 中
2. **权限验证**: 检查操作是否被允许
3. **类型验证**: Pydantic 自动验证数据类型
4. **枚举验证**: 检查枚举值是否合法
5. **数据库约束**: PostgreSQL 级别的约束检查

## 最佳实践

### 1. 字段定义

```python
# ✅ 推荐：明确列出所有可查询字段
_allowed_get_fields = [
    "id", "user_id", "name", "status",
    "created_at", "updated_at"
]

# ❌ 避免：包含关系字段
_allowed_get_fields = [
    "id", "name", "related_items"  # related_items 是关系字段
]
```

### 2. SQL 语句

```python
# ✅ 推荐：使用参数化查询
sql = "SELECT * FROM tasks WHERE user_id = %s"
cursor.execute(sql, [user_id])

# ❌ 避免：字符串拼接（SQL 注入风险）
sql = f"SELECT * FROM tasks WHERE user_id = '{user_id}'"
```

### 3. 事务管理

```python
# ✅ 推荐：使用 try-except-finally
try:
    cursor, conn = self._get_cursor()
    cursor.execute(sql, params)
    conn.commit()
except Exception as e:
    conn.rollback()  # 回滚事务
    raise e
finally:
    self._release_cursor(cursor, conn)  # 总是释放资源
```

### 4. 关系查询优化

```python
# ✅ 推荐：使用 read_with_relations 批量加载
tasks = repo.read_with_relations(user_id="user123")
for task in tasks:
    steps = task.get_related_object("task_steps")
    # 所有步骤已经在一次查询中加载

# ❌ 避免：N+1 查询
tasks = repo.read(user_id="user123")
for task in tasks:
    steps = step_repo.read(task_id=task.id)  # 每个任务一次查询
```

### 5. 索引建议

```sql
-- 外键字段创建索引
CREATE INDEX IF NOT EXISTS task_steps_task_id_idx ON task_steps (task_id);

-- 常用查询字段创建索引
CREATE INDEX IF NOT EXISTS tasks_user_id_idx ON tasks (user_id);
CREATE INDEX IF NOT EXISTS tasks_status_idx ON tasks (status);

-- 复合索引
CREATE INDEX IF NOT EXISTS tasks_user_status_idx ON tasks (user_id, status);
```

## 性能优化

### 1. 批量加载关系

关系加载已优化为批量查询：

```python
# 一对多关系：一次查询获取所有子记录
# 例如: 10 个任务，一次查询获取所有步骤，而不是 10 次查询
```

### 2. 连接池配置

```python
pool = PostgreSQLConnectionPool(
    host="localhost",
    port=5432,
    dbname="mydb",
    user="user",
    password="pass",
    min_connections=2,    # 最小连接数
    max_connections=10    # 最大连接数
)
```

### 3. 查询优化

```python
# 只查询需要的字段（使用 join_query）
results = repo.join_query(
    join_table="task_steps",
    join_condition="tasks.id = task_steps.task_id",
    select_fields=["tasks.id", "tasks.title", "task_steps.instruction"]
)

# 添加必要的 WHERE 条件
tasks = repo.read(status="pending", user_id="user123")
```

## 扩展功能

### 1. 自定义查询方法

```python
class TasksRepo(BaseRepo):
    # ... 基本配置 ...
    
    def find_overdue_tasks(self) -> List[Task]:
        """查找超期任务（自定义查询）"""
        sql = """
        SELECT * FROM tasks 
        WHERE status != 'done' 
        AND created_at < NOW() - INTERVAL '7 days'
        """
        try:
            cursor, conn = self._get_cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            tasks = []
            for row in results:
                row_dict = dict(zip(columns, row))
                tasks.append(self._model_class(**row_dict))
            
            return tasks
        finally:
            self._release_cursor(cursor, conn)
    
    def count_by_status(self, status: str) -> int:
        """统计指定状态的任务数量"""
        sql = "SELECT COUNT(*) FROM tasks WHERE status = %s"
        try:
            cursor, conn = self._get_cursor()
            cursor.execute(sql, [status])
            return cursor.fetchone()[0]
        finally:
            self._release_cursor(cursor, conn)
```

### 2. 批量操作

```python
class TasksRepo(BaseRepo):
    # ... 基本配置 ...
    
    def batch_create(self, tasks: List[Task]) -> List[Task]:
        """批量创建任务"""
        created_tasks = []
        try:
            cursor, conn = self._get_cursor()
            for task in tasks:
                data = task.model_dump(exclude_unset=True, exclude_none=True)
                # ... 插入逻辑 ...
                created_tasks.append(task)
            conn.commit()
            return created_tasks
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_cursor(cursor, conn)
```

## 完整示例

```python
# 创建连接池
from mylib.sql.Repo.DBPool import PostgreSQLConnectionPool

pool = PostgreSQLConnectionPool(
    host="localhost",
    port=5432,
    dbname="mydb",
    user="user",
    password="password"
)

# 初始化 Repo
from mylib.sql.Repo.TasksRepo import TasksRepo
repo = TasksRepo(pool)

# 创建表（首次运行）
repo.create_table()

# 创建任务
from mylib.sql.Model import Task
from mylib.sql.Model.Enum import tasks_status

task = Task(
    user_id="user123",
    title="实现新功能",
    status=tasks_status.pending
)
created_task = repo.create(task)

# 查询任务
tasks = repo.read(user_id="user123")

# 查询任务及其步骤
tasks_with_steps = repo.read_with_relations(
    relations=["task_steps"],
    user_id="user123"
)

# JOIN 查询
results = repo.join_query(
    join_table="task_steps",
    join_condition="tasks.id = task_steps.task_id",
    **{"tasks.user_id": "user123"}
)

# 更新任务
repo.update(created_task.id, status=tasks_status.running)

# 删除任务
repo.delete(created_task.id)
```

## 参考

- [sql.md](sql.md) - SQL 模块使用文档
- [Model.md](Model.md) - 模型系统文档
- [Config.md](Config.md) - 配置说明

## 注意事项

1. **并发安全**: 连接池自动管理并发访问
2. **事务隔离**: 每个操作独立提交，复杂事务需自行管理
3. **外键约束**: 数据库层面的外键约束会自动生效
4. **级联删除**: ON DELETE CASCADE 会自动删除关联记录
5. **索引优化**: 为外键和常用查询字段创建索引
6. **连接释放**: 必须在 finally 块中释放连接
