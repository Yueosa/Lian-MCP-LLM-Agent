from typing import List, Dict, Any
from ..models import MemoryLog
from .BaseRepo import BaseRepo


class MemoryLogRepo(BaseRepo):
    """memory_log 表的数据库操作类"""

    _table_name = "memory_log"
    
    # 默认字段，如果 table_meta 未提供则使用此列表
    _allowed_get_fields = [
        "id", "user_id", "role", "content", "embedding", "memory_type", "importance", "created_at"
    ]

    _model_class = MemoryLog

    def get_table_name(self) -> str:
        """获取表名"""
        return self._table_meta.name if self._table_meta else self._table_name
    
    def _verify(self) -> None:
        """重写验证逻辑，动态更新 _allowed_get_fields"""
        if self._table_meta:
            self._allowed_get_fields = list(self._table_meta.columns.keys())
        super()._verify()

    def search_by_embedding(self, embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        根据向量相似度搜索
        """
        embedding_str = str(embedding)
        
        fields = ", ".join(self._allowed_get_fields)
        
        sql = f"""
            SELECT {fields}, 1 - (embedding <=> %s) as score
            FROM {self.get_table_name()}
            ORDER BY embedding <=> %s
            LIMIT %s
        """
        
        return self.db.fetch_all(sql, [embedding_str, embedding_str, top_k])

