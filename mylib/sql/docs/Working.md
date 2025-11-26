**Working（开发者向） — SQL 模块工作说明**

目标：向模块开发者说明 `mylib/sql` 的内部构成、各子模块职责、三类数据源（Python 模型、.sql 文件、远端 PostgreSQL）之间的协作关系，以及常见扩展/调试流程。

注意：本文档面向已经熟悉 Python 与基本 SQL 的开发者，侧重职责边界与开发实践提示，而非 API 手册（API 详见 `mylib/sql/docs/` 下的其它文档）。

## 一、整体高层概览

模块分为五个主要部分：

- `config`：配置加载与环境解析（连接字符串、pool 配置、SQL 文件路径等）
- `Model`：基于 Pydantic 的数据模型与关系声明（RelationalModel）
- `Repo`：仓库层（Repository）封装 CRUD、关系加载、join_query 等逻辑
- `Sql`：SQL 元数据解析（从 `.sql` 提取表/列信息）、SQL 辅助类型与工具
- `sql.py`：模块入口与运行时工厂，负责绑定各 Repo、提供动态方法（Create*/Read*/Update*/Delete*, Read*\*\_With_Relations, Join*\_\_\_）

三类“数据源/定义”共同驱动模块行为：

1. Python 端定义的模型（`mylib/sql/Model/*.py`） — 模型结构、关系、验证规则。
2. `.sql` 文件（`mylib/sql/Sql/*.sql`） — 数据库建表语句，SqlLoader 从中提取真实的列/类型元信息。
3. 远端 PostgreSQL 数据库 — 真实存储与运行时执行（连接池由 `Repo/DBPool.py` 管理）。

## 二、模块逐项说明

1. `config`

- 位置：`mylib/sql/config` + 顶层 `mylib/sql/config/sql_config.toml`
- 作用：读取配置（Postgres 连接信息、pool 大小、SQL 文件目录等），并对外提供统一配置对象
- 输出/接口：`get_config()` 风格的方法（或 config 对象）供 `DBPool` 和 `Sql` 使用
- 注意：更改连接配置需同时考虑测试环境/生产环境区分，配置文件示例在 `sql_config.example.toml`

2. `Model`

- 位置：`mylib/sql/Model`（包括 `BaseModel.py`, `Tasks.py`, `TaskSteps.py`, `ToolCalls.py`, `Enum.py`）
- 作用：使用 Pydantic 来定义字段、默认值、类型、枚举与关系（通过 `RelationalModel` + `Relationship` 描述）
- 关键职责：
  - 定义模型字段与类型（影响 ORM 在读取数据库时的类型转换）
  - 声明关系（one_to_many、many_to_one 等）以便 `Repo.read_with_relations` 批量加载
  - 提供序列化方法如 `model_dump()` 或 `to_dict_with_relations()`（便于导出）
- 扩展指引：新增表时创建对应 Pydantic 模型，使用 `__table_name__` 保持与 SQL 表名一致；关系字段建议在 Field.description 中使用 `Relationship(...)` 以便自动提取

3. `Repo`

- 位置：`mylib/sql/Repo`（`BaseRepo.py`、各种具体 Repo）
- 作用：数据库访问层，负责 SQL 组装与执行、事务管理、连接池使用、以及高阶操作（关系加载、join 查询）
- 关键职责：
  - 提供统一的 CRUD 接口（Create*\*/Read*\_/Update\_\_/Delete\_\*），并在必要时序列化 JSON 字段
  - 提供 `read_with_relations`：批量加载并注入关联对象，避免 N+1 查询
  - 提供 `join_query`：按前端构建的条件生成 JOIN SQL 并返回字典结果
  - 管理数据库特定细节：字段白名单、表名解析、SQL 占位符
- 注意：Repo 偏向“策略/实现”层，尽量不要把业务逻辑放在 Repo 中，业务逻辑应上移至服务/任务层

4. `Sql`（SqlLoader / SqlBase）

- 位置：`mylib/sql/Sql`（`SqlLoader.py`, `SqlBase.py`, `LML_SQL.sql`）
- 作用：解析 `.sql` 文件以提取表/列元信息，生成 `TableMeta`、`ColumnMeta` 等元数据供 Repo/Model 使用
- 关键职责：
  - 读取 `.sql`（支持注释、带括号的复杂定义）并构建表/列元数据
  - 提供字段类型与 Python 类型的映射（便于 Pydantic 校验）
  - 为自动生成接口和 `_allowed_get_fields` 提供依据
- 扩展指引：当你在数据库层新增/修改表结构时，优先同步 `.sql`，以便 SqlLoader 能正确反映表结构

5. `sql.py`（模块运行时入口）

- 位置：`mylib/sql/sql.py`
- 作用：运行时的“门面”（Facade），在初始化时加载所有 Repo，创建 `Sql` 对象并导出动态方法
- 关键职责：
  - 在 `__getattr__` 中动态解析 `Create_tasks`、`Read_tasks`、`Read_tasks_With_Relations`、`Join_tasks_task_steps` 等方法并委托到对应 Repo
  - 绑定运行时的 Repo 实例（由 `Repo` 使用 `DBPool` 获取连接）
  - 提供便捷工具：`get_supported_tables()`, `get_table_fields()` 等运行时查询元数据的方法
- 注意：`sql.py` 主要做路由与暴露接口，不做复杂 DB 细节处理（由 Repo 完成）

## 三、三类底层定义/数据源如何协作

核心思想：

- `Python 模型`（Model）: 定义行为契约（字段名、类型、关系）—— 驱动代码层的验证、序列化、关系声明。
- `.sql 文件`（SqlLoader）: 定义真实数据库结构（列名、约束、索引）—— 驱动元数据、表字段白名单、SQL 生成时的字段校验。
- `远端 PostgreSQL`：最终的数据存储与执行运行时，提供事务、索引、外键约束、性能保障。

运行时数据流（简化）：

1. 开发者在 `Model` 中定义或更新模型（字段、关系）。同时在 `.sql` 中定义/同步表结构。
2. 启动时，`sql.py` 初始化：读取 `config`，SqlLoader 解析 `.sql` 并生成表元数据；创建 Repo 实例并注册。
3. 应用调用 `Sql` 门面方法（例如 `Create_tasks(task)`）：
   - `sql.py` 将调用委派给 `Repo`（tasks repo）
   - `Repo` 使用 `TableMeta` 和模型字段检查构建 INSERT/UPDATE SQL（对 dict/json 做 json.dumps）
   - `Repo` 从 `DBPool` 获取连接，执行 SQL 并返回基于 Pydantic 的模型实例
4. 关系查询（`Read_*_With_Relations`）将触发 Repo 的批量加载流程：先按父对象批量查询，再根据关系字段批量查询子对象并注入，最终返回包含关系的模型实例

## 四、协作框架图（文本/ASCII）

运行时（简化）:

    +-----------+     config      +-----------+     parse SQL    +------------+
    |  app/user | --------------> |  sql.py   | ---------------> | SqlLoader  |
    +-----------+                 +-----------+                  +------------+
    	|                              |                             |
    	| call Create_/Read_*          | load repos & metadata       | read .sql => TableMeta
    	v                              v                             v
    +----------------+           +----------------+           +------------------+
    |  Sql (Facade)  | <-------- |   Repo pool    | <-------- |  TableMeta etc.  |
    +----------------+           +----------------+           +------------------+
    	|  delegate                    | get connection
    	v                              v
    +----------------+           +----------------+
    |  Repo (tasks)  | --------> |  Postgres DB   |
    +----------------+    SQL    +----------------+
    	^  read_with_relations / join_query
    	|  construct models
    +-------------------+
    |  Model (Pydantic) |
    +-------------------+

## 五、模块架构图（职责边界）

    - config
    	- 只负责配置加载/解析
    - SqlLoader / SqlBase
    	- 只负责把 `.sql` -> `TableMeta(ColumnMeta)`，不做 SQL 执行
    - Model
    	- 负责数据验证、关系声明和序列化
    - Repo
    	- 负责 SQL 生成/执行、事务、连接管理、数据 -> 模型 映射、关系加载策略
    - sql.py (Facade)
    	- 负责动态方法路由和统一外部 API

## 六、开发者快速指南（常见任务与注意事项）

- 添加新表流程：

  1.  在 `.sql` 中新增建表语句（`mylib/sql/Sql/LML_SQL.sql` 或相应目录）并写好注释/外键；
  2.  在 `Model` 下新增对应 Pydantic 模型，设置 `__table_name__` 与关系字段（使用 `Relationship(...)` 描述）；
  3.  重新启动或调用 SqlLoader（模块初始化）以刷新 `TableMeta`；
  4.  添加 `Repo`（若需要自定义逻辑），或使用通用 `BaseRepo`。

- 添加关系时注意：

  - 在模型层用 `Relationship(..., foreign_key=...)` 标明外键字段；
  - 在 `.sql` 中定义 FOREIGN KEY 约束以保证数据库层一致性；
  - `read_with_relations` 将根据模型声明批量加载子/父对象

- 调试 JOIN 或表名问题：

  - 确认 `SqlLoader` 提取到的表名/列名（调用 `sql.get_table_fields('tasks')`）
  - 检查 `sql.py` 的动态方法名是否与 `repos` 中的表名匹配（例如 `Join_tasks_task_steps`）
    解释: 若出现 `relation 'task' does not exist` 一类错误，通常是动态路由解析表名失败或拼写不一致

- 性能提示：
  - 优先使用 `read_with_relations` 的批量加载以避免大量小查询；
  - 对于复杂报表类查询，采用 `join_query` 自定义 SELECT 字段并让数据库利用索引；
  - 使用事务（Repo 层提供）在批量写入/更新时包裹为一事务

## 七、常用命令

启动测试连接：

```sh
uv run python ./tests/sql_connect.test.py
```

运行关系测试：

```sh
uv run python ./tests/test_relations.py
```

运行完整学习与验证套件：

```sh
uv run python ./tests/test_sql_complete.py
```

—— 文档结束 ——
