"""快速测试 RGBColor 枚举"""
import base
from mylib.kit.Loutput import Loutput, RGBColor

out = Loutput()

print("测试直接使用 RGBColor 枚举（无需 .value）:\n")

# 不需要 .value
out.lput("✓ 红色测试", rgb_fg=RGBColor.RED)
out.lput("✓ 绿色测试", rgb_fg=RGBColor.GREEN)
out.lput("✓ 蓝色测试", rgb_fg=RGBColor.BLUE)
out.lput("✓ 成功颜色", rgb_fg=RGBColor.SUCCESS)
out.lput("✓ 警告颜色", rgb_fg=RGBColor.WARNING)
out.lput("✓ 危险颜色", rgb_fg=RGBColor.DANGER)
out.lput("✓ 信息颜色", rgb_fg=RGBColor.INFO)

print("\n测试元组方式（兼容）:\n")

# 仍然支持元组
out.lput("✓ 自定义红色", rgb_fg=(255, 100, 100))
out.lput("✓ 自定义绿色", rgb_fg=(100, 255, 100))
out.lput("✓ 自定义蓝色", rgb_fg=(100, 100, 255))

print("\n✅ 所有测试通过！现在可以直接使用 RGBColor 枚举,无需 .value")
