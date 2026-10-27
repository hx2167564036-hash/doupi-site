"""把 theme-doupi 的静态资源交给 openresty 直接供（Halo 的 /themes/{name}/assets/* 对自制主题 404）。

做法：
  1. 把 theme-doupi/assets 上传到宿主机 /opt/1panel/www/sites/doupi123.top/theme/assets
     （openresty 容器把该目录挂成 /www/sites/doupi123.top，所以容器里是 /www/sites/doupi123.top/theme/assets）
  2. 在 vhost /opt/1panel/www/conf.d/doupi123.top.conf 的 `location / {` 之前插一段 alias
  3. nginx -t && nginx -s reload
  4. 逐条 curl 验证

用法：python -u probe/serve_assets.py upload|conf|reload|verify|all
"""
import pathlib
import sys

import paramiko

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from deploy_theme import ssh_client  # noqa: E402

THEME = pathlib.Path(__file__).resolve().parent.parent / "theme-doupi"
REMOTE_ROOT = "/opt/1panel/www/sites/doupi123.top/theme"
VHOST = "/opt/1panel/www/conf.d/doupi123.top.conf"
MARK = "# --- theme-doupi assets (managed by serve_assets.py) ---"
BLOCK = f"""{MARK}
    location ^~ /themes/theme-doupi/assets/ {{
        alias /www/sites/doupi123.top/theme/assets/;
        access_log off;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }}
"""


def run(c, cmd):
    _i, o, e = c.exec_command(cmd, timeout=180)
    return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()


def upload(c):
    run(c, f"mkdir -p {REMOTE_ROOT}")
    sftp = c.open_sftp()

    def walk(local, remote):
        run(c, f"mkdir -p {remote}")
        for p in sorted(local.iterdir()):
            if p.is_dir():
                walk(p, f"{remote}/{p.name}")
            elif p.suffix.lower() in {".css", ".js", ".json", ".webp", ".woff2", ".svg", ".png", ".ico", ".webmanifest"}:
                sftp.put(str(p), f"{remote}/{p.name}")

    walk(THEME / "assets", f"{REMOTE_ROOT}/assets")
    sftp.close()
    print(run(c, f"find {REMOTE_ROOT}/assets -type f | wc -l"), "个文件已上传")


def conf(c):
    body = run(c, f"cat {VHOST}")
    if MARK in body:
        print("配置已存在，跳过")
        return
    assert "    location / {" in body, "找不到 location / {"
    new = body.replace("    location / {", BLOCK + "    location / {", 1)
    # 备份
    run(c, f"cp {VHOST} {VHOST}.bak.doupi-theme")
    sftp = c.open_sftp()
    with sftp.open(VHOST, "w") as f:
        f.write(new)
    sftp.close()
    print("已插入 alias（备份 .bak.doupi-theme）")


def reload(c):
    print(run(c, "docker exec 1Panel-openresty-qKv1 nginx -t 2>&1"))
    print(run(c, "docker exec 1Panel-openresty-qKv1 nginx -s reload 2>&1") or "reloaded")


def verify(c):
    for p in ["/themes/theme-doupi/assets/css/base.css",
              "/themes/theme-doupi/assets/css/home.css",
              "/themes/theme-doupi/assets/js/home.js",
              "/themes/theme-doupi/assets/data/heatmap.js",
              "/themes/theme-doupi/assets/img/avatar.webp",
              "/"]:
        print(run(c, f"curl -sk -o /dev/null -w '{p} %{{http_code}} %{{size_download}} %{{content_type}}\\n' "
                     f"--resolve doupi123.top:443:127.0.0.1 https://doupi123.top{p}"))


def main(step):
    c = ssh_client()
    if step in ("upload", "all"):
        upload(c)
    if step in ("conf", "all"):
        conf(c)
    if step in ("reload", "all"):
        reload(c)
    if step in ("verify", "all"):
        verify(c)
    c.close()


if __name__ == "__main__":
    main((sys.argv[1:] or ["all"])[0])
