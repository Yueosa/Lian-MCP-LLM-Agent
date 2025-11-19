# sql Model 说明文档

###### By - Lian 2025

---

##### `Model` 基于 `Python pydantic` 实现, 定义了每张数据表的结构

以下是一个模型的基本模板:

```python
from pydantic import BaseModel

class ModelName(BaseModel):
    field: type = value

    class Config:
        use_enum_values: bool = value
        json_encoders: dict = {
            type: lambda key: value
        }

    def __repr__(self) -> str:
        return (f"{self.field=}")
```

##### 参数解析

1. `use_enum_values`: 是否获取枚举值类型

    - 如果设置为 `True`，当字段使用枚举类型时，`Pydantic` 会返回枚举值而不是枚举对象

2. `json_encoders`: 控制自定义类型在 JSON 序列化 时的转换规则

    - 例如使用 `datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")` 来格式化时间

3. `__repr__`方法

    - 控制对象被 `repr()` 调用 或 **直接在交互式环境中显示时** 的行为
