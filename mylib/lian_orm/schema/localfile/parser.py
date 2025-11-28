import re
from enum import Enum, auto
from typing import List, Optional

from mylib.utils import LStateMachine

from ..metadata.metadata import SchemaMeta, TableMeta, ColumnMeta, IndexMeta, ExtensionMeta


class State(Enum):
    NORMAL = auto()          # 普通扫描
    SINGLE_QUOTE = auto()    # ' ... '
    DOUBLE_QUOTE = auto()    # " ... "
    LINE_COMMENT = auto()    # -- ... \n
    BLOCK_COMMENT = auto()   # /* ... */
    DOLLAR_QUOTE = auto()    # $$ 或 $tag$


class SqlSplitter(LStateMachine[State, str]):
    """基于 LStateMachine 的 SQL 语句分割器"""
    
    def __init__(self):
        super().__init__(State.NORMAL)
        
    def handle_normal(self, ch: str, i: int, content: str, n: int) -> int:
        # 1. 检查行注释 --
        if ch == '-' and i + 1 < n and content[i+1] == '-':
            self.switch_state(State.LINE_COMMENT)
            return i + 2
        
        # 2. 检查块注释 /*
        if ch == '/' and i + 1 < n and content[i+1] == '*':
            self.switch_state(State.BLOCK_COMMENT)
            return i + 2
            
        # 3. 检查 Dollar Quote ($$ 或 $tag$)
        if ch == '$':
            match = re.match(r'\$([^$]*)\$', content[i:])
            if match:
                tag = match.group(0)
                self.context['dollar_tag'] = tag
                self.switch_state(State.DOLLAR_QUOTE)
                self.append_buffer(tag)
                return i + len(tag)
        
        # 4. 检查单引号字符串
        if ch == "'":
            self.switch_state(State.SINGLE_QUOTE)
            self.append_buffer(ch)
            return i + 1
            
        # 5. 检查双引号字符串
        if ch == '"':
            self.switch_state(State.DOUBLE_QUOTE)
            self.append_buffer(ch)
            return i + 1
        
        # 6. 检查括号
        if ch == '(':
            self.stack.push('(')
            self.append_buffer(ch)
            return i + 1
        elif ch == ')':
            if not self.stack.is_empty():
                self.stack.pop()
            self.append_buffer(ch)
            return i + 1
            
        # 7. 检查分号 (语句结束)
        if ch == ';':
            if self.stack.is_empty():
                # 语句结束
                stmt = self.flush_buffer()
                if stmt:
                    self.emit(stmt)
                return i + 1
            else:
                # 在括号内的分号，视为普通字符
                self.append_buffer(ch)
                return i + 1
        
        # 普通字符
        self.append_buffer(ch)
        return i + 1

    def handle_line_comment(self, ch: str, i: int, content: str, n: int) -> int:
        if ch == '\n':
            self.switch_state(State.NORMAL)
            self.append_buffer('\n')
        return i + 1

    def handle_block_comment(self, ch: str, i: int, content: str, n: int) -> int:
        if ch == '*' and i + 1 < n and content[i+1] == '/':
            self.switch_state(State.NORMAL)
            self.append_buffer(' ')
            return i + 2
        return i + 1

    def handle_single_quote(self, ch: str, i: int, content: str, n: int) -> int:
        self.append_buffer(ch)
        if ch == "'":
            # 检查转义 ''
            if i + 1 < n and content[i+1] == "'":
                self.append_buffer("'")
                return i + 2
            else:
                self.switch_state(State.NORMAL)
                return i + 1
        return i + 1

    def handle_double_quote(self, ch: str, i: int, content: str, n: int) -> int:
        self.append_buffer(ch)
        if ch == '"':
            # 检查转义 ""
            if i + 1 < n and content[i+1] == '"':
                self.append_buffer('"')
                return i + 2
            else:
                self.switch_state(State.NORMAL)
                return i + 1
        return i + 1

    def handle_dollar_quote(self, ch: str, i: int, content: str, n: int) -> int:
        tag = self.context.get('dollar_tag', '$$')
        if content.startswith(tag, i):
            self.append_buffer(tag)
            self.switch_state(State.NORMAL)
            return i + len(tag)
        else:
            self.append_buffer(ch)
            return i + 1

    def on_finish(self):
        stmt = self.flush_buffer()
        if stmt:
            self.emit(stmt)


class SqlParser:
    """SQL解析器, 用于正则解析.sql文件并生成SchemaMeta"""

    def __init__(self):
        self.schema = SchemaMeta()
        self.splitter = SqlSplitter()

    def parse_file(self, file_path: str) -> SchemaMeta:
        """解析SQL文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_string(content)

    def parse_string(self, content: str) -> SchemaMeta:
        """解析SQL字符串"""
        # 使用状态机分割语句
        statements = self.splitter.parse(content)
        
        # 解析每个语句
        for stmt in statements:
            stmt = stmt.strip()
            if not stmt:
                continue
            
            if self._is_create_table(stmt):
                self._parse_create_table(stmt)
            elif self._is_create_index(stmt):
                self._parse_create_index(stmt)
            elif self._is_create_extension(stmt):
                self._parse_create_extension(stmt)
                
        return self.schema

    # ...existing code...
    def _is_create_table(self, stmt: str) -> bool:
        return re.match(r'CREATE\s+TABLE', stmt, re.IGNORECASE) is not None

    def _is_create_index(self, stmt: str) -> bool:
        return re.match(r'CREATE\s+(UNIQUE\s+)?INDEX', stmt, re.IGNORECASE) is not None

    def _is_create_extension(self, stmt: str) -> bool:
        return re.match(r'CREATE\s+EXTENSION', stmt, re.IGNORECASE) is not None

    def _parse_create_extension(self, stmt: str):
        match = re.search(r'CREATE\s+EXTENSION\s+(IF\s+NOT\s+EXISTS\s+)?(\w+)', stmt, re.IGNORECASE)
        if match:
            if_not_exists = bool(match.group(1))
            name = match.group(2)
            self.schema.extensions.append(ExtensionMeta(name=name, if_not_exists=if_not_exists))

    def _parse_create_table(self, stmt: str):
        # 提取表名
        # CREATE TABLE IF NOT EXISTS table_name ( ... )
        match = re.match(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\((.*)\)', stmt, re.IGNORECASE | re.DOTALL)
        if not match:
            return

        table_name = match.group(1)
        body = match.group(2)
        
        table_meta = TableMeta(name=table_name)
        
        # 分割列定义
        # 需要处理括号嵌套，例如 DECIMAL(10, 2)
        columns_defs = self._split_columns(body)
        
        for col_def in columns_defs:
            col_meta = self._parse_column_definition(col_def)
            if col_meta:
                table_meta.columns[col_meta.name] = col_meta
                if col_meta.is_primary_key:
                    table_meta.primary_key = col_meta.name

        self.schema.tables[table_name] = table_meta

    def _split_columns(self, body: str) -> List[str]:
        """分割列定义，处理括号"""
        defs = []
        current = []
        paren_count = 0
        
        for char in body:
            if char == '(':
                paren_count += 1
                current.append(char)
            elif char == ')':
                paren_count -= 1
                current.append(char)
            elif char == ',' and paren_count == 0:
                defs.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
        
        if current:
            defs.append(''.join(current).strip())
            
        return defs

    def _parse_column_definition(self, col_def: str) -> Optional[ColumnMeta]:
        """解析单个列定义"""
        # 示例: id SERIAL PRIMARY KEY
        # 示例: user_id VARCHAR(64) DEFAULT 'default'
        # 示例: task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE
        
        parts = col_def.split()
        if not parts:
            return None
            
        name = parts[0]
        if len(parts) < 2:
            return None
            
        # 类型可能包含括号，如 VARCHAR(64)
        data_type = parts[1]
        
        # 剩余部分是约束
        # 不直接upper，以免破坏DEFAULT中的字符串大小写
        constraints_raw = ' '.join(parts[2:])
        constraints_upper = constraints_raw.upper()
        
        is_primary_key = 'PRIMARY KEY' in constraints_upper
        is_nullable = 'NOT NULL' not in constraints_upper
        
        default_val = None
        # 使用 case-insensitive regex 匹配 DEFAULT
        default_match = re.search(r'DEFAULT\s+([^,\s]+|\'[^\']*\')', constraints_raw, re.IGNORECASE)
        if default_match:
            default_val = default_match.group(1)
            
        references = None
        ref_match = re.search(r'REFERENCES\s+(\w+)\s*\((\w+)\)', constraints_raw, re.IGNORECASE)
        if ref_match:
            references = f"{ref_match.group(1)}({ref_match.group(2)})"
            
        return ColumnMeta(
            name=name,
            data_type=data_type,
            is_primary_key=is_primary_key,
            is_nullable=is_nullable,
            default=default_val,
            references=references,
            constraints=parts[2:] # 保存原始约束部分
        )

    def _parse_create_index(self, stmt: str):
        # CREATE INDEX IF NOT EXISTS idx_name ON table_name USING method (col1, col2) ...
        match = re.match(r'CREATE\s+(UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+ON\s+(\w+)', stmt, re.IGNORECASE)
        if not match:
            return
            
        is_unique = bool(match.group(1))
        index_name = match.group(2)
        table_name = match.group(3)
        
        # 尝试解析列和方法
        rest = stmt[match.end():].strip()
        
        method = None
        method_match = re.match(r'USING\s+(\w+)', rest, re.IGNORECASE)
        if method_match:
            method = method_match.group(1)
            
        # 提取括号内的列
        # 寻找第一个左括号和对应的右括号
        start_paren = rest.find('(')
        end_paren = rest.find(')', start_paren)
        
        columns = []
        if start_paren != -1 and end_paren != -1:
            cols_str = rest[start_paren+1:end_paren]
            # 处理列名，可能包含 opclass (e.g., embedding vector_l2_ops)
            columns = [c.strip().split()[0] for c in cols_str.split(',')]
            
        index_meta = IndexMeta(
            name=index_name,
            table_name=table_name,
            columns=columns,
            method=method,
            unique=is_unique,
            definition=stmt
        )
        
        # 将索引添加到对应的表元数据中
        if table_name in self.schema.tables:
            self.schema.tables[table_name].indices[index_name] = index_meta
