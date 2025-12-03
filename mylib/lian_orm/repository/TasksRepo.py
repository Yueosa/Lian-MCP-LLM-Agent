from ..models import Task
from .BaseRepo import BaseRepo


class TasksRepo(BaseRepo):
    """tasks 表的数据库操作类"""

    _table_name = "tasks"
    
    _allowed_get_fields = [
        "id", "user_id", "title", "description", "status", "created_at", "updated_at"
    ]

    _model_class = Task

    def get_table_name(self) -> str:
        """获取表名"""
        return self._table_meta.name if self._table_meta else self._table_name

    def _verify(self) -> None:
        """重写验证逻辑，动态更新 _allowed_get_fields"""
        if self._table_meta:
            self._allowed_get_fields = list(self._table_meta.columns.keys())
        super()._verify()
