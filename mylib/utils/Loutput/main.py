from typing import List, Optional, TextIO, Union
import sys

from .processor import StyleProcessor


class Loutput:
    """更好用的终端打印工具。

    lput 的样式参数接受字符串、Enum 或二者的列表；
    解析逻辑由 `StyleProcessor` 负责，从而使 `lput` 更简洁。
    """

    ESC = "\033["

    def __init__(self):
        self.style = StyleProcessor()

    def lput(
            self,
            *args: object,
            sep: str = " ",
            end: str = "\n",
            file: TextIO = sys.stdout,
            flush: bool = False,

            # 样式参数：支持字符串/Enum/列表
            text_effects: Union[str, List[Union[str, object]], None] = None,
            font_color: Optional[Union[str, object]] = None,
            background: Optional[Union[str, object]] = None,

            # 256 色
            c256_fg: Optional[int] = None,
            c256_bg: Optional[int] = None,

            # RGB
            rgb_fg: Optional[tuple[int, int, int]] = None,
            rgb_bg: Optional[tuple[int, int, int]] = None
    ) -> None:
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
