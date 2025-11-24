# Loutput 使用文档 — `lput` 函数

本文档说明 `Loutput.lput` 的用法与所有可用样式参数。

---

## 简介

`Loutput` 是一个小巧的**终端输出工具**，`lput` 是其主要输出方法。

样式 (颜色、文本效果) 解析由 `StyleProcessor` 负责，参数支持字符串、Enum 成员或二者的混合列表。

## 函数参数

```py
def lput(
		self,
		*args: object,
		sep: str = " ",
		end: str = "\n",
		file: TextIO = sys.stdout,
		flush: bool = False,

		# 样式相关
		text_effects: Union[str, List[Union[str, Enum]], None] = None,
		font_color: Optional[Union[str, Enum]] = None,
		background: Optional[Union[str, Enum]] = None,

		# 256 色/TrueColor
		c256_fg: Optional[int] = None,
		c256_bg: Optional[int] = None,
		rgb_fg: Optional[tuple[int,int,int]] = None,
		rgb_bg: Optional[tuple[int,int,int]] = None,
) -> None:
```

> 注：实际的类型注解在代码中使用更宽松的 `Union[str, object]` 来同时支持 Enum 实例与字符串。

## 常规参数说明 (继承于标准方法`print()`)

-   `*args`：要打印的任意对象，会被 `str()` 后 join。
-   `sep`：参数之间的分隔符，默认空格。
-   `end`：行尾字符，默认换行 `"\n"`。
-   `file`：输出目标，默认为 `sys.stdout`。
-   `flush`：是否立即刷新输出流。

## 样式参数

样式参数一类负责描述输出的颜色与文本效果。所有样式会被 `StyleProcessor.build_ansi(...)` 解析并生成 ANSI 前缀与重置序列。

#### 支持的参数：

##### |`text_effects`|：文本效果。可传入：

1.  单个字符串，例如 `"bold"`、`"underline"` (不区分大小写) ；
2.  单个 Enum 成员，例如 `TextEffect.BOLD`；
3.  字符串 或 Enum 的 列表，例如 `["bold", TextEffect.UNDERLINE]`。
4.  数字 或 数字字符串, 例如 `"3"` `3`

    | 可用值      | 说明 |     | 可用值          | 说明   |     | 可用值        | 说明 |
    | ----------- | ---- | --- | --------------- | ------ | --- | ------------- | ---- |
    | `RESET (0)` | 重置 |     | `UNDERLINE (4)` | 下划线 |     | `BLINK (5)`   | 闪烁 |
    | `BOLD (1)`  | 粗体 |     | `STRIKE (9)`    | 删除线 |     | `REVERSE (7)` | 反色 |
    | `DIM (2)`   | 暗淡 |     | `HIDE (8)`      | 隐藏   |     | `ITALIC (3)`  | 斜体 |

##### |`font_color`|：前景色。支持:

1. 字符串 (例如 `"red"`、`"blue"`，不区分大小写) ；
2. Enum 成员：`FontColor8.RED` 或 `FontColor8.RED_HIGH`；
3. 数字 或 数字字符串 (例如 `"30"` `90`)

##### |`background`|：背景色。支持:

1. 字符串 (例如 `"red"`、`"blue"`，不区分大小写) ；
2. Enum 成员：`Background.RED` 或 `Background.RED_HIGH`；
3. 数字 或 数字字符串 (例如 `"40"` `100`)

##### |`c256_fg`| / |`c256_bg`|：256 色模式。

-   传入整数 0–255。例如 `c256_fg=196`。

##### |`rgb_fg`| / |`rgb_bg`|：TrueColor (24-bit) 颜色

-   传入三元组 `(r,g,b)`，取值 0–255。例如 `rgb_fg=(255,128,0)`。

---

## 颜色显示问题？

如果你发现颜色在不同终端/主题下显示不一致（比如黑白色互换），请参考：

📖 **[颜色显示指南 (ColorGuide.md)](ColorGuide.md)**

快速解决方案：

```python
from mylib.utils.Loutput import Loutput, RGBColor

out = Loutput()

# 使用 RGB 精确颜色（不受终端主题影响）
out.lput("精确红色", rgb_fg=RGBColor.RED)
out.lput("成功消息", rgb_fg=RGBColor.SUCCESS)
```

---

