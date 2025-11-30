from typing import Literal, Dict


class Printer:
    """彩色打印"""
    COLORS: Dict[str, str] = {
        "red": "31",    # 红色
        "blue": "34",   # 蓝色
        "green": "32",  # 绿色
        "yellow": "33", # 黄色
        "cyan": "36",   # 青色
        "magenta": "35" # 洋红
    }

    def cprint(
        self,
        color: Literal["red", "blue", "green", "yellow", "cyan", "magenta"],
        message: str
    ) -> None:
        color_code = self.COLORS.get(color, "0")
        print(f"\033[{color_code}m{message}\033[0m")
