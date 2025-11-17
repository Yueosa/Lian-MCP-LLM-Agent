from .BaseRepo import BaseRepo
from .Model.ToolCalls import ToolCall
from .sql.SqlLoader import get_sql_loader


class ToolCallsRepo(BaseRepo):
    """tool_calls 表的数据库操作类"""

    # 从 SqlLoader 动态获取元数据
    _sql_loader = get_sql_loader()
    _table_name = "tool_calls"
    _table_meta = _sql_loader.get_table_meta(_table_name)

    # CREATE_TABLE_SQL 从 SqlLoader 动态获取（不硬编码）
    CREATE_TABLE_SQL = _sql_loader.get_table_create_sql(_table_name)

    # 允许查询的字段
    _allowed_get_fields = _table_meta.get_allowed_fields() if _table_meta else [
        "id", "task_id", "step_id", "tool_name", "status", "created_at"
    ]

    # 模型类
    _model_class = ToolCall

    def get_table_name(self) -> str:
        """获取表名"""
        return self._table_name

    def create(self, tool_call: ToolCall) -> ToolCall:
        """
        创建新的 tool_call 记录

        :param tool_call: ToolCall 对象
        :return: 包含 id 的 ToolCall 对象
        """
        if not self._can_create:
            raise Exception("cannot create tool_call")

        sql = """
        INSERT INTO tool_calls (task_id, step_id, tool_name, arguments, response, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        try:
            import json
            cursor, conn = self._get_cursor()
            cursor.execute(sql, (
                tool_call.task_id,
                tool_call.step_id,
                tool_call.tool_name,
                json.dumps(tool_call.arguments) if tool_call.arguments else None,
                json.dumps(tool_call.response) if tool_call.response else None,
                tool_call.status.value
            ))
            id_ = cursor.fetchone()[0]
            conn.commit()
            tool_call.id = id_
            return tool_call
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_cursor(cursor, conn)

    def update(self, tool_call: ToolCall) -> bool:
        """
        更新 tool_call 记录

        :param tool_call: ToolCall 对象
        :return: 更新是否成功
        """
        if not self._can_update:
            raise Exception("cannot update tool_call")

        sql = """
        UPDATE tool_calls
        SET task_id = %s, step_id = %s, tool_name = %s, arguments = %s, response = %s, status = %s
        WHERE id = %s
        """
        try:
            import json
            cursor, conn = self._get_cursor()
            cursor.execute(sql, (
                tool_call.task_id,
                tool_call.step_id,
                tool_call.tool_name,
                json.dumps(tool_call.arguments) if tool_call.arguments else None,
                json.dumps(tool_call.response) if tool_call.response else None,
                tool_call.status.value,
                tool_call.id
            ))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_cursor(cursor, conn)
