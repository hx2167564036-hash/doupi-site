"""A 档回收（用户 2026-10-27 12:54 批准）：只做下面 4 件，路径全部写死，不用通配符。

  a1  清 /opt/1panel/docker/compose/obsidian/storage/temp 下 8 月的过期上传会话（5.0G）
  a2  ��断 Halo 容器 json 日志（723M）
  a3  清 Halo 缩略图缓存（1.35G，访问时按需重建）
  a4  journalctl --vacuum-size=20M（~45M）

用法：
    python probe/reclaim_A.py --dry-run          # 只打印将删什么、删多少
    python probe/reclaim_A.py                    # 真删（危险，需用户批准）
    python probe/reclaim_A.py a1 a2              # 只跑指定步
"""
import os
import sys

import paramiko

HOST = "120.26.139.203"
USER = "root"

TEMP = "/opt/1panel/docker/compose/obsidian/storage/temp"
LOGDIR = "/var/lib/docker/containers/38e4ec563381891af2e087f5f2c024523c747c59eea5b179e6e95cdadbd99ba4"
LOG = LOGDIR + "/38e4ec563381891af2e087f5f2c024523c747c59eea5b179e6e95cdadbd99ba4-json.log"
THUMB = "/opt/1panel/apps/halo/halo/data/attachments/thumbnails"


def conn():
    pwd = os.environ.get("WL_DEPLOY_PWD")
    if not pwd:
        raise SystemExit("缺 WL_DEPLOY_PWD 环境变量（口令不进文件）")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=pwd, timeout=25,
              allow_agent=False, look_for_keys=False)
    return c


def sh(c, cmd, t=900):
    si, so, se = c.exec_command("bash -lc " + "'" + cmd.replace("'", r"'\''") + "'", timeout=t)
    rc = so.channel.recv_exit_status()
    out = so.read().decode("utf-8", "replace").rstrip()
    err = se.read().decode("utf-8", "replace").rstrip()
    return out, err, rc


def show(title, cmd, c):
    print(f"\n--- {title}")
    out, err, rc = sh(c, cmd)
    if out:
        print(out)
    if err:
        print("[stderr] " + err[:400])
    if rc:
        print(f"[exit {rc}]")
    return out


def preflight(c):
    show("现状 df", "df -h / | tail -1", c)
    show("temp 文件数 / 字节", f"find {TEMP} -maxdepth 1 -type f | wc -l; du -sb {TEMP}", c)
    show("temp 下有没有子目录", f"find {TEMP} -mindepth 1 -maxdepth 1 -type d | wc -l", c)
    show("日志大小", f"ls -l {LOG} | awk '{{print $5\" bytes\"}}'", c)
    show("缩略图字节", f"du -sb {THUMB}", c)
    show("Halo 容器状态", "docker ps --filter name=1Panel-halo-UaWD --format '{{.Status}}'", c)


def a1(c, dry):
    print("\n===== a1 清过期 temp")
    if dry:
        show("将删除的文件数", f"find {TEMP} -maxdepth 1 -type f | wc -l", c)
        show("将删除的字节", f"du -sb {TEMP}", c)
        return
    show("删除前", f"find {TEMP} -maxdepth 1 -type f | wc -l; du -sb {TEMP}", c)
    show("执行删除", f"find {TEMP} -maxdepth 1 -type f -delete", c)
    show("删除后", f"find {TEMP} -maxdepth 1 -type f | wc -l; du -sb {TEMP}", c)


def a2(c, dry):
    print("\n===== a2 截断 Halo json 日志")
    if dry:
        show("目标", f"ls -l {LOG}", c)
        return
    show("截断前", f"ls -l {LOG}; du -h {LOG}", c)
    show("执行 truncate -s 0", f"truncate -s 0 '{LOG}'", c)
    show("截断后", f"ls -l {LOG}; du -h {LOG}", c)
    show("容器还在吗", "docker ps --filter name=1Panel-halo-UaWD --format '{{.Status}}'", c)


def a3(c, dry):
    print("\n===== a3 清缩略图缓存")
    if dry:
        show("将删除的文件数 / 字节", f"find {THUMB} -type f | wc -l; du -sb {THUMB}", c)
        show("四档明细", f"du -shx {THUMB}/* 2>/dev/null | sort -rh", c)
        return
    show("删除前", f"find {THUMB} -type f | wc -l; du -sb {THUMB}", c)
    show("执行删除", f"find {THUMB} -type f -delete", c)
    show("删除后", f"find {THUMB} -type f | wc -l; du -sb {THUMB}", c)


def a4(c, dry):
    print("\n===== a4 journal 收缩")
    if dry:
        show("journal 现状", "journalctl --disk-usage", c)
        return
    show("执行前", "journalctl --disk-usage", c)
    show("执行 vacuum", "journalctl --vacuum-size=20M", c)
    show("执行后", "journalctl --disk-usage", c)


def post(c):
    print("\n===== 收尾核对")
    show("df", "df -h / | tail -1", c)
    show("各目标现状",
         f"du -sh {TEMP} 2>/dev/null; du -sh {THUMB} 2>/dev/null; "
         f"du -sh /opt/1panel/apps/halo/halo/data 2>/dev/null; "
         f"du -sh /var/lib/docker/containers 2>/dev/null", c)
    show("容器状态", "docker ps --format '{{.Names}} {{.Status}}'", c)
    show("站点探活(本机 127.0.0.1, Host 头)",
         "curl -s -o /dev/null -m 10 -w '%{http_code}\\n' -k -H 'Host: doupi123.top' https://127.0.0.1/ || true", c)


if __name__ == "__main__":
    argv = [a for a in sys.argv[1:]]
    dry = "--dry-run" in argv
    steps = [a for a in argv if not a.startswith("--")] or ["a1", "a2", "a3", "a4"]
    c = conn()
    if dry:
        print("### DRY RUN：不会删任何东西 ###")
    preflight(c)
    for s in steps:
        {"a1": a1, "a2": a2, "a3": a3, "a4": a4}[s](c, dry)
        show("df", "df -h / | tail -1", c)
    if not dry:
        post(c)
    c.close()
