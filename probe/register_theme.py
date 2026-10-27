"""给 theme-doupi 建 Theme 资源行（否则 Halo 不认这个主题，/themes/theme-doupi/assets/* 会 404）。

Halo 的 Theme 资源存在 extensions 表里；直接用 ConfigMap 切换主题时不会自动生成，
所以这里照 theme.yaml 的内容补一行，status.phase 设成 READY。

用法：
  python -u probe/register_theme.py dry
  python -u probe/register_theme.py apply
"""
import base64
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from deploy_theme import ssh_client  # noqa: E402

KEY = "/registry/theme.halo.run/themes/theme-doupi"
MY = "docker exec 1Panel-mysql-H38k mysql -uroot -pmysql_F5s2Fm -r -N halo_c7j4re -e "


def run(c, cmd):
    _i, o, e = c.exec_command(cmd, timeout=120)
    return o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")


def fetch(c, key):
    return run(c, MY + f"\"select CAST(DATA AS CHAR) from extensions where name='{key}';\" 2>/dev/null").strip()


def build():
    return {
        "apiVersion": "theme.halo.run/v1alpha1",
        "kind": "Theme",
        "metadata": {"name": "theme-doupi", "creationTimestamp": "2026-10-27T09:49:00.000000000Z"},
        "spec": {
            "displayName": "Doupi",
            "author": {"name": "豆皮", "website": "https://doupi123.top"},
            "description": "个人档案式主题：项目 / 能力 / 课程 / 资料柜 / 记录 / 视频，亮色为主，滚动动效参考 Apple 官网。",
            "logo": "/themes/theme-doupi/assets/img/avatar.webp",
            "homepage": "https://doupi123.top",
            "repo": "https://doupi123.top",
            "version": "1.0.0",
            "requires": ">=2.0.0",
            "license": [{"name": "MIT"}],
            "customTemplates": {
                "page": [
                    {"name": "default", "description": "默认页面", "file": "page.html"},
                    {"name": "daily", "description": "记录时间轴", "file": "page-daily.html"},
                    {"name": "courses", "description": "课程清单", "file": "page-courses.html"},
                ],
                "post": [{"name": "default", "description": "默认文章", "file": "post.html"}],
                "category": [{"name": "default", "description": "默认分类", "file": "category.html"}],
                "tag": [{"name": "default", "description": "默认标签", "file": "tag.html"}],
            },
        },
        "status": {
            "phase": "READY",
            "conditions": [
                {"type": "READY", "status": "TRUE",
                 "lastTransitionTime": "2026-10-27T09:49:00.000000000Z",
                 "message": "Theme loaded successfully.", "reason": "LoadedSuccessfully"}
            ],
        },
    }


def main(mode):
    c = ssh_client()
    if fetch(c, KEY) and mode != "dry":
        print("已存在，跳过")
        c.close()
        return
    raw = json.dumps(build(), ensure_ascii=False, separators=(",", ":"))
    if mode == "dry":
        print(raw[:400], "...", len(raw), "B")
        c.close()
        return
    b64 = base64.b64encode(raw.encode("utf-8")).decode()
    q = f"INSERT INTO extensions (name, DATA, version) VALUES ('{KEY}', FROM_BASE64('{b64}'), 1);"
    print(run(c, MY + '"' + q + '" 2>&1'))
    print("写入后：", fetch(c, KEY)[:160])
    c.close()


if __name__ == "__main__":
    main((sys.argv[1:] or ["dry"])[0])
