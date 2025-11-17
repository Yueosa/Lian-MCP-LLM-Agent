from datetime import datetime
from pydantic import BaseModel, Field
from .Enum import tasks_status


class Task(BaseModel):
    """任务数据模型 - Pydantic BaseModel"""
    
    id: int = Field(..., description="主键 ID")
    user_id: str = Field(default="default", description="用户 ID")
    title: str = Field(default="", description="任务标题")
    description: str = Field(default="", description="任务描述")
    status: tasks_status = Field(default=tasks_status.pending, description="任务状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = False
        json_encoders = {
            tasks_status: lambda v: v.value,
            datetime: lambda v: v.isoformat()
        }
    
    def __repr__(self) -> str:
        """自定义表示"""
        title_preview = self.title[:50] + "..." if len(self.title) > 50 else self.title
        return (
            f"<Task(id={self.id}, user_id='{self.user_id}', "
            f"status={self.status.value}, title='{title_preview}')>"
        )
