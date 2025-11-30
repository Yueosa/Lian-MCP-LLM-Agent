"""
RGB 颜色映射 - 提供标准颜色的精确 RGB 值

当终端主题颜色映射不符合预期时，可以使用这些 RGB 值
来获得精确的颜色显示效果。
"""

from enum import Enum
from typing import Tuple


class RGBColor(Enum):
    """标准颜色的 RGB 真彩色映射
    
    使用示例:
        from mylib.kit.Loutput import Loutput, RGBColor
        
        out = Loutput()
        # 直接使用枚举,无需 .value
        out.lput("精确红色", rgb_fg=RGBColor.RED)
        out.lput("成功消息", rgb_fg=RGBColor.SUCCESS)
    """
    
    # 基础 8 色（标准 RGB 值）
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    YELLOW = (255, 255, 0)
    BLUE = (0, 0, 255)
    MAGENTA = (255, 0, 255)
    CYAN = (0, 255, 255)
    WHITE = (255, 255, 255)
    
    # 常用深色（暗色主题友好）
    DARK_GRAY = (128, 128, 128)
    DARK_RED = (139, 0, 0)
    DARK_GREEN = (0, 128, 0)
    DARK_YELLOW = (184, 134, 11)
    DARK_BLUE = (0, 0, 139)
    DARK_MAGENTA = (139, 0, 139)
    DARK_CYAN = (0, 139, 139)
    
    # 常用浅色（亮色主题友好）
    LIGHT_GRAY = (211, 211, 211)
    LIGHT_RED = (255, 182, 193)
    LIGHT_GREEN = (144, 238, 144)
    LIGHT_YELLOW = (255, 255, 224)
    LIGHT_BLUE = (173, 216, 230)
    LIGHT_MAGENTA = (255, 182, 255)
    LIGHT_CYAN = (224, 255, 255)
    
    # 常用状态颜色
    SUCCESS = (40, 167, 69)      # Bootstrap success green
    INFO = (23, 162, 184)         # Bootstrap info blue
    WARNING = (255, 193, 7)       # Bootstrap warning yellow
    DANGER = (220, 53, 69)        # Bootstrap danger red
    
    # 常用品牌/UI 颜色
    ORANGE = (255, 165, 0)
    PINK = (255, 192, 203)
    PURPLE = (128, 0, 128)
    BROWN = (165, 42, 42)
    GOLD = (255, 215, 0)
    SILVER = (192, 192, 192)


class ANSItoRGB:
    """ANSI 颜色代码到 RGB 的映射工具
    
    当终端主题导致颜色显示异常时，可以使用此工具
    将 ANSI 颜色代码转换为对应的 RGB 值。
    """
    
    # ANSI 标准色对应的标准 RGB 值
    FOREGROUND_MAP = {
        30: RGBColor.BLACK.value,
        31: RGBColor.RED.value,
        32: RGBColor.GREEN.value,
        33: RGBColor.YELLOW.value,
        34: RGBColor.BLUE.value,
        35: RGBColor.MAGENTA.value,
        36: RGBColor.CYAN.value,
        37: RGBColor.WHITE.value,
        
        # 高亮色（通常更亮）
        90: RGBColor.DARK_GRAY.value,
        91: (255, 85, 85),    # Bright Red
        92: (85, 255, 85),    # Bright Green
        93: (255, 255, 85),   # Bright Yellow
        94: (85, 85, 255),    # Bright Blue
        95: (255, 85, 255),   # Bright Magenta
        96: (85, 255, 255),   # Bright Cyan
        97: RGBColor.WHITE.value,
    }
    
    BACKGROUND_MAP = {
        40: RGBColor.BLACK.value,
        41: RGBColor.RED.value,
        42: RGBColor.GREEN.value,
        43: RGBColor.YELLOW.value,
        44: RGBColor.BLUE.value,
        45: RGBColor.MAGENTA.value,
        46: RGBColor.CYAN.value,
        47: RGBColor.WHITE.value,
        
        # 高亮背景色
        100: RGBColor.DARK_GRAY.value,
        101: (255, 85, 85),
        102: (85, 255, 85),
        103: (255, 255, 85),
        104: (85, 85, 255),
        105: (255, 85, 255),
        106: (85, 255, 255),
        107: RGBColor.WHITE.value,
    }
    
    @classmethod
    def fg_to_rgb(cls, ansi_code: int) -> Tuple[int, int, int]:
        """将前景色 ANSI 代码转换为 RGB
        
        Args:
            ansi_code: ANSI 前景色代码 (30-37, 90-97)
            
        Returns:
            (r, g, b) 元组
        """
        return cls.FOREGROUND_MAP.get(ansi_code, RGBColor.WHITE.value)
    
    @classmethod
    def bg_to_rgb(cls, ansi_code: int) -> Tuple[int, int, int]:
        """将背景色 ANSI 代码转换为 RGB
        
        Args:
            ansi_code: ANSI 背景色代码 (40-47, 100-107)
            
        Returns:
            (r, g, b) 元组
        """
        return cls.BACKGROUND_MAP.get(ansi_code, RGBColor.BLACK.value)


# 便捷导出
__all__ = ['RGBColor', 'ANSItoRGB']
