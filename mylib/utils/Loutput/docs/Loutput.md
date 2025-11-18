# Loutput 使用文档 — `lput` 函数

本文档说明 `Loutput.lput` 的用法与所有可用样式参数。

---

## 简介

`Loutput` 是一个小巧的终端输出工具，`lput` 是其主要输出方法。

样式（颜色、文本效果）解析由 `StyleProcessor` 负责，参数支持字符串、Enum 成员或二者的混合列表。

## 函数签名

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

## 常规参数说明

-   `*args`：要打印的任意对象，会被 `str()` 后 join。
-   `sep`：参数之间的分隔符，默认空格。
-   `end`：行尾字符，默认换行 `"\n"`。
-   `file`：输出目标，默认为 `sys.stdout`。
-   `flush`：是否立即刷新输出流。

## 样式参数（详尽）

样式参数一类负责描述输出的颜色与文本效果。所有样式会被 `StyleProcessor.build_ansi(...)` 解析并生成 ANSI 前缀与重置序列。

#### 支持的参数：

-   |`text_effects`|：文本效果。可传入：

    -   单个字符串，例如 `"bold"`、`"underline"`（不区分大小写）；
    -   单个 Enum 成员，例如 `TextEffect.BOLD`；
    -   字符串或 Enum 的列表，例如 `["bold", TextEffect.UNDERLINE]`。

    可用值（对应 `mylib.utils.Loutput.Enum.TextEffect`）：

    -   **RESET**
    -   **BOLD**
    -   **DIM**
    -   **ITALIC**
    -   **UNDERLINE**
    -   **BLINK**
    -   **REVERSE**
    -   **HIDE**
    -   **STRIKE**

-   |`font_color`|：前景色。支持：

    -   字符串（例如 `"red"`、`"blue"`，不区分大小写）；
    -   Enum 成员：`FontColor8.RED` 或 `FontColor8High.RED`；
    -   也支持直接传入数字字符串（例如 `"31"`）但不常用。

    ###### 标准 8 色（`FontColor8`）成员：

    -   **BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE**

    ###### 高亮 8 色（`FontColor8High`）成员：

    -   **BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE**

-   |`background`|：背景色。支持同前景色，来源于 `Background8` 与 `Background8High`。

    -   **BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE**

-   |`c256_fg`| / |`c256_bg`|：256 色模式。

    -   传入整数 0–255。例如 `c256_fg=196`。

-   |`rgb_fg`| / |`rgb_bg`|：TrueColor（24-bit）颜色

    -   传入三元组 `(r,g,b)`，取值 0–255。例如 `rgb_fg=(255,128,0)`。

---

### 解析规则要点

-   `StyleProcessor` 会首先尝试把传入值匹配为对应 Enum 成员（大小写不敏感）。
-   如果传入字符串且是数字（例如 "31"），会直接作为 ANSI code 使用。
-   `text_effects` 可以是单个值或列表；空值或 `None` 会被忽略。
