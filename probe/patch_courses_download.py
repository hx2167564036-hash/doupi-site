"""把 /courses 的课件从「纯文本」改成「登录后可下载的链接」。

改动点：
1. courses.js：files 现在是 {n, ok, sz} 对象；可下载的渲染成 <a href="/course-files/…">，其余保持灰色文本；
   文案从「本地归档 · 不下载」改成「登录后可下载 · 点文件名」；卡片旗标显示可下载份数。
2. courses.css：补 .files a / .files .off / .dl-hint 的样式。
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "theme-doupi"
JS = ROOT / "assets/js/courses.js"
CSS = ROOT / "assets/css/courses.css"

js = JS.read_text(encoding="utf-8")

# 1) 加一个渲染单条课件的小工具（放在 esc 之后）
if "function fileItem(" not in js:
    anchor = "function renderList(){"
    helper = """function enc(s){ return encodeURIComponent(s); }

function fileItem(course, f){
  const label = `${esc(f.n)}${f.sz ? `<i>${(f.sz/1048576 < 0.1 ? Math.max(1, Math.round(f.sz/1024)) + ' KB' : (f.sz/1048576).toFixed(1) + ' MB')}</i>` : ''}`;
  if (!f.ok) return `<li class="off" title="${esc(f.n)} · 本地有记录但文件没下载到">${label}</li>`;
  return `<li><a href="/course-files/${enc(course)}/${enc(f.n)}" target="_blank" rel="noopener" title="${esc(f.n)}">${label}</a></li>`;
}

"""
    js = js.replace(anchor, helper + anchor, 1)

# 2) 首屏 12 条
old_fs = """    const fs = c.files.length
      ? `<ul class="files">${c.files.slice(0, 12).map(f => `<li title="${esc(f)}">${esc(f)}</li>`).join('')}</ul>` +
        (c.files.length > 12 ? `<button class="more" data-more="${i}">全部 ${c.files.length} 份 ↗</button>` : '')
      : `<p class="none">这门课暂无课件入库。</p>`;"""
new_fs = """    const dl = c.files.filter(f => f.ok).length;
    const fs = c.files.length
      ? `<ul class="files">${c.files.slice(0, 12).map(f => fileItem(c.name, f)).join('')}</ul>` +
        (c.files.length > 12 ? `<button class="more" data-more="${i}">全部 ${c.files.length} 份 ↗</button>` : '')
      : `<p class="none">这门课暂无课件入库。</p>`;"""
if old_fs not in js:
    raise SystemExit("首屏 files 锚点没匹配")
js = js.replace(old_fs, new_fs, 1)

# 3) 旗标与文案
js = js.replace(
    """<span class="c-flag" data-has="${c.files.length ? 1 : 0}"><i></i>${c.files.length ? c.files.length + ' 份课件' : '无课件'}</span>""",
    """<span class="c-flag" data-has="${dl ? 1 : 0}"><i></i>${c.files.length ? (dl ? dl + ' 可下载' : c.files.length + ' 份记录') : '无课件'}</span>""",
    1)
js = js.replace(
    """<p class="sec-t">课件（本地归档 · 不下载）</p>${fs}""",
    """<p class="sec-t">课件（点文件名下载 · 需要口令）</p>${fs}""",
    1)

# 4) 展开全部
old_more = """    card.querySelector('.files').innerHTML = c.files.map(f => `<li title="${esc(f)}">${esc(f)}</li>`).join('');"""
new_more = """    card.querySelector('.files').innerHTML = c.files.map(f => fileItem(c.name, f)).join('');"""
if old_more not in js:
    raise SystemExit("展开全部锚点没匹配")
js = js.replace(old_more, new_more, 1)

JS.write_text(js, encoding="utf-8")
print("courses.js ✓")

css = CSS.read_text(encoding="utf-8")
if ".files a{" not in css:
    css += """
/* 课件清单：可下载的是链接，不可下载的压暗 */
.files li{white-space:nowrap; overflow:hidden; text-overflow:ellipsis; align-items:baseline}
.files a{color:var(--ink); text-decoration:none; border-bottom:1px solid transparent;
  display:block; overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
.files a:hover{border-bottom-color:color-mix(in srgb, var(--ink) 40%, transparent)}
.files li.off{color:var(--muted)}
.files i{font-style:normal; font-size:10px; color:var(--muted); margin-left:6px; letter-spacing:.02em}
.files li.off i{opacity:.6}
"""
    CSS.write_text(css, encoding="utf-8")
    print("courses.css ✓")
else:
    print("courses.css 已有")
