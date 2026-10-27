"""从服务器拉 Serenity 主题的几个参考文件（theme.yaml / layout / index 头部 / post 头部）。

口令只从环境变量读：$env:WL_DEPLOY_PWD
"""
import os
import pathlib
import posixpath

import paramiko

HOST = "120.26.139.203"
USER = "root"
BASE = "/opt/1panel/apps/halo/halo/data/themes/theme-Serenity"
OUT = pathlib.Path(r"D:\kendle\Documents\doupi123-top\notes\theme-ref")

FILES = {
    "theme.yaml": None,
    "templates/modules/layout.html": None,
    "templates/index.html": 7000,
    "templates/post.html": 5000,
    "templates/page.html": 4000,
    "templates/archives.html": 3000,
}


def main():
    pwd = os.environ.get("WL_DEPLOY_PWD")
    if not pwd:
        raise SystemExit("缺少 WL_DEPLOY_PWD")
    OUT.mkdir(parents=True, exist_ok=True)
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, 22, USER, pwd, timeout=25)
    sftp = cli.open_sftp()
    for rel, limit in FILES.items():
        remote = posixpath.join(BASE, rel)
        local = OUT / rel.replace("/", "__")
        try:
            with sftp.open(remote, "rb") as f:
                data = f.read() if limit is None else f.read(limit)
            if limit:
                data += b"\n\n... (truncated)\n"
            local.write_bytes(data)
            print(f"ok {rel} -> {local.name} ({len(data)} B)")
        except Exception as e:  # noqa: BLE001
            print(f"ERR {rel}: {e}")
    sftp.close()
    cli.close()


if __name__ == "__main__":
    main()
