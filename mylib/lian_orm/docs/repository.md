# lian_orm repository 仓库层文档

> 此文档面向 **模块开发者**，在代码层简述了各文件实现

###### By - Lian 2025 | Updated 2025-11-29

---

## 概述

`Repository` 模块实现了具体的 CRUD 逻辑，是 ORM 的核心业务层。

---

## 核心组件

### (1) BaseRepo

> 位于 `repository/BaseRepo.py`

所有 Repository 的抽象基类。

- **初始化**: 接收 `DatabaseClient` 和可选的 `TableMeta`。
- **CRUD 方法**:
    - `create(model_instance)`: 创建记录。
    - `read(**kwargs)`: 根据条件查询记录。
    - `update(id, **kwargs)`: 更新记录。
    - `delete(id)`: 删除记录。
    - `get_by_id(id)`: 根据 ID 获取记录。
- **高级查询**:
    - `read_with_relations(relations, **kwargs)`: 查询并自动加载关联对象。
    - `join_query(join_table, ...)`: 执行 SQL JOIN 查询。
- **元数据集成**: 利用注入的 `TableMeta` 和 `DataConverter` 自动处理类型转换。

### (2) 具体 Repo 实现

例如 `TasksRepo`, `MemoryLogRepo` 等，继承自 `BaseRepo`。

- **_model_class**: 指定对应的 Pydantic 模型。
- **_allowed_get_fields**: 指定允许查询/更新的字段。
- **CREATE_TABLE_SQL**: 定义建表语句。

---
