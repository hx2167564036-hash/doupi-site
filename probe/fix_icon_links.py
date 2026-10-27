"""两件事：
1) serve_assets.py 白名单补 .ico / .webmanifest（否则图标和 manifest 传不上去）；
2) 所有模板里 literal 的 href="/assets/img/favicon.ico" 改成 th:href，Halo 才会补 /themes/<name>/ 前缀。
"""
import pathlib
import re

root = pathlib.Path(__file__).resolve().parent.parent

# 1) 白名单
sa = root / "probe/serve_assets.py"
s = sa.read_text(encoding="utf-8")
old = '{".css", ".js", ".json", ".webp", ".woff2", ".svg", ".png"}'
new = '{".css", ".js", ".json", ".webp", ".woff2", ".svg", ".png", ".ico", ".webmanifest"}'
if old in s:
    sa.write_text(s.replace(old, new, 1), encoding="utf-8")
    print("serve_assets 白名单 ✓")
else:
    print("白名单锚点没匹配：" + ("已有" if ".ico" in s else "未知"))

# 2) favicon.ico 那行
n = 0
for p in (root / "theme-doupi/templates").rglob("*.html"):
    t = p.read_text(encoding="utf-8")
    if 'href="/assets/img/favicon.ico"' in t:
        t = t.replace('href="/assets/img/favicon.ico"', 'th:href="@{/assets/img/favicon.ico}"')
        p.write_text(t, encoding="utf-8")
        n += 1
print("改写的模板数:", n)
