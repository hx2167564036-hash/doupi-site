"""把 mockups/v4 的三个页面组装成 Halo 主题 theme-doupi。

· index.html / daily.html / courses.html → templates/{index,page-daily,page-courses}.html
· 内联 <style> → assets/css/{home,daily,courses}.css
· 内联 <script> → assets/js/{home,daily,courses}.js
· `const DATA = {...}` → assets/data/{daily,courses}.js（window.DAILY / window.COURSES）
· data/heatmap.js → assets/data/heatmap.js；assets/avatar.webp → assets/img/avatar.webp
"""
import json
import pathlib
import re
import shutil

ROOT = pathlib.Path(r"D:\kendle\Documents\doupi123-top")
SRC = ROOT / "mockups" / "v4"
THEME = ROOT / "theme-doupi"

PAGES = [
    # (mockup, template, css, js, active, title, desc)
    ("index", "index.html", "home.css", "home.js", "", "豆皮 · 个人档案",
     "软件工程在读本科生。项目、能力、课程、资料柜，和从 2025 年 4 月写到现在 492 篇的每日记录。"),
    ("daily", "page-daily.html", "daily.css", "daily.js", "记录", "记录 · 豆皮",
     "492 篇记录的时间轴，从 Day 000 到今天，中间留白 72 天。"),
    ("courses", "page-courses.html", "courses.css", "courses.js", "课程", "课程 · 豆皮",
     "5 个学期 57 门课、719 份课件的索引，只列课程、章节与文件名。"),
]

HEATMAP_SRC = SRC / "data" / "heatmap.js"
AVATAR_SRC = SRC / "assets" / "avatar.webp"


def split_style(html: str):
    m = re.search(r"<style>\n(.*?)\n</style>\n", html, re.S)
    if not m:
        raise SystemExit("没有找到 <style> 块")
    return html[: m.start()] + html[m.end():], m.group(1)


def split_scripts(html: str):
    """返回 (html_without_scripts, [script_inner, ...]) —— 只处理内联脚本。"""
    scripts = []
    out, pos = [], 0
    for m in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>\n?(.*?)\n?</script>\n?", html, re.S):
        out.append(html[pos:m.start()])
        scripts.append(m.group(1))
        pos = m.end()
    out.append(html[pos:])
    return "".join(out), scripts


def extract_const(js: str, name: str):
    """把 `const NAME = {...};` 抠出来 → (dict, 新 js)。"""
    idx = js.index(f"const {name} = ")
    start = idx + len(f"const {name} = ")
    obj, end = json.JSONDecoder().raw_decode(js[start:])
    tail = js[start + end:]
    tail = tail.lstrip()
    if tail.startswith(";"):
        tail = tail[1:]
    return obj, js[:idx] + f"const {name} = window.{ 'DAILY' if name == 'DATA' else 'COURSES' };" + tail


def fix_links(s: str) -> str:
    s = s.replace('href="index.html#', 'href="/#')
    s = s.replace('href="index.html"', 'href="/"')
    s = s.replace('href="courses.html"', 'href="/courses"')
    s = s.replace('href="daily.html"', 'href="/daily"')
    return s


def main():
    if not THEME.exists():
        raise SystemExit(f"主题目录不存在：{THEME}")
    (THEME / "assets" / "css").mkdir(parents=True, exist_ok=True)
    (THEME / "assets" / "js").mkdir(parents=True, exist_ok=True)
    (THEME / "assets" / "data").mkdir(parents=True, exist_ok=True)
    (THEME / "assets" / "img").mkdir(parents=True, exist_ok=True)
    (THEME / "templates").mkdir(parents=True, exist_ok=True)

    for mock, tpl, css, js, active, title, desc in PAGES:
        html = (SRC / f"{mock}.html").read_text(encoding="utf-8")

        # 1) 样式抽出
        html, style = split_style(html)

        # 2) 脚本抽出
        html, scripts = split_scripts(html)
        page_js = "\n\n".join(scripts).strip()

        # 3) 数据常量外置
        if mock == "daily":
            data, page_js = extract_const(page_js, "DATA")
            (THEME / "assets" / "data" / "daily.js").write_text(
                "window.DAILY = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n",
                encoding="utf-8")
        elif mock == "courses":
            data, page_js = extract_const(page_js, "DATA")
            (THEME / "assets" / "data" / "courses.js").write_text(
                "window.COURSES = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n",
                encoding="utf-8")

        # 4) 导航换成公共片段（mockup 里首页用 div.nav、子页用 header.nav）
        html = re.sub(r'<header class="nav"[\s\S]*?</header>\n?', '', html, count=1)
        html = re.sub(r'<div class="nav" id="nav">[\s\S]*?</button>\s*</div>\n?', '', html, count=1)
        html = fix_links(html)
        html = html.replace('src="assets/avatar.webp"', 'th:src="@{/assets/img/avatar.webp}"')
        html = html.replace('src="data/heatmap.js"', 'th:src="@{/assets/data/heatmap.js}"')
        html = html.replace("<html lang=\"zh-CN\">", "<html lang=\"zh-CN\" xmlns:th=\"https://www.thymeleaf.org\">")

        # 5) head 里补 css + description + 公共样式
        data_script = ""
        if mock == "daily":
            data_script = '  <script th:src="@{/assets/data/daily.js}"></script>\n'
        elif mock == "courses":
            data_script = '  <script th:src="@{/assets/data/courses.js}"></script>\n'

        # 去掉 mockup 自带的 description，避免重复
        html = re.sub(r'\n?<meta name="description"[^>]*>', '', html, count=1)
        head_extra = (
            f'  <link rel="stylesheet" th:href="@{{/assets/css/base.css}}" />\n'
            f'  <link rel="stylesheet" th:href="@{{/assets/css/{css}}}" />\n'
            f'  <meta name="description" content="{desc}" />\n'
        )
        html = html.replace("</head>", head_extra + "</head>", 1)

        nav = f'<header th:replace="~{{modules/layout :: nav(\'{active}\')}}"></header>\n'
        html = html.replace("<body>\n", "<body>\n" + nav, 1)
        html = html.replace("<body>", "<body>\n" + nav, 1) if "th:replace" not in html else html

        # 6) 页面脚本引用
        html = html.replace("</body>", data_script + f'  <script th:src="@{{/assets/js/{js}}}" defer></script>\n</body>', 1)

        # 首页：页脚真实外链 + 版本号 + 开场只在本次会话第一次出现 + 主题切换按钮已移除
        if mock == "index":
            html = html.replace('<a href="#">GitHub</a>', '<a href="https://github.com/" target="_blank" rel="noopener">GitHub</a>')
            html = html.replace('<a href="#">邮件</a>', '<a href="mailto:hi@doupi123.top">邮件</a>')
            html = html.replace('<a href="#">B 站</a>', '<a href="https://space.bilibili.com/285926003" target="_blank" rel="noopener">B 站</a>')
            html = html.replace('<a href="#">RSS</a>', '<a href="/rss.xml">RSS</a>')
            html = html.replace('Halo 驱动 · 主题 Doupi v4（mockup）', '由 Halo 驱动 · 主题 Doupi v1.0.0')
            page_js = page_js.replace(
                "  document.getElementById('themeBtn').addEventListener('click', function(){",
                "  var themeBtn = document.getElementById('themeBtn');\n  if (themeBtn) themeBtn.addEventListener('click', function(){")
            page_js = page_js.replace(
                "    if (reduce) { intro.remove(); docEl.classList.add('revealed'); return; }",
                "    if (reduce) { intro.remove(); docEl.classList.add('revealed'); return; }\n"
                "    var seenIntro = false;\n"
                "    try { seenIntro = sessionStorage.getItem('doupi-intro') === '1'; } catch (e) {}\n"
                "    if (seenIntro) { intro.remove(); docEl.classList.add('revealed'); return; }")
            page_js = page_js.replace(
                "      done = true;\n      intro.classList.add('done');",
                "      done = true;\n      try { sessionStorage.setItem('doupi-intro', '1'); } catch (e) {}\n      intro.classList.add('done');")

        (THEME / "templates" / tpl).write_text(html, encoding="utf-8")
        (THEME / "assets" / "css" / css).write_text(f"/* {mock} */\n" + style + "\n", encoding="utf-8")
        (THEME / "assets" / "js" / js).write_text(page_js + "\n", encoding="utf-8")
        print(f"ok {mock}: template={tpl} css={len(style)}B js={len(page_js)}B")

    # 静态资源
    shutil.copyfile(HEATMAP_SRC, THEME / "assets" / "data" / "heatmap.js")
    shutil.copyfile(AVATAR_SRC, THEME / "assets" / "img" / "avatar.webp")
    print("ok 静态资源：heatmap.js / avatar.webp")


if __name__ == "__main__":
    main()
