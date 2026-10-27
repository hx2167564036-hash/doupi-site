"""在服务器侧查 B 站视频信息并取封面（本机 DNS 被 fake-ip 污染，只能在服务器上取）。

输出的 JSON 摘要打到 stdout；封面写到 mockups/v4/assets/bili-<bvid>.jpg。
"""
import json
import os
from pathlib import Path

import paramiko

HOST = "120.26.139.203"
BVIDS = ["BV1BTfxBSE5u", "BV1KskDBtEwL", "BV1pF4cz4EYG"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"


def ssh_cmd(c, cmd, timeout=60):
    si, so, se = c.exec_command("bash -lc " + repr(cmd), timeout=timeout)
    out = so.read()
    rc = so.channel.recv_exit_status()
    return out, rc


def main():
    base = Path(__file__).resolve().parent.parent
    assets = base / "mockups" / "v4" / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=os.environ["WL_DEPLOY_PWD"], timeout=25,
              allow_agent=False, look_for_keys=False)

    for bv in BVIDS:
        cmd = (f"curl -s -m 25 -A '{UA}' -H 'Referer: https://www.bilibili.com/' "
               f"'https://api.bilibili.com/x/web-interface/view?bvid={bv}'")
        out, rc = ssh_cmd(c, cmd)
        try:
            j = json.loads(out.decode("utf-8", "replace"))
        except Exception as e:
            print(bv, "JSON 解析失败", e, out[:120])
            continue
        if j.get("code") != 0:
            print(bv, "API 返回", j.get("code"), j.get("message"))
            continue
        d = j["data"]
        info = {
            "bvid": bv,
            "title": d.get("title"),
            "duration_s": d.get("duration"),
            "pubdate": d.get("pubdate"),
            "owner": d.get("owner", {}).get("name"),
            "view": d.get("stat", {}).get("view"),
            "danmaku": d.get("stat", {}).get("danmaku"),
            "pic": d.get("pic"),
            "desc": (d.get("desc") or "")[:120],
        }
        print(json.dumps(info, ensure_ascii=False))
        if info["pic"]:
            img, irc = ssh_cmd(c, f"curl -s -m 30 -A '{UA}' -e 'https://www.bilibili.com/' '{info['pic']}'")
            dest = assets / f"bili-{bv}.jpg"
            dest.write_bytes(img)
            print(f"   cover -> {dest.name} {len(img)} B rc={irc}")

    c.close()


if __name__ == "__main__":
    main()
