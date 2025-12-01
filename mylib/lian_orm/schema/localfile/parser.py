from enum import Enum, auto
from typing import List, Optional, Any
from mylib.kit.Lparser import LParserBase
from mylib.kit.Ltokenizer import LToken
from mylib.kit.Lpda import ScopeDef
from .tokenizer import SqlTokenType, SqlTokenizer
from ..metadata import TableMeta, ColumnMeta, SchemaMeta, IndexMeta, ExtensionMeta


class SqlParserState(Enum):
    IDLE = auto()
    
    # 表相关状态
    EXPECT_TABLE_NAME = auto()
    EXPECT_TABLE_OPEN_PAREN = auto()
    INSIDE_TABLE_BODY = auto()
    
    # 索引相关状态
    EXPECT_INDEX_NAME = auto()
    EXPECT_INDEX_ON = auto()
    EXPECT_INDEX_TABLE = auto()
    EXPECT_INDEX_USING = auto()
    EXPECT_INDEX_COLUMNS = auto()
    
    # 扩展相关状态
    EXPECT_EXTENSION_NAME = auto()

class SqlScope(Enum):
    TABLE_BODY = ScopeDef("TABLE_BODY", "(", ")", "表定义主体")
    PAREN = ScopeDef("PAREN", "(", ")", "普通括号")

class SqlParser(LParserBase[SqlParserState, Any, SqlScope]):
    def __init__(self):
        super().__init__(SqlParserState.IDLE, scope_enum=SqlScope)
        self.schema = SchemaMeta()
        
        # 上下文变量
        self.current_table: Optional[TableMeta] = None
        self.current_index: Optional[IndexMeta] = None
        self.temp_index_unique = False

    def parse_file(self, file_path: str) -> SchemaMeta:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_string(content)

    def parse_string(self, content: str) -> SchemaMeta:
        tokenizer = SqlTokenizer()
        tokens = tokenizer.parse(content)
        self.parse(tokens)
        return self.schema

    # --- 空闲状态处理 ---
    def handle_idle(self, token: LToken, i: int, tokens: List[LToken], n: int) -> Optional[int]:
        if token.type == SqlTokenType.KEYWORD and token.value.upper() == "CREATE":
            # 向前查看我们要创建什么
            if i + 1 < n:
                next_token = tokens[i+1]
                val = next_token.value.upper()
                
                if val == "TABLE":
                    self.switch_state(SqlParserState.EXPECT_TABLE_NAME)
                    return i + 2
                elif val == "OR":
                    # CREATE OR REPLACE ...
                    # 跳过 OR, REPLACE
                    # 简单的跳过逻辑：找到下一个关键字是 TABLE/FUNCTION 等
                    # 目前假设不支持或简单处理 CREATE OR REPLACE FUNCTION/VIEW 等
                    # 但如果是 CREATE OR REPLACE TABLE (标准 SQL 中少见但在某些方言中可能)
                    pass
                elif val == "UNIQUE":
                    self.temp_index_unique = True
                    # 接下来期望 INDEX
                    if i + 2 < n and tokens[i+2].value.upper() == "INDEX":
                        self.switch_state(SqlParserState.EXPECT_INDEX_NAME)
                        return i + 3
                elif val == "INDEX":
                    self.temp_index_unique = False
                    self.switch_state(SqlParserState.EXPECT_INDEX_NAME)
                    return i + 2
                elif val == "EXTENSION":
                    self.switch_state(SqlParserState.EXPECT_EXTENSION_NAME)
                    return i + 2
                    
        return None

    # --- 扩展处理 ---
    def handle_expect_extension_name(self, token: LToken, i: int, tokens: List[LToken], n: int) -> Optional[int]:
        if token.value.upper() in ("IF", "NOT", "EXISTS"):
            return None
        
        if token.type == SqlTokenType.IDENTIFIER or token.type == SqlTokenType.KEYWORD:
            # 找到扩展名
            ext_name = token.value.strip('"')
            self.schema.extensions.append(ExtensionMeta(name=ext_name))
            self.switch_state(SqlParserState.IDLE)
        return None

    # --- 索引处理 ---
    def handle_expect_index_name(self, token: LToken, i: int, tokens: List[LToken], n: int) -> Optional[int]:
        if token.value.upper() in ("IF", "NOT", "EXISTS"):
            return None
        
        if token.type == SqlTokenType.IDENTIFIER:
            idx_name = token.value.strip('"')
            self.current_index = IndexMeta(
                name=idx_name, 
                table_name="", 
                columns=[], 
                unique=self.temp_index_unique
            )
            self.switch_state(SqlParserState.EXPECT_INDEX_ON)
        return None

    def handle_expect_index_on(self, token: LToken, i: int, tokens: List[LToken], n: int) -> Optional[int]:
        if token.value.upper() == "ON":
            self.switch_state(SqlParserState.EXPECT_INDEX_TABLE)
        return None

    def handle_expect_index_table(self, token: LToken, i: int, tokens: List[LToken], n: int) -> Optional[int]:
        if token.type == SqlTokenType.IDENTIFIER:
            table_name = token.value.strip('"')
            if self.current_index:
                self.current_index.table_name = table_name
            self.switch_state(SqlParserState.EXPECT_INDEX_USING)
        return None

    def handle_expect_index_using(self, token: LToken, i: int, tokens: List[LToken], n: int) -> Optional[int]:
        if token.value.upper() == "USING":
            # 下一个 Token 是方法
            if i + 1 < n:
                method = tokens[i+1].value
                if self.current_index:
                    self.current_index.method = method
                self.switch_state(SqlParserState.EXPECT_INDEX_COLUMNS)
                return i + 2
        elif token.value == "(":
            # 跳过 USING，直接处理列
            self.switch_state(SqlParserState.EXPECT_INDEX_COLUMNS)
            return i # 不消耗 '('，让下一个状态处理
        return None

    def handle_expect_index_columns(self, token: LToken, i: int, tokens: List[LToken], n: int) -> Optional[int]:
        if token.value == "(":
            # 开始收集列
            # 我们只消耗 Token 直到 ')'
            # 这是一个简单的实现，不处理索引中的复杂表达式
            j = i + 1
            cols = []
            while j < n:
                t = tokens[j]
                if t.value == ")":
                    if self.current_index:
                        self.current_index.columns = cols
                        # 如果表存在，则添加到表
                        if self.current_index.table_name in self.schema.tables:
                            self.schema.tables[self.current_index.table_name].indices[self.current_index.name] = self.current_index
                    self.current_index = None
                    self.switch_state(SqlParserState.IDLE)
                    return j + 1
                elif t.type == SqlTokenType.IDENTIFIER:
                    cols.append(t.value.strip('"'))
                j += 1
        return None

    # --- 表处理 ---
    def handle_expect_table_name(self, token: LToken, i: int, tokens: List[LToken], n: int) -> Optional[int]:
        if token.value.upper() in ("IF", "NOT", "EXISTS"):
            return None
        
        if token.type == SqlTokenType.IDENTIFIER:
            # 找到表名
            # 处理 schema.table 格式（此处尚未实现）
            table_name = token.value.strip('"')
            self.current_table = TableMeta(name=table_name, columns={})
            self.switch_state(SqlParserState.EXPECT_TABLE_OPEN_PAREN)
        return None

    def handle_expect_table_open_paren(self, token: LToken, i: int, tokens: List[LToken], n: int) -> Optional[int]:
        if token.value == "(":
            self.switch_state(SqlParserState.INSIDE_TABLE_BODY)
            # 使用基类提供的 Scope 方法
            self.enter_scope(SqlScope.TABLE_BODY)
        return None

    def handle_inside_table_body(self, token: LToken, i: int, tokens: List[LToken], n: int) -> Optional[int]:
        # 处理嵌套括号 (例如在 DEFAULT 表达式、CHECK 约束或类型定义中)
        if token.value == "(":
            self.enter_scope(SqlScope.PAREN)
            return None

        # 检查表定义结束或嵌套结束
        if token.value == ")":
            # 获取当前作用域，决定如何处理
            current_instance = self.current_scope()
            if current_instance is None:
                 self.exit_scope("UNKNOWN") # 触发错误
                 return None

            current = current_instance.definition.name
            
            if current == SqlScope.TABLE_BODY.name:
                # 退出 TABLE_BODY 作用域
                self.exit_scope(SqlScope.TABLE_BODY)
                
                if self.current_table:
                    self.schema.tables[self.current_table.name] = self.current_table
                    self.current_table = None
                self.switch_state(SqlParserState.IDLE)
                return None
            
            elif current == SqlScope.PAREN.name:
                # 退出普通括号作用域
                self.exit_scope(SqlScope.PAREN)
                return None
            
            else:
                # 栈为空或未知状态，exit_scope 会自动抛出异常，或者我们可以手动抛出
                # 这里调用 exit_scope 让它去处理空栈或不匹配的情况
                self.exit_scope("UNKNOWN") 
            
        if token.value == ",":
            return None

        # 解析列或约束
        if token.type == SqlTokenType.KEYWORD and token.value.upper() in ("CONSTRAINT", "PRIMARY", "FOREIGN", "CHECK", "UNIQUE"):
            # 表级约束 - 暂时跳过直到下一个逗号或括号
            # 我们只消耗直到遇到 ',' 或 ')'
            # 理想情况下我们应该解析它们。
            pass
        elif token.type == SqlTokenType.IDENTIFIER:
            # 列定义
            return self._parse_column_definition(token, i, tokens, n)
            
        return None

    def _parse_column_definition(self, token: LToken, i: int, tokens: List[LToken], n: int) -> int:
        """
        从 i (列名) 开始解析单个列定义。
        返回解析后的新索引。
        """
        col_name = token.value.strip('"')
        col_type = "UNKNOWN"
        
        # 下一个 Token 应该是类型
        current_idx = i + 1
        if current_idx < n:
            type_token = tokens[current_idx]
            col_type = type_token.value
            # 如果类型有参数如 VARCHAR(255)，消耗它们
            if current_idx + 1 < n and tokens[current_idx+1].value == "(":
                # 消耗 ( ... )
                current_idx += 2
                while current_idx < n and tokens[current_idx].value != ")":
                    col_type += tokens[current_idx].value # 将参数追加到类型字符串，或者忽略
                    current_idx += 1
                if current_idx < n:
                    col_type += ")" # 添加右括号
                    current_idx += 1
            else:
                current_idx += 1
        
        col = ColumnMeta(name=col_name, data_type=col_type)
        
        # 解析约束
        while current_idx < n:
            t = tokens[current_idx]
            val = t.value.upper()
            
            if val == "," or val == ")":
                # 列定义结束
                break
            
            if val == "PRIMARY":
                # 期望 KEY
                if current_idx + 1 < n and tokens[current_idx+1].value.upper() == "KEY":
                    col.is_primary_key = True
                    col.constraints.append("PRIMARY KEY")
                    current_idx += 2
                    continue
            
            if val == "NOT":
                # 期望 NULL
                if current_idx + 1 < n and tokens[current_idx+1].value.upper() == "NULL":
                    col.is_nullable = False
                    col.constraints.append("NOT NULL")
                    current_idx += 2
                    continue
            
            if val == "DEFAULT":
                # 下一个是值
                if current_idx + 1 < n:
                    col.default = tokens[current_idx+1].value
                    current_idx += 2
                    continue
            
            if val == "REFERENCES":
                # REFERENCES table(col)
                if current_idx + 1 < n:
                    ref_table = tokens[current_idx+1].value
                    ref_col = ""
                    current_idx += 2
                    if current_idx < n and tokens[current_idx].value == "(":
                        if current_idx + 1 < n:
                            ref_col = tokens[current_idx+1].value
                            current_idx += 3 # ( col )
                    col.references = f"{ref_table}({ref_col})"
                    continue

            # 如果是未知的约束部分，直接跳过或添加到原始约束
            # 目前仅跳过
            current_idx += 1

        if self.current_table:
            self.current_table.columns[col_name] = col
            if col.is_primary_key:
                self.current_table.primary_key.append(col_name)
                
        return current_idx
