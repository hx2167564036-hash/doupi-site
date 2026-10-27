/* 活数据：把站点上真实的数量填进 [data-live] / [data-live-count] / 声明段。
   数据源：公开内容 API（分类、标签、文章）+ 主题自带的 stats.json（本地存档数量）。
   结果缓存在 sessionStorage，同一次会话只拉一遍。 */
(function(){
  var API = '/apis/api.content.halo.run/v1alpha1/posts';
  var PAGE = 100;
  var CACHE = 'doupi-live-v1';
  var TTL = 1000 * 60 * 30;            // 半小时内直接用缓存
  var els = document.querySelectorAll('[data-live]');
  if (!els.length && !document.getElementById('words')) return;

  function fmt(n){ return (n || 0).toLocaleString('en-US'); }

  function applyImgs(images) {
  if (!images) return;
  var txt = images.toLocaleString('en-US') + ' 张';
  document.querySelectorAll('body *').forEach(function (el) {
    if (el.children.length) return;
    if (/^3,?169\s*张$/.test(el.textContent.trim())) el.textContent = txt;
  });
}

function apply(s){
    els.forEach(function(el){
      var k = el.getAttribute('data-live');
      if (k === 'since') { el.textContent = s.firstYM || ''; return; }
      if (k === 'images') { el.textContent = fmt(s.images); return; }
      if (k === 'pdfs') { el.textContent = fmt(s.pdfs); return; }
      var v = s[k];
      if (v === undefined || v === null) return;
      el.textContent = (k === 'posts' || k === 'days' || k === 'blank' || k === 'span') ? fmt(v) : v;
    });
    var nums = { posts: s.posts, days: s.days };
    if (window.doupiApplyNumbers) window.doupiApplyNumbers(nums);
    document.querySelectorAll('[data-count="492"]').forEach(function(el){
      if (el.getAttribute('data-live-count')) return;
      el.setAttribute('data-count', s.posts);
      if (parseInt(el.textContent.replace(/,/g, ''), 10) > 0) el.textContent = fmt(s.posts);
    });
    if (s.words && window.doupiSetStatement) window.doupiSetStatement(s.words);
    applyImgs(s.images);
    /* 标题 / description 里的「N 篇」也跟着走 */
    try {
      document.title = document.title.replace(/\d+\s*篇/, fmt(s.posts) + ' 篇');
      var md = document.querySelector('meta[name="description"]');
      if (md && md.content) md.setAttribute('content', md.content.replace(/\d+\s*篇/, s.posts + ' 篇'));
    } catch (e) {}
    document.documentElement.setAttribute('data-live-ready', '1');
  }

  /* 1. 先吃缓存，页面不会闪 */
  var cached = null;
  try {
    cached = JSON.parse(sessionStorage.getItem(CACHE) || 'null');
  } catch (e) { cached = null; }
  if (cached && Date.now() - (cached.t || 0) < TTL) { apply(cached); return; }
  if (cached) apply(cached);

  /* 2. 拉文章，算「记录 / 有字的天 / 跨度 / 留白」 */
  function page(n){
    return fetch(API + '?page=' + n + '&size=' + PAGE, { headers: { 'Accept': 'application/json' } })
      .then(function(r){ return r.ok ? r.json() : null; });
  }

  function whole(){
    return page(1).then(function(first){
      if (!first || !Array.isArray(first.items)) return null;
      var pages = Math.max(1, Math.ceil(first.total / PAGE));
      var jobs = [];
      for (var i = 2; i <= pages; i++) jobs.push(page(i));
      return Promise.all(jobs).then(function(rest){
        var seen = {}, items = [];
        var push = function(list){
          (list || []).forEach(function(it){
            var id = (it.post && it.post.metadata && it.post.metadata.name) ||
                     (it.metadata && it.metadata.name);
            if (id && seen[id]) return;
            if (id) seen[id] = 1;
            items.push(it);
          });
        };
        push(first.items);
        rest.forEach(function(r){ if (r) push(r.items); });
        return items;
      });
    });
  }

  function dayNum(item){
    var p = item.post || item;
    var spec = p.spec || {};
    var src = (spec.slug || '') + ' ' + (spec.title || '');
    var m = src.match(/day[-_ ]?(\d{1,4})/i);
    return m ? parseInt(m[1], 10) : null;
  }

  function dateIn(item){
    var p = item.post || item;
    var spec = p.spec || {};
    var src = (spec.slug || '') + ' ' + (spec.title || '');
    var m = src.match(/(\d{4})-(\d{2})-(\d{2})/);
    return m ? m[1] + '-' + m[2] + '-' + m[3] : null;
  }

  function compute(items){
    var rows = [], all = 0;
    items.forEach(function(it){
      all++;
      rows.push({ d: dateIn(it), n: dayNum(it) });
    });
    /* 少数帖子 slug 里没有日期，用 Day 号反查同号帖子的日期 */
    var byNum = {};
    rows.forEach(function(r){ if (r.n !== null && r.d) byNum[r.n] = r.d; });
    var dates = {}, rec = 0;
    rows.forEach(function(r){
      var d = r.d || (r.n !== null ? byNum[r.n] : null);
      if (!d) return;
      rec++; dates[d] = 1;
    });
    var keys = Object.keys(dates).sort();
    if (!keys.length) return null;
    var first = keys[0], last = keys[keys.length - 1];
    var days = keys.length;
    var span = Math.round((new Date(last + 'T00:00:00Z') - new Date(first + 'T00:00:00Z')) / 86400000) + 1;
    return {
      posts: rec, allPosts: all, days: days, span: span, blank: span - days,
      first: first, last: last,
      firstYM: first.slice(0, 4) + ' 年 ' + parseInt(first.slice(5, 7), 10) + ' 月',
      words: '从 ' + first.slice(0, 4) + ' 年 ' + parseInt(first.slice(5, 7), 10) + ' 月 ' +
             parseInt(first.slice(8, 10), 10) + ' 日的第 1 天，写到 ' +
             last.slice(0, 4) + ' 年 ' + parseInt(last.slice(5, 7), 10) + ' 月 ' +
             parseInt(last.slice(8, 10), 10) + ' 日的第 ' + rec + ' 篇。中间有 ' + (span - days) +
             ' 天没写，但从来没有停下来整理——因为记录只有被归档，才算真的留下来。'
    };
  }

  whole().then(function(items){
    var s = items ? compute(items) : null;
    if (!s) return;
    /* 3. 本地存档数量（部署时生成，不随文章变） */
    return fetch('/themes/theme-doupi/assets/data/stats.json', { headers: { 'Accept': 'application/json' } })
      .then(function(r){ return r.ok ? r.json() : null; })
      .catch(function(){ return null; })
      .then(function(st){
        s.images = st && st.images || 3169;
        s.pdfs = st && st.pdfs || s.posts;
        s.t = Date.now();
        try { sessionStorage.setItem(CACHE, JSON.stringify(s)); } catch (e) {}
        apply(s);
      });
  }).catch(function(){ /* 拉失败就保持模板里的静态数字 */ });
})();
