"""重生成 theme-doupi/assets/data/courses.js：给每份课件带上「服务器上是否已有」标记。

数据源：D:\\应用信息互联\\data\\context.db（只读）+ 本地文件是否存在（决定 ok）
服务器端是否已上传不参与判断——上传脚本按同样规则落盘，两边一致。
"""
import json
import os
import pathlib
import sqlite3

HUB = r"D:\应用信息互联"
DB = os.path.join(HUB, "data", "context.db")
DATA = pathlib.Path(__file__).resolve().parent.parent / "theme-doupi/assets/data/courses.js"


def main():
    old = DATA.read_text(encoding="utf-8")
    data = json.loads(old.split("=", 1)[1].strip().rstrip(";"))

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """select f.name, f.local_path, coalesce(co.name, '未关联课程') as course
           from tron_files f left join tron_courses co on co.id = f.course_id"""
    ).fetchall()
    con.close()

    by_course = {}
    for r in rows:
        p = (r["local_path"] or "").strip()
        ok = 0
        sz = 0
        if p:
            full = os.path.join(HUB, p.replace("/", "\\"))
            if os.path.exists(full):
                ok = 1
                sz = os.path.getsize(full)
        by_course.setdefault(r["course"], []).append({"n": r["name"], "ok": ok, "sz": sz})

    total_ok = 0
    for c in data["courses"]:
        files = by_course.get(c["name"], [])
        # 同名去重（DB 里偶有重复行）
        seen, uniq = set(), []
        for f in files:
            if f["n"] in seen:
                continue
            seen.add(f["n"])
            uniq.append(f)
        # 可下载的排前面，按体积降序
        uniq.sort(key=lambda f: (-f["ok"], -f["sz"], f["n"]))
        c["files"] = uniq
        total_ok += sum(1 for f in uniq if f["ok"])

    DATA.write_text("window.COURSES = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    n_files = sum(len(c["files"]) for c in data["courses"])
    print(f"ok: {len(data['courses'])} 门课 / {n_files} 条文件记录 / {total_ok} 份可下载，{DATA.stat().st_size} 字节")


if __name__ == "__main__":
    main()
