"""SSH 样板：只从环境变量读口令，绝不硬编码。

用法（PowerShell 先把口令读进当前会话的环境变量）：
    $line = Get-Content 'C:\\Users\\kendle\\.qoder-cn\\projects\\C--Users-kendle-Documents-Qoder-2026-09-21-5e6cb6a5\\memory\\reference-wenlv-deploy.md' -TotalCount 8
    $env:WL_DEPLOY_PWD = $line[7].Split([char]96)[1]
    python probe/ssh_sample.py "df -h /"
"""
import os
import sys

import paramiko

HOST = "120.26.139.203"
USER = "root"


def conn():
    pwd = os.environ.get("WL_DEPLOY_PWD")
    if not pwd:
        raise SystemExit("缺 WL_DEPLOY_PWD 环境变量（口令不进文件）")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=pwd, timeout=25,
              allow_agent=False, look_for_keys=False)
    return c


def run(c, cmd, t=300):
    _, so, _ = c.exec_command(cmd, timeout=t)
    rc = so.channel.recv_exit_status()
    return so.read().decode("utf-8", "replace").strip(), rc


if __name__ == "__main__":
    cmd = " ".join(sys.argv[1:]) or "uptime; df -h / | tail -1"
    c = conn()
    out, rc = run(c, cmd)
    print(out)
    c.close()
    raise SystemExit(rc)
