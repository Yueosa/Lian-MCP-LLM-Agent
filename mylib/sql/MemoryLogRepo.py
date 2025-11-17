from .BaseRepo import BaseRepo
from .Model.MemoryLog import MemoryLog
from .sql.SqlLoader import get_sql_loader


class MemoryLogRepo(BaseRepo):
    """memory_log 表的数据库操作类"""

    # 从 SqlLoader 动态获取元数据
    _sql_loader = get_sql_loader()
    _table_name = "memory_log"
    _table_meta = _sql_loader.get_table_meta(_table_name)

    # CREATE_TABLE_SQL 从 SqlLoader 动态获取（不硬编码）
    CREATE_TABLE_SQL = _sql_loader.get_table_create_sql(_table_name)

    # 允许查询的字段（从元数据生成）
    _allowed_get_fields = _table_meta.get_allowed_fields() if _table_meta else [
        "id", "user_id", "role", "content", "memory_type", "importance", "created_at"
    ]

    # 模型类
    _model_class = MemoryLog

    def get_table_name(self) -> str:
        """获取表名"""
        return self._table_name

    def create(self, memory_log: MemoryLog) -> MemoryLog:
        """
        创建新的 memory_log 记录

        :param memory_log: MemoryLog 对象
        :return: 包含 id 的 MemoryLog 对象
        """
        if not self._can_create:
            raise Exception("cannot create memory_log")

        sql = """
        INSERT INTO memory_log (user_id, role, content, embedding, memory_type, importance)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        try:
            cursor, conn = self._get_cursor()
            cursor.execute(sql, (
                memory_log.user_id,
                memory_log.role.value,
                memory_log.content,
                memory_log.embedding if memory_log.embedding else None,
                memory_log.memory_type.value,
                memory_log.importance
            ))
            id_ = cursor.fetchone()[0]
            conn.commit()
            memory_log.id = id_
            return memory_log
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_cursor(cursor, conn)

    def update(self, memory_log: MemoryLog) -> bool:
        """
        更新 memory_log 记录

        :param memory_log: MemoryLog 对象
        :return: 更新是否成功
        """
        if not self._can_update:
            raise Exception("cannot update memory_log")

        sql = """
        UPDATE memory_log
        SET user_id = %s, role = %s, content = %s, embedding = %s, memory_type = %s, importance = %s
        WHERE id = %s
        """
        try:
            cursor, conn = self._get_cursor()
            cursor.execute(sql, (
                memory_log.user_id,
                memory_log.role.value,
                memory_log.content,
                memory_log.embedding if memory_log.embedding else None,
                memory_log.memory_type.value,
                memory_log.importance,
                memory_log.id
            ))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_cursor(cursor, conn)
