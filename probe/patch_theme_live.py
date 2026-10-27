"""把「活数据」接进模板：数字都换成 [data-live] 占位，视频页走新模板分支。

可重复执行（已改过的会被断言跳过）。
用法：python -u probe/patch_theme_live.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent / "theme-doupi"
T = ROOT / "templates"


def sub(path, old, new, count=1):
    p = T / path
    s = p.read_text(encoding="utf-8")
    if new in s and old not in s:
        print(f"  跳过 {path}（已改）")
        return
    assert old in s, f"{path} 里找不到锚点：{old[:60]}"
    p.write_text(s.replace(old, new, count), encoding="utf-8")
    print(f"  {path} ✓")


def live(key, inner, tag="b"):
    return f'<{tag} data-live="{key}">{inner}</{tag}>'


# ---------- index.html ----------
print("index.html")
sub("index.html",
    "白天备考雅思，晚上把每天发生的事写成字和截图。<b>从 2025 年 4 月到现在，492 篇。</b>",
    '白天备考雅思，晚上把每天发生的事写成字和截图。<b>从 <span data-live="since">2025 年 4 月</span>到现在，'
    '<span data-live="posts">492</span> 篇。</b>')
sub("index.html", "<div>记录<b>492 篇</b></div>", '<div>记录<b><span data-live="posts">492</span> 篇</b></div>')
sub("index.html", "<div>有字的天<b>476 天</b></div>", '<div>有字的天<b><span data-live="days">476</span> 天</b></div>')
sub("index.html", "<div>图片资料<b>3,169 张</b></div>", '<div>图片资料<b><span data-live="images">3,169</span> 张</b></div>')
sub("index.html", '<span><i></i><b>492</b> 篇记录</span>', '<span><i></i><b data-live="posts">492</b> 篇记录</span>', 2)
sub("index.html", '<span><i></i><b>3,169</b> 张图片资料</span>', '<span><i></i><b data-live="images">3,169</b> 张图片资料</span>', 2)
sub("index.html", '<span><i></i>476 天有字 · 72 天留白</span>',
    '<span><i></i><span data-live="days">476</span> 天有字 · <span data-live="blank">72</span> 天留白</span>', 2)
sub("index.html", '<span><i></i>自 2025-04-09</span>', '<span><i></i>自 <span data-live="first">2025-04-09</span></span>', 2)
sub("index.html", '<div class="n" data-count="492">0</div><div class="t">每日记录</div>',
    '<div class="n" data-count="492" data-live-count="posts">0</div><div class="t">每日记录</div>')
sub("index.html", '<div class="n" data-count="492">0</div><div class="t">每日记录 PDF</div>',
    '<div class="n" data-count="492">0</div><div class="t">每日记录 PDF</div>')
sub("index.html", '<em>492 份 PDF · 按天编号 · 本地保管</em>',
    '<em><span data-live="pdfs">492</span> 份 PDF · 按天编号 · 本地保管</em>')
sub("index.html", '查看全部 492 篇 ↗', '查看全部 <span data-live="posts">492</span> 篇 ↗')
sub("index.html", '<script th:src="@{/assets/js/home.js}" defer></script>',
    '<script th:src="@{/assets/js/home.js}" defer></script>\n<script th:src="@{/assets/js/live.js}" defer></script>')

# ---------- 页脚统计 ----------
print("modules/layout.html")
sub("modules/layout.html", '<div class="row"><span>记录 / 有字的天</span><span>492 / 476</span></div>',
    '<div class="row"><span>记录 / 有字的天</span><span><span data-live="posts">492</span> / '
    '<span data-live="days">476</span></span></div>')
sub("modules/layout.html", '<div class="row"><span>图片资料</span><span>3,169 张</span></div>',
    '<div class="row"><span>图片资料</span><span><span data-live="images">3,169</span> 张</span></div>')
sub("modules/layout.html", '<a th:href="@{/#videos}" th:classappend="${active == \'视频\'} ? \'on\'">视频</a>',
    '<a th:href="@{/videos}" th:classappend="${active == \'视频\'} ? \'on\'">视频</a>')
sub("modules/layout.html", '<a th:href="@{/daily}">记录</a>',
    '<a th:href="@{/daily}">记录</a>\n      <a th:href="@{/videos}">视频</a>')

# ---------- page.html：视频分支 + daily 数字 ----------
print("page.html")
sub("page.html",
    '  <link rel="stylesheet" th:href="@{/assets/css/courses.css}" th:if="${singlePage.spec.slug == \'courses\'}" />',
    '  <link rel="stylesheet" th:href="@{/assets/css/courses.css}" th:if="${singlePage.spec.slug == \'courses\'}" />\n'
    '  <link rel="stylesheet" th:href="@{/assets/css/videos.css}" th:if="${singlePage.spec.slug == \'videos\'}" />')
sub("page.html", '<p class="sub"><b>492 篇</b>，从 2025-04-09 写到 2026-10-08；一共 548 天，其中 <b>476 天有字</b>，\n      72 天留白。点任意一天跳到原文。</p>',
    '<p class="sub"><b><span data-live="posts">492</span> 篇</b>，从 <span data-live="first">2025-04-09</span> 写到 '
    '<span data-live="last">2026-10-08</span>；一共 <span data-live="span">548</span> 天，其中 '
    '<b><span data-live="days">476</span> 天有字</b>，<span data-live="blank">72</span> 天留白。点任意一天跳到原文。</p>')
sub("page.html", '<script th:src="@{/assets/js/courses.js}" defer></script>',
    '<script th:src="@{/assets/js/courses.js}" defer></script>')

VIDEOS_BLOCK = '''
<!-- /videos -->
<th:block th:if="${slug == 'videos'}">
  <main class="vwrap">
    <section class="vhead">
      <p class="kicker">06 / VIDEOS</p>
      <h1>视频</h1>
      <p>记录类短片，横屏与竖屏各一版。点封面就在这一页看，也可以去 B 站（画质与弹幕更全）。</p>
    </section>

    <div class="vgrid" id="vgrid"></div>

    <section class="drafts">
      <h2>还在剪的</h2>
      <p class="sub">本地剪映工程，还没成片 —— 素材先存着，等有空再剪。</p>
      <ul id="drafts"></ul>
    </section>

    <p class="vfoot">全部作品在 <a href="https://space.bilibili.com/285926003" target="_blank" rel="noopener">B 站 · 豆皮 ↗</a></p>
  </main>

  <script th:src="@{/assets/data/videos.js}"></script>
  <script th:src="@{/assets/js/videos.js}" defer></script>
</th:block>
'''
sub("page.html", "<!-- 其他页面：直接渲染正文", VIDEOS_BLOCK + "\n<!-- 其他页面：直接渲染正文")
sub("page.html", '<header th:replace="~{modules/layout :: nav(${slug == \'daily\' ? \'记录\' : (slug == \'courses\' ? \'课程\' : \'\')})}"></header>',
    '<header th:replace="~{modules/layout :: nav(${slug == \'daily\' ? \'记录\' : (slug == \'courses\' ? \'课程\' : '
    '(slug == \'videos\' ? \'视频\' : \'\'))})}"></header>')
sub("page.html", '<footer>', '<script th:src="@{/assets/js/live.js}" defer></script>\n<footer>')

print("done")
