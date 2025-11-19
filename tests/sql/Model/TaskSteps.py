from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING, List
from .Enum import task_steps_status # type: ignore
from .BaseModel import RelationalModel, ForeignKey, Relationship

if TYPE_CHECKING:
    from .Tasks import Task
    from .ToolCalls import ToolCall # type: ignore


class TaskStep(RelationalModel):
    """任务步骤数据模型 - Pydantic BaseModel"""
    
    __table_name__ = "task_steps"
    
    id: int = Field(None, description="主键 ID")
    task_id: int = ForeignKey("Task", related_name="task_steps", on_delete="CASCADE")
    step_index: int = Field(default=0, description="步骤序号")
    instruction: str = Field(default="", description="步骤指令")
    output: str = Field(default="", description="步骤输出结果")
    status: task_steps_status = Field(default=task_steps_status.pending, description="步骤状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    # 关系定义
    task: Optional["Task"] = Relationship("Task", "many_to_one", back_populates="task_steps")
    tool_calls: Optional[List["ToolCall"]] = Relationship("ToolCall", "one_to_many", back_populates="step")
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = False
        json_encoders = {
            task_steps_status: lambda v: v.value,
            datetime: lambda v: v.isoformat()
        }
    
    def __repr__(self) -> str:
        """自定义表示"""
        return (
            f"<TaskStep(id={self.id}, task_id={self.task_id}, "
            f"step_index={self.step_index}, status={self.status.value})>"
        )
