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
    """前景色 (8色 + 高亮8色)
    
    标准 8 色: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE
    高亮 8 色: BLACK_HIGH, RED_HIGH, GREEN_HIGH, YELLOW_HIGH, BLUE_HIGH, MAGENTA_HIGH, CYAN_HIGH, WHITE_HIGH
    """
    # 标准 8 色
    BLACK = "30"
    RED = "31"
    GREEN = "32"
    YELLOW = "33"
    BLUE = "34"
    MAGENTA = "35"
    CYAN = "36"
    WHITE = "37"
    
    # 高亮 8 色
    BLACK_HIGH = "90"
    RED_HIGH = "91"
    GREEN_HIGH = "92"
    YELLOW_HIGH = "93"
    BLUE_HIGH = "94"
    MAGENTA_HIGH = "95"
    CYAN_HIGH = "96"
    WHITE_HIGH = "97"


class Background8(Enum):
    """背景色 (8色 + 高亮8色)
    
    标准 8 色: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE
    高亮 8 色: BLACK_HIGH, RED_HIGH, GREEN_HIGH, YELLOW_HIGH, BLUE_HIGH, MAGENTA_HIGH, CYAN_HIGH, WHITE_HIGH
    """
    # 标准 8 色
    BLACK = "40"
    RED = "41"
    GREEN = "42"
    YELLOW = "43"
    BLUE = "44"
    MAGENTA = "45"
    CYAN = "46"
    WHITE = "47"
    
    # 高亮 8 色
    BLACK_HIGH = "100"
    RED_HIGH = "101"
    GREEN_HIGH = "102"
    YELLOW_HIGH = "103"
    BLUE_HIGH = "104"
    MAGENTA_HIGH = "105"
    CYAN_HIGH = "106"
    WHITE_HIGH = "107"
