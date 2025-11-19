from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from .Enum import memory_log_role, memory_log_memory_type


class MemoryLog(BaseModel):
    """记忆日志数据模型 - Pydantic BaseModel"""
    
    id: int = Field(None, description="主键 ID")
    user_id: str = Field(default="default", description="用户 ID")
    role: memory_log_role = Field(..., description="角色 (user/assistant/system) ")
    content: str = Field(default="", description="内容")
    embedding: Optional[List[float]] = Field(default=None, description="向量嵌入 (pgvector) ")
    memory_type: memory_log_memory_type = Field(..., description="记忆类型")
    importance: float = Field(default=0.5, description="重要性评分 (0-1) ")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = False
        json_encoders = {
            memory_log_role: lambda v: v.value,
            memory_log_memory_type: lambda v: v.value,
            datetime: lambda v: v.isoformat()
        }
    
    def __repr__(self) -> str:
        """自定义表示"""
        return (
            f"<MemoryLog(id={self.id}, user_id='{self.user_id}', "
            f"role={self.role.value}, memory_type={self.memory_type.value}, "
            f"importance={self.importance})>"
        )
