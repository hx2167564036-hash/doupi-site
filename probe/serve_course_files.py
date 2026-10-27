"""给 /course-files/ 加 basic auth，并把 nginx 指向 /opt/1panel/www/course-files。

用法：
    python -u probe/serve_course_files.py conf     # 写入 vhost 并 nginx -t + reload
    python -u probe/serve_course_files.py verify   # 无口令应 401、有口令应 200/404
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deploy_theme import ssh_client  # noqa: E402

CONF = "/opt/1panel/www/conf.d/doupi123.top.conf"
BACKUP = CONF + ".bak.course-files"

REMOTE_PATCH = """import re, pathlib
p = pathlib.Path('%(conf)s')
s = p.read_text(encoding='utf-8')
s = re.sub(r'\\n    # 课程课件下载区.*?\\n    \\}\\n', '\\n', s, flags=re.S)
block = '''    # 课程课件下载区（basic auth）
    location ^~ /course-files/ {
        auth_basic "doupi course files";
        auth_basic_user_file /www/.htpasswd-doupi;
        alias /www/course-files/;
        autoindex off;
        charset utf-8;
        add_header Cache-Control "private, max-age=0";
    }

'''
i = s.find('    location / {')
if i < 0:
    raise SystemExit('vhost 里找不到 location / {')
s = s[:i] + block + s[i:]
p.write_text(s, encoding='utf-8')
print('patched')
""" % {"conf": CONF}


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "verify"
    c = ssh_client()

    def run(cmd, t=120):
        _, o, e = c.exec_command(cmd, timeout=t)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    if action in ("conf", "all"):
        if run("test -f %s && echo yes" % CONF) != "yes":
            raise SystemExit("找不到 vhost：" + CONF)
        run("cp -n %s %s" % (CONF, BACKUP))
        # 远程写一个补丁脚本再执行（避免 heredoc 转义地狱）
        remote = "/tmp/_patch_vhost.py"
        sftp = c.open_sftp()
        with sftp.open(remote, "w") as f:
            f.write(REMOTE_PATCH)
        sftp.close()
        print(run("python3 %s" % remote))
        print(run("docker exec 1Panel-openresty-qKv1 nginx -t 2>&1 | tail -2"))
        print(run("docker exec 1Panel-openresty-qKv1 nginx -s reload 2>&1 | tail -2"))
        print("已 reload")

    if action in ("verify", "all"):
        R = "--resolve doupi123.top:443:127.0.0.1"
        print("无口令:", run("curl -sk -o /dev/null -w '%%{http_code}\\n' %s https://doupi123.top/course-files/" % R))
        print("有口令:", run("curl -sk -u doupi:doupi-gdvgykln -o /dev/null -w '%%{http_code}\\n' %s https://doupi123.top/course-files/" % R))
        print("目录:", run("ls /opt/1panel/www/course-files/ | head -8"))
        print("体积:", run("du -sh /opt/1panel/www/course-files/ 2>/dev/null | tail -1"))

    c.close()


if __name__ == "__main__":
    main()
