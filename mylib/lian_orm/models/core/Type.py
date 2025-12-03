from typing import TypeVar, Union, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .BaseModel import RelationalModel

# ============================================
# ModelType: 泛型变量
# ============================================
# 用于表示任何继承自 RelationalModel 的类
# 在方法签名中使用，可以让 IDE 推断出具体的模型类型
T = TypeVar("T", bound="RelationalModel")


# ============================================
# RelatedData: 关联数据类型
# ============================================
# 用于表示关联对象的类型，它可能是：
# 1. 单个模型实例 (例如 TaskStep.task -> Task)
# 2. 模型实例列表 (例如 Task.task_steps -> List[TaskStep])
# 3. None (未加载或无关联)
RelatedData = Union["RelationalModel", List["RelationalModel"], None]
