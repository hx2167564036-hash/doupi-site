"""只看 theme-Serenity-configmap，把天气/定位相关字段挑出来。"""
import json
import re
import sys

sys.path.insert(0, "probe")
from deploy_theme import ssh_client  # noqa: E402

MYSQL = "docker exec 1Panel-mysql-H38k mysql -uroot -pmysql_F5s2Fm halo_c7j4re -r -N -e "

c = ssh_client()


def run(cmd, timeout=180):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    return o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")


name = "/registry/configmaps/theme-Serenity-configmap"
raw = run(MYSQL + f"\"select convert(DATA using utf8mb4) from extensions where name='{name}'\"")
print("len", len(raw))

# Halo ConfigMap: {"data":{"basic":"{...}","themeSerenity":"{...}"}, ...}
try:
    outer = json.loads(raw)
except json.JSONDecodeError:
    outer, _ = json.JSONDecoder().raw_decode(raw)
for k, v in outer.get("data", {}).items():
    print(f"\n=== data['{k}']  ({len(str(v))} chars)")
    try:
        inner = json.loads(v)
    except Exception:
        print("  非 JSON，跳过")
        continue
    flat = {}

    def walk(node, path=""):
        if isinstance(node, dict):
            for kk, vv in node.items():
                walk(vv, f"{path}.{kk}" if path else kk)
        elif isinstance(node, list):
            for i, vv in enumerate(node):
                walk(vv, f"{path}[{i}]")
        else:
            flat[path] = node

    walk(inner)
    pat = re.compile(r"weather|qweather|seniverse|xinzhi|amap|gaode|heart|city|location|lat|lon|addr|area|天气|城市|地址", re.I)
    for key, val in flat.items():
        if pat.search(key):
            s = str(val)
            print(f"  {key} = {s[:160]}")

c.close()
