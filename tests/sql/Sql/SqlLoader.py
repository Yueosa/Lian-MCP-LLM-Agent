import re
from pathlib import Path
from typing import Dict, List, Optional, Union

from .SqlBase import TableMeta, ColumnMeta, RelationMeta
from ..Repo.DBPool import PostgreSQLConnectionPool # type: ignore


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
# DatabaseMetaLoader：从数据库直接加载表结构元数据
# ============================================
class DatabaseMetaLoader:
    """从数据库直接加载表结构元数据"""
    
    def __init__(self, connection_pool: PostgreSQLConnectionPool):
        """初始化数据库元数据加载器
        
        Args:
            connection_pool: 数据库连接池
        """
        self.connection_pool = connection_pool
        self.tables: Dict[str, TableMeta] = {}
    
    def load(self, schema: str = 'public') -> Dict[str, TableMeta]:
        """从数据库加载表结构元数据
        
        Args:
            schema: 数据库模式名，默认为 'public'
            
        Returns:
            表名到表元数据的映射
        """
        conn = self.connection_pool.get_connection()
        try:
            with conn.cursor() as cursor:
                # 获取所有表名
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s
                    ORDER BY table_name
                """, (schema,))
                
                table_names = [row[0] for row in cursor.fetchall()]
                
                # 为每个表加载元数据
                for table_name in table_names:
                    table_meta = self._load_table_meta(cursor, table_name, schema)
                    if table_meta:
                        self.tables[table_name] = table_meta
                
                # 加载所有外键关系
                self._load_foreign_key_relations(cursor, schema)
                
                return self.tables
        finally:
            self.connection_pool.release_connection(conn)
    
    def _load_table_meta(self, cursor, table_name: str, schema: str) -> Optional[TableMeta]:
        """加载单个表的元数据"""
        # 获取列信息
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable, 
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, table_name))
        
        columns = []
        column_rows = cursor.fetchall()
        
        for row in column_rows:
            column_name, data_type, is_nullable, column_default, max_length, precision, scale = row
            
            # 构建完整的SQL类型
            sql_type = data_type.upper()
            if data_type.lower() in ['varchar', 'character varying'] and max_length:
                sql_type = f"VARCHAR({max_length})"
            elif data_type.lower() in ['numeric', 'decimal'] and precision:
                sql_type = f"NUMERIC({precision},{scale or 0})"
            
            column_meta = ColumnMeta(
                name=column_name,
                sql_type=sql_type,
                is_primary_key=False,  # 稍后设置
                is_nullable=is_nullable == 'YES',
                default_value=column_default
            )
            columns.append(column_meta)
        
        # 获取主键信息
        cursor.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_schema = %s
                AND tc.table_name = %s
        """, (schema, table_name))
        
        pk_rows = cursor.fetchall()
        pk_columns = [row[0] for row in pk_rows]
        
        # 设置主键标志
        for col in columns:
            if col.name in pk_columns:
                col.is_primary_key = True
        
        # 获取表的创建SQL（简化版）
        create_table_sql = f"CREATE TABLE {table_name} (\n"
        create_table_sql += ",\n".join([
            f"    {col.name} {col.sql_type}{' NOT NULL' if not col.is_nullable else ''}"
            for col in columns
        ])
        create_table_sql += "\n)"
        
        return TableMeta(
            name=table_name,
            columns=columns,
            create_table_sql=create_table_sql
        )
    
    def _load_foreign_key_relations(self, cursor, schema: str):
        """加载所有外键关系"""
        cursor.execute("""
            SELECT
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule,
                rc.update_rule
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints AS rc
                ON tc.constraint_name = rc.constraint_name
                AND tc.table_schema = rc.constraint_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_schema = %s
        """, (schema,))
        
        fk_rows = cursor.fetchall()
        
        for row in fk_rows:
            table_name, column_name, foreign_table_name, foreign_column_name, delete_rule, update_rule = row
            
            # 更新列的外键信息
            if table_name in self.tables:
                table_meta = self.tables[table_name]
                column = table_meta.get_column(column_name)
                if column:
                    column.is_foreign_key = True
                    column.fk_table = foreign_table_name
                    column.fk_column = foreign_column_name
                
                # 创建关系元数据
                relation_name = f"{table_name}_{column_name}_to_{foreign_table_name}_{foreign_column_name}"
                relation_type = "many_to_one"  # 默认为多对一
                
                # 创建关系
                relation = RelationMeta(
                    name=relation_name,
                    type=relation_type,
                    source_table=table_name,
                    source_column=column_name,
                    target_table=foreign_table_name,
                    target_column=foreign_column_name,
                    on_delete=delete_rule,
                    on_update=update_rule
                )
                
                table_meta.add_relation(relation)
    
    def get_table_meta(self, table_name: str) -> Optional[TableMeta]:
        """获取指定表的元数据"""
        return self.tables.get(table_name)
    
    def get_all_tables(self) -> Dict[str, TableMeta]:
        """获取所有表的元数据"""
        return self.tables


# ============================================
# 全局加载器实例（单例）
# ============================================
_loader_instance: Optional[Union[SqlLoader, DatabaseMetaLoader]] = None
_loader_type: str = "file"  # "file" 或 "database"


def get_sql_loader(sql_file_path: Optional[str] = None, 
                    connection_pool: Optional[PostgreSQLConnectionPool] = None,
                    loader_type: str = "file") -> Union[SqlLoader, DatabaseMetaLoader]:
    """获取或创建 SQL 加载器实例
    
    Args:
        sql_file_path: SQL文件路径（仅当loader_type="file"时使用）
        connection_pool: 数据库连接池（仅当loader_type="database"时使用）
        loader_type: 加载器类型，"file"或"database"
        
    Returns:
        SQL加载器实例
    """
    global _loader_instance, _loader_type
    
    # 如果加载器类型改变，需要重新创建实例
    if _loader_instance is None or _loader_type != loader_type:
        if loader_type == "file":
            if sql_file_path is None:
                sql_file_path = Path(__file__).parent / "LML_SQL.sql"
            
            _loader_instance = SqlLoader(str(sql_file_path))
            _loader_instance.load()
        elif loader_type == "database":
            if connection_pool is None:
                raise ValueError("当loader_type='database'时，必须提供connection_pool参数")
            
            _loader_instance = DatabaseMetaLoader(connection_pool)
            _loader_instance.load()
        else:
            raise ValueError(f"不支持的loader_type: {loader_type}，必须是'file'或'database'")
        
        _loader_type = loader_type
    
    return _loader_instance
