import psycopg2


class PostgreSQLConnectionPool:
    def __init__(self, minconn=1, maxconn=10, **kwargs):
        self._pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=minconn,
            maxconn=maxconn,
            **kwargs
        )
        self._kwargs = kwargs

    def get_connection(self):
        return self._pool.getconn()

    def release_connection(self, conn):
        self._pool.putconn(conn)

    def clear_connections(self):
        self._pool.closeall()

    @property
    def pool_size(self) -> int:
        return self._pool.maxconn
