from pydantic import Field
from datetime import datetime
from typing import Optional, List

from mylib.kernel.Lenum import MemoryLogMemoryType, MemoryLogRole

from ..core.BaseModel import RelationalModel


class MemoryLog(RelationalModel):
    """记忆日志数据模型 - 支持关系的 Pydantic BaseModel"""
    
    __table_name__ = "memory_log"
    
    id: Optional[int] = Field(None, description="主键 ID")
    user_id: str = Field(default="default", description="用户 ID")
    role: MemoryLogRole = Field(..., description="角色 (user/assistant/system/tool) ")
    content: str = Field(default="", description="内容")
    embedding: Optional[List[float]] = Field(default=None, description="向量嵌入 (pgvector) ")
    memory_type: MemoryLogMemoryType = Field(..., description="记忆类型 (conversation/summary/reflection/preference/plan)")
    importance: float = Field(default=0.5, description="重要性评分 (0-1) ")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    class Config:
        """Pydantic 配置"""
        use_enum_values = False
    
    def __repr__(self) -> str:
        """自定义表示"""
        emb_status = f"<Vector({len(self.embedding)})>" if self.embedding else "None"
        return (
            f"<MemoryLog(id={self.id}, user_id='{self.user_id}', "
            f"role={self.role.value}, content='{self._truncate(self.content)}', "
            f"embedding={emb_status}, memory_type={self.memory_type.value}, "
            f"importance={self.importance}, created_at={self.created_at})>"
        )
