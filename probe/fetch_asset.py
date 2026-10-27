"""从服务器侧拉取站点静态资源到本机（绕开本机 DNS/TLS 问题）。"""
import os
import sys
from pathlib import Path

import paramiko

HOST = "120.26.139.203"
RES = "120.26.139.203"


def fetch(url_path, dest, c):
    cmd = (f"curl -sk -m 30 --resolve doupi123.top:443:{RES} "
           f"'https://doupi123.top{url_path}' -H 'Accept-Encoding: identity'")
    si, so, se = c.exec_command("bash -lc " + repr(cmd), timeout=60)
    data = so.read()
    rc = so.channel.recv_exit_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"{len(data):>8} B  rc={rc}  {url_path[:70]} -> {dest.name}")


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=os.environ["WL_DEPLOY_PWD"], timeout=25,
              allow_agent=False, look_for_keys=False)
    base = Path(__file__).resolve().parent.parent
    fetch("/upload/u=1713559136,613445356&fm=253&fmt=auto&app=120&f=JPEG-ckvX.webp",
          base / "mockups" / "v1" / "assets" / "avatar.webp", c)
    # 顺便看看分类的真实数量
    for p in ("/apis/api.content.halo.run/v1alpha1/categories?page=0&size=20",
              "/apis/api.content.halo.run/v1alpha1/posts?page=0&size=1"):
        si, so, se = c.exec_command(
            "bash -lc " + repr(f"curl -sk -m 20 --resolve doupi123.top:443:{RES} 'https://doupi123.top{p}'"), timeout=40)
        print(p.split("?")[0].split("/")[-1], "->", so.read().decode("utf-8", "replace")[:400])
    c.close()


if __name__ == "__main__":
    main()
