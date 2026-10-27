const DATA = window.DAILY;
const SITE = "https://doupi123.top/archives/";
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
