from typing import Optional, Type, Any, List, Dict
from pydantic import BaseModel, Field


# ============================================
# TableMeta 模型：表结构元数据（Pydantic）
# ============================================
class ColumnMeta(BaseModel):
    """表列元数据 - Pydantic 模型"""
    name: str = Field(..., description="列名")
    sql_type: str = Field(..., description="原始 SQL 类型，如 VARCHAR(64)")
    is_primary_key: bool = Field(default=False, description="是否为主键")
    is_nullable: bool = Field(default=True, description="是否允许 NULL")
    default_value: Optional[str] = Field(default=None, description="默认值")
    is_foreign_key: bool = Field(default=False, description="是否为外键")
    fk_table: Optional[str] = Field(default=None, description="外键关联的表名")
    fk_column: Optional[str] = Field(default=None, description="外键关联的列名")
    comment: str = Field(default="", description="列注释")

    class Config:
        """Pydantic 配置"""
        frozen = False
        use_enum_values = False

    def python_type(self) -> Type:
        """将 SQL 类型映射到 Python 类型"""
        sql_lower = self.sql_type.lower()
        if "varchar" in sql_lower or "text" in sql_lower:
            return str
        elif "int" in sql_lower or "serial" in sql_lower:
            return int
        elif "float" in sql_lower or "double" in sql_lower or "numeric" in sql_lower:
            return float
        elif "timestamp" in sql_lower or "date" in sql_lower:
            return Any  # datetime 需要手动处理
        elif "boolean" in sql_lower or "bool" in sql_lower:
            return bool
        elif "jsonb" in sql_lower or "json" in sql_lower:
            return dict
        elif "vector" in sql_lower:
            return list
        else:
            return Any

    @property
    def is_json_type(self) -> bool:
        """是否为 JSON 类型 (json, jsonb)"""
        sql_lower = self.sql_type.lower()
        return "json" in sql_lower or "jsonb" in sql_lower

    @property
    def is_vector_type(self) -> bool:
        """是否为向量类型 (vector)"""
        sql_lower = self.sql_type.lower()
        return "vector" in sql_lower


class TableMeta(BaseModel):
    """表元数据 - Pydantic 模型"""
    name: str = Field(..., description="表名")
    columns: List[ColumnMeta] = Field(default_factory=list, description="列元数据列表")
    create_table_sql: str = Field(default="", description="原始 CREATE TABLE 语句")
    indexes: List[str] = Field(default_factory=list, description="索引列表")

    class Config:
        """Pydantic 配置"""
        frozen = False
        use_enum_values = False

    def get_table_name(self) -> str:
        """返回表名"""
        return self.name
    
    def get_allowed_fields(self) -> List[str]:
        """返回所有可查询的字段（包括外键字段）
        
        排除规则：
        - 列名以 '--' 开头的（注释列，解析错误产生的）
        - 列名为空的
        """
        return [
            col.name for col in self.columns 
            if col.name and not col.name.startswith('--')
        ]

    def get_primary_key(self) -> Optional[str]:
        """返回主键字段名"""
        for col in self.columns:
            if col.is_primary_key:
                return col.name
        return None

    def get_column(self, name: str) -> Optional[ColumnMeta]:
        """按名称获取列"""
        for col in self.columns:
            if col.name == name:
                return col
        return None
