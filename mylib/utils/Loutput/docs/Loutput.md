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

- `*args`：要打印的任意对象，会被 `str()` 后 join。
- `sep`：参数之间的分隔符，默认空格。
- `end`：行尾字符，默认换行 `"\n"`。
- `file`：输出目标，默认为 `sys.stdout`。
- `flush`：是否立即刷新输出流。

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

- 传入整数 0–255。例如 `c256_fg=196`。

##### |`rgb_fg`| / |`rgb_bg`|：TrueColor (24-bit) 颜色

支持三种方式传入 RGB 颜色：

1. **三元组**：`(r,g,b)`，取值 0–255。例如 `rgb_fg=(255,128,0)`。
2. **RGBColor 枚举**：使用预定义的颜色常量。例如 `rgb_fg=RGBColor.RED`。
3. **列表**：`[r,g,b]`，例如 `rgb_fg=[255, 128, 0]`。

**RGBColor 枚举值列表：**

| 分类          | 枚举值          | RGB 值          | 说明   |
| ------------- | --------------- | --------------- | ------ |
| **基础 8 色** | `BLACK`         | (0, 0, 0)       | 黑色   |
|               | `RED`           | (255, 0, 0)     | 红色   |
|               | `GREEN`         | (0, 255, 0)     | 绿色   |
|               | `YELLOW`        | (255, 255, 0)   | 黄色   |
|               | `BLUE`          | (0, 0, 255)     | 蓝色   |
|               | `MAGENTA`       | (255, 0, 255)   | 品红   |
|               | `CYAN`          | (0, 255, 255)   | 青色   |
|               | `WHITE`         | (255, 255, 255) | 白色   |
| **暗色系**    | `DARK_GRAY`     | (128, 128, 128) | 深灰   |
|               | `DARK_RED`      | (139, 0, 0)     | 深红   |
|               | `DARK_GREEN`    | (0, 128, 0)     | 深绿   |
|               | `DARK_YELLOW`   | (184, 134, 11)  | 深黄   |
|               | `DARK_BLUE`     | (0, 0, 139)     | 深蓝   |
|               | `DARK_MAGENTA`  | (139, 0, 139)   | 深品红 |
|               | `DARK_CYAN`     | (0, 139, 139)   | 深青   |
| **亮色系**    | `LIGHT_GRAY`    | (211, 211, 211) | 浅灰   |
|               | `LIGHT_RED`     | (255, 182, 193) | 浅红   |
|               | `LIGHT_GREEN`   | (144, 238, 144) | 浅绿   |
|               | `LIGHT_YELLOW`  | (255, 255, 224) | 浅黄   |
|               | `LIGHT_BLUE`    | (173, 216, 230) | 浅蓝   |
|               | `LIGHT_MAGENTA` | (255, 182, 255) | 浅品红 |
|               | `LIGHT_CYAN`    | (224, 255, 255) | 浅青   |
| **状态色**    | `SUCCESS`       | (40, 167, 69)   | 成功绿 |
|               | `INFO`          | (23, 162, 184)  | 信息蓝 |
|               | `WARNING`       | (255, 193, 7)   | 警告黄 |
|               | `DANGER`        | (220, 53, 69)   | 危险红 |
| **其他**      | `ORANGE`        | (255, 165, 0)   | 橙色   |
|               | `PINK`          | (255, 192, 203) | 粉色   |
|               | `PURPLE`        | (128, 0, 128)   | 紫色   |
|               | `BROWN`         | (165, 42, 42)   | 棕色   |
|               | `GOLD`          | (255, 215, 0)   | 金色   |
|               | `SILVER`        | (192, 192, 192) | 银色   |

📖 **更多 RGB 使用技巧请参考：[RGBColor 使用指南 (RGBColor.md)](RGBColor.md)**

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
