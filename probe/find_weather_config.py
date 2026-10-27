"""在 Halo 的 configmaps 里找天气/定位相关的配置（Serenity 主题设置等）。"""
import json
import sys

sys.path.insert(0, "probe")
from deploy_theme import ssh_client  # noqa: E402

MYSQL = (
    "docker exec 1Panel-mysql-H38k mysql -uroot -pmysql_F5s2Fm halo_c7j4re -r -N -e "
)

c = ssh_client()


def run(cmd, timeout=120):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode("utf-8", "replace")
    err = e.read().decode("utf-8", "replace")
    return out + err


names = run(MYSQL + "\"select name from extensions where name like '/registry/configmaps%'\"")
print("== configmaps ==")
print(names.strip())

KEYS = ("weather", "qweather", "xinzhi", "seniverse", "amap", "gaode", "city", "location",
        "heart", "heartbeat", "heweather", "经纬", "城市", "天气")

for line in names.split():
    if not line.startswith("/registry/configmaps/"):
        continue
    name = line.strip()
    raw = run(MYSQL + f"\"select convert(DATA using utf8mb4) from extensions where name='{name}'\"")
    low = raw.lower()
    hits = [k for k in KEYS if k.lower() in low]
    print(f"\n== {name}  len={len(raw)}  hits={hits}")
    if hits:
        # 只打印命中的上下文，避免把整个配置灌进上下文
        for k in hits[:6]:
            idx = low.find(k.lower())
            print(f"   ...{raw[max(0, idx - 90):idx + 130].replace(chr(10), ' ')}...")

c.close()
