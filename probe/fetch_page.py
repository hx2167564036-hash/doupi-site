"""从服务器侧抓任意站点路径到本地（绕过本机 DNS/TLS）。

用法：python -u probe/fetch_page.py <站点路径> <本地文件>
口令仍从 $env:WL_DEPLOY_PWD 读，绝不落盘。
"""
import os
import sys
from pathlib import Path

import paramiko

HOST = "120.26.139.203"
RES = "120.26.139.203"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    url_path, dest = sys.argv[1], Path(sys.argv[2])
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=os.environ["WL_DEPLOY_PWD"], timeout=25,
              allow_agent=False, look_for_keys=False)
    cmd = (f"curl -sk -m 40 --resolve doupi123.top:443:{RES} "
           f"'https://doupi123.top{url_path}' -H 'Accept-Encoding: identity'")
    si, so, se = c.exec_command("bash -lc " + repr(cmd), timeout=60)
    data = so.read()
    rc = so.channel.recv_exit_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"{len(data):>9} B  rc={rc}  {url_path} -> {dest}")


if __name__ == "__main__":
    main()
