from typing import Any, Type

class SQLTypeMapper:
    """SQL类型到Python类型的映射器"""

    @staticmethod
    def map_to_python_type(sql_type: str) -> Type:
        """将 SQL 类型映射到 Python 类型"""
        sql_lower = sql_type.lower()
        
        if "varchar" in sql_lower or "text" in sql_lower or "char" in sql_lower:
            return str
        elif "int" in sql_lower or "serial" in sql_lower:
            return int
        elif "float" in sql_lower or "double" in sql_lower or "numeric" in sql_lower or "real" in sql_lower:
            return float
        elif "timestamp" in sql_lower or "date" in sql_lower:
            # 通常返回 datetime 对象，但在某些简单场景下可能是 Any 或 str
            return Any 
        elif "boolean" in sql_lower or "bool" in sql_lower:
            return bool
        elif "jsonb" in sql_lower or "json" in sql_lower:
            return dict
        elif "vector" in sql_lower:
            return list
        else:
            return Any

    @staticmethod
    def is_json_type(sql_type: str) -> bool:
        """是否为 JSON 类型 (json, jsonb)"""
        sql_lower = sql_type.lower()
        return "json" in sql_lower or "jsonb" in sql_lower

    @staticmethod
    def is_vector_type(sql_type: str) -> bool:
        """是否为向量类型 (vector)"""
        sql_lower = sql_type.lower()
        return "vector" in sql_lower
