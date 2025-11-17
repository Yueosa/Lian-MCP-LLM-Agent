from .BaseRepo import BaseRepo
from .Model.Tasks import Task
from .sql.SqlLoader import get_sql_loader


class TasksRepo(BaseRepo):
    """tasks 表的数据库操作类"""

    # 从 SqlLoader 动态获取元数据
    _sql_loader = get_sql_loader()
    _table_name = "tasks"
    _table_meta = _sql_loader.get_table_meta(_table_name)

    # CREATE_TABLE_SQL 从 SqlLoader 动态获取（不硬编码）
    CREATE_TABLE_SQL = _sql_loader.get_table_create_sql(_table_name)

    # 允许查询的字段
    _allowed_get_fields = _table_meta.get_allowed_fields() if _table_meta else [
        "id", "user_id", "title", "status", "created_at", "updated_at"
    ]

    # 模型类
    _model_class = Task

    def get_table_name(self) -> str:
        """获取表名"""
        return self._table_name

    def create(self, task: Task) -> Task:
        """
        创建新的 task 记录

        :param task: Task 对象
        :return: 包含 id 的 Task 对象
        """
        if not self._can_create:
            raise Exception("cannot create task")

        sql = """
        INSERT INTO tasks (user_id, title, description, status)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """
        try:
            cursor, conn = self._get_cursor()
            cursor.execute(sql, (
                task.user_id,
                task.title,
                task.description,
                task.status.value
            ))
            id_ = cursor.fetchone()[0]
            conn.commit()
            task.id = id_
            return task
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_cursor(cursor, conn)

    def update(self, task: Task) -> bool:
        """
        更新 task 记录

        :param task: Task 对象
        :return: 更新是否成功
        """
        if not self._can_update:
            raise Exception("cannot update task")

        sql = """
        UPDATE tasks
        SET user_id = %s, title = %s, description = %s, status = %s, updated_at = NOW()
        WHERE id = %s
        """
        try:
            cursor, conn = self._get_cursor()
            cursor.execute(sql, (
                task.user_id,
                task.title,
                task.description,
                task.status.value,
                task.id
            ))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_cursor(cursor, conn)
