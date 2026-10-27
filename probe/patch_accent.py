"""给黑白版加一层克制的颜色：暖纸底 + 单一赭红强调色（不是色块，是点、线、数字）。

只改颜色 token 与少量强调规则，不动版式。
"""
import pathlib
import re

CSS = pathlib.Path(__file__).resolve().parent.parent / "theme-doupi/assets/css"

TOKENS = """  --pad:clamp(20px,4.6vw,68px);
  --bg:#FAF7F2; --bg-2:#F2EDE5; --surface:#FFFDF9; --ink:#1A1917; --muted:#7E776C;
  --line:rgba(26,25,23,.12); --line-2:#EAE4D9; --card:#FFFDF9;
  --accent:#B4553B; --accent-2:#8E3F2A; --accent-soft:#F7E9E3; --accent-line:rgba(180,85,59,.35);
  --sans:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  --mono:"SF Mono",ui-monospace,Menlo,Consolas,"Liberation Mono",monospace;
  --ease:cubic-bezier(.16,1,.3,1);
  --wrap:1120px;"""

HOME_TOKENS = """    --bg:#FAF7F2; --bg-2:#F2EDE5; --surface:#FFFDF9; --card:#FFFDF9;
    --ink:#1A1917; --ink-2:#4A453E; --muted:#7E776C;
    --line:#E6DFD4; --line-2:#EFE9DF;
    --accent:#B4553B; --accent-2:#8E3F2A; --accent-soft:#F7E9E3; --accent-line:rgba(180,85,59,.35);
    --dark:#141110; --dark-2:#1C1815;"""

DARK_TOKENS = """  html[data-theme="dark"]{
    --bg:#0B0A09; --bg-2:#141210; --surface:#191614; --ink:#F3EFE8; --ink-2:#C8C1B6; --muted:#948C80;
    --line:#2A2621; --line-2:#201D19;
    --accent:#E08A6E; --accent-2:#F0A98F; --accent-soft:#2A1D18; --accent-line:rgba(224,138,110,.4);
    --dark:#050505; --dark-2:#0D0B0A;"""

LAYER = """
/* ================= 强调色层：只上点、线、数字，不做色块 ================= */
::selection{background:var(--accent-soft); color:var(--ink)}
.kicker{color:var(--muted)}
.kicker::before{content:""; display:inline-block; width:6px; height:6px; border-radius:50%;
  background:var(--accent); margin-right:9px; vertical-align:2px; opacity:.9}
.band .kicker::before,.band .mono::before,.dark .kicker::before{background:var(--accent-2); opacity:1}

/* 首屏：事实条数字、档案卡编号 */
.facts b{color:var(--accent-2)}
.dos-head em{color:var(--accent-2)}
.dos-head em b{color:var(--accent)}
.dossier{border-color:var(--line); background:color-mix(in srgb, var(--card) 92%, var(--accent-soft))}
.dos-foot img{filter:grayscale(1) contrast(1.05)}

/* 跑马灯、时间轴热力、进度条 */
.strip i{background:var(--accent)}
.progress{background:var(--accent)}
.hm-grid i.on{background:color-mix(in srgb, var(--accent) 42%, var(--bg))}
.hm-grid i.warm{background:color-mix(in srgb, var(--accent) 80%, var(--bg))}
.hm i[data-v="1"]{background:color-mix(in srgb, var(--accent) 78%, var(--bg))}

/* 记录区的大数字与说明 */
.pin-num span{background:linear-gradient(180deg, var(--ink) 8%, color-mix(in srgb, var(--accent) 62%, var(--ink)))}
.pin-num em{color:var(--accent-2)}
.pin-sub b{color:var(--accent-2)}

/* 引文里的关键词 */
.statement b,.stmt b{color:var(--accent-2); box-shadow:none}

/* 按钮与链接 */
.btn.primary:hover{background:var(--accent); border-color:var(--accent)}
.btn.ghost:hover{border-color:var(--accent-line); color:var(--accent-2)}
a:hover{text-decoration-color:var(--accent-line)}
.proj:hover .p-name,.proj:hover .row-title{color:var(--accent-2)}
.files a:hover{border-bottom-color:var(--accent-line)}

/* 课程旗标、标签点 */
.c-flag[data-has="1"] i{background:var(--accent)}
.c-flag[data-has="0"] i{background:var(--muted)}
.ch{color:var(--accent-2); border-color:var(--accent-line)}

/* 页脚与外链 */
.foot a:hover,.fbrand em{color:var(--accent)}
.nav nav a.on{color:var(--ink)}
.nav nav a.on::after{content:""; display:block; height:2px; margin-top:-2px; border-radius:2px; background:var(--accent)}
"""


def main():
    base = CSS / "base.css"
    s = base.read_text(encoding="utf-8")
    s = re.sub(r"  --pad:clamp\(20px,4\.6vw,68px\);\n  --bg:#FAFAFC;[^\n]*\n[^\n]*--line:rgba\(0,0,0,\.10\)[^\n]*\n",
               TOKENS + "\n", s, count=1)
    if "强调色层" not in s:
        s += LAYER
    base.write_text(s, encoding="utf-8")
    print("base.css ✓")

    home = CSS / "home.css"
    h = home.read_text(encoding="utf-8")
    h = re.sub(r"    --bg:#FAFAFC;[^\n]*\n[^\n]*--dark-2:#141417;\n[^\n]*--link:#0066CC;\n",
               HOME_TOKENS + "\n", h, count=1)
    h = re.sub(r'  html\[data-theme="dark"\]\{[^\n]*\n[^\n]*\n[^\n]*--line[^\n]*\n',
               DARK_TOKENS + "\n", h, count=1)
    if "强调色层" not in h:
        h += LAYER
    home.write_text(h, encoding="utf-8")
    print("home.css ✓")
    print("base 有 --accent:", "--accent:#B4553B" in base.read_text(encoding="utf-8"))
    print("home 有 --accent:", "--accent:#B4553B" in home.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
