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