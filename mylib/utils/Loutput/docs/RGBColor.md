# RGBColor 使用指南

## 概述

`RGBColor` 是一个枚举类,提供了常用颜色的精确 RGB 值。现在你可以**直接使用枚举**,无需添加 `.value`。

## 快速开始

```python
from mylib.utils.Loutput import Loutput, RGBColor

out = Loutput()

# ✅ 推荐: 直接使用枚举
out.lput("红色文字", rgb_fg=RGBColor.RED)
out.lput("成功消息", rgb_fg=RGBColor.SUCCESS)

# ✅ 也支持: 使用 .value (向后兼容)
out.lput("红色文字", rgb_fg=RGBColor.RED.value)

# ✅ 也支持: 直接使用元组
out.lput("自定义颜色", rgb_fg=(255, 100, 50))
```

## 可用颜色

### 基础 8 色
- `RGBColor.BLACK` - 黑色 (0, 0, 0)
- `RGBColor.RED` - 红色 (255, 0, 0)
- `RGBColor.GREEN` - 绿色 (0, 255, 0)
- `RGBColor.YELLOW` - 黄色 (255, 255, 0)
- `RGBColor.BLUE` - 蓝色 (0, 0, 255)
- `RGBColor.MAGENTA` - 洋红 (255, 0, 255)
- `RGBColor.CYAN` - 青色 (0, 255, 255)
- `RGBColor.WHITE` - 白色 (255, 255, 255)

### 深色系（适合暗色主题背景）
- `RGBColor.DARK_GRAY` - 深灰 (128, 128, 128)
- `RGBColor.DARK_RED` - 深红 (139, 0, 0)
- `RGBColor.DARK_GREEN` - 深绿 (0, 128, 0)
- `RGBColor.DARK_YELLOW` - 深黄 (184, 134, 11)
- `RGBColor.DARK_BLUE` - 深蓝 (0, 0, 139)
- `RGBColor.DARK_MAGENTA` - 深洋红 (139, 0, 139)
- `RGBColor.DARK_CYAN` - 深青 (0, 139, 139)

### 浅色系（适合亮色主题背景）
- `RGBColor.LIGHT_GRAY` - 浅灰 (211, 211, 211)
- `RGBColor.LIGHT_RED` - 浅红 (255, 182, 193)
- `RGBColor.LIGHT_GREEN` - 浅绿 (144, 238, 144)
- `RGBColor.LIGHT_YELLOW` - 浅黄 (255, 255, 224)
- `RGBColor.LIGHT_BLUE` - 浅蓝 (173, 216, 230)
- `RGBColor.LIGHT_MAGENTA` - 浅洋红 (255, 182, 255)
- `RGBColor.LIGHT_CYAN` - 浅青 (224, 255, 255)

### 状态颜色（Bootstrap 风格）
- `RGBColor.SUCCESS` - 成功绿 (40, 167, 69)
- `RGBColor.INFO` - 信息蓝 (23, 162, 184)
- `RGBColor.WARNING` - 警告黄 (255, 193, 7)
- `RGBColor.DANGER` - 危险红 (220, 53, 69)

### 其他常用颜色
- `RGBColor.ORANGE` - 橙色 (255, 165, 0)
- `RGBColor.PINK` - 粉色 (255, 192, 203)
- `RGBColor.PURPLE` - 紫色 (128, 0, 128)
- `RGBColor.BROWN` - 棕色 (165, 42, 42)
- `RGBColor.GOLD` - 金色 (255, 215, 0)
- `RGBColor.SILVER` - 银色 (192, 192, 192)

## 使用场景

### 1. 状态消息

```python
from mylib.utils.Loutput import Loutput, RGBColor

out = Loutput()

out.lput("✓ 操作成功", rgb_fg=RGBColor.SUCCESS)
out.lput("ℹ 提示信息", rgb_fg=RGBColor.INFO)
out.lput("⚠ 警告信息", rgb_fg=RGBColor.WARNING)
out.lput("✗ 错误信息", rgb_fg=RGBColor.DANGER)
```

### 2. 品牌色展示

```python
# 显示公司 Logo/品牌色
out.lput("🏢 公司名称", rgb_fg=RGBColor.PURPLE)
out.lput("📱 产品名称", rgb_fg=RGBColor.ORANGE)
```

### 3. 数据可视化

```python
# 进度条颜色
out.lput("█" * 50, rgb_fg=RGBColor.SUCCESS)  # 完成部分
out.lput("░" * 50, rgb_fg=RGBColor.DARK_GRAY)  # 未完成部分

# 图表颜色
out.lput("■ 销售额", rgb_fg=RGBColor.BLUE)
out.lput("■ 利润", rgb_fg=RGBColor.GREEN)
out.lput("■ 成本", rgb_fg=RGBColor.RED)
```

### 4. 主题适配

```python
import os

# 检测终端背景
def is_dark_theme():
    # 简单检测,实际可能需要更复杂的逻辑
    term = os.environ.get('TERM_PROGRAM', '')
    return 'dark' in term.lower()

if is_dark_theme():
    # 暗色主题使用浅色文字
    text_color = RGBColor.LIGHT_GRAY
else:
    # 亮色主题使用深色文字
    text_color = RGBColor.DARK_GRAY

out.lput("自适应颜色文字", rgb_fg=text_color)
```

### 5. 背景色

```python
# 背景色也支持
out.lput("高亮文字", rgb_bg=RGBColor.YELLOW, font_color="black")
out.lput("危险警告", rgb_bg=RGBColor.DANGER, font_color="white")
```

## ANSItoRGB 工具

如果你想将 ANSI 颜色代码转换为 RGB:

```python
from mylib.utils.Loutput import Loutput, ANSItoRGB

out = Loutput()

# 将 ANSI 31 (红色) 转换为 RGB
rgb_red = ANSItoRGB.fg_to_rgb(31)
out.lput("转换后的红色", rgb_fg=rgb_red)

# 将 ANSI 44 (蓝色背景) 转换为 RGB
rgb_blue_bg = ANSItoRGB.bg_to_rgb(44)
out.lput("转换后的蓝色背景", rgb_bg=rgb_blue_bg)
```

## 技术细节

### 自动类型转换

`lput` 方法内部会自动处理枚举类型:

```python
# 在 Loutput.lput 内部
if rgb_fg is not None and isinstance(rgb_fg, Enum):
    rgb_fg = rgb_fg.value  # 自动提取 (r, g, b) 元组
```

这意味着你可以:
- ✅ 直接传入 `RGBColor.RED`
- ✅ 也可以传入 `RGBColor.RED.value`
- ✅ 还可以传入 `(255, 0, 0)`

所有方式都能正常工作！

### 类型提示

```python
def lput(
    self,
    *args: object,
    rgb_fg: Optional[Union[tuple[int, int, int], object]] = None,
    rgb_bg: Optional[Union[tuple[int, int, int], object]] = None
) -> None:
```

类型系统接受:
- 元组: `(255, 0, 0)`
- 枚举: `RGBColor.RED`
- 任何对象: IDE 不会报错

## 最佳实践

### ✅ 推荐

```python
# 使用语义化的枚举
out.lput("成功", rgb_fg=RGBColor.SUCCESS)
out.lput("警告", rgb_fg=RGBColor.WARNING)

# 使用品牌色
BRAND_COLOR = RGBColor.PURPLE
out.lput("品牌标语", rgb_fg=BRAND_COLOR)
```

### ⚠️ 注意

```python
# 避免硬编码魔法数字
out.lput("文字", rgb_fg=(123, 45, 67))  # 这是什么颜色？

# 更好的方式
CUSTOM_BRAND = (123, 45, 67)  # 定义为常量
out.lput("文字", rgb_fg=CUSTOM_BRAND)
```

## 迁移指南

如果你之前使用 `.value`,现在可以移除它:

```python
# 旧代码
out.lput("文字", rgb_fg=RGBColor.RED.value)
out.lput("文字", rgb_fg=RGBColor.SUCCESS.value)

# 新代码（更简洁）
out.lput("文字", rgb_fg=RGBColor.RED)
out.lput("文字", rgb_fg=RGBColor.SUCCESS)
```

旧代码仍然可以工作,但新代码更简洁！

## 完整示例

查看 `tests/rgb_demo.py` 和 `tests/rgb_quick_test.py` 获取完整示例。
