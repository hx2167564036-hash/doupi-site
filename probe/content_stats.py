"""公开内容 API 只读统计：分类/标签/文章/页面数量，供 mockup 用真实数字。"""
import json
import os

import paramiko

HOST = "120.26.139.203"
RES = "120.26.139.203"
API = "/apis/api.content.halo.run/v1alpha1"


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=os.environ["WL_DEPLOY_PWD"], timeout=25,
              allow_agent=False, look_for_keys=False)

    def get(path):
        cmd = (f"curl -sk -m 25 --resolve doupi123.top:443:{RES} "
               f"'https://doupi123.top{API}{path}'")
        si, so, se = c.exec_command("bash -lc " + repr(cmd), timeout=60)
        raw = so.read().decode("utf-8", "replace")
        try:
            return json.loads(raw)
        except Exception:
            return {"_raw": raw[:300]}

    cats = get("/categories?page=0&size=50")
    print(f"\n分类 total={cats.get('total')}")
    for it in cats.get("items", []):
        spec = it.get("spec", {})
        print(f"  - {spec.get('displayName'):<12} posts={it.get('postCount'):<5} slug={spec.get('slug'):<14} "
              f"desc={str(spec.get('description'))[:30]}")

    tags = get("/tags?page=0&size=50")
    print(f"\n标签 total={tags.get('total')}")
    for it in tags.get("items", [])[:15]:
        spec = it.get("spec", {})
        print(f"  - {spec.get('displayName'):<16} count={it.get('postCount')}")

    posts = get("/posts?page=0&size=5&sort=spec.publishTime,desc")
    print(f"\n文章 total={posts.get('total')}")
    for it in posts.get("items", []):
        spec = it.get("spec", {})
        print(f"  - {spec.get('publishTime', '')[:10]}  {spec.get('title', '')[:40]}")

    for ep in ("/pages?page=0&size=20", "/singlepages?page=0&size=20"):
        r = get(ep)
        print(f"\n{ep} -> total={r.get('total')} keys={list(r)[:4]}")
    c.close()


if __name__ == "__main__":
    main()
