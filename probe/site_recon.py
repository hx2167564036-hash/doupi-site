"""只读侦察：站点现在用哪个模板、模板文件结构、首页/文章页真实 HTML、内容量。

产物（本机）：
  notes/site-snapshot/home.html      首页完整 HTML
  notes/site-snapshot/post.html      一篇最新文章的完整 HTML
  notes/site-snapshot/recon.txt      侦察报告
"""
import os
from pathlib import Path

import paramiko

HOST = "120.26.139.203"
RES = "120.26.139.203"
BASE = "https://doupi123.top"
SNAP = Path(__file__).resolve().parent.parent / "notes" / "site-snapshot"


def main():
    SNAP.mkdir(parents=True, exist_ok=True)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=os.environ["WL_DEPLOY_PWD"], timeout=25,
              allow_agent=False, look_for_keys=False)

    report = []

    def sh(cmd, t=120):
        si, so, se = c.exec_command("bash -lc " + repr(cmd), timeout=t)
        out = so.read().decode("utf-8", "replace").rstrip()
        rc = so.channel.recv_exit_status()
        report.append(f"\n>>> {cmd}\n{out[:3000]}\n[rc {rc}]")
        return out

    def fetch(path, dest):
        """从服务器 curl 拉页面并存到本机。"""
        cmd = (f"curl -sk -m 30 --resolve doupi123.top:443:{RES} '{BASE}{path}' "
               f"-H 'Accept-Encoding: identity'")
        si, so, se = c.exec_command("bash -lc " + repr(cmd), timeout=90)
        data = so.read()
        rc = so.channel.recv_exit_status()
        dest.write_bytes(data)
        report.append(f"\n>>> GET {path} -> {dest.name} {len(data)} bytes [rc {rc}]")
        return data.decode("utf-8", "replace")

    print("=== 1. 模板目录")
    sh("ls -la /opt/1panel/apps/halo/halo/data/themes/")
    sh("for d in /opt/1panel/apps/halo/halo/data/themes/*/; do echo \"--- $d\"; "
       "grep -E '^(name|displayName|version|author|description|repo|homepage)' \"$d/theme.yaml\" 2>/dev/null | head -12; done")

    print("=== 2. 模板文件结构")
    sh("find /opt/1panel/apps/halo/halo/data/themes -maxdepth 2 -type d | head -40")
    sh("find /opt/1panel/apps/halo/halo/data/themes -name '*.html' | wc -l")
    sh("du -sh /opt/1panel/apps/halo/halo/data/themes/*/ 2>/dev/null")

    print("=== 3. Halo 数据库配置（只看驱动和库名，不打印口令）")
    sh("docker inspect 1Panel-halo-UaWD --format '{{range .Config.Env}}{{println .}}{{end}}' "
       "| grep -Ei 'spring|datasource|db|url' | sed -E 's/(password|PASSWORD)=.*/\\1=<masked>/' | head -20")
    sh("ls /opt/1panel/apps/halo/halo/data/application*.y*ml 2>/dev/null && "
       "grep -vE 'password|secret' /opt/1panel/apps/halo/halo/data/application*.y*ml 2>/dev/null | head -30")

    print("=== 4. 拉首页与文章页")
    home = fetch("/", SNAP / "home.html")
    sh(f"curl -sk -m 30 --resolve doupi123.top:443:{RES} '{BASE}/sitemap.xml' | head -40")

    sitemap = sh(f"curl -sk -m 30 --resolve doupi123.top:443:{RES} '{BASE}/sitemap.xml' | "
                 "grep -oE '<loc>[^<]+</loc>' | wc -l")
    post_url = ""
    for line in sitemap.splitlines():
        if "/posts/" in line:
            post_url = line.strip()
            break
    if not post_url:
        import re
        m = re.findall(r'href="(/archives/[^"]+)"', home)
        if m:
            post_url = m[0]
    print(f"[post url] {post_url!r}")
    if post_url:
        fetch(post_url, SNAP / "post.html")

    print("=== 5. 首页 head 与结构摘要")
    sh(f"curl -sk -m 30 --resolve doupi123.top:443:{RES} '{BASE}/' | "
       "sed -n '1,60p' | cut -c1-200")
    sh(f"curl -sk -m 30 --resolve doupi123.top:443:{RES} '{BASE}/' | "
       "grep -oE '<(nav|header|main|footer|section|article)[^>]*class=\"[^\"]*\"' | head -30")
    sh(f"curl -sk -m 30 --resolve doupi123.top:443:{RES} '{BASE}/' | "
       "grep -oE '(src|href)=\"[^\"]*\\.(css|js)[^\"]*\"' | head -20")

    print("=== 6. 内容量")
    sh(f"curl -sk -m 30 --resolve doupi123.top:443:{RES} '{BASE}/apis/api.content.halo.run/v1alpha1/posts?page=0&size=1' "
       "| head -c 600")

    (SNAP / "recon.txt").write_text("\n".join(report), encoding="utf-8")
    # 控制台只打前 6000 字符，全文在文件里
    print("\n".join(report)[:6000])
    print(f"\n[全文] {SNAP / 'recon.txt'}")
    c.close()


if __name__ == "__main__":
    main()
