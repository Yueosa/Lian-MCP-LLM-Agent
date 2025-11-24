from typing import List, Optional, TextIO, Union
import sys
from enum import Enum

from .processor import StyleProcessor


class Loutput:
    """更好用的终端打印工具。

    lput 的样式参数接受字符串、Enum 或二者的列表；
    解析逻辑由 `StyleProcessor` 负责，从而使 `lput` 更简洁。
    """

    ESC = "\033["

    def __init__(self):
        self.style = StyleProcessor()

    def __call__(self, *args, **kwargs):
        """直接通过实例呼叫lput方法"""
        return self.lput(*args, **kwargs)

    def lput(
            self,
            *args: object,
            sep: str = " ",
            end: str = "\n",
            file: TextIO = sys.stdout,
            flush: bool = False,

            # 样式参数：支持字符串/Enum/列表
            text_effects: Union[str, object, List[Union[str, object]], None] = None,
            font_color: Optional[Union[str, object]] = None,
            background: Optional[Union[str, object]] = None,

            # 256 色
            c256_fg: Optional[int] = None,
            c256_bg: Optional[int] = None,

            # RGB - 支持元组或 RGBColor 枚举
            rgb_fg: Optional[Union[tuple[int, int, int], object]] = None,
            rgb_bg: Optional[Union[tuple[int, int, int], object]] = None
    ) -> None:
        # 自动提取枚举值(如果是枚举类型)
        if rgb_fg is not None and isinstance(rgb_fg, Enum):
            rgb_fg = rgb_fg.value
        if rgb_bg is not None and isinstance(rgb_bg, Enum):
            rgb_bg = rgb_bg.value
        
        prefix, reset = self.style.build_ansi(
            text_effects=text_effects,
            font_color=font_color,
            background=background,
            c256_fg=c256_fg,
            c256_bg=c256_bg,
            rgb_fg=rgb_fg,
            rgb_bg=rgb_bg,
        )

        text = sep.join(map(str, args))

        print(prefix + text + reset, sep=sep, end=end, file=file, flush=flush)
