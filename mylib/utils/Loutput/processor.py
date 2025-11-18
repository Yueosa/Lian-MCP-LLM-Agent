from typing import Any, List, Optional, Tuple, Union

from .Enum import (
    TextEffect,
    FontColor8,
    Background8,
)


class StyleProcessor:
    """负责将用户友好的样式输入解析为 ANSI 片段。

    支持的输入类型：
        - 单个字符串 (例如 "red"、"bold") 
        - Enum 成员 (TextEffect / FontColor8 / Background8 等) 
        - 字符串或 Enum 列表

    返回值：
        - prefix: 包含 ANSI 前缀 (例如 "\033[1;31m") 的字符串
        - reset: 重置字符串 (例如 "\033[0m") 
    """

    def __init__(self):
        pass

    def _find_enum(self, enum_cls, name: Any):
        """查找 Enum 成员。支持字符串转为大写后查找，以及 '_high' 后缀自动转为 '_HIGH'。"""
        if name is None:
            return None
        if isinstance(name, enum_cls):
            return name
        if not isinstance(name, str):
            return None
        
        key = name.upper()
        
        for item in enum_cls:
            if item.name == key:
                return item
        
        return None

    def build_ansi(self,
                    text_effects: Optional[Union[str, Any, List[Union[str, Any]]]] = None,
                    font_color: Optional[Union[str, Any]] = None,
                    background: Optional[Union[str, Any]] = None,
                    c256_fg: Optional[int] = None,
                    c256_bg: Optional[int] = None,
                    rgb_fg: Optional[tuple] = None,
                    rgb_bg: Optional[tuple] = None) -> Tuple[str, str]:
        """将所有样式参数解析为 ANSI 前缀和重置字符串。"""
        ansi_parts: List[str] = []

        if isinstance(text_effects, (list, tuple)):
            items = text_effects
        else:
            items = [text_effects] if text_effects is not None else []

        for eff in items:
            if eff is None:
                continue
            eff_enum = self._find_enum(TextEffect, eff)
            if eff_enum:
                ansi_parts.append(eff_enum.value)
                continue
            if isinstance(eff, str) and eff.isdigit():
                ansi_parts.append(eff)

        if font_color is not None:
            font_enum = self._find_enum(FontColor8, font_color)
            if font_enum:
                ansi_parts.append(font_enum.value)
            elif isinstance(font_color, str) and font_color.isdigit():
                ansi_parts.append(font_color)

        if background is not None:
            bg_enum = self._find_enum(Background8, background)
            if bg_enum:
                ansi_parts.append(bg_enum.value)
            elif isinstance(background, str) and background.isdigit():
                ansi_parts.append(background)

        if c256_fg is not None:
            ansi_parts.append(f"38;5;{int(c256_fg)}")
        if c256_bg is not None:
            ansi_parts.append(f"48;5;{int(c256_bg)}")

        if rgb_fg:
            r, g, b = rgb_fg
            ansi_parts.append(f"38;2;{int(r)};{int(g)};{int(b)}")
        if rgb_bg:
            r, g, b = rgb_bg
            ansi_parts.append(f"48;2;{int(r)};{int(g)};{int(b)}")

        prefix = f"\033[{';'.join(ansi_parts)}m" if ansi_parts else ""
        reset = "\033[0m"
        return prefix, reset
