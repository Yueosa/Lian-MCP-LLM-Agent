from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class ColumnMeta:
    """列(Column)元数据描述结构。

    本数据结构仅用于描述数据库表字段的静态结构，不包含任何运行时数据
    name: 字段名
    data_type: 字段类型
    is_primary_key: 是否为主键
    is_nullable: 能否为空
    default: 默认值
    references: 外键引用
    constraints: 字段约束
    description: 注释文本
    """
    name: str
    data_type: str
    is_primary_key: bool = False
    is_nullable: bool = True
    default: Optional[str] = None
    references: Optional[str] = None  # 格式: "table(column)"
    constraints: List[str] = field(default_factory=list)
    description: Optional[str] = None

@dataclass
class IndexMeta:
    """索引(Index)元数据描述结构。

    本结构只表达数据库中的索引定义，不包含任何运行时状态
    name: 索引名
    table: 所属表
    columns: 列名表
    method: 存储、访问方法
    unique: 是否唯一
    definition: 原始定义语句
    """
    name: str
    table_name: str
    columns: List[str]
    method: Optional[str] = None  # e.g., "ivfflat", "btree"
    unique: bool = False
    definition: str = "" # 原始定义语句

@dataclass
class TableMeta:
    """表(Table)元数据结构。

    用于描述一张数据库表的全部结构信息(不包含任何数据)
    name: 表名
    columns: 所有列
    indices: 索引
    primary_key: 主键列名
    comment: 表注释
    """
    name: str
    columns: Dict[str, ColumnMeta] = field(default_factory=dict)
    indices: Dict[str, IndexMeta] = field(default_factory=dict)
    primary_key: List[str] = field(default_factory=list)
    comment: Optional[str] = None

@dataclass
class ExtensionMeta:
    """ SQL 扩展(Extension)元数据。

    描述数据库中需要启用的扩展插件
    name: 扩展名
    if_not_exists: 防止重复安装
    
    """
    name: str
    if_not_exists: bool = True

@dataclass
class SchemaMeta:
    """完整 Schema 的元数据

    表示一个数据库结构的整体
    tables: 所有表
    extensions: 所有扩展
    """
    tables: Dict[str, TableMeta] = field(default_factory=dict)
    extensions: List[ExtensionMeta] = field(default_factory=list)

    def get_table(self, name: str) -> TableMeta:
        return self.tables.get(name)
    
    def add_table(self, table: TableMeta) -> None:
        self.tables[table.name] = table
