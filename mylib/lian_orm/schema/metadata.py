from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class ColumnMeta:
    """列元数据"""
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
    """索引元数据"""
    name: str
    table_name: str
    columns: List[str]
    method: Optional[str] = None  # e.g., "ivfflat", "btree"
    unique: bool = False
    definition: str = "" # 原始定义语句

@dataclass
class TableMeta:
    """表元数据"""
    name: str
    columns: Dict[str, ColumnMeta] = field(default_factory=dict)
    indices: Dict[str, IndexMeta] = field(default_factory=dict)
    primary_key: Optional[str] = None
    comment: Optional[str] = None

@dataclass
class ExtensionMeta:
    """扩展元数据"""
    name: str
    if_not_exists: bool = True

@dataclass
class SchemaMeta:
    """整个Schema的元数据"""
    tables: Dict[str, TableMeta] = field(default_factory=dict)
    extensions: List[ExtensionMeta] = field(default_factory=list)
