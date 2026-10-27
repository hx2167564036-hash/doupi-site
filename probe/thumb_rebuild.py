"""确认 Halo 缩略图在删除后能按需重建：试几种 URL 形态，看 thumbnails 目录是否重新长出文件。"""
import os
import paramiko

HOST = "120.26.139.203"
THUMB = "/opt/1panel/apps/halo/halo/data/attachments/thumbnails"
UPLOAD = "/opt/1panel/apps/halo/halo/data/attachments/upload"
RES = "120.26.139.203"


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=os.environ["WL_DEPLOY_PWD"], timeout=25,
              allow_agent=False, look_for_keys=False)

    def run(cmd, t=90):
        si, so, se = c.exec_command("bash -lc " + repr(cmd), timeout=t)
        out = so.read().decode("utf-8", "replace").rstrip()
        rc = so.channel.recv_exit_status()
        print(">>> " + cmd[:100])
        if out:
            print(out[:1500])
        print(f"[rc {rc}]\n")
        return out

    name = run(f"ls -t {UPLOAD}/*.jpg 2>/dev/null | head -1 | xargs -r basename")
    print("pick jpg: " + name)
    if not name:
        c.close()
        return

    run(f"find {THUMB} -type f | wc -l")

    # 形态 A：附件 URL 加 width 查询参数（Halo 2 前端缩略图用法）
    run(f"curl -sk -m 25 -o /dev/null -w 'A ?width=400 -> %{{http_code}}\\n' "
        f"--resolve doupi123.top:443:{RES} 'https://doupi123.top/upload/{name}?width=400'")
    run(f"find {THUMB} -type f | wc -l; du -sh {THUMB}")

    # 形态 B：/upload/thumbnails/w400/<name>
    run(f"curl -sk -m 25 -o /dev/null -w 'B /upload/thumbnails/w400 -> %{{http_code}}\\n' "
        f"--resolve doupi123.top:443:{RES} 'https://doupi123.top/upload/thumbnails/w400/{name}'")
    run(f"find {THUMB} -type f | wc -l")

    # 形态 C：直接看首页 HTML 里图片的真实 src
    run(f"curl -sk -m 25 --resolve doupi123.top:443:{RES} https://doupi123.top/ "
        f"| grep -oE '(src|srcset)=\"[^\"]*(upload|thumbnail)[^\"]*\"' | head -5")

    c.close()


if __name__ == "__main__":
    main()
