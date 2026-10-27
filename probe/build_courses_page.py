"""生成 /courses 详情页（mockup），数据来自「上下文中枢」的 sqlite。

· 学期 → 课程 → 章节模块 + 课件文件名（只列名字，不含文件本体）
· 输出单文件 `mockups/v4/courses.html`，与 v4 index 同一套配色/字体
· 只取 code 形如 (2026-2027-1)-XXX 的真实课程，杂项（晚自习之类）丢弃
"""
import json
import pathlib
import re
import sqlite3
from collections import defaultdict

DB = r"D:\应用信息互联\data\context.db"
OUT = pathlib.Path(r"D:\kendle\Documents\doupi123-top\mockups\v4\courses.html")

CODE_RE = re.compile(r"^\((\d{4})-(\d{4})-(\d)\)")
LECT_RE = re.compile(r"第\s*(\d+)\s*讲\s*([\s\S]*?)(?=\s*第\s*\d+\s*讲\s|\[来源\]|$)", re.S)
SEM = {"1": "秋", "2": "春", "3": "夏"}


def main():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    cur = con.cursor()

    files = defaultdict(list)
    for cid, name in cur.execute("select course_id, name from tron_files order by name"):
        files[cid].append(name)

    chapters = defaultdict(list)
    for cid, body in cur.execute(
        "select json_extract(meta,'$.courseId'), body from documents where kind='章节'"
    ):
        if not cid or not body:
            continue
        if "章节结构" in body and "第1讲" not in body and "第 1 讲" not in body:
            continue
        for n, title in LECT_RE.findall(body):
            t = " ".join(title.split())
            t = re.sub(r"^[：:\s]+", "", t)
            if t:
                chapters[cid].append({"n": int(n), "t": t})

    courses = []
    for cid, name, code, start in cur.execute(
        "select id, name, code, start_date from tron_courses"
    ):
        m = CODE_RE.match(code or "")
        if not m or not start:
            continue
        y1, y2, term = m.groups()
        courses.append({
            "id": cid,
            "name": name,
            "code": code,
            "sem": f"{y1}-{y2}-{term}",
            "semLabel": f"{y1}—{y2} {SEM.get(term, term)}",
            "start": start[:10],
            "chapters": sorted(chapters.get(cid, []), key=lambda c: c["n"]),
            "files": files.get(cid, []),
        })

    # 同一学期同名课（-1A 这种重复同步）合并
    merged = {}
    for c in courses:
        key = (c["sem"], c["name"])
        if key in merged:
            merged[key]["files"] = sorted(set(merged[key]["files"]) | set(c["files"]))
            if len(c["chapters"]) > len(merged[key]["chapters"]):
                merged[key]["chapters"] = c["chapters"]
        else:
            merged[key] = c
    courses = list(merged.values())

    # 章节按源编号排好后，显示编号统一改成 1..N（有的课源编号是 0 起）
    for c in courses:
        c["chapters"] = [{"n": i + 1, "t": ch["t"]} for i, ch in enumerate(c["chapters"])]

    courses.sort(key=lambda c: c["name"])
    # 学期倒序 → 有课件优先 → 有章节优先 → 名字正序（稳定排序，两次排）
    courses.sort(key=lambda c: (c["start"], 1 if c["files"] else 0, 1 if c["chapters"] else 0),
                 reverse=True)
    terms = []
    seen = set()
    for c in courses:
        if c["sem"] not in seen:
            seen.add(c["sem"])
            terms.append({"sem": c["sem"], "label": c["semLabel"], "start": c["start"]})

    payload = json.dumps({"terms": terms, "courses": courses}, ensure_ascii=False)
    total_files = sum(len(c["files"]) for c in courses)
    total_ch = sum(len(c["chapters"]) for c in courses)

    html = TEMPLATE.replace("__DATA__", payload) \
                   .replace("__COURSES__", str(len(courses))) \
                   .replace("__TERMS__", str(len(terms))) \
                   .replace("__FILES__", str(total_files)) \
                   .replace("__CHAPTERS__", str(total_ch))
    OUT.write_text(html, encoding="utf-8")
    print(f"ok {OUT.name}: {len(terms)} 学期 / {len(courses)} 门 / "
          f"{total_files} 份课件 / {total_ch} 条章节，{len(html)} 字节")


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>课程 · 豆皮</title>
<style>
  :root{
    --bg:#FAFAFC; --bg-2:#F2F2F5; --ink:#1D1D1F; --muted:#86868B; --line:rgba(0,0,0,.10);
    --card:#FFFFFF; --dark:#0A0A0C; --sans:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
    --mono:"SF Mono",ui-monospace,Menlo,Consolas,"Liberation Mono",monospace;
    --ease:cubic-bezier(.16,1,.3,1);
  }
  *{box-sizing:border-box}
  html{overflow-x:clip; scroll-behavior:smooth}
  body{margin:0; background:var(--bg); color:var(--ink); font:16.5px/1.65 var(--sans);
    -webkit-font-smoothing:antialiased; letter-spacing:-.011em}
  a{color:inherit; text-decoration:none}
  .nav{position:sticky; top:0; z-index:50; display:flex; align-items:center; justify-content:space-between;
    gap:20px; padding:10px clamp(18px,4.6vw,68px); background:color-mix(in srgb,var(--bg) 86%, transparent);
    backdrop-filter:blur(18px) saturate(180%); border-bottom:1px solid transparent; transition:border-color .3s}
  .nav.solid{border-bottom-color:var(--line)}
  .brand{display:flex; align-items:baseline; gap:8px; font-weight:600; letter-spacing:-.02em}
  .brand small{font-family:var(--mono); font-size:9.5px; letter-spacing:.16em; color:var(--muted)}
  .nav nav{display:flex; gap:clamp(12px,2vw,26px); font-size:13.5px; color:var(--muted)}
  .nav nav a:hover{color:var(--ink)}
  .nav nav a.on{color:var(--ink); font-weight:500}

  .head{padding:clamp(44px,7vw,104px) clamp(18px,4.6vw,68px) clamp(20px,3vw,36px)}
  .kicker{font-family:var(--mono); font-size:10.5px; letter-spacing:.2em; text-transform:uppercase;
    color:var(--muted); margin:0 0 14px}
  h1{font-size:clamp(44px,8vw,116px); line-height:.96; letter-spacing:-.045em; margin:0 0 18px; font-weight:600}
  .head .sub{margin:0; max-width:46em; color:var(--muted); font-size:15px; line-height:1.75}
  .head .sub b{color:var(--ink); font-weight:500}

  .layout{display:grid; grid-template-columns:220px 1fr; gap:clamp(20px,3.4vw,56px);
    padding:0 clamp(18px,4.6vw,68px) clamp(60px,9vw,140px); align-items:start}
  .side{position:sticky; top:76px; display:flex; flex-direction:column; gap:18px}
  .search{position:relative}
  .search input{width:100%; padding:10px 12px 10px 32px; border-radius:10px; border:1px solid var(--line);
    background:var(--card); font:13px var(--sans); color:var(--ink); outline:none; transition:border-color .25s, box-shadow .25s}
  .search input:focus{border-color:color-mix(in srgb,var(--ink) 35%, transparent); box-shadow:0 0 0 4px rgba(0,0,0,.04)}
  .search::before{content:""; position:absolute; left:11px; top:50%; width:12px; height:12px; margin-top:-7px;
    border:1.5px solid var(--muted); border-radius:50%}
  .search::after{content:""; position:absolute; left:21px; top:50%; width:5px; height:1.5px; margin-top:5px;
    background:var(--muted); transform:rotate(45deg)}
  .terms{display:flex; flex-direction:column; gap:2px}
  .terms button{all:unset; cursor:pointer; display:flex; justify-content:space-between; align-items:baseline;
    gap:10px; padding:7px 10px; border-radius:8px; font-size:13.5px; color:var(--muted); transition:background .2s, color .2s}
  .terms button:hover{background:var(--bg-2); color:var(--ink)}
  .terms button.on{background:var(--ink); color:#fff}
  .terms button em{font-style:normal; font-family:var(--mono); font-size:10px; opacity:.7}

  .list{display:flex; flex-direction:column; gap:12px; min-height:40vh}
  .empty{color:var(--muted); font-size:14px; padding:24px 0}
  .course{border:1px solid var(--line); border-radius:16px; background:var(--card); overflow:hidden;
    transition:box-shadow .35s var(--ease), transform .35s var(--ease), border-color .25s}
  .course:hover{box-shadow:0 14px 40px -18px rgba(0,0,0,.24)}
  .c-head{display:grid; grid-template-columns:1fr auto; gap:6px 18px; align-items:baseline;
    width:100%; padding:18px clamp(16px,2.4vw,26px); background:none; border:0; text-align:left; cursor:pointer;
    font:inherit; color:inherit}
  .c-name{font-size:clamp(17px,1.7vw,21px); font-weight:600; letter-spacing:-.02em; display:flex; align-items:center; gap:10px}
  .c-name .ch{font-family:var(--mono); font-size:10px; font-weight:400; letter-spacing:.1em; color:var(--muted);
    border:1px solid var(--line); border-radius:6px; padding:2px 6px; white-space:nowrap}
  .c-meta{grid-column:1/-1; display:flex; flex-wrap:wrap; gap:6px 14px; font-family:var(--mono);
    font-size:10.5px; letter-spacing:.06em; color:var(--muted); text-transform:uppercase}
  .c-flag{font-size:11px; color:var(--muted); display:flex; align-items:center; gap:6px; white-space:nowrap}
  .c-flag i{display:block; width:7px; height:7px; border-radius:50%; background:var(--line)}
  .c-flag[data-has="1"] i{background:#1D9A5B}
  .c-body{display:none; padding:0 clamp(16px,2.4vw,26px) 20px; border-top:1px solid var(--line)}
  .course.open .c-body{display:block}
  .course.open{box-shadow:0 18px 50px -22px rgba(0,0,0,.28)}
  .sec-t{font-family:var(--mono); font-size:10px; letter-spacing:.18em; text-transform:uppercase;
    color:var(--muted); margin:20px 0 10px}
  .chapters{list-style:none; margin:0; padding:0; display:grid; gap:2px}
  .chapters li{display:grid; grid-template-columns:38px 1fr; gap:10px; padding:7px 0;
    border-bottom:1px solid color-mix(in srgb,var(--line) 60%, transparent); font-size:14px; line-height:1.6}
  .chapters li:last-child{border-bottom:0}
  .chapters .n{font-family:var(--mono); font-size:11px; color:var(--muted); padding-top:3px}
  .files{display:grid; grid-template-columns:repeat(auto-fill, minmax(260px,1fr)); gap:2px 18px; margin:0; padding:0; list-style:none}
  .files li{font-size:12.5px; line-height:1.6; color:var(--muted); padding:3px 0;
    overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
  .files li::before{content:"·"; margin-right:7px; color:var(--line)}
  .more{all:unset; cursor:pointer; font-size:12px; color:var(--ink); border-bottom:1px solid var(--ink);
    padding-bottom:1px; margin-top:12px; display:inline-block}
  .none{font-size:13px; color:var(--muted); margin:0}
  footer{border-top:1px solid var(--line); padding:clamp(30px,5vw,64px) clamp(18px,4.6vw,68px);
    display:flex; flex-wrap:wrap; gap:14px 32px; justify-content:space-between; align-items:baseline;
    font-size:12px; color:var(--muted)}
  footer b{color:var(--ink); font-weight:500}
  @media (max-width:880px){
    .layout{grid-template-columns:1fr}
    .side{position:static; flex-direction:row; flex-wrap:wrap; align-items:center; gap:12px}
    .search{flex:1 1 200px}
    .terms{flex-direction:row; flex-wrap:wrap; gap:6px; order:3; flex-basis:100%}
    .terms button{padding:6px 10px; border:1px solid var(--line)}
    .terms button.on{border-color:transparent}
  }
</style>
</head>
<body>
<header class="nav" id="nav">
  <a class="brand" href="index.html">豆皮<small>DOUPI</small></a>
  <nav>
    <a href="index.html#work">项目</a>
    <a href="index.html#skills">能力</a>
    <a class="on" href="courses.html">课程</a>
    <a href="index.html#shelf">资料柜</a>
    <a href="index.html#journal">记录</a>
    <a href="index.html#videos">视频</a>
  </nav>
</header>

<section class="head">
  <p class="kicker">03 / COURSES</p>
  <h1>课程</h1>
  <p class="sub">__TERMS__ 个学期 · <b>__COURSES__ 门课</b> · <b>__FILES__ 份课件</b> · __CHAPTERS__ 条章节在本地归档。
    这里只列课程、章节与文件名，课件本身不上站。</p>
</section>

<div class="layout">
  <aside class="side">
    <div class="search"><input id="q" type="search" placeholder="搜课程 / 章节…" autocomplete="off"></div>
    <div class="terms" id="terms"></div>
  </aside>
  <div class="list" id="list"></div>
</div>

<footer>
  <span><b>豆皮</b> · doupi123.top</span>
  <span>数据来自「上下文中枢」· 课件与作业只在本地保管</span>
</footer>

<script>
const DATA = __DATA__;
const listEl = document.getElementById('list');
const termsEl = document.getElementById('terms');
const qEl = document.getElementById('q');
let activeTerm = DATA.terms[0] ? DATA.terms[0].sem : null;
let keyword = '';

function esc(s){ return String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

function renderTerms(){
  termsEl.innerHTML = DATA.terms.map(t => {
    const n = DATA.courses.filter(c => c.sem === t.sem).length;
    return `<button data-sem="${t.sem}" class="${t.sem === activeTerm ? 'on' : ''}">
      <span>${t.label}</span><em>${n}</em></button>`;
  }).join('');
  termsEl.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
    activeTerm = b.dataset.sem; renderTerms(); renderList();
  }));
}

function match(c){
  if (!keyword) return true;
  const k = keyword.toLowerCase();
  if (c.name.toLowerCase().includes(k)) return true;
  if ((c.code || '').toLowerCase().includes(k)) return true;
  return c.chapters.some(ch => ch.t.toLowerCase().includes(k));
}

function renderList(){
  const items = DATA.courses.filter(c => (keyword ? true : c.sem === activeTerm) && match(c));
  if (!items.length){ listEl.innerHTML = '<p class="empty">没有匹配的课程。</p>'; return; }
  listEl.innerHTML = items.map((c, i) => {
    const chs = c.chapters.length
      ? `<ol class="chapters">${c.chapters.map(ch => `<li><span class="n">${String(ch.n).padStart(2,'0')}</span><span>${esc(ch.t)}</span></li>`).join('')}</ol>`
      : `<p class="none">教务系统还没有同步到章节结构。</p>`;
    const fs = c.files.length
      ? `<ul class="files">${c.files.slice(0, 12).map(f => `<li title="${esc(f)}">${esc(f)}</li>`).join('')}</ul>` +
        (c.files.length > 12 ? `<button class="more" data-more="${i}">全部 ${c.files.length} 份 ↗</button>` : '')
      : `<p class="none">这门课暂无课件入库。</p>`;
    return `<article class="course" data-i="${i}">
      <button class="c-head">
        <span class="c-name">${esc(c.name)}<span class="ch">${(c.code.split(')')[1] || '').replace(/^-/, '').split('-')[0] || ''}</span></span>
        <span class="c-flag" data-has="${c.files.length ? 1 : 0}"><i></i>${c.files.length ? c.files.length + ' 份课件' : '无课件'}</span>
        <span class="c-meta"><span>${c.semLabel}</span><span>${c.chapters.length ? c.chapters.length + ' 讲' : '章节待同步'}</span><span>${esc(c.code)}</span></span>
      </button>
      <div class="c-body">
        <p class="sec-t">章节结构</p>${chs}
        <p class="sec-t">课件（本地归档 · 不下载）</p>${fs}
      </div>
    </article>`;
  }).join('');

  listEl.querySelectorAll('.c-head').forEach(h => h.addEventListener('click', () => {
    h.parentElement.classList.toggle('open');
  }));
  listEl.querySelectorAll('.more').forEach(b => b.addEventListener('click', ev => {
    ev.stopPropagation();
    const c = items[+b.dataset.more];
    const card = b.closest('.course');
    card.querySelector('.files').innerHTML = c.files.map(f => `<li title="${esc(f)}">${esc(f)}</li>`).join('');
    b.remove();
  }));
}

qEl.addEventListener('input', () => { keyword = qEl.value.trim(); renderList(); });

const nav = document.getElementById('nav');
addEventListener('scroll', () => nav.classList.toggle('solid', scrollY > 8), {passive:true});

renderTerms(); renderList();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
