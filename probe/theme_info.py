"""看当前主题的清单/模板面：theme.yaml、目录、模板清单、资源体积。"""
import os

import paramiko

HOST = "120.26.139.203"
T = "/opt/1panel/apps/halo/halo/data/themes/theme-Serenity"


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=os.environ["WL_DEPLOY_PWD"], timeout=25,
              allow_agent=False, look_for_keys=False)

    def sh(cmd):
        si, so, se = c.exec_command("bash -lc " + repr(cmd), timeout=120)
        out = so.read().decode("utf-8", "replace").rstrip()
        rc = so.channel.recv_exit_status()
        print(">>> " + cmd[:120])
        print(out[:3000] or "(empty)")
        print(f"[rc {rc}]\n")

    sh(f"cat {T}/theme.yaml")
    sh(f"ls -la {T}")
    sh(f"find {T}/templates -type f -name '*.html' | sed 's|.*/templates/||' | sort | tr '\\n' ' '")
    sh(f"du -sh {T}/assets/* 2>/dev/null | sort -rh | head -15")
    sh(f"ls {T}/assets/css 2>/dev/null; ls {T}/assets/js 2>/dev/null")
    c.close()


if __name__ == "__main__":
    main()
