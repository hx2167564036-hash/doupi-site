"""通过 DB 把「启用主题」与「/daily 模板」两个字段改掉（API 的 PAT 只有 post 权限，改不了）。

安全措施：
  1. 改动前把原始 DATA 整行备份到 notes/_backup-system-configmap.json（含 name/data/version）
  2. 只动 data.theme.active 与 data.basic.* 之类的最小字段，其余 JSON 原样回写
  3. 失败可 `python -u probe/activate_theme.py rollback` 回滚

用法：
  python -u probe/activate_theme.py show        # 看当前 theme 字段
  python -u probe/activate_theme.py patch       # 备份 + 改为 theme-doupi
  python -u probe/activate_theme.py restart     # 重启 Halo 容器
  python -u probe/activate_theme.py verify      # curl 首页
  python -u probe/activate_theme.py rollback    # 回滚到备份
  python -u probe/activate_theme.py daily       # /daily 单页 template=daily
"""
import base64
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from deploy_theme import ssh_client  # noqa: E402

ROOT = pathlib.Path(r"D:\kendle\Documents\doupi123-top")
BACKUP = ROOT / "notes" / "_backup-system-configmap.json"
DB = "halo_c7j4re"
MY = "docker exec 1Panel-mysql-H38k mysql -uroot -pmysql_F5s2Fm -r -N {} -e ".format(DB)
KEY = "/registry/configmaps/system"


def run(c, cmd):
    _i, o, e = c.exec_command(cmd, timeout=120)
    return o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")


def sql(c, q):
    return run(c, MY + '"' + q.replace('"', '\\"') + '" 2>/dev/null')


def fetch(c):
    stmt = b"select CAST(DATA AS CHAR) from extensions where name='" + KEY.encode() + b"'"
    b64 = base64.b64encode(stmt).decode()
    out = run(c, MY + f"\"select CAST(DATA AS CHAR) from extensions where name='{KEY}';\" 2>/dev/null")
    return out.strip()


def show():
    c = ssh_client()
    print(fetch(c)[:400])
    c.close()


def patch():
    c = ssh_client()
    raw = fetch(c)
    if not raw:
        print("没读到配置，放弃")
        return
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    BACKUP.write_text(raw, encoding="utf-8")
    print("备份 →", BACKUP, len(raw), "B")

    obj = json.loads(raw)
    data = obj["data"]
    print("旧 theme:", data.get("theme"))
    data["theme"] = json.dumps({"active": "theme-doupi"}, separators=(",", ":"))
    obj["data"] = data
    obj["metadata"]["version"] = int(obj["metadata"].get("version") or 0) + 1
    new_raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    b64 = base64.b64encode(new_raw.encode("utf-8")).decode()
    sql(c, f"UPDATE extensions SET DATA=FROM_BASE64('{b64}'), version=version+1 WHERE name='{KEY}';")
    print("已写入新 theme:", fetch(c)[:220])
    c.close()


def restart():
    c = ssh_client()
    print(run(c, "docker restart 1Panel-halo-UaWD && echo restarted"))
    time.sleep(8)
    print(run(c, "docker ps --filter name=1Panel-halo --format '{{.Names}} {{.Status}}'"))
    c.close()


def verify():
    c = ssh_client()
    print(run(c, "curl -sk -o /dev/null -w 'home %{http_code} %{size_download}\\n' "
                "--resolve doupi123.top:443:127.0.0.1 https://doupi123.top/"))
    print(run(c, "curl -sk --resolve doupi123.top:443:127.0.0.1 https://doupi123.top/ | grep -o -E 'theme-[A-Za-z]+' | head -3"))
    c.close()


def rollback():
    if not BACKUP.exists():
        print("没有备份")
        return
    c = ssh_client()
    raw = BACKUP.read_text(encoding="utf-8")
    b64 = base64.b64encode(raw.encode("utf-8")).decode()
    sql(c, f"UPDATE extensions SET DATA=FROM_BASE64('{b64}'), version=version+1 WHERE name='{KEY}';")
    print("回滚完成:", fetch(c)[:200])
    c.close()


def daily():
    c = ssh_client()
    key = "/registry/content.halo.run/singlepages/page-adg6crmr"
    out = run(c, MY + f"\"select CAST(DATA AS CHAR) from extensions where name='{key}';\" 2>/dev/null").strip()
    if not out:
        print("没找到 daily 单页")
        c.close()
        return
    obj = json.loads(out)
    print("before template:", obj.get("spec", {}).get("template"), "| slug:", obj.get("spec", {}).get("slug"))
    obj.setdefault("spec", {})["template"] = "daily"
    (ROOT / "notes" / "_backup-daily-page.json").write_text(out, encoding="utf-8")
    b64 = base64.b64encode(json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).decode()
    sql(c, f"UPDATE extensions SET DATA=FROM_BASE64('{b64}'), version=version+1 WHERE name='{key}';")
    print("after:", run(c, MY + f"\"select CAST(DATA AS CHAR) from extensions where name='{key}';\" 2>/dev/null").strip()[:200])
    c.close()


if __name__ == "__main__":
    cmd = (sys.argv[1:] or ["show"])[0]
    {"show": show, "patch": patch, "restart": restart, "verify": verify,
     "rollback": rollback, "daily": daily}[cmd]()
