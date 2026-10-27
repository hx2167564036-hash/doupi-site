"""把本地存档 PDF（Day491 / Day492）发布成 Halo 文章。

流程：
  1. pypdf 抽每页文字（NFKC 归一）+ 每页图片
  2. paramiko SFTP 把图片放进 Halo 的 attachments/upload（文件名 day491-01.jpg 这类），
     站点用 /upload/<name> 直接静态服务（已实测 200）
  3. 用 Halo console API 建草稿（POST /posts，body {post, content}），再 PUT /posts/{name}/publish
  4. 打印文章地址

用法：
    python -u probe/publish_day.py               # 真发
    python -u probe/publish_day.py --dry-run     # 只打印，不写服务器
"""
import html
import json
import pathlib
import re
import sys
import unicodedata

import pypdf

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import halo

PDF_DIR = pathlib.Path(r"D:\kendle\Documents\豆皮笔记")
REMOTE_ATT = "/opt/1panel/apps/halo/halo/data/attachments/upload"
CATEGORY = "category-iyrrqfnr"  # 每日记录
PERM_PATTERN = "/archives/{slug}"

# 段落起点标记（PDF 里段落之间没有空行，只能靠首句切）
JOBS = [
    {
        "pdf": "2026-10-2 Day491.pdf",
        "title": "2026-10-02 Day491",
        "slug": "2026-10-02-day491",
        "publish_time": "2026-10-02T02:00:00Z",
        "prefix": "day491",
        "paras": ["震惊", "应该提及的是", "转眼间就到了", "还有一个想提及的事情"],
    },
    {
        "pdf": "2026-10-8 Day492.pdf",
        "title": "2026-10-08 Day492",
        "slug": "2026-10-08-day492",
        "publish_time": "2026-10-08T02:00:00Z",
        "prefix": "day492",
        "paras": ["国庆假期结束", "上午上完课后去健身", "最近一直在 struggle"],
    },
]

PWD_FILE = r"C:\Users\kendle\.qoder-cn\projects\C--Users-kendle-Documents-Qoder-2026-09-21-5e6cb6a5\memory\reference-wenlv-deploy.md"


_KANGXI = re.compile(r"[\u2F00-\u2FDF\u2E80-\u2EFF\uF900-\uFAFF]")


def norm(text):
    # 只把康熙部首/CJK 兼容区归一，别动全角标点（NFKC 会把 ，。： 变成半角）
    t = _KANGXI.sub(lambda m: unicodedata.normalize("NFKC", m.group(0)), text or "")
    t = t.replace("\u3000", " ")
    # PDF 里一行一个断行：中文直接拼回，行首行尾空白丢掉
    t = re.sub(r"[ \t]*\n[ \t]*", "", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def split_paras(text, markers):
    idxs = []
    for m in markers:
        i = text.find(m)
        if i < 0:
            raise SystemExit("段落标记没找到: " + m)
        idxs.append(i)
    idxs.sort()
    out = []
    for k, i in enumerate(idxs):
        j = idxs[k + 1] if k + 1 < len(idxs) else len(text)
        out.append(text[i:j].strip())
    return out


def pdf_parts(pdf_path):
    r = pypdf.PdfReader(str(pdf_path))
    pages = []
    for i, pg in enumerate(r.pages, 1):
        txt = norm(pg.extract_text() or "")
        imgs = [(im.name, im.data) for im in pg.images]
        pages.append({"no": i, "text": txt, "imgs": imgs})
    return pages


def ssh_client():
    import paramiko

    pwd = pathlib.Path(PWD_FILE).read_text(encoding="utf-8").splitlines()[7].split("`")[1]
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect("120.26.139.203", 22, "root", pwd, timeout=30)
    return c


def existing_slugs(tk):
    slugs = set()
    for page in range(0, 8):
        st, d = halo.call("GET", f"{halo.API}/posts?page={page}&size=100", tok=tk)
        items = (d or {}).get("items") or []
        for it in items:
            slugs.add((it.get("post", {}).get("spec", {}) or {}).get("slug"))
        if len(items) < 100:
            break
    return slugs


def build_html(paras, imgs):
    parts = []
    for p in paras:
        parts.append(f"<p>{html.escape(p)}</p>")
    if imgs:
        parts.append('<div style="display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));margin-top:24px">')
        for i, (name, url) in enumerate(imgs, 1):
            parts.append(
                f'<figure style="margin:0"><img src="{url}" alt="{html.escape(name)}" '
                f'style="width:100%;height:auto;border-radius:8px;display:block">'
                f'<figcaption style="font-size:12px;opacity:.6;margin-top:6px">图 {i}</figcaption></figure>'
            )
        parts.append("</div>")
    return "\n".join(parts)


def main():
    dry = "--dry-run" in sys.argv
    tk = None if dry else halo.token()

    if not dry:
        have = existing_slugs(tk)
        for j in JOBS:
            if j["slug"] in have:
                raise SystemExit("站点上已有 slug=" + j["slug"] + "，先确认再跑")

    ssh = None if dry else ssh_client()
    sftp = ssh.open_sftp() if ssh else None

    results = []
    for job in JOBS:
        pages = pdf_parts(PDF_DIR / job["pdf"])
        text = norm("\n".join(p["text"] for p in pages if p["text"]))
        paras = split_paras(text, job["paras"])

        uploads = []
        n = 0
        for p in pages:
            for name, data in p["imgs"]:
                n += 1
                remote_name = f"{job['prefix']}-{n:02d}.jpg"
                uploads.append((remote_name, data, f"/upload/{remote_name}"))
        print(f"\n== {job['title']} ==  pages={len(pages)} paras={len(paras)} imgs={len(uploads)}")
        print("   paras lens:", [len(x) for x in paras])
        print("   imgs:", [(u[0], len(u[1])) for u in uploads])

        if sftp:
            for remote_name, data, _ in uploads:
                with sftp.open(f"{REMOTE_ATT}/{remote_name}", "wb") as f:
                    f.write(data)

        body_html = build_html(paras, [(u[0], u[2]) for u in uploads])
        results.append({**job, "paras": paras, "html": body_html, "uploads": uploads, "pages": pages})

    if dry:
        out = pathlib.Path("mockups/_publish_preview")
        out.mkdir(parents=True, exist_ok=True)
        for r in results:
            (out / f"{r['slug']}.html").write_text(r["html"], encoding="utf-8")
        print("\n[dry-run] 预览写到", out)
        if sftp:
            sftp.close()
        return

    for r in results:
        body = {
            "post": {
                "apiVersion": "content.halo.run/v1alpha1",
                "kind": "Post",
                "metadata": {"generateName": "post-", "annotations": {"content.halo.run/permalink-pattern": PERM_PATTERN}},
                "spec": {
                    "title": r["title"],
                    "slug": r["slug"],
                    "template": "",
                    "cover": r["uploads"][0][2] if r["uploads"] else "",
                    "deleted": False,
                    "publish": False,
                    "pinned": False,
                    "priority": 0,
                    "allowComment": True,
                    "visible": "PUBLIC",
                    "tags": [],
                    "categories": [CATEGORY],
                    "htmlMetas": [],
                    "publishTime": r["publish_time"],
                    "excerpt": {"autoGenerate": True, "raw": ""},
                },
            },
            "content": {"raw": r["html"], "content": r["html"], "rawType": "html"},
        }
        st, post = halo.call("POST", f"{halo.API}/posts", body=body, tok=tk)
        print("create", r["slug"], "->", st)
        if st not in (200, 201):
            print("  failed:", str(post)[:300])
            continue
        name = post["metadata"]["name"]
        snap = post["spec"]["headSnapshot"]
        st2, pub = halo.call("PUT", f"{halo.API}/posts/{name}/publish", body={"headSnapshot": snap}, tok=tk)
        print("  publish ->", st2, "name=", name, "url=/archives/" + r["slug"])

    if sftp:
        sftp.close()
    if ssh:
        ssh.close()


if __name__ == "__main__":
    main()
