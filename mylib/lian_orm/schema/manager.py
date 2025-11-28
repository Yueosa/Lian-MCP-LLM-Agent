from typing import Optional, Callable, Any
from .localfile.parser import SqlParser
from .metadata.metadata import SchemaMeta, TableMeta, ColumnMeta

class SchemaManager:
    """Schema管理器, 提供对Schema元数据的访问接口"""

    def __init__(self, sql_file_path: Optional[str] = None):
        self.parser = SqlParser()
        self.schema: Optional[SchemaMeta] = None
        if sql_file_path:
            self.load_from_file(sql_file_path)

    def load_from_file(self, file_path: str):
        """从本地SQL文件加载Schema"""
        self.schema = self.parser.parse_file(file_path)

    def load_from_remote(self, url: str):
        """从远程URL加载Schema (暂未实现)"""
        raise NotImplementedError("Remote loading is not supported yet.")

    def get_table(self, table_name: str) -> TableMeta:
        """获取指定表的元数据"""
        if not self.schema:
             raise RuntimeError("Schema not loaded. Please call load_from_file() first.")
        if table_name not in self.schema.tables:
             raise ValueError(f"Table '{table_name}' not found in schema.")
        return self.schema.tables[table_name]

    def _get_field(self, table_name: str, field_name: str) -> ColumnMeta:
        """获取指定表字段的元数据"""
        table = self.get_table(table_name)
        if field_name not in table.columns:
             raise ValueError(f"Column '{field_name}' not found in table '{table_name}'.")
        return table.columns[field_name]

    def __getattr__(self, name: str) -> Callable[..., Any]:
        """动态处理 get_table_{name} 和 get_field_{name} 方法"""
        
        # 处理 get_table_{table_name}()
        if name.startswith("get_table_"):
            table_name = name[len("get_table_"):]
            
            def get_table_wrapper():
                return self.get_table(table_name)
            
            return get_table_wrapper
        
        # 处理 get_field_{table_name}(field_name)
        if name.startswith("get_field_"):
            table_name = name[len("get_field_"):]
            
            def get_field_wrapper(field_name: str):
                return self._get_field(table_name, field_name)
                
            return get_field_wrapper
            
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @property
    def all_tables(self):
        """获取所有表名"""
        if not self.schema:
            return []
        return list(self.schema.tables.keys())
