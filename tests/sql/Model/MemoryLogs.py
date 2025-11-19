from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from .BaseModel import RelationalModel


class MemoryLog(RelationalModel):
    """记忆日志数据模型 - Pydantic BaseModel"""
    
    __table_name__ = "memory_log"
    
    id: int = Field(None, description="主键 ID")
    user_id: str = Field(default="default", description="用户 ID")
    role: str = Field(..., description="角色: user / assistant / system")
    content: str = Field(..., description="内容")
    embedding: Optional[List[float]] = Field(default=None, description="向量嵌入")
    memory_type: str = Field(default="conversation", description="记忆类型: summary / reflection / preference / plan 等")
    importance: float = Field(default=0, description="重要性")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    # MemoryLog 模型没有外键关系，因为它是一个独立的日志表
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = False
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def __repr__(self) -> str:
        """自定义表示"""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return (
            f"<MemoryLog(id={self.id}, user_id='{self.user_id}', "
            f"role='{self.role}', content='{content_preview}')>"
        )
