from enum import Enum, auto
from typing import Optional
from mylib.kit.Ltokenizer import LTokenizerBase

class SqlTokenType(Enum):
    KEYWORD = auto()      # 关键字
    IDENTIFIER = auto()   # 标识符
    STRING = auto()       # 字符串字面量
    SYMBOL = auto()       # 符号 (如括号, 逗号, 分号)
    COMMENT = auto()      # 注释 (可选发射)
    WHITESPACE = auto()   # 空白 (可选发射)

class SqlTokenizerState(Enum):
    NORMAL = auto()             # 普通模式
    IN_STRING_SINGLE = auto()   # 单引号字符串内部 '...'
    IN_STRING_DOLLAR = auto()   # Dollar 引用字符串内部 $$...$$
    IN_COMMENT_LINE = auto()    # 单行注释内部 -- ...
    IN_COMMENT_BLOCK = auto()   # 块注释内部 /* ... */

class SqlTokenizer(LTokenizerBase[SqlTokenizerState]):
    def __init__(self):
        super().__init__(SqlTokenizerState.NORMAL)
        self.dollar_tag = ""

    def handle_normal(self, char: str, i: int, content: str, n: int) -> Optional[int]:
        # 跳过空白字符
        if char.isspace():
            if self.buffer:
                self._flush_buffer_as_token()
            return None

        # 检查单行注释开始 --
        if char == '-' and i + 1 < n and content[i+1] == '-':
            if self.buffer:
                self._flush_buffer_as_token()
            self.switch_state(SqlTokenizerState.IN_COMMENT_LINE)
            return i + 2 # 跳过 --

        # 检查块注释开始 /*
        if char == '/' and i + 1 < n and content[i+1] == '*':
            if self.buffer:
                self._flush_buffer_as_token()
            self.switch_state(SqlTokenizerState.IN_COMMENT_BLOCK)
            return i + 2

        # 检查单引号字符串开始 '
        if char == "'":
            if self.buffer:
                self._flush_buffer_as_token()
            self.switch_state(SqlTokenizerState.IN_STRING_SINGLE)
            self.mark_start() # 标记 Token 开始位置
            return None

        # 检查 Dollar 引用字符串开始 $
        if char == '$':
            if self.buffer:
                self._flush_buffer_as_token()
            # 检查是否是 dollar tag
            # 简单检查: 寻找下一个 $
            tag_end = content.find('$', i + 1)
            if tag_end != -1:
                tag = content[i:tag_end+1]
                # 这里可以添加对 tag 字符合法性的验证
                self.dollar_tag = tag
                self.switch_state(SqlTokenizerState.IN_STRING_DOLLAR)
                self.mark_start()
                return tag_end + 1
            else:
                # 只是一个单独的 $ 符号
                self.emit(SqlTokenType.SYMBOL, "$")
                return None

        # 处理符号
        if char in "(),;":
            if self.buffer:
                self._flush_buffer_as_token()
            self.mark_start()
            self.emit(SqlTokenType.SYMBOL, char)
            return None

        # 累积到缓冲区
        if not self.buffer:
            self.mark_start()
        self.buffer.append(char)
        return None

    def handle_in_string_single(self, char: str, i: int, content: str, n: int) -> Optional[int]:
        if char == "'":
            # 检查转义引号 '' (SQL 标准转义)
            if i + 1 < n and content[i+1] == "'":
                self.buffer.append("'")
                return i + 2
            else:
                # 字符串结束
                self.emit(SqlTokenType.STRING)
                self.switch_state(SqlTokenizerState.NORMAL)
                return None
        self.buffer.append(char)
        return None

    def handle_in_string_dollar(self, char: str, i: int, content: str, n: int) -> Optional[int]:
        # 检查是否遇到结束标签
        if char == '$':
            if content.startswith(self.dollar_tag, i):
                self.emit(SqlTokenType.STRING)
                self.switch_state(SqlTokenizerState.NORMAL)
                return i + len(self.dollar_tag)
        self.buffer.append(char)
        return None

    def handle_in_comment_line(self, char: str, i: int, content: str, n: int) -> Optional[int]:
        if char == '\n':
            self.switch_state(SqlTokenizerState.NORMAL)
        return None

    def handle_in_comment_block(self, char: str, i: int, content: str, n: int) -> Optional[int]:
        if char == '*' and i + 1 < n and content[i+1] == '/':
            self.switch_state(SqlTokenizerState.NORMAL)
            return i + 2
        return None

    def _flush_buffer_as_token(self):
        if not self.buffer:
            return
        text = "".join(self.buffer)
        # 确定 Token 类型: KEYWORD 或 IDENTIFIER
        # 简单启发式规则: 如果全大写或者是已知关键字 -> KEYWORD
        # 目前我们假设所有非关键字都是 IDENTIFIER，Parser 会进一步检查
        
        KEYWORDS = {
            "CREATE", "TABLE", "IF", "NOT", "EXISTS", "PRIMARY", "KEY", 
            "FOREIGN", "REFERENCES", "CONSTRAINT", "DEFAULT", "NULL", 
            "UNIQUE", "INDEX", "ON", "USING", "EXTENSION", "CHECK", 
            "OR", "REPLACE", "ASC", "DESC", "NULLS", "FIRST", "LAST"
        }
        
        if text.upper() in KEYWORDS:
            self.emit(SqlTokenType.KEYWORD, text)
        else:
            self.emit(SqlTokenType.IDENTIFIER, text)
        
        self.buffer = []

    def on_finish(self):
        if self.buffer:
            self._flush_buffer_as_token()
