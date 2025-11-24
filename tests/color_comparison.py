import base
from mylib.utils.Loutput import Loutput, FontColor8, Background8

out = Loutput()

print("=== 标准 ANSI 8色 vs RGB 真彩色对比 ===\n")

# 红色对比
print("标准红色 (ANSI 31):")
out.lput("  这是标准红色文字", font_color=FontColor8.RED)
print("真红色 (RGB 255,0,0):")
out.lput("  这是真红色文字", rgb_fg=(255, 0, 0))

print()

# 绿色对比
print("标准绿色 (ANSI 32):")
out.lput("  这是标准绿色文字", font_color=FontColor8.GREEN)
print("真绿色 (RGB 0,255,0):")
out.lput("  这是真绿色文字", rgb_fg=(0, 255, 0))

print()

# 蓝色对比
print("标准蓝色 (ANSI 34):")
out.lput("  这是标准蓝色文字", font_color=FontColor8.BLUE)
print("真蓝色 (RGB 0,0,255):")
out.lput("  这是真蓝色文字", rgb_fg=(0, 0, 255))

print()

# 黄色对比
print("标准黄色 (ANSI 33):")
out.lput("  这是标准黄色文字", font_color=FontColor8.YELLOW)
print("真黄色 (RGB 255,255,0):")
out.lput("  这是真黄色文字", rgb_fg=(255, 255, 0))

print()

# 黑色白色对比
print("标准黑色 (ANSI 30):")
out.lput("  这是标准黑色文字", font_color=FontColor8.BLACK)
print("真黑色 (RGB 0,0,0):")
out.lput("  这是真黑色文字", rgb_fg=(0, 0, 0))

print()

print("标准白色 (ANSI 37):")
out.lput("  这是标准白色文字", font_color=FontColor8.WHITE)
print("真白色 (RGB 255,255,255):")
out.lput("  这是真白色文字", rgb_fg=(255, 255, 255))

print("\n=== 背景色对比 ===\n")

print("标准红色背景 (ANSI 41):")
out.lput("  红色背景", background=Background8.RED, font_color="white")
print("真红色背景 (RGB 255,0,0):")
out.lput("  红色背景", rgb_bg=(255, 0, 0), font_color="white")

print()

print("标准蓝色背景 (ANSI 44):")
out.lput("  蓝色背景", background=Background8.BLUE, font_color="white")
print("真蓝色背景 (RGB 0,0,255):")
out.lput("  蓝色背景", rgb_bg=(0, 0, 255), font_color="white")

print("\n=== 直接 printf 测试 (作为参考) ===\n")
import os
os.system('printf "\\x1b[38;2;255;0;0m真红色 (RGB)\\x1b[0m\\n"')
os.system('printf "\\x1b[31m标准红色 (ANSI)\\x1b[0m\\n"')
