#标准色预览
import base

from mylib.kit.Loutput import Loutput
from mylib.kit.Loutput import FontColor8, Background8, TextEffect

out = Loutput()

out.lput("标准黑色", font_color=30)
out.lput("标准红色", font_color=31)
out.lput("标准绿色", font_color="32")
out.lput("标准蓝色", font_color="33")
out.lput("标准黄色", font_color=FontColor8.BLUE)
out.lput("标准紫色", font_color=FontColor8.MAGENTA_HIGH)
out.lput("标准淡蓝", font_color="CYAN")
out.lput("标准白色", font_color="white")

print('=' * 8)

out.lput("背景黑色", font_color="white", background=40)
out.lput("背景红色", font_color="white", background=41)
out.lput("背景绿色", font_color="white", background="42")
out.lput("背景蓝色", font_color="white", background="43")
out.lput("背景黄色", font_color="white", background=Background8.YELLOW)
out.lput("背景紫色", font_color="white", background=Background8.MAGENTA_HIGH)
out.lput("背景淡蓝", font_color="white", background="CYAN")
out.lput("背景白色", font_color="white", background="white")

print('=' * 8)

out.lput("测试文字", text_effects=0)
out.lput("测试文字", text_effects=1)
out.lput("测试文字", text_effects="2")
out.lput("测试文字", text_effects="3")
out.lput("测试文字", text_effects=TextEffect.UNDERLINE)
out.lput("测试文字", text_effects=TextEffect.BLINK)
out.lput("测试文字", text_effects="reverse")
out.lput("测试文字", text_effects="hide")
out.lput("测试文字", text_effects="STRIKE")
