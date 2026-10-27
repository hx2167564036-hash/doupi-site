"""在 DB 里停用插件（PAT 无 plugin 作用域，控制台也没法脚本化）。

用法：python -u probe/disable_plugins.py floating-particles plugin-theme-roaming
"""
import base64
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from deploy_theme import ssh_client  # noqa: E402

MY = "docker exec 1Panel-mysql-H38k mysql -uroot -pmysql_F5s2Fm -r -N halo_c7j4re -e "


def run(c, cmd):
    _i, o, e = c.exec_command(cmd, timeout=120)
    return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()


def main(names):
    c = ssh_client()
    for name in names:
        key = f"/registry/plugin.halo.run/plugins/{name}"
        raw = run(c, MY + f"\"select CAST(DATA AS CHAR) from extensions where name='{key}';\" 2>/dev/null")
        if not raw:
            print("未找到", name)
            continue
        j = json.loads(raw)
        j.setdefault("spec", {})["enabled"] = False
        st = j.setdefault("status", {})
        st["phase"] = "DISABLED"
        for cond in st.get("conditions", []):
            if cond.get("type") == "DISABLED":
                cond["status"] = "TRUE"
        out = json.dumps(j, ensure_ascii=False, separators=(",", ":"))
        b64 = base64.b64encode(out.encode("utf-8")).decode()
        run(c, MY + f"\"update extensions set DATA=FROM_BASE64('{b64}'), version=version+1 where name='{key}';\"")
        print("已停用", name)
    c.close()


if __name__ == "__main__":
    main(sys.argv[1:])
