from .BaseRepo import BaseRepo
from ..models import MemoryLog
from ..schema.SqlLoader import get_sql_loader


class MemoryLogRepo(BaseRepo):
    """memory_log 表的数据库操作类"""

    _sql_loader = get_sql_loader()
    _table_name = "memory_log"
    _table_meta = _sql_loader.get_table_meta(_table_name)

    CREATE_TABLE_SQL = _sql_loader.get_table_create_sql(_table_name)

    _allowed_get_fields = _table_meta.get_allowed_fields() if _table_meta else [
        "id", "user_id", "role", "content", "embedding", "memory_type", "importance", "created_at"
    ]

    _model_class = MemoryLog

    def get_table_name(self) -> str:
        """获取表名"""
        return self._table_meta.get_table_name() if self._table_meta else self._table_name
