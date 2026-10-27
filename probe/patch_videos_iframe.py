"""给 /videos 的 iframe 补 allow 属性、点开后隐藏时长角标。"""
import pathlib

p = pathlib.Path(__file__).resolve().parent.parent / "theme-doupi/assets/js/videos.js"
s = p.read_text(encoding="utf-8")

old = "    f.src = 'https://player.bilibili.com/player.html?bvid=' + v.bvid + '&autoplay=1&high_quality=1&danmaku=1';"
add = old + """
    f.setAttribute('allow', 'autoplay; fullscreen; encrypted-media');
    f.setAttribute('allowfullscreen', 'true');
    f.setAttribute('referrerpolicy', 'no-referrer-when-downgrade');
    var du = c.querySelector('.dur'); if (du) du.style.display = 'none';
    c.classList.add('playing');"""

if add.strip() in s:
    print("already patched")
elif old in s:
    p.write_text(s.replace(old, add, 1), encoding="utf-8")
    print("patched videos.js")
else:
    print("anchor missing")
