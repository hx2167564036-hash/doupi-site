"""首页改版第 2 轮：
1) 首屏去掉大只的章鱼哥头像，换成「档案卡」（保留天气、地区、小头像）；
2) 导航品牌前加 22px 圆头像，吉祥物不丢；
3) 项目区加「天枢」与「豆皮的生活台」两条，事实条 4 个 → 6 个。
"""
import pathlib
import re

root = pathlib.Path(__file__).resolve().parent.parent
tpl = root / "theme-doupi/templates/index.html"
css = root / "theme-doupi/assets/css/home.css"
layout = root / "theme-doupi/templates/modules/layout.html"

# ---------- 1. hero：portrait → dossier ----------
s = tpl.read_text(encoding="utf-8")
old_hero = """    <figure class="portrait zoom" data-in data-par="0.06" style="margin:0">
      <img th:src="@{/assets/img/avatar.webp}" alt="豆皮的头像">
      <figcaption class="cap"><span>北京 · 海淀</span><span>阴 14°C · 15:10</span></figcaption>
    </figure>"""

new_hero = """    <aside class="dossier zoom" data-in data-par="0.05">
      <div class="dos-head"><span>档案卡</span><em>NO. <b data-live="posts">492</b></em></div>
      <dl>
        <div><dt>现在</dt><dd>北京 · 海淀</dd></div>
        <div><dt>天气</dt><dd>阴 14°C · 15:10</dd></div>
        <div><dt>在读</dt><dd>浙大城市学院 · 软件工程</dd></div>
        <div><dt>起笔</dt><dd><span data-live="first">2025-04-09</span> 起，一天一篇</dd></div>
        <div><dt>眼下</dt><dd>雅思 11 月首考 · 期中周</dd></div>
      </dl>
      <div class="dos-foot">
        <img th:src="@{/assets/img/avatar.webp}" alt="豆皮的头像">
        <span>豆皮 · 持续记录中</span>
        <em>DOUPI123.TOP</em>
      </div>
    </aside>"""

if old_hero not in s:
    raise SystemExit("hero 锚点没匹配到")
s = s.replace(old_hero, new_hero, 1)

# ---------- 2. 事实条：4 个 → 6 个 ----------
s = s.replace("<div>在做的项目<b>4 个</b></div>", "<div>在做的项目<b>6 个</b></div>")

# ---------- 3. 项目区追加两条 ----------
anchor = """          <ul><li>80 份资料</li><li>题库拆分</li><li>双版本练习</li></ul></div>
        <span class="go">↗</span>
      </a>
    </div>
"""
add = anchor + """
    <div class="proj zoom" data-in style="--d:360">
      <div class="hoverbg"></div>
      <a href="#">
        <span class="n">05</span>
        <h3>天枢 · 上下文中枢<small>2026 · 在做 · Node.js / SQLite FTS5 / MCP / Electron</small></h3>
        <div class="desc">把散在本机与校园平台的文件汇成一座能搜的库：课程课件、Obsidian 笔记、微信与手机通知都进同一个索引，再以 MCP 接口交给任何 AI 直接读。
          <ul><li>2,255 份文档</li><li>57 门课 / 719 份课件</li><li>MCP 接口</li></ul></div>
        <span class="go">↗</span>
      </a>
    </div>

    <div class="proj zoom" data-in style="--d:450">
      <div class="hoverbg"></div>
      <a href="#">
        <span class="n">06</span>
        <h3>豆皮的生活台<small>2026 · 在做 · 微信小程序 / 云开发 / 12 个页面</small></h3>
        <div class="desc">一个只给自己的生活工作台：今天、课程表、记账、习惯、健身、作业、成绩都在里面，一句话就能把事扔进收集箱；云开发多用户架构，一人一份数据。
          <ul><li>openid 隔离</li><li>自然语言收集箱</li><li>1.0.4 待发布</li></ul></div>
        <span class="go">↗</span>
      </a>
    </div>
"""
if "天枢 · 上下文中枢" not in s:
    if anchor not in s:
        raise SystemExit("项目区锚点没匹配到")
    s = s.replace(anchor, add, 1)
tpl.write_text(s, encoding="utf-8")

# ---------- 4. 品牌前小头像 ----------
l = layout.read_text(encoding="utf-8")
if 'class="brand-ava"' not in l:
    l = l.replace('<a class="brand" th:href="@{/}">豆皮<small>DOUPI</small></a>',
                  '<a class="brand" th:href="@{/}"><img class="brand-ava" th:src="@{/assets/img/avatar.webp}" '
                  'alt="">豆皮<small>DOUPI</small></a>')
    layout.write_text(l, encoding="utf-8")

# ---------- 5. CSS ----------
c = css.read_text(encoding="utf-8")
if ".dossier{" not in c:
    c = c.replace("  .hero-foot{", """  .brand-ava{width:22px; height:22px; border-radius:50%; object-fit:cover; vertical-align:-6px;
    margin-right:8px; filter:grayscale(1) contrast(1.06); opacity:.9}

  .dossier{position:relative; width:100%; max-width:390px; margin-left:auto; padding:26px 26px 20px;
    border:1px solid var(--line); border-radius:18px; background:color-mix(in srgb, var(--surface) 92%, transparent);
    box-shadow:0 24px 60px -34px rgba(0,0,0,.28), 0 1px 3px rgba(0,0,0,.04); will-change:transform}
  .dos-head{display:flex; justify-content:space-between; align-items:baseline; padding-bottom:14px;
    border-bottom:1px solid var(--line-2); font-family:var(--mono); font-size:10.5px; letter-spacing:.16em;
    text-transform:uppercase; color:var(--muted)}
  .dos-head em{font-style:normal; color:var(--ink); letter-spacing:.08em}
  .dos-head b{font-variant-numeric:tabular-nums}
  .dossier dl{margin:6px 0 0}
  .dossier dl > div{display:grid; grid-template-columns:64px 1fr; gap:14px; align-items:baseline;
    padding:11px 0; border-bottom:1px solid color-mix(in srgb, var(--line) 55%, transparent)}
  .dossier dl > div:last-child{border-bottom:0}
  .dossier dt{font-family:var(--mono); font-size:10.5px; letter-spacing:.14em; color:var(--muted);
    text-transform:uppercase}
  .dossier dd{margin:0; font-size:14.5px; letter-spacing:-.01em; color:var(--ink)}
  .dos-foot{display:flex; align-items:center; gap:10px; margin-top:14px; padding-top:14px;
    border-top:1px solid var(--line-2); font-size:12px; color:var(--muted)}
  .dos-foot img{width:30px; height:30px; border-radius:50%; object-fit:cover; filter:grayscale(1) contrast(1.05);
    opacity:.92}
  .dos-foot em{margin-left:auto; font-style:normal; font-family:var(--mono); font-size:10px; letter-spacing:.14em}

  .hero-foot{""", 1)
    css.write_text(c, encoding="utf-8")

print("index/layout/css 已更新")
print("项目数:", s.count('class="proj zoom"'))
