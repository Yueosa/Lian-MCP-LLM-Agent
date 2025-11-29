from psycopg2 import pool


class PostgreSQLConnectionPool:
    """PostgreSQL 数据库连接池管理类
    
    封装了 psycopg2 的 ThreadedConnectionPool，提供连接的获取和释放功能。
    """
    
    def __init__(self, minconn=1, maxconn=10, **kwargs):
        """初始化连接池
        
        Args:
            minconn: 连接池中的最小连接数
            maxconn: 连接池中的最大连接数
            **kwargs: 传递给 psycopg2 的连接参数，如 host, port, dbname, user, password 等
        """
        self._pool = pool.ThreadedConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            **kwargs
        )
        self._kwargs = kwargs

    def get_connection(self):
        """获取数据库连接
        
        Returns:
            数据库连接对象
        """
        return self._pool.getconn()

    def release_connection(self, conn):
        """释放数据库连接回连接池
        
        Args:
            conn: 要释放的数据库连接对象
        """
        self._pool.putconn(conn)

    def clear_connections(self):
        """关闭所有连接
        
        清空连接池中的所有连接。
        """
        self._pool.closeall()

    @property
    def pool_size(self) -> int:
        """获取连接池的最大连接数
        
        Returns:
            连接池的最大连接数
        """
        return self._pool.maxconn
