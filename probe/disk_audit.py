"""只读磁盘体检：连一次跑一批**只读**命令，分段打印。

用法（口令只从环境变量读，绝不落文件）：
    $p='C:\\Users\\kendle\\.qoder-cn\\projects\\C--Users-kendle-Documents-Qoder-2026-09-21-5e6cb6a5\\memory\\reference-wenlv-deploy.md'
    $env:WL_DEPLOY_PWD=(Get-Content $p -Encoding UTF8)[7].Split([char]96)[1]
    python probe/disk_audit.py            # 全部段落
    python probe/disk_audit.py 3 5        # 只跑第 3、5 段

本脚本不含任何写操作（没有 rm/mv/truncate/docker prune），可放心反复跑。
"""
import os
import sys

import paramiko

HOST = "120.26.139.203"
USER = "root"

# (标题, 命令)。全部只读。
SECTIONS = [
    ("1. 整盘与顶层目录", r"""
df -h /
echo '--- 顶层 du (xdev, 只跨同一文件系统)'
du -shx /opt /var /usr /root /home /tmp 2>/dev/null
echo '--- inode'
df -i / | tail -1
"""),

    ("2. /opt 分解", r"""
du -shx /opt/* 2>/dev/null | sort -rh | head -12
echo '--- /opt/1panel'
du -shx /opt/1panel/* 2>/dev/null | sort -rh | head -12
echo '--- /opt/1panel/apps (各应用)'
du -shx /opt/1panel/apps/* 2>/dev/null | sort -rh | head -15
"""),

    ("3. /var 与 docker 存储", r"""
du -shx /var/* 2>/dev/null | sort -rh | head -10
echo '--- /var/lib/docker'
du -shx /var/lib/docker/* 2>/dev/null | sort -rh | head -10
echo '--- /var/lib/containerd'
du -shx /var/lib/containerd/* 2>/dev/null | sort -rh | head -5
echo '--- docker system df'
docker system df 2>/dev/null
echo '--- docker volumes'
docker volume ls 2>/dev/null | head -20
"""),

    ("4. 容器 json 日志排行", r"""
du -sm /var/lib/docker/containers/*/*-json.log 2>/dev/null | sort -rn | head -8
echo '--- 各容器日志驱动'
docker inspect $(docker ps -q) --format '{{.Name}} {{.HostConfig.LogConfig.Type}} {{.HostConfig.LogConfig.Config}}' 2>/dev/null
"""),

    ("5. Halo 容器挂载与配置", r"""
docker inspect 1Panel-halo-UaWD --format '{{range .Mounts}}{{.Source}} => {{.Destination}} ({{.Type}}){{"\n"}}{{end}}' 2>/dev/null
echo '--- image / 入口'
docker inspect 1Panel-halo-UaWD --format '{{.Config.Image}} | {{.Config.WorkingDir}} | {{.Config.Entrypoint}} | {{.Config.Cmd}}' 2>/dev/null
echo '--- 环境变量(脱敏打印, 只显示键名)'
docker inspect 1Panel-halo-UaWD --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | cut -d= -f1
"""),

    ("6. Halo 数据目录", r"""
D=/opt/1panel/apps/halo/halo/data
ls -la $D 2>/dev/null | head -20
echo '--- data 一级目录大小'
du -shx $D/* 2>/dev/null | sort -rh | head -20
echo '--- attachments 一级'
du -shx $D/attachments/* 2>/dev/null | sort -rh | head -20
echo '--- attachments 文件数 / 总大小'
find $D/attachments -type f 2>/dev/null | wc -l
du -shx $D/attachments 2>/dev/null
"""),

    ("7. 附件按扩展名统计", r"""
D=/opt/1panel/apps/halo/halo/data
find $D/attachments -type f -printf '%s\t%f\n' 2>/dev/null | awk -F'\t' '{n=$2; i=index(n,"."); e=(i>0)?substr(n,i+1):"none"; c[e]++; s[e]+=$1} END{for(e in c) printf "%10.1fM  %6d  %s\n", s[e]/1048576, c[e], e}' | sort -rn | head -25
"""),

    ("8. docker 数据根目录到底在哪", r"""
du -shx /opt/1panel/docker/* 2>/dev/null | sort -rh | head -12
echo '--- docker info'
docker info 2>/dev/null | grep -Ei 'docker root dir|storage driver|containerd|images|server version'
echo '--- daemon.json'
cat /etc/docker/daemon.json 2>/dev/null || echo '(无 daemon.json)'
echo '--- 是否有第二个 docker 根'
ls -d /opt/1panel/docker/*/ 2>/dev/null | head
"""),

    ("9. 日志面（Halo 自己的 + 系统 journal）", r"""
D=/opt/1panel/apps/halo/halo/data
ls -lh $D/logs 2>/dev/null | head -15
du -shx $D/logs 2>/dev/null
echo '--- journal'
journalctl --disk-usage 2>/dev/null
echo '--- /var/log 前 10'
du -shx /var/log/* 2>/dev/null | sort -rh | head -10
"""),

    ("10. 全盘 >100M 的文件", r"""
find /opt /var /usr /root /home /tmp -xdev -type f -size +100M -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -25
"""),

    ("11. /opt/1panel/docker/compose 到底是什么（14G）", r"""
du -shx /opt/1panel/docker/compose/* 2>/dev/null | sort -rh | head -20
echo '--- 二级'
du -shx /opt/1panel/docker/compose/*/* 2>/dev/null | sort -rh | head -20
echo '--- >50M 的文件'
find /opt/1panel/docker/compose -type f -size +50M -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -20
"""),

    ("12. 缩略图与附件分布（可否瘦身）", r"""
D=/opt/1panel/apps/halo/halo/data/attachments
du -shx $D/upload/* 2>/dev/null | sort -rh | head -10
echo '--- thumbnails 月份分布'
du -shx $D/thumbnails/* 2>/dev/null | sort -rh | head -10
echo '--- 单文件尺寸分布(全部附件)'
find $D -type f -printf '%s\n' 2>/dev/null | awk '{if($1>4*1048576)a++; else if($1>1*1048576)b++; else if($1>300*1024)c++; else if($1>100*1024)d++; else e++} END{printf ">4M:%d\n1-4M:%d\n300K-1M:%d\n100-300K:%d\n<100K:%d\n",a,b,c,d,e}'
echo '--- 最大的 10 个附件'
find $D -type f -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -10
"""),

    ("13. 真正的大户：obsidian livesync 14G", r"""
S=/opt/1panel/docker/compose/obsidian/storage
du -shx $S/* 2>/dev/null | sort -rh | head -12
echo '--- 二级'
du -shx $S/*/* 2>/dev/null | sort -rh | head -12
echo '--- 文件数'
find $S -type f 2>/dev/null | wc -l
echo '--- compose 定义'
cat /opt/1panel/docker/compose/obsidian/docker-compose.yml 2>/dev/null
echo '--- 该容器挂载'
docker inspect 1Panel-obsidian_livesync-WJYC --format '{{range .Mounts}}{{.Source}} => {{.Destination}}{{"\n"}}{{end}}' 2>/dev/null
"""),

    ("14. mysql 数据与 binlog", r"""
du -shx /opt/1panel/apps/mysql/mysql/data/* 2>/dev/null | sort -rh | head -12
echo '--- binlog 文件'
ls -lh /opt/1panel/apps/mysql/mysql/data/binlog.* 2>/dev/null | head
echo '--- /root 里有什么'
du -shx /root/* /root/.[a-z]* 2>/dev/null | sort -rh | head -8
"""),

    ("15. 可回收量估算（只算，不删）", r"""
echo '--- snap 占多少'
du -shx /var/lib/snapd 2>/dev/null
echo '--- apt 缓存'
du -shx /var/cache/apt 2>/dev/null
echo '--- 镜像清单'
docker image ls -a --format '{{.Repository}}:{{.Tag}} {{.Size}}' 2>/dev/null
echo '--- 系统信息'
free -h | head -2
swapon --show 2>/dev/null
"""),

    ("16. fast-note-sync 的 temp 是不是可清", r"""
S=/opt/1panel/docker/compose/obsidian/storage
echo '== temp 顶层条目数'
find $S/temp -maxdepth 1 -mindepth 1 2>/dev/null | wc -l
echo '== temp 文件按天分布'
find $S/temp -type f -printf '%TY-%Tm-%Td\n' 2>/dev/null | sort | uniq -c | tail -8
echo '== temp 最大 5 个'
find $S/temp -type f -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -5
echo '== temp 一级内容举例'
ls -la $S/temp 2>/dev/null | head -6
echo '== vault 文件数 / 最大文件'
find $S/vault -type f 2>/dev/null | wc -l
find $S/vault -type f -printf '%s\t%p\n' 2>/dev/null | sort -rn | head -5
echo '== config'
ls -la /opt/1panel/docker/compose/obsidian/config 2>/dev/null
cat /opt/1panel/docker/compose/obsidian/config/*.* 2>/dev/null | head -40
echo '== 日志'
ls -lt $S/logs 2>/dev/null | head -5
"""),

    ("17. Halo json 日志为什么一天 10M", r"""
L=$(ls -S /var/lib/docker/containers/*/*-json.log 2>/dev/null | head -1)
echo "file=$L"
echo '== 尾部 3MB 的行数与级别分布'
tail -c 3000000 "$L" | wc -l
tail -c 3000000 "$L" | grep -oE '"log":"[A-Z]+ ?' | tr -d '"log: ' | sort | uniq -c | sort -rn | head -8
echo '== 尾部 3MB 里的重复消息（去掉时间戳后）'
tail -c 3000000 "$L" | sed -E 's/.*"log":"(.*)","stream".*/\1/' | sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9:.,+]+//' | cut -c1-110 | sort | uniq -c | sort -rn | head -12
"""),

    ("18. 那个异常到底是什么", r"""
L=$(ls -S /var/lib/docker/containers/*/*-json.log 2>/dev/null | head -1)
echo '== 异常类名排行（尾部 3MB）'
tail -c 3000000 "$L" | sed -E 's/.*"log":"(.*)","stream".*/\1/' | grep -oE '[A-Za-z0-9_.]*(Exception|Error)[A-Za-z0-9_.]*' | sort | uniq -c | sort -rn | head -10
echo '== 报错首行样例（去掉堆栈帧）'
tail -c 3000000 "$L" | sed -E 's/.*"log":"(.*)","stream".*/\1/' | grep -vE '^\\u0009|^[[:space:]]*at ' | grep -E 'ERROR|Exception|WARN' | cut -c1-300 | sort | uniq -c | sort -rn | head -8
"""),
]


def conn():
    pwd = os.environ.get("WL_DEPLOY_PWD")
    if not pwd:
        raise SystemExit("缺 WL_DEPLOY_PWD 环境变量（口令不进文件）")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=pwd, timeout=25,
              allow_agent=False, look_for_keys=False)
    return c


def run(c, cmd, t=420):
    _, so, se = c.exec_command("bash -lc " + "'" + cmd.replace("'", r"'\''") + "'", timeout=t)
    rc = so.channel.recv_exit_status()
    out = so.read().decode("utf-8", "replace")
    err = se.read().decode("utf-8", "replace")
    return out, err, rc


def human(n):
    n = float(n)
    for u in ("B", "K", "M", "G", "T"):
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}P"


if __name__ == "__main__":
    want = [int(a) for a in sys.argv[1:]] or None
    c = conn()
    for i, (title, cmd) in enumerate(SECTIONS, 1):
        if want and i not in want:
            continue
        print("\n" + "=" * 72)
        print(f"## {title}")
        print("=" * 72)
        try:
            out, err, rc = run(c, cmd)
        except Exception as e:  # noqa: BLE001
            print(f"[失败] {e}")
            continue
        print(out.rstrip() or "(空)")
        if err.strip():
            print("[stderr] " + err.strip()[:800])
        if rc:
            print(f"[exit {rc}]")
    c.close()
