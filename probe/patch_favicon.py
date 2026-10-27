"""给所有模板挂图标 + manifest + theme-color；并让 live.js 顺手把标题里的篇数改成实时值。"""
import json
import pathlib
import re

root = pathlib.Path(__file__).resolve().parent.parent
tpl_dir = root / "theme-doupi/templates"

HEAD = """  <link rel="icon" href="/assets/img/favicon.ico" sizes="any" />
  <link rel="icon" type="image/png" sizes="32x32" th:href="@{/assets/img/favicon-32.png}" />
  <link rel="apple-touch-icon" th:href="@{/assets/img/apple-touch-icon.png}" />
  <link rel="manifest" th:href="@{/assets/site.webmanifest}" />
  <meta name="theme-color" content="#FAFAFC" />
"""

count = 0
for p in tpl_dir.rglob("*.html"):
    s = p.read_text(encoding="utf-8")
    if "favicon.ico" in s:
        continue
    m = re.search(r'<meta name="viewport"[^>]*>', s)
    if not m:
        # layout 片段没有 head，跳过
        continue
    s = s[: m.end()] + "\n" + HEAD + s[m.end():]
    p.write_text(s, encoding="utf-8")
    count += 1
print("挂上图标的模板数:", count)

# manifest
manifest = {
    "name": "豆皮 · doupi123.top",
    "short_name": "豆皮",
    "description": "软件工程在读本科生。项目、能力、课程、资料柜与每日记录。",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#FAFAFC",
    "theme_color": "#FAFAFC",
    "icons": [
        {"src": "/assets/img/favicon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "/assets/img/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "/assets/img/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
mp = root / "theme-doupi/assets/site.webmanifest"
mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("manifest:", mp.relative_to(root), mp.stat().st_size, "B")

# live.js：标题与 description 里的篇数跟着实时数走
lp = root / "theme-doupi/assets/js/live.js"
s = lp.read_text(encoding="utf-8")
hook = """  function applyAll(nums) {"""
if hook in s and "document.title" not in s:
    s = s.replace(hook, """  function syncHead(nums) {
    try {
      document.title = document.title.replace(/\\d+\\s*篇/, nums.posts + ' 篇');
      var md = document.querySelector('meta[name="description"]');
      if (md) md.setAttribute('content',
        md.getAttribute('content').replace(/\\d+\\s*篇/, nums.posts + ' 篇'));
    } catch (e) {}
  }

  function applyAll(nums) {
    syncHead(nums);""", 1)
    lp.write_text(s, encoding="utf-8")
    print("live.js 标题同步 ✓")
else:
    print("live.js 跳过（已改或无钩子）:", hook in s, "document.title" in s)
