"""本地分析 notes/site-snapshot/*.html：结构、导航、文章列表、文章页要素。"""
import re
from pathlib import Path

SNAP = Path(__file__).resolve().parent.parent / "notes" / "site-snapshot"


def clean(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def find(pat, html, flags=re.S):
    return re.findall(pat, html, flags)


def head_info(html, label):
    print(f"\n########## {label}")
    t = re.search(r"<title>(.*?)</title>", html, re.S)
    d = re.search(r'name="description" content="(.*?)"', html, re.S)
    print("title      :", clean(t.group(1)) if t else "-")
    print("description:", (d.group(1)[:120] if d else "-"))
    css = find(r'<link[^>]+href="([^"]+\.css[^"]*)"', html)
    js = find(r'<script[^>]+src="([^"]+\.js[^"]*)"', html)
    print("css        :", css[:6])
    print("js         :", js[:8])
    print("html bytes :", len(html))


def nav(html):
    print("\n--- 导航 / 菜单")
    blocks = find(r"<(?:nav|header)[^>]*>(.*?)</(?:nav|header)>", html)
    for b in blocks[:3]:
        for href, text in find(r'<a[^>]+href="([^"]*)"[^>]*>(.*?)</a>', b)[:20]:
            txt = clean(text)
            if txt:
                print(f"  {txt[:24]:<26} -> {href[:60]}")
        print("  ---")


def layout(html):
    print("\n--- 顶层结构（class 家族）")
    for tag, cls in find(r'<(header|nav|main|footer|section|article|aside|div)[^>]*class="([^"]+)"', html):
        if any(k in cls for k in ("container", "layout", "wrapper", "main", "page", "card", "post", "home", "hero", "sidebar", "toc")):
            print(f"  <{tag}> {cls[:100]}")


def posts_list(html):
    print("\n--- 首页文章条目")
    items = find(r'<article[^>]*>(.*?)</article>', html)
    print(f"  article 数: {len(items)}")
    for it in items[:12]:
        h = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", it, re.S)
        a = re.search(r'href="([^"]+)"', it)
        t = re.search(r"<time[^>]*datetime=\"([^\"]+)\"", it)
        print(f"  · {clean(h.group(1))[:40] if h else '-'}  | {t.group(1)[:10] if t else '-'} | {a.group(1)[:50] if a else '-'}")
    heads = [clean(x) for x in find(r"<h[12][^>]*>(.*?)</h[12]>", html)]
    print("  页面里 h1/h2:", [h[:30] for h in heads if h][:15])


def post_page(html):
    print("\n--- 文章页要素")
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    print("  标题:", clean(h1.group(1))[:80] if h1 else "-")
    for k in ("toc", "table-of-contents", "comment", "share", "like", "reaction", "sidebar", "pre", "blockquote", "img"):
        print(f"  {k:<20} 出现 {html.count(k)} 次")
    print("  图片数:", len(find(r'<img[^>]+src="([^"]+)"', html)))
    print("  h2/h3 小节:", [clean(x)[:24] for x in find(r"<h[23][^>]*>(.*?)</h[23]>", html)][:10])
    body = find(r'<div[^>]*class="[^"]*(?:post-content|markdown-body|article-content)[^"]*"[^>]*>(.*?)</div>\s*</div>', html)
    if body:
        txt = clean(body[0])
        print(f"  正文前 300 字: {txt[:300]}")
        print(f"  正文总字数(去标签): {len(txt)}")


def main():
    for name, label in (("home.html", "首页"), ("post.html", "文章页")):
        p = SNAP / name
        if not p.exists():
            print("缺", p)
            continue
        html = p.read_text("utf-8", "replace")
        head_info(html, label)
        if label == "首页":
            nav(html)
            layout(html)
            posts_list(html)
        else:
            post_page(html)


if __name__ == "__main__":
    main()
