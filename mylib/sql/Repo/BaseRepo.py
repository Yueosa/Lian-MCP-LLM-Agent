from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union
from enum import Enum
from .DBPool import PostgreSQLConnectionPool
from ..Model import MemoryLog, Task, TaskStep, ToolCall


class BaseRepo(ABC):
    """
    数据库仓库抽象类, 提供统一的CRUD操作接口

    子类需要实现: 
        - get_table_name(): 获取表名
        - 需设置的类变量: 
            - _model_class: 对应的数据模型类
            - _allowed_get_fields: 允许查询的字段列表
            - CREATE_TABLE_SQL: 创建表的SQL语句
    """

    _model_class = None
    _allowed_get_fields = []
    CREATE_TABLE_SQL = None

    # 操作权限控制
    _can_create = True
    _can_read = True
    _can_update = True
    _can_delete = True

    def __init__(self, connection_pool: PostgreSQLConnectionPool):
        """
        初始化数据库连接池

        Args:
            connection_pool: 数据库连接池实例
        """
        self._connection_pool = connection_pool
        self._verify()

    def _verify(self) -> None:
        if self._model_class is None:
            raise ValueError(f"{self.__class__.__name__} 必须设置 _model_class 类变量")
        if not self._allowed_get_fields:
            raise ValueError(f"{self.__class__.__name__} 必须设置 _allowed_get_fields 类变量")

    def create(self, model_instance: Union[MemoryLog, Task, TaskStep, ToolCall]) -> Any:
        """
        创建记录

        Args:
            model_instance: 数据模型实例

        Returns:
            创建后的模型实例 (包含生成的ID) 

        Raises:
            ValueError: 如果不允许创建操作或参数错误
            Exception: 数据库操作异常
        """
        if not self._can_create:
            raise ValueError(f"表 '{self.get_table_name()}' 不允许创建操作")

        data = model_instance.model_dump(exclude_unset=True, exclude_none=True)
        
        if hasattr(model_instance, 'id') and model_instance.id is not None:
            data.pop('id', None)
        
        for field in ['created_at', 'updated_at']:
            data.pop(field, None)

        for k, v in data.items():
            if isinstance(v, Enum):
                data[k] = v.value

        if not data:
            raise ValueError("没有可插入的数据")

        fields = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        sql = f"INSERT INTO {self.get_table_name()} ({fields}) VALUES ({placeholders}) RETURNING id"

        try:
            cursor, conn = self._get_cursor()
            cursor.execute(sql, list(data.values()))
            result = cursor.fetchone()
            if result:
                model_instance.id = result[0]
            conn.commit()
            return model_instance
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_cursor(cursor, conn)

    def read(self, **kwargs) -> List[Any]:
        """
        读取记录, 支持多字段查询

        Args:
            **kwargs: 查询条件, 支持_allowed_get_fields中的字段

        Returns:
            符合条件的模型实例列表

        Raises:
            ValueError: 如果不允许读取操作或查询字段无效
        """
        if not self._can_read:
            raise ValueError(f"表 '{self.get_table_name()}' 不允许读取操作")

        invalid_fields = [field for field in kwargs.keys() if field not in self._allowed_get_fields]
        if invalid_fields:
            raise ValueError(f"无效的查询字段: {invalid_fields}, 允许的字段: {self._allowed_get_fields}")

        if kwargs:
            conditions = ' AND '.join([f"{field} = %s" for field in kwargs.keys()])
            sql = f"SELECT * FROM {self.get_table_name()} WHERE {conditions}"
            params = list(kwargs.values())
        else:
            sql = f"SELECT * FROM {self.get_table_name()}"
            params = []

        try:
            cursor, conn = self._get_cursor()
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            
            instances = []
            for row in results:
                row_dict = dict(zip(columns, row))
                instance = self._model_class(**row_dict)
                instances.append(instance)
            
            return instances
        finally:
            self._release_cursor(cursor, conn)

    def update(self, id: int, **kwargs) -> bool:
        """
        根据ID更新记录

        Args:
            id: 记录ID
            **kwargs: 要更新的字段和值

        Returns:
            更新是否成功

        Raises:
            ValueError: 如果不允许更新操作或参数错误
        """
        if not self._can_update:
            raise ValueError(f"表 '{self.get_table_name()}' 不允许更新操作")

        invalid_fields = [field for field in kwargs.keys() if field not in self._allowed_get_fields]
        if invalid_fields:
            raise ValueError(f"无效的更新字段: {invalid_fields}, 允许的字段: {self._allowed_get_fields}")

        if 'id' in kwargs:
            raise ValueError("不能更新ID字段")

        if not kwargs:
            return True

        for field, value in kwargs.items():
            field_type = getattr(self._model_class, '__annotations__', {}).get(field)
            if field_type is None:
                continue
            if isinstance(field_type, type) and issubclass(field_type, Enum):
                valid_values = [e.value for e in field_type]
                if isinstance(value, Enum):
                    value_to_check = value.value
                else:
                    value_to_check = value
                if value_to_check not in valid_values:
                    raise ValueError(
                        f"字段 '{field}' 的值 '{value}' 不合法, 可选值: {valid_values}"
                    )

        set_clause = ', '.join([f"{k} = %s" for k in kwargs.keys()])
        sql = f"UPDATE {self.get_table_name()} SET {set_clause} WHERE id = %s"

        try:
            cursor, conn = self._get_cursor()
            values = [
                v.value if isinstance(v, Enum) else v
                for v in kwargs.values()
            ]
            cursor.execute(sql, values + [id])
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_cursor(cursor, conn)

    def delete(self, id: int) -> bool:
        """
        根据ID删除记录

        Args:
            id: 记录ID

        Returns:
            删除是否成功

        Raises:
            ValueError: 如果不允许删除操作
        """
        if not self._can_delete:
            raise ValueError(f"表 '{self.get_table_name()}' 不允许删除操作")

        sql = f"DELETE FROM {self.get_table_name()} WHERE id = %s"

        try:
            cursor, conn = self._get_cursor()
            cursor.execute(sql, (id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._release_cursor(cursor, conn)

    def get_by_id(self, id: int) -> Optional[Any]:
        """
        根据ID获取单条记录

        Args:
            id: 记录ID

        Returns:
            模型实例或None
        """
        results = self.read(id=id)
        return results[0] if results else None

    def _get_cursor(self):
        """
        获取数据库游标和连接

        Returns:
            tuple: (cursor, connection)
        """
        conn = self._connection_pool.get_connection()
        return conn.cursor(), conn

    def _release_cursor(self, cursor, connection):
        """
        释放数据库游标和连接

        Args:
            cursor: 数据库游标
            connection: 数据库连接
        """
        cursor.close()
        self._connection_pool.release_connection(connection)

    @abstractmethod
    def get_table_name(self) -> str:
        """
        获取数据库表名, 子类中实现

        Returns:
            表名字符串
        """
        pass

    def create_table(self):
        """
        创建数据库表

        Raises:
            ValueError: 如果CREATE_TABLE_SQL未设置
            Exception: 数据库操作异常
        """
        if self.CREATE_TABLE_SQL is None:
            raise ValueError(f"{self.__class__.__name__} 必须设置 CREATE_TABLE_SQL 类变量")

        conn = self._connection_pool.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(self.CREATE_TABLE_SQL)
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self._connection_pool.release_connection(conn)

    def has_field(self, field_name: str) -> bool:
        """
        检查表是否包含指定字段

        Args:
            field_name: 字段名

        Returns:
            bool: 是否包含该字段
        """
        return field_name in self._allowed_get_fields
