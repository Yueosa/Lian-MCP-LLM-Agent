from typing import Any, List, Optional, Dict
from contextlib import contextmanager
from .pool import PostgreSQLConnectionPool

class DatabaseClient:
    def __init__(self, connection_pool: PostgreSQLConnectionPool):
        self._pool = connection_pool

    @contextmanager
    def _get_cursor(self):
        conn = self._pool.get_connection()
        try:
            cursor = conn.cursor()
            yield cursor, conn
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self._pool.release_connection(conn)

    def execute(self, sql: str, params: Optional[List[Any]] = None) -> int:
        """Execute a write operation (INSERT, UPDATE, DELETE)"""
        with self._get_cursor() as (cursor, conn):
            cursor.execute(sql, params or [])
            conn.commit()
            return cursor.rowcount

    def execute_returning(self, sql: str, params: Optional[List[Any]] = None) -> Any:
        """Execute an operation that returns a value (e.g. INSERT ... RETURNING id)"""
        with self._get_cursor() as (cursor, conn):
            cursor.execute(sql, params or [])
            result = cursor.fetchone()
            conn.commit()
            return result[0] if result else None

    def fetch_all(self, sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Execute a read operation and return list of dicts"""
        with self._get_cursor() as (cursor, conn):
            cursor.execute(sql, params or [])
            if cursor.description is None:
                return []
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]

    def fetch_one(self, sql: str, params: Optional[List[Any]] = None) -> Optional[Dict[str, Any]]:
        """Execute a read operation and return single dict"""
        with self._get_cursor() as (cursor, conn):
            cursor.execute(sql, params or [])
            if cursor.description is None:
                return None
            columns = [desc[0] for desc in cursor.description]
            result = cursor.fetchone()
            return dict(zip(columns, result)) if result else None
