# SQL Model 模型系统文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-24

---

## 概述

`Model` 基于 `Pydantic` 实现，定义了 **数据表的结构和 Python 对象的映射关系**。

是整个 **ORM** 中基于 `Python` 面向 `PostgreSQL` 的底层数据封装

---

## 类与方法

#### (1) `ForeignKeyField` (外键定义类)

- 定义外键字段 (链接到外表的主键)
- 支持反向查询 (基于 `related_name`)
  1. 例如 `tasks.id` 作为 `task_steps.task_id` 的外键
  2. 在 `tasks` 表中反向查询 `task_steps` 表中所有关联字段
- 支持绑定更新、删除策略 (枚举 `on_update` `on_delete` 默认为 `CASCADE`)
  - 外键表发生变化时，表自身的策略

**外键策略速查**
| 策略类型    | update 行为 | delete 行为 |
| ----------- | ----------- | ----------- |
| `CASCADE`   | 一起更新    | 一起删除    |
| `SET NULL`  | 设为空      | 设为空      |
| `RESTRICT`  | 禁止改动    | 禁止改动    |
| `NO ACTION` | 无操作      | 无操作      |

#### (2) `RelationshipField` (关系定义类)

- 定义关系字段(枚举 `relationship` 默认为 `one_to_many`)
- 定义反向关系字段名
- 定义外键字段名 (关系为多的一方需要 定义本表字段)

#### (3) `RelationalModel` (继承于 `BaseModel` 注册了 `ForeignKeyField` `RelationshipField`)

> 此部分在下方详细展开介绍

---

## 核心 模型基类 `RelationalModel`

> `RelatonalModel` 是所有表模型的基类

#### 类变量 

> 在类的创建阶段(type.__init__)定义，用于注册模型的结构信息
>
> 在子类初始化时会进行重写(__init_subclass__)，避免相互污染

1. **__foreign_keys__**: `Dict[str, ForeignKeyFoeld]`
   - 存储所有外键字段
2. **__relationships__**: `Dict[str, RelationshipField]`
   - 存储所有外表字段
3. **__table_name__**: `Optional[str] = None`
   - **默认值为类名全小写**
   - 建议重写为实例属性
   - 模型映射的 `PostgreSQL` 表名
4. **_related_cache**: `Dict[str, Any]`
   - 存储已加载的关联对象

#### 初始化方法

##### (1) \_\_init__(self, **data)

> 初始化模型实例

- **`super().__init__(**data)`**: 调用 **Pydantic** 的 `BaseModel` 初始化逻辑，进行字段验证、默认值填充
- **`object.__setattr__(self, "_related_cache", {})`**: 直接在实例上设置 `_related_cache` 为一个空字典

##### (2) \_\_init_subclass__(cls, **kwargs)

> 子类初始化时处理外键和关系定义

- **`__init_subclass__`**: 因为当子类被定义 (class X(RelationalModel)) 后，会调用基类的 `__init_subclass__`
- **`super().__init_subclass__(**kwargs)`**: 调用父类的 `__init_subclass__` ，保证继承链连续

1. **`hasattr(cls)`**: 检查 `__foreign_keys__` 和 `__relationships__`
    - 如果 **不存在** / **与父类一致** -> 初始化为 **空字典**
    - 否则 -> `copy()` **父类** / **已有值** (用于多级继承)
2. **`for field_name in dir(cls)`**
    - 提取当前类的所有属性名 (如果以 '_' 开头则过滤)
    - `getattr(cls, field_name) -> field_value`: 取出属性值
    - `isinstance(field_value, ForeignKeyField | RelationshipField)`: 如果值类型是 **外键字段** / **关系字段**，自动注册到类属性中

> 使用 `dir()` + `getattr()` 的优点是简单，**但是需要小心类属性过多和副作用描述符**
>
> 一种更精确的方法是扫描 `__annotations__` / `__dict__` / `model_fields(Pydantic)` 来读取声明字段

#### 类方法

##### (1) _extract_relationships_from_fields(cls)

##### (2) get_table_name(cls) -> str

> 获取表名

- 如果 `cls.__table_name__` 存在 -> 返回
- 否则 -> 返回 `cls.__name__.lower()` (小写类名)

##### (3) get_foreign_keys(cls) -> Dict[str, ForeignKeyField]

> 获取所有外键定义

- 返回 -> `cls.__foreign_keys__.copy()`

##### (4) get_relationships(cls) -> Dict[str, RelationshipField]

> 获取所有关系定义

- 返回 -> `cls.__relationships__.copy()`

##### (5) get_relationship_fields(cls) -> List[str]

> 获取关系字段名

- 返回 -> list(cls.__relationships__.keys())
