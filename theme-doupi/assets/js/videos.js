/* 视频页：渲染卡片；点封面才加载 B 站 iframe（不点就不连第三方） */
(function(){
  var list = window.VIDEOS || [];
  var drafts = window.DRAFTS || [];
  var grid = document.getElementById('vgrid');
  var box = document.getElementById('drafts');
  if(!grid) return;

  var coverStyle = [
    'linear-gradient(140deg,#2b2f3a 0%,#151820 55%,#0d0f14 100%)',
    'linear-gradient(140deg,#3a3128 0%,#221c16 60%,#120e0b 100%)',
    'linear-gradient(140deg,#26333a 0%,#141d22 60%,#0b1013 100%)'
  ];

  grid.innerHTML = list.map(function(v, i){
    return '<article class="vcard" data-bvid="' + v.bvid + '">' +
      '<div class="cover" style="background:' + coverStyle[i % 3] + '" role="button" tabindex="0" aria-label="播放 ' + v.title + '">' +
        '<span class="disc"></span>' +
        '<span class="dur">' + v.dur + '</span>' +
      '</div>' +
      '<div class="body">' +
        '<h3>' + v.title + '</h3>' +
        '<p>' + v.desc + '</p>' +
        '<div class="meta"><span class="tag">BILIBILI</span><span>' + v.plays + ' 播放</span><span>' + v.date + '</span></div>' +
        '<a class="go" href="https://www.bilibili.com/video/' + v.bvid + '" target="_blank" rel="noopener">在 B 站看 ↗</a>' +
      '</div></article>';
  }).join('');

  grid.addEventListener('click', function(e){
    var cover = e.target.closest('.cover');
    if(!cover) return;
    var card = cover.parentNode;
    if(cover.dataset.loaded) return;
    var bvid = card.getAttribute('data-bvid');
    var f = document.createElement('iframe');
    f.src = 'https://player.bilibili.com/player.html?bvid=' + bvid + '&autoplay=1&high_quality=1&danmaku=1';
    f.setAttribute('allowfullscreen', 'true');
    f.setAttribute('allow', 'autoplay; fullscreen; encrypted-media');
    f.setAttribute('referrerpolicy', 'no-referrer-when-downgrade');
    f.setAttribute('scrolling', 'no');
    f.setAttribute('frameborder', '0');
    cover.dataset.loaded = '1';
    cover.appendChild(f);
    cover.classList.add('playing');
    cover.querySelector('.disc').style.display = 'none';
    var du = cover.querySelector('.dur'); if (du) du.style.display = 'none';
  });
  grid.addEventListener('keydown', function(e){
    if(e.key === 'Enter' || e.key === ' '){
      var cover = e.target.closest('.cover');
      if(cover){ e.preventDefault(); cover.click(); }
    }
  });

  if(box){
    box.innerHTML = drafts.map(function(d){
      return '<li><span class="d">' + d.d + '</span><span class="n">' + d.n + '</span><span class="s">' + d.s + '</span></li>';
    }).join('');
  }
})();
