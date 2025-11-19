from .BaseRepo import BaseRepo
from ..Model.ToolCalls import ToolCall
from ..Sql.SqlLoader import get_sql_loader


class ToolCallsRepo(BaseRepo):
    """tool_calls 表的数据库操作类"""

    _sql_loader = get_sql_loader()
    _table_name = "tool_calls"
    _table_meta = _sql_loader.get_table_meta(_table_name)

    CREATE_TABLE_SQL = _sql_loader.get_table_create_sql(_table_name)

    _allowed_get_fields = _table_meta.get_allowed_fields() if _table_meta else [
        "id", "task_id", "step_id", "tool_name", "arguments", "response", "status", "created_at"
    ]

    _model_class = ToolCall

    def get_table_name(self) -> str:
        """获取表名"""
        return self._table_name
