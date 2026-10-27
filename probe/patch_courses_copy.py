"""课程页文案与清单排版：说清「点文件名下载（要口令）」，长文件名省略号、体积右对齐。"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "theme-doupi"

# 1) courses 页顶部说明
page = ROOT / "templates/page.html"
s = page.read_text(encoding="utf-8")
old = "这里只列课程、章节与文件名，课件本身不上站。"
new = "章节结构来自教务系统；课件放在服务器上，点文件名下载（需要口令）。"
if old in s:
    s = s.replace(old, new)
    page.write_text(s, encoding="utf-8")
    print("page.html 文案 ✓")
else:
    print("page.html 文案未匹配")

# 2) 首页课程区的说明
idx = ROOT / "templates/index.html"
s = idx.read_text(encoding="utf-8")
old2 = "课件、作业与考试只在本地保管，站上只放课程与数量。"
new2 = "课件放在服务器上，登录口令后可下载；作业与考试只留记录。"
if old2 in s:
    s = s.replace(old2, new2)
    idx.write_text(s, encoding="utf-8")
    print("index.html 文案 ✓")
else:
    print("index.html 文案未匹配")

# 3) 清单排版：一行 = 名称(可省略) + 体积(右)
css = ROOT / "assets/css/courses.css"
c = css.read_text(encoding="utf-8")
old3 = """.files li{white-space:nowrap; overflow:hidden; text-overflow:ellipsis; align-items:baseline}
.files a{color:var(--ink); text-decoration:none; border-bottom:1px solid transparent;
  display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.files a:hover{border-bottom-color:color-mix(in srgb, var(--ink) 40%, transparent)}
.files li.off{color:var(--muted)}
.files i{font-style:normal; font-size:10px; color:var(--muted); margin-left:6px; letter-spacing:.02em}
.files li.off i{opacity:.6}"""
new3 = """.files li{display:flex; align-items:baseline; gap:8px; min-width:0}
.files li > a, .files li > span{flex:1 1 auto; min-width:0; overflow:hidden; text-overflow:ellipsis;
  white-space:nowrap; color:var(--ink); text-decoration:none}
.files li > a{border-bottom:1px solid transparent}
.files li > a:hover{border-bottom-color:color-mix(in srgb, var(--ink) 40%, transparent)}
.files li.off > span{color:var(--muted)}
.files i{flex:none; font-style:normal; font-size:10px; color:var(--muted); letter-spacing:.02em}"""
if old3 in c:
    css.write_text(c.replace(old3, new3), encoding="utf-8")
    print("courses.css 排版 ✓")
else:
    print("courses.css 锚点未匹配")
