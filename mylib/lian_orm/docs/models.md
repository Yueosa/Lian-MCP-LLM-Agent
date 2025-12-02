# lian_orm models 模型系统文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-25

---

## 目录

- [SQL Model 模型系统文档](#sql-model-模型系统文档)
          - [By - Lian 2025 | Updated 2025-11-24](#by---lian-2025--updated-2025-11-24)
  - [目录](#目录)
  - [概述](#概述)
  - [自定义枚举与泛型](#自定义枚举与泛型)
      - [(1) 枚举 Enum](#1-枚举-enum-继承于enumenum)
      - [(2) 泛型 TypeVar](#2-泛型-typevar)
  - [Pydantic 模型配置](#pydantic-模型配置)
        - [(1) class Config | ConfigDict()](#1-class-config--configdict)
  - [类与方法](#类与方法)
      - [(1) RelationshipField](#1-relationshipfield-关系定义类)
      - [(2) RelationalModel](#2-relationalmodel-继承于-basemodel-注册了-relationshipfield)
  - [核心 模型基类 RelationalModel](#核心-模型基类-relationalmodel)
      - [类变量](#类变量)
      - [初始化方法](#初始化方法)
        - [(1) \_\_init\_\_(self, \*\*data)](#1-__init__self-data)
        - [(2) \_\_init\_subclass\_\_(cls, \*\*kwargs)](#2-__init_subclass__cls-kwargs)
      - [类方法](#类方法)
        - [(1) \_extract\_relationships\_from\_fields(cls)](#1-_extract_relationships_from_fieldscls)
        - [(2) get\_table\_name(cls) -\> str](#2-get_table_namecls---str)
        - [(3) get\_relationships(cls) -\> Dict[str, RelationshipField]](#3-get_relationshipscls---dictstr-relationshipfield)
        - [(4) get\_relationship\_fields(cls) -\> List[str]](#4-get_relationship_fieldscls---liststr)
      - [实例方法](#实例方法)
        - [(1) get\_related\_object(self, field\_name: str) -\> RelatedData](#1-get_related_objectself-field_name-str---relateddata)
        - [(2) get\_related\_objects(self) -\> Dict[str, RelatedData]](#2-get_related_objectsself---dictstr-relateddata)
        - [(3) set\_related\_object(self, field\_name: str, obj: RelaredData) -\> None](#3-set_related_objectself-field_name-str-obj-relateddata---none)
        - [(4) clear\_related\_object(self) -\> None](#4-clear_related_objectself---none)
        - [(5) has\_related\_object(self, filed\_name: str) -\> bool](#5-has_related_objectself-filed_name-str---bool)
        - [(6) to\_dict\_with\_relations(self, include\_relations: Optional[List[str]] = None) -\> Dict[str, Any]](#6-to_dict_with_relationsself-include_relations-optionalliststr--none---dictstr-any)
      - [静态方法](#静态方法)
        - [(1) \_truncate(value: Any, length: int = 30) -\> str](#1-_truncatevalue-any-length-int--30---str)
  - [模型](#模型)
      - [(1) MemoryLog](#1-memorylog)
      - [(2) Task](#2-task)
      - [(3) TaskStep](#3-taskstep)
      - [(4) ToolCall](#4-toolcall)


---

## 概述

`Model` 基于 `Pydantic` 实现，定义了 **数据表的结构和 Python 对象的映射关系**。

是整个 **lian_orm** 中基于 `Python` 面向 `PostgreSQL` 的底层数据封装

---

## 自定义枚举与泛型

#### (1) 枚举 Enum (继承于`enum.Enum`)

- `memory_log_role`: 表 `memory_log` 中 `role` 字段的枚举
- `memory_log_memory_type`: 表 `memory_log` 中 `memory_type` 字段的枚举
- `tasks_status`: 表 `tasks` 中 `status` 字段的枚举
- `task_steps_status`: 表 `task_steps` 中 `status` 字段的枚举
- `tool_calls_status`: 表 `tool_calls` 中 `status` 字段的枚举
- `on_update`: 类 `RelationshipField` 外键更新策略参数的枚举
- `on_delete`: 类 `RelationshipField` 外键删除策略参数的枚举
- `relationship`: 类 `RelationshipField` 外键关系参数的枚举

#### (2) 泛型 TypeVar

- `T`: 表示任何继承自 `RelationalModel` 的类
- `RelatedData`: 关联对象允许的类型

---

## `Pydantic` 模型配置

##### (1) class Config | ConfigDict()

> `Pydantic` 的快捷配置项

- `arbitrary_types_allowed = True`: 允许字段类型是 `Pydantic` 无法验证的或序列化的**任意类型**
- `use_enum_values = False`: 不允许字段直接使用枚举值
- `validate_assignment = True`: 实例化后重新赋值也进行检查

---

## 类与方法

#### (1) `RelationshipField` (关系定义类)

- 定义关系字段(枚举 `relationship` 默认为 `one_to_many`)
- 定义关系字段 (外键) 的更新、删除策略
- 定义反向关系字段名
- 定义外键字段名 (关系为多的一方需要 定义本表字段)

#### (2) `RelationalModel` (继承于 `BaseModel` 注册了 `RelationshipField`)

> 此部分在下方详细展开介绍

---

## 核心 模型基类 `RelationalModel`

> `RelatonalModel` 是所有表模型的基类

#### 类变量 

> 在类的创建阶段(**type.\_\_init__**)定义，用于注册模型的结构信息
>
> 在子类初始化时会进行重写(**\_\_init_subclass__**)，避免相互污染

1. **\_\_relationships__**: `Dict[str, RelationshipField]`
   - 存储所有外表字段
2. **\_\_table_name__**: `Optional[str] = None`
   - **默认值为类名全小写**
   - 建议重写为实例属性
   - 模型映射的 `PostgreSQL` 表名
3. **_related_cache**: `Dict[str, Any]`
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

1. **`hasattr(cls)`**: 检查 `__relationships__`
    - 如果 **不存在** / **与父类一致** -> 初始化为 **空字典**
    - 否则 -> `copy()` **父类** / **已有值** (用于多级继承)
2. **`for field_name in dir(cls)`**
    - `cls.__dict__.get('__annotations__', {})`: 获取当前类定义的属性名
    - `cls.__dict__.get(name, None)`： 获取指定属性值
    - `isinstance(value, RelationshipField)`: 如果值类型是 **关系字段**，自动注册到类属性中

> 旧实现中使用 `dir()` + `getattr()` 的优点是简单，**但是需要小心类属性过多和副作用描述符**
>
> 新的方法是扫描 `__annotations__` / `__dict__` 来读取声明字段

#### 类方法

##### (1) _extract_relationships_from_fields(cls)

> 将 `Pydantic` 中的 `model_fields` 注册进类变量

> `Pydantic` 会将所有字段的元数据存储在 `model_fields(dict)` 中
> `model_fields` 的 `value: FieldInfo` 包含了所有信息，例如 `default` `annotation` `description`

- 扫描 `model_fields` 中所有 `field_info.description`，如果是 `RelationshipField` 类型则注册进 `__relationships__`

##### (2) get_table_name(cls) -> str

> 获取表名

- 如果 `cls.__table_name__` 存在 -> 返回
- 否则 -> 返回 `cls.__name__.lower()` (小写类名)

##### (3) get_relationships(cls) -> Dict[str, RelationshipField]

> 获取所有关系定义

- 返回 -> `cls.__relationships__.copy()`

##### (4) get_relationship_fields(cls) -> List[str]

> 获取关系字段列表

- 返回 -> `list(cls.__relationships__.keys())`

#### 实例方法

##### (1) get_related_object(self, field_name: str) -> RelatedData

> 返回指定的关联对象

- 返回 -> `self._related_cache.get(field_name)`

##### (2) get_related_objects(self) -> Dict[str, RelatedData]

> 返回所有关联对象

- 返回 -> `self._related_cache.copy()`

##### (3) set_related_object(self, field_name: str, obj: RelatedData) -> None

> 设置关联对象

- 报错 -> 如果 `field_name` 不存在于 `__relationships__.keys()`

##### (4) clear_related_object(self) -> None

> 清楚所有关联对象

- 对 `_related_cache` 执行 `clear()`

##### (5) has_related_object(self, filed_name: str) -> bool

> 检查某个关系对象是否加载

- 检查 -> `field_name` 是否存在于 `_related_cache`

##### (6) to_dict_with_relations(self, include_relations: Optional[List[str]] = None) -> Dict[str, Any]

> 导出包含关联对象的字典

- **include_relations**: 指定要导出的关系列表，默认为 None (导出所有已加载关系)
- 返回 -> 包含基本字段和关联对象的字典

#### 静态方法

##### (1) _truncate(value: Any, length: int = 30) -> str

> 对任意显示类型进行字符截断

- 返回 -> 前`{length}`个字符

---

## 模型

> 顶级父类为 `RelationalModel`，定义了 `Python` 端底层数据结构

#### (1) MemoryLog

> 对应数据库的表 `memory_log`

- **必填项**: `role` `memory_type`

#### (2) Task

> 对应数据库的表 `tasks`

#### (3) TaskStep

> 对应数据库的表 `task_steps`

- **必填项**: `task_id`

#### (4) ToolCall

> 对应数据库的表 `tool_calls`
