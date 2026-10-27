(function(){
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var docEl = document.documentElement;

  /* 主题 */
  var saved = localStorage.getItem('doupi-theme');
  if (saved) docEl.setAttribute('data-theme', saved);
  var themeBtn = document.getElementById('themeBtn');
  if (themeBtn) themeBtn.addEventListener('click', function(){
    var next = docEl.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    docEl.setAttribute('data-theme', next);
    localStorage.setItem('doupi-theme', next);
  });

  /* 入场：元素进入视口时加 .in */
  var targets = document.querySelectorAll('[data-in]');
  if (reduce || !('IntersectionObserver' in window)) {
    targets.forEach(function(el){ el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(e){ if (e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.12 });
    targets.forEach(function(el){ io.observe(el); });
  }

  /* 开场幕：数字 0→492 快速计数，1.75s 后幕布升起；任何输入跳过 */
  (function(){
    var intro = document.getElementById('intro');
    if (!intro) { docEl.classList.add('revealed'); return; }
    var hold = /intro[-=]hold/.test(location.search + location.hash);
    if (reduce) { intro.remove(); docEl.classList.add('revealed'); return; }
    var seenIntro = false;
    try { seenIntro = sessionStorage.getItem('doupi-intro') === '1'; } catch (e) {}
    if (seenIntro) { intro.remove(); docEl.classList.add('revealed'); return; }
    if (hold) { var hc = document.getElementById('introCount'); if (hc) hc.textContent = '492'; return; }
    docEl.classList.add('intro-lock');

    var numEl = document.getElementById('introCount');
    if (numEl) {
      var t0 = performance.now(), dur = 900;
      requestAnimationFrame(function tick(now){
        var p = Math.min(1, (now - t0) / dur);
        var eased = 1 - Math.pow(1 - p, 3);
        numEl.textContent = Math.round(492 * eased).toLocaleString('en-US');
        if (p < 1) requestAnimationFrame(tick);
      });
    }

    var done = false;
    function finish(){
      if (done) return;
      done = true;
      try { sessionStorage.setItem('doupi-intro', '1'); } catch (e) {}
      intro.classList.add('done');
      docEl.classList.remove('intro-lock');
      docEl.classList.add('revealed');
      setTimeout(function(){ if (intro.parentNode) intro.parentNode.removeChild(intro); }, 1150);
    }
    var timer = setTimeout(finish, 1750);
    ['wheel','touchstart','keydown','click'].forEach(function(ev){
      window.addEventListener(ev, function(){ clearTimeout(timer); finish(); }, { passive: true, once: true });
    });
  })();

  /* 区块巨号 */
  document.querySelectorAll('[data-ghost]').forEach(function(sec){
    var g = document.createElement('span');
    g.className = 'ghost';
    g.setAttribute('aria-hidden', 'true');
    g.textContent = sec.getAttribute('data-ghost');
    sec.appendChild(g);
  });

  /* 首屏光斑跟随鼠标 */
  (function(){
    var spot = document.getElementById('spot');
    var hero = document.querySelector('.hero');
    if (!spot || !hero || !matchMedia('(pointer:fine)').matches || reduce) return;
    hero.addEventListener('mousemove', function(e){
      var r = hero.getBoundingClientRect();
      spot.style.transform = 'translate(' + (e.clientX - r.left) + 'px,' + (e.clientY - r.top) + 'px) translate(-50%,-50%)';
    }, { passive: true });
  })();

  /* 首屏随滚动轻微缩小淡出（苹果式退场） */
  var heroEl = document.querySelector('.hero');

  /* 数字滚动 */
  var counters = document.querySelectorAll('[data-count]');
  function runCounter(el){
    var to = parseInt(el.getAttribute('data-count'), 10) || 0;
    if (reduce) { el.textContent = to.toLocaleString('en-US'); return; }
    var start = performance.now(), dur = 1200;
    function tick(now){
      var p = Math.min(1, (now - start) / dur);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(to * eased).toLocaleString('en-US');
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  if ('IntersectionObserver' in window) {
    var cio = new IntersectionObserver(function(entries){
      entries.forEach(function(e){ if (e.isIntersecting){ runCounter(e.target); cio.unobserve(e.target); } });
    }, { threshold: 0.5 });
    counters.forEach(function(el){ cio.observe(el); });
  } else {
    counters.forEach(runCounter);
  }

  /* 给 live.js 用的入口 */
  window.doupiApplyNumbers = function(nums){
    window.DOUPI_NUM = window.DOUPI_NUM || {};
    Object.keys(nums).forEach(function(k){ window.DOUPI_NUM[k] = nums[k]; });
    document.querySelectorAll('[data-live-count]').forEach(function(el){
      var v = nums[el.getAttribute('data-live-count')];
      if (typeof v === 'number'){ el.setAttribute('data-count', v); el.textContent = v.toLocaleString('en-US'); }
    });
    if (pinCount && nums.posts) pinCount.textContent = nums.posts.toLocaleString('en-US');
    if (pinDays && nums.days) pinDays.textContent = nums.days.toLocaleString('en-US');
  };
  window.doupiSetStatement = function(text){
    var el = document.getElementById('words');
    if (!el) return;
    el.textContent = text;
    wordSpans.length = 0;
    el.textContent = '';
    Array.from(text).forEach(function(ch){
      var s = document.createElement('span');
      s.textContent = ch;
      el.appendChild(s);
      if (ch.trim()) wordSpans.push(s);
    });
    if (reduce) wordSpans.forEach(function(s){ s.classList.add('on'); });
  };

  /* 逐字点亮 */
  var wordsEl = document.getElementById('words');
  var wordSpans = [];
  if (wordsEl) {
    var text = wordsEl.textContent;
    wordsEl.textContent = '';
    Array.from(text).forEach(function(ch){
      var s = document.createElement('span');
      s.textContent = ch;
      wordsEl.appendChild(s);
      if (ch.trim()) wordSpans.push(s);
    });
    if (reduce) wordSpans.forEach(function(s){ s.classList.add('on'); });
  }

  /* 热力图（移动端只画最近 28 周，避免横向溢出） */
  var days = window.DAYS || [];
  var cells = [];
  var weeks = 0, colFrom = 0, startDate = null;
  (function buildHeatmap(){
    if (!days.length) return;
    var set = {};
    days.forEach(function(d){ set[d] = (set[d] || 0) + 1; });
    var parse = function(s){ var p = s.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); };
    var first = parse(days[0]), last = parse(days[days.length - 1]);
    startDate = new Date(first);
    startDate.setDate(startDate.getDate() - ((startDate.getDay() + 6) % 7));
    weeks = Math.ceil(((last - startDate) / 86400000 + 1) / 7);
    colFrom = window.innerWidth <= 620 ? Math.max(0, weeks - 28) : 0;
    var shown = weeks - colFrom;

    var grid = document.getElementById('hmGrid');
    var months = document.getElementById('hmMonths');
    grid.style.gridTemplateColumns = 'repeat(' + shown + ',var(--cell,12px))';
    grid.style.gridTemplateRows = 'repeat(7,var(--cell,12px))';
    months.style.gridTemplateColumns = 'repeat(' + shown + ',var(--cell,12px))';

    var names = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'];
    var prev = -1;
    for (var w = colFrom; w < weeks; w++){
      for (var r = 0; r < 7; r++){
        var d = new Date(startDate);
        d.setDate(startDate.getDate() + w * 7 + r);
        var key = d.getFullYear() + '-' + ('0' + (d.getMonth()+1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
        var n = set[key] || 0;
        var cell = document.createElement('i');
        cell.title = key + (n ? ' · ' + n + ' 篇' : ' · 留白');
        cell.style.gridColumn = (w - colFrom) + 1;
        cell.style.gridRow = r + 1;
        grid.appendChild(cell);
        cells.push({ el: cell, col: w - colFrom, n: n });
      }
      var mon = new Date(startDate);
      mon.setDate(startDate.getDate() + w * 7);
      if (mon.getMonth() !== prev){
        prev = mon.getMonth();
        var sp = document.createElement('span');
        sp.textContent = mon.getMonth() === 0 ? (mon.getFullYear() + ' 年') : names[mon.getMonth()];
        sp.style.gridColumn = (w - colFrom) + 1;
        months.appendChild(sp);
      }
    }
    if (reduce) cells.forEach(function(c){ if (c.n) c.el.classList.add('on'); });
  })();

  /* 滚动驱动：进度条、视差、固定区数字与热力图 */
  var pin = document.querySelector('.pin');
  var pinNum = document.getElementById('pinNum');
  var pinCount = document.getElementById('pinCount');
  var pinDays = document.getElementById('pinDays');
  var progressEl = document.getElementById('progress');
  var navEl = document.getElementById('nav');
  var parallax = Array.prototype.slice.call(document.querySelectorAll('[data-par]'));
  var ticking = false;

  function update(){
    ticking = false;
    var y = window.scrollY || window.pageYOffset;
    var vh = window.innerHeight;
    var max = Math.max(1, document.documentElement.scrollHeight - vh);
    progressEl.style.width = (Math.min(1, y / max) * 100).toFixed(2) + '%';
    if (y > 40) navEl.classList.add('solid'); else navEl.classList.remove('solid');

    if (heroEl && !reduce) {
      var hp = Math.min(1, y / Math.max(1, heroEl.offsetHeight));
      heroEl.style.transform = 'scale(' + (1 - hp * 0.05).toFixed(4) + ')';
      heroEl.style.opacity = (1 - hp * 0.85).toFixed(3);
    }

    if (!reduce) {
      parallax.forEach(function(el){
        var k = parseFloat(el.getAttribute('data-par')) || 0;
        var rect = el.getBoundingClientRect();
        var center = rect.top + rect.height / 2 - vh / 2;
        el.style.transform = 'translate3d(0,' + (-center * k).toFixed(2) + 'px,0)';
      });
    }

    /* 固定区进度 */
    if (pin && pinNum){
      var rect = pin.getBoundingClientRect();
      var total = pin.offsetHeight - vh;
      var p = Math.min(1, Math.max(0, (-rect.top) / Math.max(1, total)));
      var eased = p;
      var pinTo = window.DOUPI_NUM && window.DOUPI_NUM.posts || 492;
      var pinDayTo = window.DOUPI_NUM && window.DOUPI_NUM.days || 476;
      if (pinCount) pinCount.textContent = Math.round(pinTo * Math.min(1, eased * 1.12)).toLocaleString('en-US');
      if (pinDays) pinDays.textContent = Math.round(pinDayTo * Math.min(1, eased * 1.12));
      if (!reduce){
        pinNum.style.transform = 'scale(' + (0.92 + eased * 0.12).toFixed(3) + ')';
        pinNum.style.opacity = (0.35 + eased * 0.65).toFixed(3);
      }
      var revealCols = Math.ceil(eased * (weeks - colFrom));
      for (var i = 0; i < cells.length; i++){
        var c = cells[i];
        if (!c.n) continue;
        if (c.col <= revealCols){ if (!c.el.classList.contains('on')) c.el.classList.add('on'); }
        else if (c.el.classList.contains('on')) c.el.classList.remove('on');
      }
    }

    /* 逐字点亮 */
    if (wordsEl && wordSpans.length){
      var wrect = wordsEl.getBoundingClientRect();
      var wp = 1 - (wrect.top - vh * 0.12) / (vh * 0.62);
      wp = Math.min(1, Math.max(0, wp));
      var upto = Math.round(wordSpans.length * wp);
      for (var j = 0; j < wordSpans.length; j++){
        var on = j < upto;
        if (on !== wordSpans[j].classList.contains('on')) wordSpans[j].classList.toggle('on', on);
      }
    }
  }

  function onScroll(){ if (!ticking){ ticking = true; requestAnimationFrame(update); } }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);
  update();
})();
