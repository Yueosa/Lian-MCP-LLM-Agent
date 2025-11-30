# Loutput 颜色显示指南

## 颜色模式说明

Loutput 支持三种颜色模式，各有特点：

### 1. 标准 ANSI 8/16 色（推荐日常使用）

```python
from mylib.kit.Loutput import Loutput, FontColor8, Background8

out = Loutput()
out.lput("红色文字", font_color=FontColor8.RED)
out.lput("蓝色背景", background=Background8.BLUE)
```

**特点：**
- ✅ **自动适配终端主题** - 颜色会根据用户的终端配色方案自动调整
- ✅ **兼容性最好** - 所有终端都支持
- ✅ **与系统融合** - 保持界面一致性
- ⚠️ **实际颜色由终端主题决定** - 在不同主题下显示效果不同

**适用场景：**
- 日常开发输出
- 需要适配用户终端主题的应用
- 通用命令行工具
\2f
### 2. RGB 真彩色（精确颜色控制）

```python
out.lput("精确红色", rgb_fg=(255, 0, 0))
out.lput("精确蓝色背景", rgb_bg=(0, 0, 255), font_color="white")

# 或使用 RGBColor 枚举（更方便）
from mylib.kit.Loutput import RGBColor
out.lput("精确红色", rgb_fg=RGBColor.RED)
out.lput("成功消息", rgb_fg=RGBColor.SUCCESS)
```

**特点：**
- ✅ **颜色精确** - RGB 值决定显示颜色，不受主题影响
- ✅ **跨平台一致** - 在支持真彩色的终端上显示相同
- ⚠️ **需要终端支持** - 较旧的终端可能不支持
- ⚠️ **可能与主题冲突** - 固定颜色可能在某些主题下不易阅读

**适用场景：**
- 数据可视化（图表、进度条等）
- 品牌色显示（Logo、特定配色）
- 需要精确颜色的场景

### 3. 256 色模式（中间方案）

```python
out.lput("256色红色", c256_fg=196)
out.lput("256色蓝色背景", c256_bg=21)
```

**特点：**
- ✅ 更多颜色选择（256种）
- ✅ 广泛支持
- ⚠️ 仍受终端配置影响（但比 8 色稳定）

## 颜色显示异常？

如果你发现颜色显示"不对"（比如黑白互换），这通常是**正常现象**：

### 原因

终端主题会重新映射 ANSI 颜色代码：
- **暗色主题**：`BLACK(30)` → 浅色显示（便于阅读）
- **亮色主题**：`BLACK(30)` → 深色显示
- **自定义主题**：可能使用任意映射

### 解决方案

根据使用场景选择：

#### 方案 1：保持使用 ANSI 色（推荐）
接受终端主题的颜色映射，这是**用户期望的行为**。

```python
# 保持简单
out.lput("错误信息", font_color="red")
out.lput("成功信息", font_color="green")
```

#### 方案 2：使用 RGB 精确控制
当你**必须**显示特定颜色时（如 Logo、品牌色）：

```python
# 使用 RGBColor 枚举
from mylib.kit.Loutput import RGBColor
out.lput("公司 Logo", rgb_fg=RGBColor.DANGER)  # Bootstrap 品牌红

# 或使用自定义 RGB 值
out.lput("公司 Logo", rgb_fg=(220, 38, 38))  # 自定义品牌红
```

#### 方案 3：提供颜色映射表
为需要精确控制的用户提供 RGB 映射：

```python
# 使用内置的 RGBColor 枚举
from mylib.kit.Loutput import RGBColor

out.lput("精确红色", rgb_fg=RGBColor.RED)
out.lput("成功消息", rgb_fg=RGBColor.SUCCESS)
out.lput("警告消息", rgb_fg=RGBColor.WARNING)
```

## 最佳实践

### 1. 语义化使用颜色

```python
# ✅ 好 - 使用语义化名称
out.lput("Error: 文件不存在", font_color="red")
out.lput("Success: 操作完成", font_color="green")
out.lput("Warning: 内存不足", font_color="yellow")

# ❌ 避免 - 硬编码特定颜色用途
out.lput("错误", rgb_fg=(255, 0, 0))  # 除非有特殊需求
```

### 2. 测试多种终端

在发布前测试：
- 暗色主题
- 亮色主题  
- 不同终端（Kitty、iTerm2、Windows Terminal 等）

### 3. 提供配置选项

```python
class MyApp:
    def __init__(self, use_rgb_colors=False):
        self.out = Loutput()
        self.use_rgb = use_rgb_colors
    
    def print_error(self, msg):
        if self.use_rgb:
            from mylib.kit.Loutput import RGBColor
            self.out.lput(msg, rgb_fg=RGBColor.RED)
        else:
            self.out.lput(msg, font_color="red")
```

## 检测终端能力

```python
import os
import sys

def supports_truecolor():
    """检测终端是否支持真彩色"""
    colorterm = os.environ.get('COLORTERM', '')
    return 'truecolor' in colorterm or '24bit' in colorterm

def get_term_program():
    """获取终端程序名称"""
    return os.environ.get('TERM_PROGRAM', os.environ.get('TERM', 'unknown'))

# 使用示例
if supports_truecolor():
    print("✅ 终端支持 RGB 真彩色")
else:
    print("⚠️ 终端可能不支持真彩色，建议使用 ANSI 标准色")

print(f"终端: {get_term_program()}")
```

## FAQ

**Q: 为什么我的黑色显示成白色了？**  
A: 你的终端使用了暗色主题，为了可读性自动将"黑色"映射为浅色。这是正常行为。

**Q: 如何显示"真正的黑色"？**  
A: 使用 RGB: `out.lput("真黑色", rgb_fg=(0, 0, 0))` 或 `out.lput("真黑色", rgb_fg=RGBColor.BLACK)`

**Q: 应该用 ANSI 色还是 RGB？**  
A: 大多数情况用 ANSI 色，让用户终端主题生效。只有需要精确颜色时才用 RGB。

**Q: 如何查看我的终端主题配色？**  
A: 运行以下测试脚本查看 ANSI 色的实际显示：

```python
from mylib.kit.Loutput import Loutput, FontColor8

out = Loutput()
colors = ["BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE"]

for color_name in colors:
    color_enum = getattr(FontColor8, color_name)
    out.lput(f"■■■ {color_name:10}", font_color=color_enum)
```

## 参考资料

- [ANSI Escape Code - Wikipedia](https://en.wikipedia.org/wiki/ANSI_escape_code)
- [Terminal Colors](https://github.com/termstandard/colors)
- [True Color Support in Terminals](https://gist.github.com/XVilka/8346728)
