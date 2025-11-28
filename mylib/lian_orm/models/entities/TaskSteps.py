from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pydantic import Field
from ..core.Enum import task_steps_status
from ..core.BaseModel import RelationalModel, RelationshipField

if TYPE_CHECKING:
    from .Tasks import Task
    from .ToolCalls import ToolCall


class TaskStep(RelationalModel):
    """任务步骤数据模型 - 支持关系的 Pydantic BaseModel"""
    
    __table_name__ = "task_steps"
    
    id: Optional[int] = Field(None, description="主键 ID")
    task_id: int = Field(..., description="关联任务 ID (外键)")
    step_index: int = Field(default=0, description="步骤序号")
    instruction: str = Field(default="", description="步骤指令")
    output: Optional[str] = Field(default=None, description="步骤输出结果")
    status: task_steps_status = Field(default=task_steps_status.pending, description="步骤状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    # 关系定义
    task: Optional["Task"] = Field(
        default=None, exclude=True, repr=False,
        description=RelationshipField("Task", "many_to_one", back_populates="task_steps", foreign_key="task_id")
    )
    tool_calls: Optional[List["ToolCall"]] = Field(
        default=None, exclude=True, repr=False,
        description=RelationshipField("ToolCall", "one_to_many", back_populates="task_step")
    )
    
    class Config:
        """Pydantic配置"""
        use_enum_values=False
        arbitrary_types_allowed=True
        validate_assignment=True
    
    def __repr__(self) -> str:
        """自定义表示"""
        return (
            f"<TaskStep(id={self.id}, task_id={self.task_id}, "
            f"step_index={self.step_index}, "
            f"instruction='{self._truncate(self.instruction)}', "
            f"output='{self._truncate(self.output)}', "
            f"status={self.status.value}, "
            f"created_at={self.created_at}, updated_at={self.updated_at})>"
        )
