from .BaseRepo import BaseRepo
from .Model.TaskSteps import TaskStep
from .sql.SqlLoader import get_sql_loader


class TaskStepsRepo(BaseRepo):
    """task_steps 表的数据库操作类"""

    # 从 SqlLoader 动态获取元数据
    _sql_loader = get_sql_loader()
    _table_name = "task_steps"
    _table_meta = _sql_loader.get_table_meta(_table_name)

    # CREATE_TABLE_SQL 从 SqlLoader 动态获取（不硬编码）
    CREATE_TABLE_SQL = _sql_loader.get_table_create_sql(_table_name)

    # 允许查询的字段
    _allowed_get_fields = _table_meta.get_allowed_fields() if _table_meta else [
        "id", "task_id", "step_index", "instruction", "output", "status", "created_at", "updated_at"
    ]

    # 模型类
    _model_class = TaskStep

    def get_table_name(self) -> str:
        """获取表名"""
        return self._table_name

    def create(self, task_step: TaskStep) -> TaskStep:
        """
        创建新的 task_step 记录

        :param task_step: TaskStep 对象
        :return: 包含 id 的 TaskStep 对象
        """
        if not self._can_create:
            raise Exception("cannot create task_step")

        sql = """
        INSERT INTO task_steps (task_id, step_index, instruction, output, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """
        try:
            cursor, conn = self._get_cursor()
            cursor.execute(sql, (
                task_step.task_id,
                task_step.step_index,
                task_step.instruction,
                task_step.output,
                task_step.status.value
            ))
            id_ = cursor.fetchone()[0]
            conn.commit()
            task_step.id = id_
            return task_step
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_cursor(cursor, conn)

    def update(self, task_step: TaskStep) -> bool:
        """
        更新 task_step 记录

        :param task_step: TaskStep 对象
        :return: 更新是否成功
        """
        if not self._can_update:
            raise Exception("cannot update task_step")

        sql = """
        UPDATE task_steps
        SET task_id = %s, step_index = %s, instruction = %s, output = %s, status = %s, updated_at = NOW()
        WHERE id = %s
        """
        try:
            cursor, conn = self._get_cursor()
            cursor.execute(sql, (
                task_step.task_id,
                task_step.step_index,
                task_step.instruction,
                task_step.output,
                task_step.status.value,
                task_step.id
            ))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_cursor(cursor, conn)
