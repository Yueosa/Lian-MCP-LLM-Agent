from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
from pydantic import Field
from mylib.kernel.Lenum import ToolCallsStatus
from ..core.BaseModel import RelationalModel, RelationshipField

if TYPE_CHECKING:
    from .Tasks import Task
    from .TaskSteps import TaskStep


class ToolCall(RelationalModel):
    """工具调用数据模型 - 支持关系的 Pydantic BaseModel"""
    
    __table_name__ = "tool_calls"
    
    id: Optional[int] = Field(None, description="主键 ID")
    task_id: int = Field(..., description="关联任务 ID (外键)")
    step_id: int = Field(..., description="关联步骤 ID (外键)")
    tool_name: str = Field(default="", description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具调用参数")
    response: Dict[str, Any] = Field(default_factory=dict, description="工具响应结果")
    status: ToolCallsStatus = Field(default=ToolCallsStatus.SUCCESS, description="执行状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    # 关系定义
    task: Optional["Task"] = Field(
        default=None, exclude=True, repr=False,
        description=RelationshipField("Task", "many_to_one", back_populates="tool_calls", foreign_key="task_id")
    )
    task_step: Optional["TaskStep"] = Field(
        default=None, exclude=True, repr=False,
        description=RelationshipField("TaskStep", "many_to_one", back_populates="tool_calls", foreign_key="step_id")
    )
    
    class Config:
        """Pydantic配置"""
        use_enum_values=False
        arbitrary_types_allowed=True
        validate_assignment=True
    
    def __repr__(self) -> str:
        """自定义表示"""
        return (
            f"<ToolCall(id={self.id}, task_id={self.task_id}, step_id={self.step_id}, "
            f"tool_name='{self.tool_name}', "
            f"arguments={self._truncate(self.arguments)}, "
            f"response={self._truncate(self.response)}, "
            f"status={self.status.value}, created_at={self.created_at})>"
        )
