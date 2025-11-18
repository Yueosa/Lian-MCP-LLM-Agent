from enum import Enum


class TextEffect(Enum):
    """文本效果"""
    RESET = "0"
    BOLD = "1"
    DIM = "2"
    ITALIC = "3"
    UNDERLINE = "4"
    BLINK = "5"
    REVERSE = "7"
    HIDE = "8"
    STRIKE = "9"


class FontColor8(Enum):
    """前景色 (标准8色)"""
    BLACK = "30"
    RED = "31"
    GREEN = "32"
    YELLOW = "33"
    BLUE = "34"
    MAGENTA = "35"
    CYAN = "36"
    WHITE = "37"


class FontColor8High(Enum):
    """前景色 (高亮8色)"""
    BLACK = "90"
    RED = "91"
    GREEN = "92"
    YELLOW = "93"
    BLUE = "94"
    MAGENTA = "95"
    CYAN = "96"
    WHITE = "97"


class Background8(Enum):
    """背景色 {标准8色}"""
    BLACK = "40"
    RED = "41"
    GREEN = "42"
    YELLOW = "43"
    BLUE = "44"
    MAGENTA = "45"
    CYAN = "46"
    WHITE = "47"


class Background8High(Enum):
    """背景色 (高亮8色)"""
    BLACK = "100"
    RED = "101"
    GREEN = "102"
    YELLOW = "103"
    BLUE = "104"
    MAGENTA = "105"
    CYAN = "106"
    WHITE = "107"
