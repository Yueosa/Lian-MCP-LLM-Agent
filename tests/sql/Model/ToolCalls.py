from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field
from .Enum import tool_calls_status # type: ignore
from .BaseModel import RelationalModel, ForeignKey, Relationship

if TYPE_CHECKING:
    from .Tasks import Task
    from .TaskSteps import TaskStep


class ToolCall(RelationalModel):
    """工具调用数据模型 - Pydantic BaseModel"""
    
    __table_name__ = "tool_calls"
    
    id: int = Field(None, description="主键 ID")
    task_id: Optional[int] = ForeignKey("Task", related_name="tool_calls", on_delete="SET NULL")
    step_id: Optional[int] = ForeignKey("TaskStep", related_name="tool_calls", on_delete="SET NULL")
    tool_name: str = Field(default="", description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具调用参数")
    response: Dict[str, Any] = Field(default_factory=dict, description="工具响应结果")
    status: tool_calls_status = Field(default=tool_calls_status.success, description="执行状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    # 关系定义
    task: Optional["Task"] = Relationship("Task", "many_to_one", back_populates="tool_calls")
    step: Optional["TaskStep"] = Relationship("TaskStep", "many_to_one", back_populates="tool_calls")
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = False
        json_encoders = {
            tool_calls_status: lambda v: v.value,
            datetime: lambda v: v.isoformat()
        }
    
    def __repr__(self) -> str:
        """自定义表示"""
        return (
            f"<ToolCall(id={self.id}, task_id={self.task_id}, step_id={self.step_id}, "
            f"tool_name='{self.tool_name}', status={self.status.value})>"
        )
