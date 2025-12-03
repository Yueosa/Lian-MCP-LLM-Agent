import json
from enum import Enum
from typing import Any, Dict, Optional

from ..schema.metadata import TableMeta
from .types import SQLTypeMapper


class DataConverter:
    @staticmethod
    def python_to_sql(data: Dict[str, Any], table_meta: Optional[TableMeta] = None) -> Dict[str, Any]:
        """Convert Python dictionary to SQL-compatible dictionary"""
        converted = {}
        for k, v in data.items():
            # 1. Handle Enum
            if isinstance(v, Enum):
                converted[k] = v.value
                continue
            
            # 2. Handle JSON/Vector based on metadata
            if table_meta:
                col_meta = table_meta.columns.get(k)
                if col_meta:
                    if SQLTypeMapper.is_json_type(col_meta.data_type) or SQLTypeMapper.is_vector_type(col_meta.data_type):
                        if not isinstance(v, str):
                            converted[k] = json.dumps(v)
                        else:
                            converted[k] = v
                        continue

            # 3. Fallback for dicts
            if isinstance(v, dict):
                converted[k] = json.dumps(v)
            else:
                converted[k] = v
                
        return converted

    @staticmethod
    def sql_to_python(row_dict: Dict[str, Any], table_meta: Optional[TableMeta] = None) -> Dict[str, Any]:
        """Convert SQL result dictionary to Python dictionary"""
        converted = row_dict.copy()
        
        for k, v in converted.items():
            should_parse = False
            
            # 1. Metadata check
            if table_meta:
                col_meta = table_meta.columns.get(k)
                if col_meta:
                    if SQLTypeMapper.is_json_type(col_meta.data_type) or SQLTypeMapper.is_vector_type(col_meta.data_type):
                        should_parse = True
            
            # 2. Fallback check
            if not should_parse and isinstance(v, str) and len(v) >= 2:
                if (v.startswith('[') and v.endswith(']')) or (v.startswith('{') and v.endswith('}')):
                    should_parse = True
            
            if should_parse and isinstance(v, str):
                try:
                    converted[k] = json.loads(v)
                except Exception:
                    pass
                    
        return converted
