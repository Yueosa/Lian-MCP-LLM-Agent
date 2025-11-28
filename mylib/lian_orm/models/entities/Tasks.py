from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pydantic import Field
from ..core.Enum import tasks_status
from ..core.BaseModel import RelationalModel, RelationshipField

if TYPE_CHECKING:
    from .TaskSteps import TaskStep
    from .ToolCalls import ToolCall


class Task(RelationalModel):
    """任务数据模型 - 支持关系的 Pydantic BaseModel"""
    
    __table_name__ = "tasks"
    
    id: Optional[int] = Field(None, description="主键 ID")
    user_id: str = Field(default="default", description="用户 ID")
    title: str = Field(default="", description="任务标题")
    description: Optional[str] = Field(default="", description="任务描述")
    status: tasks_status = Field(default=tasks_status.pending, description="任务状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    # 关系定义
    task_steps: Optional[List["TaskStep"]] = Field(
        default=None, exclude=True, repr=False,
        description=RelationshipField("TaskStep", "one_to_many", back_populates="task")
    )
    tool_calls: Optional[List["ToolCall"]] = Field(
        default=None, exclude=True, repr=False,
        description=RelationshipField("ToolCall", "one_to_many", back_populates="task")
    )
    
    class Config:
        """Pydantic配置"""
        use_enum_values = False
        arbitrary_types_allowed = True
        validate_assignment = True
    
    def __repr__(self) -> str:
        """自定义表示"""
        return (
            f"<Task(id={self.id}, user_id='{self.user_id}', "
            f"title='{self._truncate(self.title)}', "
            f"description='{self._truncate(self.description)}', "
            f"status={self.status.value}, "
            f"created_at={self.created_at}, updated_at={self.updated_at})>"
        )
