"""
RGB 颜色映射使用示例
演示如何使用 RGBColor 和 ANSItoRGB 工具
"""
import base

from mylib.kit.Loutput import Loutput, FontColor8, RGBColor, ANSItoRGB


out = Loutput()

print("=" * 50)
print("场景 1: 标准 ANSI 颜色（适配终端主题）")
print("=" * 50)

out.lput("错误信息", font_color=FontColor8.RED)
out.lput("成功信息", font_color=FontColor8.GREEN)
out.lput("警告信息", font_color=FontColor8.YELLOW)
out.lput("信息提示", font_color=FontColor8.CYAN)

print("\n" + "=" * 50)
print("场景 2: 使用 RGBColor 获得精确颜色")
print("=" * 50)

out.lput("精确红色（不受主题影响）", rgb_fg=RGBColor.RED)
out.lput("精确绿色（不受主题影响）", rgb_fg=RGBColor.GREEN)
out.lput("精确蓝色（不受主题影响）", rgb_fg=RGBColor.BLUE)

print("\n" + "=" * 50)
print("场景 3: 使用状态颜色（现代 UI 风格）")
print("=" * 50)

out.lput("✓ 操作成功", rgb_fg=RGBColor.SUCCESS)
out.lput("ℹ 提示信息", rgb_fg=RGBColor.INFO)
out.lput("⚠ 警告提示", rgb_fg=RGBColor.WARNING)
out.lput("✗ 错误信息", rgb_fg=RGBColor.DANGER)

print("\n" + "=" * 50)
print("场景 4: ANSI 转 RGB（解决颜色异常）")
print("=" * 50)

print("如果你的终端主题让红色显示不正常：")
out.lput("ANSI 红色（可能异常）", font_color=31)
out.lput("转换为 RGB 红色（正常显示）", rgb_fg=ANSItoRGB.fg_to_rgb(31))

print("\n如果黑白色互换：")
out.lput("ANSI 黑色", font_color=30)
out.lput("RGB 黑色", rgb_fg=ANSItoRGB.fg_to_rgb(30))

print("\n" + "=" * 50)
print("场景 5: 暗色/亮色主题适配")
print("=" * 50)

print("\n暗色主题推荐（深色背景）：")
out.lput("浅色文字易读", rgb_fg=RGBColor.LIGHT_GRAY)
out.lput("高亮红色", rgb_fg=(255, 85, 85))
out.lput("高亮绿色", rgb_fg=(85, 255, 85))

print("\n亮色主题推荐（浅色背景）：")
out.lput("深色文字易读", rgb_fg=RGBColor.DARK_GRAY)
out.lput("深红色", rgb_fg=RGBColor.DARK_RED)
out.lput("深绿色", rgb_fg=RGBColor.DARK_GREEN)

print("\n" + "=" * 50)
print("场景 6: 品牌色/Logo 显示")
print("=" * 50)

out.lput("🍊 橙色品牌", rgb_fg=RGBColor.ORANGE)
out.lput("💜 紫色品牌", rgb_fg=RGBColor.PURPLE)
out.lput("💗 粉色品牌", rgb_fg=RGBColor.PINK)
out.lput("🏆 金色徽章", rgb_fg=RGBColor.GOLD)

print("\n" + "=" * 50)
print("完整的 RGBColor 颜色展示")
print("=" * 50)

colors = [
    "BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE",
    "DARK_GRAY", "DARK_RED", "DARK_GREEN", "DARK_YELLOW", 
    "DARK_BLUE", "DARK_MAGENTA", "DARK_CYAN",
    "LIGHT_GRAY", "LIGHT_RED", "LIGHT_GREEN", "LIGHT_YELLOW",
    "LIGHT_BLUE", "LIGHT_MAGENTA", "LIGHT_CYAN",
    "SUCCESS", "INFO", "WARNING", "DANGER",
    "ORANGE", "PINK", "PURPLE", "BROWN", "GOLD", "SILVER"
]

for color_name in colors:
    color_enum = getattr(RGBColor, color_name)
    out.lput(f"■■■ {color_name:15} RGB{color_enum.value}", rgb_fg=color_enum)

print("\n" + "=" * 50)
print("建议使用策略")
print("=" * 50)

print("""
1. 日常开发：使用 ANSI 颜色（FontColor8, Background8）
   - 自动适配用户终端主题
   - 最好的兼容性

2. 颜色异常时：使用 RGBColor 或 ANSItoRGB
   - 获得一致的颜色显示
   - 不受终端主题影响

3. 品牌展示：使用自定义 RGB 值
   - 精确的品牌色
   - 跨平台一致性

4. 提供配置：让用户选择颜色模式
   - 默认 ANSI，可选 RGB
   - 适应不同用户需求
""")
