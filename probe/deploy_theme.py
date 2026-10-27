"""把 theme-doupi 传上服务器、启用，并把 /daily、/courses 两个单页绑到自定义模板。

步骤（每步都可单独跑）：
  python -u probe/deploy_theme.py upload      # SFTP 上传（跳过 _preview*/_p*.png）
  python -u probe/deploy_theme.py activate    # 启用主题
  python -u probe/deploy_theme.py pages       # 建 /courses、给 /daily 与 /courses 设模板
  python -u probe/deploy_theme.py status      # 看当前主题与单页模板
"""
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import halo  # noqa: E402

ROOT = pathlib.Path(r"D:\kendle\Documents\doupi123-top")
THEME_DIR = ROOT / "theme-doupi"
REMOTE_THEME = "/opt/1panel/apps/halo/halo/data/themes/theme-doupi"
SKIP_SUFFIX = (".png",)
SKIP_PREFIX = ("_preview", "_p")


def pwd():
    p = pathlib.Path(
        r"C:\Users\kendle\.qoder-cn\projects\C--Users-kendle-Documents-Qoder-2026-09-21-5e6cb6a5"
        r"\memory\reference-wenlv-deploy.md"
    )
    return p.read_text(encoding="utf-8").splitlines()[7].split("`")[1]


def ssh_client():
    import paramiko

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect("120.26.139.203", 22, "root", pwd(), timeout=30)
    return c


def files():
    out = []
    for p in sorted(THEME_DIR.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(THEME_DIR)
        if rel.name.startswith(SKIP_PREFIX) or p.suffix in SKIP_SUFFIX:
            continue
        out.append((p, rel.as_posix()))
    return out


def upload():
    c = ssh_client()
    sftp = c.open_sftp()

    def ensure(remote_dir):
        parts = remote_dir.strip("/").split("/")
        cur = ""
        for part in parts:
            cur += "/" + part
            try:
                sftp.stat(cur)
            except IOError:
                sftp.mkdir(cur)

    ensure(REMOTE_THEME)
    total = 0
    for local, rel in files():
        remote = f"{REMOTE_THEME}/{rel}"
        ensure(os.path.dirname(remote))
        sftp.put(str(local), remote)
        total += local.stat().st_size
        print("  ↑", rel, local.stat().st_size, "B")
    sftp.close()
    c.close()
    print(f"上传完成：{len(files())} 个文件，{total/1024:.1f} KB")


def activate():
    tk = halo.token()
    st, d = halo.call("PUT", f"{halo.API}/themes/theme-doupi/activate", tok=tk)
    print("activate:", st, str(d)[:300])


def status():
    tk = halo.token()
    st, d = halo.call("GET", f"{halo.API}/themes", tok=tk)
    if isinstance(d, dict):
        items = d.get("items") or []
        for it in items:
            md = it.get("metadata") or {}
            spec = it.get("spec") or {}
            print("theme:", md.get("name"), "| active:", spec.get("activated"), "|", str(spec.get("displayName")))
    else:
        print("themes:", st, str(d)[:200])

    st, d = halo.call("GET", f"{halo.API}/singlepages?page=0&size=50", tok=tk)
    items = (d or {}).get("items") or []
    print("singlepages:", len(items))
    for it in items:
        sp = it.get("page") if "page" in it else it
        md = sp.get("metadata") or {}
        spec = sp.get("spec") or {}
        print(" ", md.get("name"), "|", spec.get("slug"), "| template:", spec.get("template"), "|", spec.get("title"))


def pages():
    tk = halo.token()
    st, d = halo.call("GET", f"{halo.API}/singlepages?page=0&size=50", tok=tk)
    items = (d or {}).get("items") or []
    by_slug = {}
    for it in items:
        sp = it.get("page") if "page" in it else it
        md = sp.get("metadata") or {}
        spec = sp.get("spec") or {}
        by_slug[spec.get("slug")] = (md.get("name"), sp)

    # /daily → template daily
    if "daily" in by_slug:
        name, sp = by_slug["daily"]
        sp.setdefault("spec", {})["template"] = "daily"
        st, r = halo.call("PUT", f"{halo.API}/singlepages/{name}", sp, tok=tk)
        print("daily template:", st, str(r)[:160])
    else:
        print("!! 找不到 slug=daily 的单页")

    # /courses → 新建（若不存在）
    if "courses" in by_slug:
        name, sp = by_slug["courses"]
        sp.setdefault("spec", {})["template"] = "courses"
        st, r = halo.call("PUT", f"{halo.API}/singlepages/{name}", sp, tok=tk)
        print("courses template:", st, str(r)[:160])
    else:
        body = {
            "page": {
                "apiVersion": "content.halo.run/v1alpha1",
                "kind": "SinglePage",
                "metadata": {"generateName": "page-"},
                "spec": {
                    "title": "课程",
                    "slug": "courses",
                    "template": "courses",
                    "deleted": False,
                    "publish": True,
                    "pinned": False,
                    "priority": 0,
                    "allowComment": False,
                    "visible": "PUBLIC",
                    "excerpt": {"autoGenerate": False, "raw": "5 个学期 57 门课的索引"},
                },
            },
            "content": {"raw": "<p>课程索引由主题的 courses 模板渲染。</p>", "content": "<p>课程索引由主题的 courses 模板渲染。</p>", "rawType": "MARKDOWN"},
        }
        st, r = halo.call("POST", f"{halo.API}/singlepages", body, tok=tk)
        print("create courses:", st, str(r)[:300])


if __name__ == "__main__":
    cmds = {"upload": upload, "activate": activate, "pages": pages, "status": status}
    args = sys.argv[1:] or ["status"]
    for a in args:
        print(f"=== {a} ===")
        cmds[a]()
