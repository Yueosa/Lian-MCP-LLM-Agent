import re
from pathlib import Path
from typing import Dict, List, Optional

from .SqlBase import TableMeta, ColumnMeta


# ============================================
# SqlLoader：解析 SQL 并生成表元数据
# ============================================
class SqlLoader:
    """从 SQL 文件动态加载表结构并生成元数据"""

    def __init__(self, sql_file_path: str):
        self.sql_file_path = Path(sql_file_path)
        self.tables: Dict[str, TableMeta] = {}
        self.raw_sql = ""

    def load(self) -> Dict[str, TableMeta]:
        """加载并解析 SQL 文件"""
        if not self.sql_file_path.exists():
            raise FileNotFoundError(f"SQL file not found: {self.sql_file_path}")

        with open(self.sql_file_path, 'r', encoding='utf-8') as f:
            self.raw_sql = f.read()

        create_table_blocks = re.split(r'(?i)CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS', self.raw_sql)
        
        for block in create_table_blocks[1:]:
            table_meta = self._parse_create_table(block)
            if table_meta:
                self.tables[table_meta.name] = table_meta

        return self.tables

    def _parse_create_table(self, block: str) -> Optional[TableMeta]:
        """解析单个 CREATE TABLE 块"""
        table_name_match = re.match(r'\s*(\w+)\s*\(', block)
        if not table_name_match:
            return None

        table_name = table_name_match.group(1)
        
        paren_start = block.find('(')
        paren_end = block.rfind(')')
        if paren_start == -1 or paren_end == -1:
            return None

        columns_str = block[paren_start + 1:paren_end]
        
        columns = self._parse_columns(columns_str)
        
        raw_create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"
        
        table_meta = TableMeta(
            name=table_name,
            columns=columns,
            create_table_sql=raw_create_sql
        )

        return table_meta

    def _parse_columns(self, columns_str: str) -> List[ColumnMeta]:
        """解析列定义字符串"""
        columns = []
        
        col_defs = self._split_columns(columns_str)
        
        for col_def in col_defs:
            col_def = col_def.strip()
            if not col_def or col_def.upper().startswith("CONSTRAINT"):
                continue

            col_meta = self._parse_single_column(col_def)
            if col_meta:
                columns.append(col_meta)

        return columns

    def _split_columns(self, columns_str: str) -> List[str]:
        """按逗号分割列定义，考虑括号嵌套"""
        result = []
        current = ""
        depth = 0

        for char in columns_str:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ',' and depth == 0:
                result.append(current)
                current = ""
                continue

            current += char

        if current.strip():
            result.append(current)

        return result

    def _parse_single_column(self, col_def: str) -> Optional[ColumnMeta]:
        """解析单列定义"""
        tokens = col_def.split()
        if not tokens:
            return None

        name = tokens[0]
        
        sql_type_tokens = []
        idx = 1
        constraints = []
        
        while idx < len(tokens):
            token_upper = tokens[idx].upper()
            
            if token_upper in ("PRIMARY", "REFERENCES", "DEFAULT", "NOT", "CHECK", "UNIQUE", "CONSTRAINT"):
                break
            
            sql_type_tokens.append(tokens[idx])
            idx += 1

        sql_type = " ".join(sql_type_tokens)
        
        is_primary_key = False
        is_nullable = True
        default_value = None
        is_foreign_key = False
        fk_table = None
        fk_column = None
        
        while idx < len(tokens):
            token_upper = tokens[idx].upper()
            
            if token_upper == "PRIMARY":
                is_primary_key = True
                idx += 2
            elif token_upper == "NOT":
                if idx + 1 < len(tokens) and tokens[idx + 1].upper() == "NULL":
                    is_nullable = False
                    idx += 2
                else:
                    idx += 1
            elif token_upper == "DEFAULT":
                if idx + 1 < len(tokens):
                    default_value = tokens[idx + 1]
                    idx += 2
                else:
                    idx += 1
            elif token_upper == "REFERENCES":
                is_foreign_key = True
                if idx + 1 < len(tokens):
                    fk_table = tokens[idx + 1]
                    if idx + 2 < len(tokens) and tokens[idx + 2].startswith("("):
                        fk_column_match = re.search(r'\((\w+)\)', tokens[idx + 2])
                        if fk_column_match:
                            fk_column = fk_column_match.group(1)
                    idx += 3
                else:
                    idx += 1
            else:
                idx += 1

        return ColumnMeta(
            name=name,
            sql_type=sql_type,
            is_primary_key=is_primary_key,
            is_nullable=is_nullable,
            default_value=default_value,
            is_foreign_key=is_foreign_key,
            fk_table=fk_table,
            fk_column=fk_column
        )

    def get_table_meta(self, table_name: str) -> Optional[TableMeta]:
        """获取指定表的元数据"""
        return self.tables.get(table_name)

    def get_table_create_sql(self, table_name: str) -> Optional[str]:
        """获取指定表的原始 CREATE TABLE SQL 语句"""
        table_meta = self.tables.get(table_name)
        if table_meta:
            return table_meta.create_table_sql
        return None

    def get_all_tables(self) -> Dict[str, TableMeta]:
        """获取所有表的元数据"""
        return self.tables

    def print_tables(self):
        """打印所有表和列信息"""
        for table_name, table_meta in self.tables.items():
            print(f"\n表: {table_name}")
            print(f"  字段数: {len(table_meta.columns)}")
            for col in table_meta.columns:
                pk_str = " [PK]" if col.is_primary_key else ""
                fk_str = f" [FK->{col.fk_table}({col.fk_column})]" if col.is_foreign_key else ""
                nullable_str = "" if col.is_nullable else " NOT NULL"
                print(f"    - {col.name}: {col.sql_type}{pk_str}{fk_str}{nullable_str}")


# ============================================
# 全局加载器实例（单例）
# ============================================
_loader_instance: Optional[SqlLoader] = None


def get_sql_loader(sql_file_path: Optional[str] = None) -> SqlLoader:
    """获取或创建 SqlLoader 实例"""
    global _loader_instance
    
    if _loader_instance is None:
        if sql_file_path is None:
            sql_file_path = str(Path(__file__).parent / "LML_SQL.sql")
        
        _loader_instance = SqlLoader(str(sql_file_path))
        _loader_instance.load()
    
    return _loader_instance
