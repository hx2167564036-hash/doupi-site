"""抓全站文章，按 slug 里的真实日期生成 mockup 热力图数据。

注意：站点的 spec.publishTime 全是 2026-07-22（批量导入造成），真实日期在
slug / 标题里，形如 `2025-04-10-day-002` / `2025-04-10 Day 002`。

产出：
  mockups/v1/data/posts.json    [{day, date, title, slug}] 按日期正序
  mockups/v1/data/heatmap.js    window.DAYS = ['2025-04-09', ...]
"""
import json
import os
import pathlib
import re
from datetime import date, timedelta

import paramiko

HOST = "120.26.139.203"
API = "/apis/api.content.halo.run/v1alpha1"
OUT = pathlib.Path(__file__).resolve().parent.parent / "mockups" / "v1" / "data"
DATE_IN_SLUG = re.compile(r"(\d{4}-\d{2}-\d{2})-day-?(\d+)")
DATE_IN_TITLE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def parse(it):
    spec = it.get("spec", {})
    slug = spec.get("slug") or ""
    title = spec.get("title") or ""
    m = DATE_IN_SLUG.search(slug)
    if m:
        return m.group(1), int(m.group(2)), title, slug
    m = DATE_IN_TITLE.search(title)
    if m:
        return m.group(1), None, title, slug
    return None, None, title, slug


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=os.environ["WL_DEPLOY_PWD"], timeout=25,
              allow_agent=False, look_for_keys=False)

    def api(path):
        cmd = (f"curl -sk -m 30 --resolve doupi123.top:443:{HOST} "
               f"'https://doupi123.top{API}{path}'")
        si, so, se = c.exec_command("bash -lc " + repr(cmd), timeout=90)
        return json.loads(so.read().decode("utf-8", "replace"))

    seen, rows, page, total = set(), [], 0, None
    while True:
        r = api(f"/posts?page={page}&size=100&sort=metadata.creationTimestamp,desc")
        batch = r.get("items", [])
        total = r.get("total", total)
        for it in batch:
            key = it.get("metadata", {}).get("name")
            if key in seen:
                continue
            seen.add(key)
            d, day, title, slug = parse(it)
            if d:
                rows.append({"day": day, "date": d, "title": title, "slug": slug})
        page += 1
        if not batch or page > 30:
            break

    rows.sort(key=lambda x: (x["date"], x["day"] or 0))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "posts.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")

    days = sorted({r["date"] for r in rows})
    (OUT / "heatmap.js").write_text(
        "window.DAYS = " + json.dumps(days) + ";\n", encoding="utf-8")

    dup = len(rows) - len(days)
    d0, d1 = date.fromisoformat(days[0]), date.fromisoformat(days[-1])
    have = set(days)
    missing = []
    d = d0
    while d <= d1:
        if d.isoformat() not in have:
            missing.append(d.isoformat())
        d += timedelta(days=1)

    print(f"API total={total} fetched={len(rows)} unique_days={len(days)} dup_days={dup}")
    print(f"range {days[0]} .. {days[-1]} span={(d1 - d0).days + 1}d missing={len(missing)}")
    print(f"max day number={max((r['day'] or 0) for r in rows)}")
    print("missing (first 20):", ", ".join(missing[:20]))
    c.close()


if __name__ == "__main__":
    main()
