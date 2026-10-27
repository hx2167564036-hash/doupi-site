"""生成站点图标：墨底圆角方块 + 纸色「豆」字。

产出 theme-doupi/assets/img/ 下：
  favicon.ico（16/32/48 多尺寸）
  favicon-32.png
  favicon-192.png
  apple-touch-icon.png（180，圆角留白少一点）
  icon-512.png
"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "theme-doupi/assets/img"
OUT.mkdir(parents=True, exist_ok=True)

INK = (22, 24, 28, 255)        # #16181C
PAPER = (250, 250, 252, 255)   # #FAFAFC
FONT_PATH = r"C:\Windows\Fonts\msyhbd.ttc"

S = 1024
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# 圆角方块（22% 半径，跟站内卡片一致）
radius = int(S * 0.22)
d.rounded_rectangle((0, 0, S - 1, S - 1), radius=radius, fill=INK)

# 「豆」字：字号按视觉面积调，基线略上移
font = ImageFont.truetype(FONT_PATH, int(S * 0.52))
d.text((S / 2, S * 0.515), "豆", font=font, fill=PAPER, anchor="mm")

img.save(OUT / "icon-512.png")

for size in (192, 180, 32):
    small = img.resize((size, size), Image.LANCZOS)
    name = "apple-touch-icon.png" if size == 180 else f"favicon-{size}.png"
    small.save(OUT / name)

ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
img.resize((256, 256), Image.LANCZOS).save(OUT / "favicon.ico", sizes=ico_sizes)

for f in sorted(OUT.glob("favicon*")) + sorted(OUT.glob("apple-touch-icon.png")) + [OUT / "icon-512.png"]:
    print(f"{f.name:24s} {f.stat().st_size:>7d} B")
