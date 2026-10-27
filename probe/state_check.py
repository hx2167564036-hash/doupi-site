"""A 档回收后状态核对：df / 日志 / journal / 端口 / 缩略图重建。"""
import os
import paramiko

HOST = "120.26.139.203"
LOG = ("/var/lib/docker/containers/38e4ec563381891af2e087f5f2c024523c747c59eea5b179e6e95cdadbd99ba4/"
       "38e4ec563381891af2e087f5f2c024523c747c59eea5b179e6e95cdadbd99ba4-json.log")
THUMB = "/opt/1panel/apps/halo/halo/data/attachments/thumbnails"
UPLOAD = "/opt/1panel/apps/halo/halo/data/attachments/upload"


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=os.environ["WL_DEPLOY_PWD"], timeout=25,
              allow_agent=False, look_for_keys=False)

    def sh(cmd, t=90):
        si, so, se = c.exec_command("bash -lc " + repr(cmd), timeout=t)
        out = so.read().decode("utf-8", "replace").rstrip()
        rc = so.channel.recv_exit_status()
        print(">>> " + cmd[:80])
        print(out[:1200])
        print(f"[rc {rc}]\n")

    sh("df -h / | tail -1")
    sh(f"ls -l '{LOG}' | awk '{{print $5\" bytes, mtime \"$6\" \"$7\" \"$8}}'")
    sh("journalctl --disk-usage")
    sh("ss -lntp | grep -E ':(80|443) ' || ss -lnt | head -20")

    print("=== 缩略图重建测试")
    si, so, se = c.exec_command("bash -lc 'ls " + UPLOAD + " | head -1'")
    name = so.read().decode().strip()
    so.channel.recv_exit_status()
    print("[pick] " + name)
    if name:
        sh(f"curl -sk -m 20 -o /dev/null -w 'upload -> %{{http_code}}\\n' "
           f"--resolve doupi123.top:443:120.26.139.203 'https://doupi123.top/upload/{name}'")
        sh(f"curl -sk -m 20 -o /dev/null -w 'thumb w400 -> %{{http_code}}\\n' "
           f"--resolve doupi123.top:443:120.26.139.203 "
           f"'https://doupi123.top/upload/thumbnails/w400/{name}'")
        sh(f"sleep 2; find {THUMB} -type f | wc -l; du -sh {THUMB}")

    print("=== 站点")
    sh("curl -sk -m 20 -o /dev/null -w 'GET / -> %{http_code}\\n' "
       "--resolve doupi123.top:443:120.26.139.203 https://doupi123.top/")
    print("=== 容器")
    sh("docker ps --format '{{.Names}} {{.Status}}'")
    c.close()


if __name__ == "__main__":
    main()
