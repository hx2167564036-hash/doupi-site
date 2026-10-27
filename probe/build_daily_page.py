"""生成 /daily 时间轴页（mockup），数据来自 mockups/v1/data/posts.json。

· 492 篇记录按 年 → 月 分组，逐日一行（日期 · 星期 · Day 号 · 外链）
· 断更处插「留白 N 天」行；顶部一条 76 周热力条
· 单文件 `mockups/v4/daily.html`，与 v4 同一套配色/字体；与 courses.html 互为二级页
"""
import json
import pathlib
from datetime import date

ROOT = pathlib.Path(r"D:\kendle\Documents\doupi123-top")
DATA = ROOT / "mockups" / "v1" / "data" / "posts.json"
OUT = ROOT / "mockups" / "v4" / "daily.html"
SITE = "https://doupi123.top/archives/"


def main():
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    rows.sort(key=lambda r: r["date"])

    days = [r["date"] for r in rows]
    uniq = sorted(set(days))
    d0, d1 = date.fromisoformat(uniq[0]), date.fromisoformat(uniq[-1])
    span = (d1 - d0).days + 1
    fill = len(uniq)

    payload = {
        "rows": [{"d": r["date"], "n": r.get("day"), "t": r["title"], "s": r["slug"]} for r in rows],
        "stats": {"rows": len(rows), "days": fill, "span": span, "blank": span - fill,
                  "from": uniq[0], "to": uniq[-1]},
    }

    html = TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False)) \
                   .replace("__FROM__", uniq[0]) \
                   .replace("__TO__", uniq[-1]) \
                   .replace("__ROWS__", str(len(rows))) \
                   .replace("__DAYS__", str(fill)) \
                   .replace("__SPAN__", str(span)) \
                   .replace("__BLANK__", str(span - fill)) \
                   .replace("__SITE__", SITE)
    OUT.write_text(html, encoding="utf-8")
    print(f"ok {OUT.name}: {len(rows)} 篇 / {fill} 天有字 / 跨 {span} 天 / 空 {span - fill} 天，{len(html)} 字节")


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>记录 · 豆皮</title>
<style>
  :root{
    --bg:#FAFAFC; --bg-2:#F2F2F5; --ink:#1D1D1F; --muted:#86868B; --line:rgba(0,0,0,.10);
    --card:#FFFFFF; --sans:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
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

  .head{padding:clamp(42px,6.4vw,96px) clamp(18px,4.6vw,68px) clamp(14px,2vw,24px)}
  .kicker{font-family:var(--mono); font-size:10.5px; letter-spacing:.2em; text-transform:uppercase;
    color:var(--muted); margin:0 0 14px}
  h1{font-size:clamp(44px,8vw,116px); line-height:.96; letter-spacing:-.045em; margin:0 0 16px; font-weight:600}
  .head .sub{margin:0; max-width:52em; color:var(--muted); font-size:15px; line-height:1.75}
  .head .sub b{color:var(--ink); font-weight:500}

  .hm-wrap{padding:clamp(10px,2vw,18px) clamp(18px,4.6vw,68px) 0}
  .hm{display:grid; grid-auto-flow:column; grid-template-rows:repeat(7,9px); gap:3px;
    overflow-x:auto; padding-bottom:6px; scrollbar-width:thin}
  .hm i{display:block; width:9px; height:9px; border-radius:2px; background:#E9E9EE}
  .hm i[data-v="1"]{background:#1D1D1F}
  .hm-gap{width:7px; flex:none}
  .hm-legend{display:flex; align-items:center; gap:8px; margin-top:8px; font-family:var(--mono);
    font-size:9.5px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted)}
  .hm-legend span{display:flex; gap:3px; align-items:center}

  .layout{display:grid; grid-template-columns:190px 1fr; gap:clamp(20px,3.4vw,56px);
    padding:clamp(20px,3vw,36px) clamp(18px,4.6vw,68px) clamp(60px,9vw,140px); align-items:start}
  .side{position:sticky; top:76px; display:flex; flex-direction:column; gap:16px; max-height:calc(100vh - 100px); overflow:auto}
  .search input{width:100%; padding:10px 12px 10px 32px; border-radius:10px; border:1px solid var(--line);
    background:var(--card); font:13px var(--sans); color:var(--ink); outline:none}
  .search{position:relative}
  .search input:focus{border-color:color-mix(in srgb,var(--ink) 35%, transparent); box-shadow:0 0 0 4px rgba(0,0,0,.04)}
  .search::before{content:""; position:absolute; left:11px; top:50%; width:12px; height:12px; margin-top:-7px;
    border:1.5px solid var(--muted); border-radius:50%}
  .search::after{content:""; position:absolute; left:21px; top:50%; width:5px; height:1.5px; margin-top:5px;
    background:var(--muted); transform:rotate(45deg)}
  .rail{display:flex; flex-direction:column; gap:2px}
  .rail .y{font-family:var(--mono); font-size:10px; letter-spacing:.18em; color:var(--muted); margin:10px 0 4px 8px}
  .rail a{display:flex; justify-content:space-between; align-items:baseline; gap:8px;
    padding:5px 8px; border-radius:7px; font-size:13px; color:var(--muted); transition:background .2s, color .2s}
  .rail a:hover{background:var(--bg-2); color:var(--ink)}
  .rail a em{font-style:normal; font-family:var(--mono); font-size:10px; opacity:.65}

  .tl{min-height:50vh}
  .mblock{margin-bottom:clamp(26px,3.6vw,44px)}
  .mhead{position:sticky; top:58px; z-index:5; display:flex; align-items:baseline; gap:14px;
    padding:8px 0 10px; background:linear-gradient(var(--bg) 72%, transparent); backdrop-filter:blur(4px)}
  .mhead .mnum{font-size:clamp(26px,3.4vw,40px); font-weight:600; letter-spacing:-.04em; line-height:1}
  .mhead .mmeta{font-family:var(--mono); font-size:10px; letter-spacing:.14em; text-transform:uppercase; color:var(--muted)}
  .rows{display:flex; flex-direction:column}
  .row{display:grid; grid-template-columns:64px 64px 1fr; gap:clamp(8px,1.6vw,20px); align-items:baseline;
    padding:9px 2px; border-bottom:1px solid color-mix(in srgb,var(--line) 65%, transparent);
    transition:background .18s, padding-left .18s}
  .row:hover{background:color-mix(in srgb,var(--bg-2) 70%, transparent); padding-left:8px}
  .row .d{font-family:var(--mono); font-size:12.5px; color:var(--ink)}
  .row .w{font-size:12px; color:var(--muted)}
  .row .t{font-size:14px; color:var(--ink); overflow:hidden; text-overflow:ellipsis; white-space:nowrap}
  .row .t small{color:var(--muted); font-size:11.5px; margin-left:8px; font-family:var(--mono)}
  .row .go{font-size:11px; color:var(--muted); opacity:0; transition:opacity .2s}
  .row:hover .go{opacity:1}
  .chips{display:flex; flex-wrap:wrap; gap:6px}
  .chip{font-family:var(--mono); font-size:11px; letter-spacing:.02em; padding:3px 9px;
    border:1px solid var(--line); border-radius:999px; color:var(--ink); white-space:nowrap;
    transition:background .18s, border-color .18s, color .18s}
  .chip:hover{background:var(--ink); border-color:var(--ink); color:var(--bg)}
  .chip.free{font-family:var(--sans); font-size:12px; color:var(--muted)}
  .gap{display:flex; align-items:center; gap:10px; padding:7px 2px; color:var(--muted);
    font-family:var(--mono); font-size:10px; letter-spacing:.12em; text-transform:uppercase}
  .gap::before,.gap::after{content:""; height:1px; background:color-mix(in srgb,var(--line) 80%, transparent); flex:1}
  .empty{color:var(--muted); font-size:14px; padding:24px 0}

  footer{border-top:1px solid var(--line); padding:clamp(30px,5vw,64px) clamp(18px,4.6vw,68px);
    display:flex; flex-wrap:wrap; gap:14px 32px; justify-content:space-between; align-items:baseline;
    font-size:12px; color:var(--muted)}
  footer b{color:var(--ink); font-weight:500}

  @media (max-width:880px){
    .layout{grid-template-columns:1fr}
    .side{position:static; flex-direction:row; flex-wrap:wrap; align-items:center; gap:12px; max-height:none}
    .search{flex:1 1 180px}
    .rail{flex-direction:row; flex-wrap:wrap; gap:4px; order:3; flex-basis:100%}
    .rail .y{display:none}
    .rail a{padding:5px 9px; border:1px solid var(--line)}
    .row{grid-template-columns:52px 1fr}
    .row .w{display:none}
    .mhead{top:52px}
  }
</style>
</head>
<body>
<header class="nav" id="nav">
  <a class="brand" href="index.html">豆皮<small>DOUPI</small></a>
  <nav>
    <a href="index.html#work">项目</a>
    <a href="index.html#skills">能力</a>
    <a href="courses.html">课程</a>
    <a href="index.html#shelf">资料柜</a>
    <a class="on" href="daily.html">记录</a>
    <a href="index.html#videos">视频</a>
  </nav>
</header>

<section class="head">
  <p class="kicker">05 / JOURNAL</p>
  <h1>记录</h1>
  <p class="sub"><b>__ROWS__ 篇</b>，从 __FROM__ 写到 __TO__；一共 __SPAN__ 天，其中 <b>__DAYS__ 天有字</b>，
    __BLANK__ 天留白。点任意一天跳到原文。</p>
</section>

<div class="hm-wrap">
  <div class="hm" id="hm"></div>
  <div class="hm-legend"><span>少</span><span><i style="width:9px;height:9px;border-radius:2px;background:#E9E9EE;display:block"></i>
    <i style="width:9px;height:9px;border-radius:2px;background:#1D1D1F;display:block"></i></span><span>有字</span>
    <span style="margin-left:auto">每周一列 · 悬停看日期</span></div>
</div>

<div class="layout">
  <aside class="side">
    <div class="search"><input id="q" type="search" placeholder="搜日期 / Day 号…" autocomplete="off"></div>
    <div class="rail" id="rail"></div>
  </aside>
  <div class="tl" id="tl"></div>
</div>

<footer>
  <span><b>豆皮</b> · doupi123.top</span>
  <span>原文托管在 Halo · 本地另有 492 份按天导出的 PDF</span>
</footer>

<script>
const DATA = __DATA__;
const SITE = "__SITE__";
const rows = DATA.rows, st = DATA.stats;
const WEEK = ['周日','周一','周二','周三','周四','周五','周六'];
const monthName = m => String(+m).padStart(2,'0');

/* ---------- 热力条 ---------- */
(function heat(){
  const have = new Set(rows.map(r => r.d));
  const d0 = new Date(st.from + 'T00:00:00'), d1 = new Date(st.to + 'T00:00:00');
  const start = new Date(d0);
  start.setDate(start.getDate() - (start.getDay() + 6) % 7);   // 回到本周一
  const el = document.getElementById('hm');
  let html = '';
  for (let d = new Date(start); d <= d1; d.setDate(d.getDate() + 1)) {
    const iso = d.toISOString().slice(0, 10);
    if (d < d0) { html += '<i style="opacity:0"></i>'; continue; }
    const on = have.has(iso) ? 1 : 0;
    html += `<i data-v="${on}" title="${iso}${on ? ' · 有记录' : ' · 留白'}"></i>`;
  }
  el.innerHTML = html;
})();

/* ---------- 月份索引 ---------- */
const months = [];
(function buildMonths(){
  const map = new Map();
  rows.forEach(r => {
    const key = r.d.slice(0, 7);
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(r);
  });
  for (const [k, v] of map) months.push({key: k, rows: v});
})();

const rail = document.getElementById('rail');
(function buildRail(){
  let html = '', year = '';
  months.forEach(m => {
    const y = m.key.slice(0, 4);
    if (y !== year) { html += `<div class="y">${y}</div>`; year = y; }
    html += `<a href="#m${m.key}" data-m="${m.key}"><span>${y} · ${monthName(m.key.slice(5,7))} 月</span><em>${m.rows.length}</em></a>`;
  });
  rail.innerHTML = html;
})();

/* ---------- 时间轴 ---------- */
const tl = document.getElementById('tl');
function esc(s){ return String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function gapText(prev, next){
  const a = new Date(prev + 'T00:00:00'), b = new Date(next + 'T00:00:00');
  return Math.round((b - a) / 86400000) - 1;
}
function render(filter){
  const f = (filter || '').trim().toLowerCase();
  let out = '';
  months.forEach(m => {
    const list = m.rows.filter(r => !f || r.d.includes(f) ||
      String(r.n ?? '') === f || ('day ' + (r.n ?? '')).includes(f) || r.d.replaceAll('-','').includes(f));
    if (!list.length) return;

    // 同一天可能有多篇（早期重复导入）→ 一天一行，篇数用 chip 列出
    const days = [];
    const byDate = new Map();
    list.forEach(r => {
      if (!byDate.has(r.d)) { byDate.set(r.d, []); days.push(r.d); }
      byDate.get(r.d).push(r);
    });

    out += `<section class="mblock" id="m${m.key}">
      <div class="mhead"><span class="mnum">${monthName(m.key.slice(5,7))}</span>
        <span class="mmeta">${m.key.slice(0,4)} · ${days.length} 天 / ${list.length} 篇</span></div>
      <div class="rows">`;

    let prev = null;
    days.forEach(d => {
      if (prev) {
        const g = gapText(prev, d);
        if (g > 0) out += `<div class="gap">留白 ${g} 天</div>`;
      }
      prev = d;
      const wd = WEEK[new Date(d + 'T00:00:00').getDay()];
      const seen = new Set();
      const chips = byDate.get(d).slice().sort((a, b) => (a.n ?? 999) - (b.n ?? 999)).filter(r => {
        const k = String(r.n) + '|' + r.t;           // 同一天同标题的重复帖只列一次
        if (seen.has(k)) return false;
        seen.add(k); return true;
      }).map(r => {
        const std = /^\d{4}-\d{2}-\d{2}\s*Day\s*0*(\d+)$/i.test(r.t);
        const label = std ? `Day ${String(r.n).padStart(3,'0')}` : r.t;
        const cls = 'chip' + (std ? '' : ' free');
        return `<a class="${cls}" href="${SITE}${r.s}" target="_blank" rel="noopener"
          title="${esc(r.t)}">${esc(label.length > 26 ? label.slice(0, 26) + '…' : label)}</a>`;
      }).join('');
      out += `<div class="row">
        <span class="d">${d.slice(5)}</span><span class="w">${wd}</span>
        <span class="chips">${chips}</span></div>`;
    });
    out += '</div></section>';
  });
  tl.innerHTML = out || '<p class="empty">没有匹配的日期。</p>';
}

document.getElementById('q').addEventListener('input', e => render(e.target.value));
const nav = document.getElementById('nav');
addEventListener('scroll', () => nav.classList.toggle('solid', scrollY > 8), {passive:true});

render('');
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
