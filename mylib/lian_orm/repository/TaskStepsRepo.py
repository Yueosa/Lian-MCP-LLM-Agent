from ..models import TaskStep
from .BaseRepo import BaseRepo


class TaskStepsRepo(BaseRepo):
    """task_steps 表的数据库操作类"""

    _table_name = "task_steps"
    
    _allowed_get_fields = [
        "id", "task_id", "step_index", "instruction", "output", "status", "created_at", "updated_at"
    ]

    _model_class = TaskStep

    def get_table_name(self) -> str:
        """获取表名"""
        return self._table_meta.name if self._table_meta else self._table_name

    def _verify(self) -> None:
        """重写验证逻辑，动态更新 _allowed_get_fields"""
        if self._table_meta:
            self._allowed_get_fields = list(self._table_meta.columns.keys())
        super()._verify()
