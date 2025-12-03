from enum import Enum, auto
from typing import List, Optional, Any

from mylib.kit.Lparser import LParserBase
from mylib.kit.Ltokenizer import LToken
from mylib.kit.Lpda import ScopeDef

from ..metadata import TableMeta, ColumnMeta, SchemaMeta, IndexMeta, ExtensionMeta
from .tokenizer import SqlTokenType, SqlTokenizer


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
        """解析.sql文本"""
        super().__init__(SqlParserState.IDLE, scope_enum=SqlScope)
        self.schema = SchemaMeta()

    def parse_file(self, file_path: str) -> SchemaMeta:
        """打开文件, 返回parse_string处理过的文本对象"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_string(content)

    def parse_string(self, content: str) -> SchemaMeta:
        """调用SqlTokenizer, 将处理得到的 token 列表传入 parse 解析流, 返回 SchemaMeta"""
        tokenizer = SqlTokenizer()
        tokens = tokenizer.parse(content)
        self.parse(tokens)
        return self.schema

    def handle_idle(self, token: LToken, i: int, tokens: List[LToken], n: int) -> int:
        """
        处理 IDLE 状态。
        主要职责:
        1. 识别 CREATE 语句 (TABLE, INDEX, EXTENSION)
        2. 初始化相应的上下文
        3. 切换到对应的 EXPECT 状态
        """
        if token.type == SqlTokenType.KEYWORD:
            match token.value.upper():
                case "CREATE":
                    if i + 1 < n:
                        next_token = tokens[i+1]
                        match next_token.value.upper():
                            case "TABLE":
                                self.switch_state(SqlParserState.EXPECT_TABLE_NAME)
                                return i + 2
                            case "UNIQUE":
                                self.context["temp_index_unique"] = True
                                if i + 2 < n and tokens[i+2].value.upper() == "INDEX":
                                    self.switch_state(SqlParserState.EXPECT_INDEX_NAME)
                                    return i + 3
                            case "INDEX":
                                self.context["temp_index_unique"] = False
                                self.switch_state(SqlParserState.EXPECT_INDEX_NAME)
                                return i + 2
                            case "EXTENSION":
                                self.switch_state(SqlParserState.EXPECT_EXTENSION_NAME)
                                return i + 2
                            case _:
                                pass
        return i + 1

    # --- 扩展处理 ---
    def handle_expect_extension_name(self, token: LToken, i: int, tokens: List[LToken], n: int) -> int:
        """
        处理 EXPECT_EXTENSION_NAME 状态。
        主要职责:
        1. 跳过 IF, NOT, EXISTS 修饰符
        2. 提取扩展名并存入 schema
        3. 返回 IDLE 状态
        """
        match token.value.upper():
            case "IF" | "NOT" | "EXISTS":
                return i + 1
            case _:
                if token.type in (SqlTokenType.IDENTIFIER, SqlTokenType.KEYWORD):
                    self.schema.extensions.append(ExtensionMeta(name=token.value.strip('"')))
                    self.switch_state(SqlParserState.IDLE)
                return i + 1

    # --- 索引处理 ---
    def handle_expect_index_name(self, token: LToken, i: int, tokens: List[LToken], n: int) -> int:
        """
        处理 EXPECT_INDEX_NAME 状态。
        主要职责:
        1. 跳过修饰符
        2. 提取索引名
        3. 初始化 IndexMeta 并存入 context
        """
        match token.value.upper():
            case "IF" | "NOT" | "EXISTS":
                return i + 1
            case _:
                if token.type == SqlTokenType.IDENTIFIER:
                    self.context["current_index"] = IndexMeta(
                        name=token.value.strip('"'),
                        table_name="",
                        columns=[],
                        unique=self.context.get("temp_index_unique", False)
                    )
                    self.switch_state(SqlParserState.EXPECT_INDEX_ON)
                return i + 1

    def handle_expect_index_on(self, token: LToken, i: int, tokens: List[LToken], n: int) -> int:
        """
        处理 EXPECT_INDEX_ON 状态。
        主要职责: 确认 ON 关键字。
        """
        if token.value.upper() == "ON":
            self.switch_state(SqlParserState.EXPECT_INDEX_TABLE)
        return i + 1

    def handle_expect_index_table(self, token: LToken, i: int, tokens: List[LToken], n: int) -> int:
        """
        处理 EXPECT_INDEX_TABLE 状态。
        主要职责: 提取表名并更新 context 中的 current_index。
        """
        if token.type == SqlTokenType.IDENTIFIER:
            current_index = self.context.get("current_index")
            if current_index:
                current_index.table_name = token.value.strip('"')
                self.context["current_index"] = current_index # 显式更新
            self.switch_state(SqlParserState.EXPECT_INDEX_USING)
        return i + 1

    def handle_expect_index_using(self, token: LToken, i: int, tokens: List[LToken], n: int) -> int:
        """
        处理 EXPECT_INDEX_USING 状态。
        主要职责:
        1. 处理 USING 子句 (可选)
        2. 提取索引方法 (如 btree)
        3. 准备进入列定义
        """
        match token.value.upper():
            case "USING":
                if i + 1 < n:
                    current_index = self.context.get("current_index")
                    if current_index:
                        current_index.method = tokens[i+1].value
                        self.context["current_index"] = current_index # 显式更新
                    self.switch_state(SqlParserState.EXPECT_INDEX_COLUMNS)
                    return i + 2
            case "(":
                self.switch_state(SqlParserState.EXPECT_INDEX_COLUMNS)
                return i # 这里必须返回 i, 因为 '(' 需要被下一个状态处理
            case _:
                pass
        return i + 1

    def handle_expect_index_columns(self, token: LToken, i: int, tokens: List[LToken], n: int) -> int:
        """
        处理 EXPECT_INDEX_COLUMNS 状态。
        主要职责:
        1. 解析括号内的列名列表
        2. 完成索引创建并挂载到 TableMeta
        3. 清理 context 并返回 IDLE
        """
        if token.value == "(":
            j = i + 1
            cols = []
            while j < n:
                t = tokens[j]
                match t.value:
                    case ")":
                        current_index = self.context.get("current_index")
                        if current_index:
                            current_index.columns = cols
                            if current_index.table_name in self.schema.tables:
                                self.schema.tables[current_index.table_name].indices[current_index.name] = current_index
                            self.context["current_index"] = None # 显式更新/清理
                        self.switch_state(SqlParserState.IDLE)
                        return j + 1
                    case _:
                        if t.type == SqlTokenType.IDENTIFIER:
                            cols.append(t.value.strip('"'))
                j += 1
        return i + 1

    # --- 表处理 ---
    def handle_expect_table_name(self, token: LToken, i: int, tokens: List[LToken], n: int) -> int:
        """
        处理 EXPECT_TABLE_NAME 状态。
        主要职责: 提取表名, 初始化 TableMeta 并存入 context。
        """
        match token.value.upper():
            case "IF" | "NOT" | "EXISTS":
                return i + 1
            case _:
                if token.type == SqlTokenType.IDENTIFIER:
                    self.context["current_table"] = TableMeta(name=token.value.strip('"'), columns={})
                    self.switch_state(SqlParserState.EXPECT_TABLE_OPEN_PAREN)
                return i + 1

    def handle_expect_table_open_paren(self, token: LToken, i: int, tokens: List[LToken], n: int) -> int:
        """
        处理 EXPECT_TABLE_OPEN_PAREN 状态。
        主要职责: 确认表定义开始的左括号, 并进入 TABLE_BODY 作用域。
        """
        if token.value == "(":
            self.switch_state(SqlParserState.INSIDE_TABLE_BODY)
            self.enter_scope(SqlScope.TABLE_BODY)
        return i + 1

    def handle_inside_table_body(self, token: LToken, i: int, tokens: List[LToken], n: int) -> int:
        """
        处理 INSIDE_TABLE_BODY 状态。
        主要职责:
        1. 管理嵌套作用域 (括号)
        2. 识别表定义结束
        3. 分发列定义解析
        """
        match token.value:
            case "(":
                self.enter_scope(SqlScope.PAREN)
                return i + 1
            case ")":
                current_instance = self.current_scope()
                if current_instance is None:
                    self.exit_scope("UNKNOWN")
                    return i + 1
                
                match current_instance.definition.name:
                    case SqlScope.TABLE_BODY.name:
                        self.exit_scope(SqlScope.TABLE_BODY)
                        current_table = self.context.get("current_table")
                        if current_table:
                            self.schema.tables[current_table.name] = current_table
                            self.context["current_table"] = None # 显式清理
                        self.switch_state(SqlParserState.IDLE)
                        return i + 1
                    case SqlScope.PAREN.name:
                        self.exit_scope(SqlScope.PAREN)
                        return i + 1
                    case _:
                        self.exit_scope("UNKNOWN")
                        return i + 1
            case ",":
                return i + 1
            case _:
                # 检查关键字
                if token.type == SqlTokenType.KEYWORD:
                    match token.value.upper():
                        case "CONSTRAINT" | "PRIMARY" | "FOREIGN" | "CHECK" | "UNIQUE":
                            return i + 1
                
                # 解析列
                if token.type == SqlTokenType.IDENTIFIER:
                    return self._parse_column_definition(token, i, tokens, n)
                
                return i + 1

    def _parse_column_definition(self, token: LToken, i: int, tokens: List[LToken], n: int) -> int:
        """
        辅助方法: 解析列定义。
        从当前位置开始, 解析列名、类型和约束, 直到遇到逗号或右括号。
        """
        col_name = token.value.strip('"')
        col_type = "UNKNOWN"
        
        current_idx = i + 1
        # 解析类型
        if current_idx < n:
            type_token = tokens[current_idx]
            col_type = type_token.value
            if current_idx + 1 < n and tokens[current_idx+1].value == "(":
                current_idx += 2
                while current_idx < n and tokens[current_idx].value != ")":
                    col_type += tokens[current_idx].value
                    current_idx += 1
                if current_idx < n:
                    col_type += ")"
                    current_idx += 1
            else:
                current_idx += 1
        
        col = ColumnMeta(name=col_name, data_type=col_type)
        
        # 解析约束
        while current_idx < n:
            t = tokens[current_idx]
            val = t.value.upper()
            
            match val:
                case "," | ")":
                    break
                case "PRIMARY":
                    if current_idx + 1 < n and tokens[current_idx+1].value.upper() == "KEY":
                        col.is_primary_key = True
                        col.constraints.append("PRIMARY KEY")
                        current_idx += 2
                        continue
                case "NOT":
                    if current_idx + 1 < n and tokens[current_idx+1].value.upper() == "NULL":
                        col.is_nullable = False
                        col.constraints.append("NOT NULL")
                        current_idx += 2
                        continue
                case "DEFAULT":
                    if current_idx + 1 < n:
                        col.default = tokens[current_idx+1].value
                        current_idx += 2
                        continue
                case "REFERENCES":
                    if current_idx + 1 < n:
                        ref_table = tokens[current_idx+1].value
                        ref_col = ""
                        current_idx += 2
                        if current_idx < n and tokens[current_idx].value == "(":
                            if current_idx + 1 < n:
                                ref_col = tokens[current_idx+1].value
                                current_idx += 3
                        col.references = f"{ref_table}({ref_col})"
                        continue
                case _:
                    pass
            
            current_idx += 1

        current_table = self.context.get("current_table")
        if current_table:
            current_table.columns[col_name] = col
            if col.is_primary_key:
                current_table.primary_key.append(col_name)
            self.context["current_table"] = current_table # 显式更新
                
        return current_idx
