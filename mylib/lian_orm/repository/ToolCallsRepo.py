from ..models import ToolCall
from .BaseRepo import BaseRepo


class ToolCallsRepo(BaseRepo):
    """tool_calls 表的数据库操作类"""

    _table_name = "tool_calls"
    
    _allowed_get_fields = [
        "id", "task_id", "step_id", "tool_name", "arguments", "response", "status", "created_at"
    ]

    _model_class = ToolCall

    def get_table_name(self) -> str:
        """获取表名"""
        return self._table_meta.name if self._table_meta else self._table_name

    def _verify(self) -> None:
        """重写验证逻辑，动态更新 _allowed_get_fields"""
        if self._table_meta:
            self._allowed_get_fields = list(self._table_meta.columns.keys())
        super()._verify()
