"""把「上下文中枢」里已下载的课程文件上传到服务器，供站点做「登录后可见」的下载区。

用法：
    $env:PYTHONPATH = (Resolve-Path '.deps').Path
    python -u probe/upload_course_files.py --plan          # 只统计，不上传
    python -u probe/upload_course_files.py --limit 3       # 传 3 个测试速度
    python -u probe/upload_course_files.py                 # 全量（跳过服务器已存在且大小一致的）

服务器落点：/opt/1panel/www/course-files/<课程>/<文件名>
（openresty 容器里是 /www/course-files/…，由 nginx 的 /course-files/ 段带 basic auth 提供）
"""
import argparse
import os
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deploy_theme import ssh_client  # noqa: E402

HUB = r"D:\应用信息互联"
DB = os.path.join(HUB, "data", "context.db")
REMOTE_DIR = "/opt/1panel/www/course-files"


def plan():
    """返回 [(course, name, local_abs, size)]，只含磁盘上真实存在的文件。"""
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """select f.name, f.local_path, coalesce(co.name, '未关联课程') as course
           from tron_files f left join tron_courses co on co.id = f.course_id"""
    ).fetchall()
    con.close()

    out, missing = [], []
    for r in rows:
        p = (r["local_path"] or "").strip()
        if not p:
            missing.append((r["course"], r["name"]))
            continue
        full = os.path.join(HUB, p.replace("/", "\\"))
        if not os.path.exists(full):
            missing.append((r["course"], r["name"]))
            continue
        out.append((r["course"], r["name"], full, os.path.getsize(full)))
    return out, missing, len(rows)


def safe(name):
    return name.replace("/", "_").replace("\\", "_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--every", type=int, default=25)
    a = ap.parse_args()

    files, missing, total_rows = plan()
    bytes_total = sum(f[3] for f in files)
    print(f"DB 记录 {total_rows} 条 | 本地有文件 {len(files)} 份 / {bytes_total/1048576:.1f} MB | 缺文件 {len(missing)} 份")
    if a.plan:
        byc = {}
        for c, n, _, s in files:
            byc.setdefault(c, [0, 0])
            byc[c][0] += 1
            byc[c][1] += s
        for c, (n, s) in sorted(byc.items(), key=lambda x: -x[1][1]):
            print(f"  {c}: {n} 份 / {s/1048576:.1f} MB")
        return

    c = ssh_client()
    sftp = c.open_sftp()

    def ensure(path):
        try:
            sftp.stat(path)
            return
        except IOError:
            pass
        parts = path.strip("/").split("/")
        cur = ""
        for part in parts:
            cur += "/" + part
            try:
                sftp.stat(cur)
            except IOError:
                sftp.mkdir(cur)

    ensure(REMOTE_DIR)
    todo = files[: a.limit] if a.limit else files
    done = skip = 0
    sent = 0
    t0 = time.time()
    fails = []
    for course, name, local, size in todo:
        rdir = f"{REMOTE_DIR}/{safe(course)}"
        rpath = f"{rdir}/{safe(name)}"
        ensure(rdir)
        try:
            st = sftp.stat(rpath)
            if st.st_size == size:
                skip += 1
                continue
        except IOError:
            pass
        try:
            sftp.put(local, rpath)
            done += 1
            sent += size
        except Exception as e:  # noqa: BLE001
            fails.append((course, name, str(e)[:80]))
        if done and done % a.every == 0:
            dt = time.time() - t0
            rate = sent / dt / 1024 if dt else 0
            print(f"  已传 {done} 份 / {sent/1048576:.1f} MB | {rate:.0f} KB/s | 用时 {dt/60:.1f} min", flush=True)
    dt = time.time() - t0
    print(f"完成：新传 {done} 份，跳过（已存在同大小）{skip} 份，失败 {len(fails)} 份，"
          f"共 {sent/1048576:.1f} MB，用时 {dt/60:.1f} min", flush=True)
    for f in fails[:10]:
        print("  失败:", f)
    sftp.close()
    c.close()


if __name__ == "__main__":
    main()
