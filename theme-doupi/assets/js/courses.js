const DATA = window.COURSES || window.DAILY;
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

function enc(s){ return encodeURIComponent(s); }

function fileItem(course, f){
  const size = f.sz ? `<i>${(f.sz/1048576 < 0.1 ? Math.max(1, Math.round(f.sz/1024)) + ' KB' : (f.sz/1048576).toFixed(1) + ' MB')}</i>` : '';
  if (!f.ok) return `<li class="off" title="${esc(f.n)} · 本地有记录但文件没下载到"><span>${esc(f.n)}</span>${size}</li>`;
  return `<li title="${esc(f.n)}（点击下载）"><a href="/course-files/${enc(course)}/${enc(f.n)}" target="_blank" rel="noopener">${esc(f.n)}</a>${size}</li>`;
}

function renderList(){
  const items = DATA.courses.filter(c => (keyword ? true : c.sem === activeTerm) && match(c));
  if (!items.length){ listEl.innerHTML = '<p class="empty">没有匹配的课程。</p>'; return; }
  listEl.innerHTML = items.map((c, i) => {
    const chs = c.chapters.length
      ? `<ol class="chapters">${c.chapters.map(ch => `<li><span class="n">${String(ch.n).padStart(2,'0')}</span><span>${esc(ch.t)}</span></li>`).join('')}</ol>`
      : `<p class="none">教务系统还没有同步到章节结构。</p>`;
    const dl = c.files.filter(f => f.ok).length;
    const fs = c.files.length
      ? `<ul class="files">${c.files.slice(0, 12).map(f => fileItem(c.name, f)).join('')}</ul>` +
        (c.files.length > 12 ? `<button class="more" data-more="${i}">全部 ${c.files.length} 份 ↗</button>` : '')
      : `<p class="none">这门课暂无课件入库。</p>`;
    return `<article class="course" data-i="${i}">
      <button class="c-head">
        <span class="c-name">${esc(c.name)}<span class="ch">${(c.code.split(')')[1] || '').replace(/^-/, '').split('-')[0] || ''}</span></span>
        <span class="c-flag" data-has="${dl ? 1 : 0}"><i></i>${c.files.length ? (dl ? dl + ' 可下载' : c.files.length + ' 份记录') : '无课件'}</span>
        <span class="c-meta"><span>${c.semLabel}</span><span>${c.chapters.length ? c.chapters.length + ' 讲' : '章节待同步'}</span><span>${esc(c.code)}</span></span>
      </button>
      <div class="c-body">
        <p class="sec-t">章节结构</p>${chs}
        <p class="sec-t">课件（点文件名下载 · 需要口令）</p>${fs}
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
    card.querySelector('.files').innerHTML = c.files.map(f => fileItem(c.name, f)).join('');
    b.remove();
  }));
}

qEl.addEventListener('input', () => { keyword = qEl.value.trim(); renderList(); });

const nav = document.getElementById('nav');
addEventListener('scroll', () => nav.classList.toggle('solid', scrollY > 8), {passive:true});

renderTerms(); renderList();
