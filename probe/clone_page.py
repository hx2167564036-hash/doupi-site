"""克隆一个 SinglePage 行，做出 /courses 页面（Halo 的 PAT 只有 post 权限，改不了页面）。

做法：复制 slug=daily 的那行 JSON，改 name / slug / title / permalink，
沿用同一份内容快照（模板会忽略正文），写回 extensions 表。之后需要重启 Halo 才会被加载。

用法：
  python -u probe/clone_page.py dry     # 只打印将要写入的 JSON
  python -u probe/clone_page.py apply   # 真正写入
"""
import base64
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from deploy_theme import ssh_client  # noqa: E402

ROOT = pathlib.Path(r"D:\kendle\Documents\doupi123-top")
KEY_SRC = "/registry/content.halo.run/singlepages/page-adg6crmr"   # slug=daily
NEW_NAME = "page-courses0001"
NEW_KEY = f"/registry/content.halo.run/singlepages/{NEW_NAME}"
MY = "docker exec 1Panel-mysql-H38k mysql -uroot -pmysql_F5s2Fm -r -N halo_c7j4re -e "


def run(c, cmd):
    _i, o, e = c.exec_command(cmd, timeout=120)
    return o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")


def fetch(c, key):
    return run(c, MY + f"\"select CAST(DATA AS CHAR) from extensions where name='{key}';\" 2>/dev/null").strip()


def main(mode):
    c = ssh_client()
    existing = fetch(c, NEW_KEY)
    if existing:
        print("已存在，跳过：", existing[:120])
        c.close()
        return

    raw = fetch(c, KEY_SRC)
    if not raw:
        print("没读到模板页面")
        c.close()
        return
    obj = json.loads(raw)
    obj["metadata"]["name"] = NEW_NAME
    obj["metadata"].pop("uid", None)
    obj["spec"]["slug"] = "courses"
    obj["spec"]["title"] = "课程"
    obj["spec"]["template"] = ""
    obj["status"]["permalink"] = "/courses"
    obj["status"].pop("excerpt", None)
    obj["status"]["phase"] = "PUBLISHED"
    new_raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))

    if mode == "dry":
        print(new_raw[:600])
        print("...", len(new_raw), "B")
        c.close()
        return

    (ROOT / "notes" / "_new-courses-page.json").write_text(new_raw, encoding="utf-8")
    b64 = base64.b64encode(new_raw.encode("utf-8")).decode()
    q = (f"INSERT INTO extensions (name, DATA, version) VALUES ('{NEW_KEY}', FROM_BASE64('{b64}'), 1);")
    print(run(c, MY + '"' + q + '" 2>&1'))
    print("插入后：", fetch(c, NEW_KEY)[:160])
    c.close()


if __name__ == "__main__":
    main((sys.argv[1:] or ["dry"])[0])
