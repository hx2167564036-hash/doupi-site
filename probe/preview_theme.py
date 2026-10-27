"""把主题模板渲染成本地可看的静态预览（只处理 nav 片段与资源路径），用于上传前自查。

只处理 index / page-daily / page-courses 三个模板 —— 文章、归档页需要服务端数据。
产物写到 theme-doupi/_preview-*.html，截图完可以删。
"""
import pathlib
import re

ROOT = pathlib.Path(r"D:\kendle\Documents\doupi123-top")
THEME = ROOT / "theme-doupi"

NAV = """<header class="nav" id="nav">
  <a class="brand" href="_preview-index.html">豆皮<small>DOUPI</small></a>
  <nav>
    <a href="_preview-index.html#work"{a1}>项目</a>
    <a href="_preview-index.html#skills"{a2}>能力</a>
    <a href="_preview-courses.html"{a3}>课程</a>
    <a href="_preview-index.html#shelf"{a4}>资料柜</a>
    <a href="_preview-daily.html"{a5}>记录</a>
    <a href="_preview-index.html#videos"{a6}>视频</a>
  </nav>
</header>"""

PAGES = [
    ("templates/index.html", "_preview-index.html", ""),
    ("templates/page-daily.html", "_preview-daily.html", "记录"),
    ("templates/page-courses.html", "_preview-courses.html", "课程"),
]


def main():
    for src, out, active in PAGES:
        html = (THEME / src).read_text(encoding="utf-8")
        marks = {
            "a1": ' class="on"' if active == "项目" else "",
            "a2": ' class="on"' if active == "能力" else "",
            "a3": ' class="on"' if active == "课程" else "",
            "a4": ' class="on"' if active == "资料柜" else "",
            "a5": ' class="on"' if active == "记录" else "",
            "a6": ' class="on"' if active == "视频" else "",
        }
        nav = NAV
        for k, v in marks.items():
            nav = nav.replace("{" + k + "}", v)
        html = re.sub(r'<header th:replace="~\{modules/layout :: nav\([^)]*\)\}"></header>', nav, html, count=1)
        html = re.sub(r'th:(href|src)="@\{/assets/([^"]+)\}"', r'\1="assets/\2"', html)
        html = html.replace('href="@{/}"', 'href="_preview-index.html"')
        html = html.replace('href="/courses"', 'href="_preview-courses.html"')
        html = html.replace('href="/daily"', 'href="_preview-daily.html"')
        html = html.replace('href="/#', 'href="_preview-index.html#')
        (THEME / out).write_text(html, encoding="utf-8")
        print("ok", out, len(html), "B")


if __name__ == "__main__":
    main()
