/* 天气与时间：心知天气（Seniverse）免费接口，key 沿用 Serenity 主题里配的那个。
   20 次/分钟限流，所以结果缓存 10 分钟；失败时保留模板里的兜底文案。 */

(function () {
  var KEY = 'SAIrqQERUFoY2a3Ad';
  var CITY = 'hangzhou';          // 杭州；想跟随访问者 IP 可改成 'ip'
  var LABEL = '杭州 · 拱墅';
  var TTL = 10 * 60 * 1000;
  var STORE = 'doupi-weather-v1';

  function fmtTime(d) {
    var p = function (n) { return (n < 10 ? '0' : '') + n; };
    return p(d.getHours()) + ':' + p(d.getMinutes());
  }

  function paint(city, text, temp, when) {
    var short = city.split(' · ')[0];         // kicker 里只写城市，档案卡里写「城市 · 区」
    document.querySelectorAll('[data-city]').forEach(function (el) {
      el.textContent = el.closest('.kicker') ? short : city;
    });
    document.querySelectorAll('[data-weather]').forEach(function (el) {
      el.textContent = text + ' ' + temp + '°C';
    });
    document.querySelectorAll('[data-clock]').forEach(function (el) { el.textContent = when; });
  }

  function fallback() {
    paint(LABEL, '—', '--', fmtTime(new Date()));
  }

  function cached() {
    try {
      var raw = sessionStorage.getItem(STORE);
      if (!raw) return null;
      var o = JSON.parse(raw);
      if (Date.now() - o.t > TTL) return null;
      return o;
    } catch (e) { return null; }
  }

  function load() {
    var hit = cached();
    if (hit) { paint(hit.city, hit.text, hit.temp, hit.when); return; }

    var url = 'https://api.seniverse.com/v3/weather/now.json?key=' + KEY +
              '&location=' + CITY + '&language=zh-Hans&unit=c';
    fetch(url, { mode: 'cors' })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (d) {
        var res = (d && d.results && d.results[0]) || null;
        if (!res || !res.now) throw new Error('empty');
        var city = LABEL;
        var when = fmtTime(new Date());
        paint(city, res.now.text, res.now.temperature, when);
        try {
          sessionStorage.setItem(STORE, JSON.stringify({
            t: Date.now(), city: city, text: res.now.text, temp: res.now.temperature, when: when
          }));
        } catch (e) {}
      })
      .catch(function () { fallback(); });
  }

  function tick() {
    document.querySelectorAll('[data-clock]').forEach(function (el) {
      el.textContent = fmtTime(new Date());
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }
  tick();
  setInterval(tick, 30 * 1000);
})();
