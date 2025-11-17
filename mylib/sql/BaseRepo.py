from abc import ABC, abstractmethod
from .DBPool import PostgreSQLConnectionPool


class BaseRepo(ABC):
    """
    连接库抽象类，封装了数据库连接池，提供数据库操作方法

    需创建的变量：
        CREATE_TABLE_SQL

        _allowed_get_fields

        _model_class

        _can_delete


    需实现的抽象方法：
        get_table_name


    可实现的方法：
        create

        update
    """

    CREATE_TABLE_SQL = None
    _can_create = True
    _can_delete = True
    _can_get = True
    _can_update = True

    def __init__(self, connection_pool: PostgreSQLConnectionPool):
        """
        初始化数据库连接池

        :param connection_pool: 数据库连接池
        """
        self._connection_pool = connection_pool

    def __getattr__(self, name):
        """
        动态生成字段相关方法

        :param name: 调用的方法名
        :return: 对应的方法
        """
        if name.startswith('get_all_by_') and self._can_get:
            if '_and_' in name:
                field_names = name[len('get_all_by_'):].split('_and_')
                if hasattr(self, '_allowed_get_fields') and all(
                        field_name in self._allowed_get_fields for field_name in field_names):
                    def get_all_by(*field_values: str):
                        """
                        根据多个字段值获取所有匹配记录

                        :param field_values: 字段值列表，顺序应与字段名一致
                        :return: 匹配的记录列表
                        """
                        if len(field_values) != len(field_names):
                            raise ValueError(f"need to provide {len(field_names)} params，but got {len(field_values)} params")

                        conditions = ' AND '.join([f"{field_name} = %s" for field_name in field_names])
                        sql = f"SELECT * FROM {self.get_table_name()} WHERE {conditions}"
                        try:
                            cursor, conn = self._get_cursor()
                            cursor.execute(sql, field_values)
                            results = cursor.fetchall()
                            return [self._model_class(*row) for row in results] if results else []
                        finally:
                            self._release_cursor(cursor, conn)

                    return get_all_by
                else:
                    raise AttributeError(f"table '{self.__class__.__name__}' has no column named in these fields: '{field_names}'")
            else:
                field_name = name[len('get_all_by_'):]
                if hasattr(self, '_allowed_get_fields') and field_name in self._allowed_get_fields:
                    def get_all_by(field_value: str):
                        """
                        根据字段值获取所有匹配记录

                        :param field_value: 字段值
                        :return: 匹配的记录列表
                        """
                        sql = f"SELECT * FROM {self.get_table_name()} WHERE {field_name} = %s"
                        try:
                            cursor, conn = self._get_cursor()
                            cursor.execute(sql, (field_value,))
                            results = cursor.fetchall()
                            return [self._model_class(*row) for row in results] if results else []
                        finally:
                            self._release_cursor(cursor, conn)

                    return get_all_by
                else:
                    raise AttributeError(f"table '{self.get_table_name()}' has no column named '{field_name}'")

        elif name == 'get_by_id' and self._can_get:
            if not self.has_field("id"):
                raise AttributeError(f"table '{self.get_table_name()}' has no column named 'id'")

            def get_by_id(id: int):
                """
                获取指定id的记录

                :param id: 数据id
                :return: 数据对象
                """
                sql = f"SELECT * FROM {self.get_table_name()} WHERE id = %s"
                try:
                    cursor, conn = self._get_cursor()
                    cursor.execute(sql, (id,))
                    result = cursor.fetchone()
                    return self._model_class(*result) if result else None
                finally:
                    self._release_cursor(cursor, conn)

            return get_by_id

        elif name == 'delete_by_id':
            if not self.has_field("id") and self._can_delete:
                raise AttributeError(f"table '{self.get_table_name()}' has no column named 'id'")

            def delete_by_id(id: int) -> bool:
                """
                删除指定id的记录

                :param id: 数据id
                :return: 删除成功返回True, 否则返回False
                """
                sql = f"DELETE * FROM {self.get_table_name()} WHERE id = %s"
                try:
                    cursor, conn = self._get_cursor()
                    cursor.execute(sql, (id,))
                    result = cursor.fetchone()
                    return self._model_class(*result) if result else None
                finally:
                    self._release_cursor(cursor, conn)

            return delete_by_id

        else:
            raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def has_field(self, field_name: str) -> bool:
        """
        判断当前表是否包含指定字段

        :param field_name: 字段名
        :return: bool
        """
        sql = f"SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '{self.get_table_name()}' AND column_name = '{field_name}');"
        cursor, conn = self._get_cursor()
        cursor.execute(sql)
        has = cursor.fetchone()[0]
        self._release_cursor(cursor, conn)
        return has or False

    def _get_cursor(self):
        """
        获取数据库游标

        :returns: conn.cursor(), conn: 返回数据库游标及数据库连接
        """
        conn = self._connection_pool.get_connection()
        return conn.cursor(), conn

    def _release_cursor(self, cursor, connection):
        """
        释放数据库游标与数据库连接

        :param cursor: 数据库游标
        :param connection: 数据库连接
        """
        cursor.close()
        self._connection_pool.release_connection(connection)

    @abstractmethod
    def get_table_name(self) -> str:
        """
        获取数据库表名

        :return: 数据库表名
        """
        pass

    def create_table(self):
        """
        根据预置sql创建数据库表
        """
        if self.CREATE_TABLE_SQL is None:
            raise ValueError("CREATE_TABLE_SQL is None")

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
