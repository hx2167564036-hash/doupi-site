"""Halo 站点 API 客户端（走服务器真实 IP + 显式 SNI，绕开本机 fake-ip DNS）。

用法：
    python -u probe/halo.py check                 # 读：列文章 + 打印一篇的结构
    python -u probe/halo.py check 2026-09-19-day490
    python -u probe/halo.py publish               # 发布 Day491 / Day492

Token 从 Obsidian Halo 插件配置里读，不打印、不落盘。
"""
import http.client
import json
import re
import ssl
import socket
import sys
import unicodedata
from pathlib import Path

HOST_IP = "120.26.139.203"
HOST_NAME = "doupi123.top"
TOKEN_FILE = Path(r"D:\kendle\Documents\chx的美好生活\.obsidian\plugins\halo\data.json")

API = "/apis/api.console.halo.run/v1alpha1"
CONTENT = "/apis/content.halo.run/v1alpha1"


def token():
    d = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    found = []

    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str) and o.startswith("pat_"):
            found.append(o)

    walk(d)
    if not found:
        raise SystemExit("没在插件配置里找到 pat_ token")
    print("token: pat_***（长度 %d）" % len(found[0]))
    return found[0]


def call(method, path, body=None, tok=None):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    raw = socket.create_connection((HOST_IP, 443), timeout=25)
    s = ctx.wrap_socket(raw, server_hostname=HOST_NAME)
    conn = http.client.HTTPConnection(HOST_NAME, timeout=25)
    conn.sock = s
    headers = {"Host": HOST_NAME, "Accept": "application/json"}
    if tok:
        headers["Authorization"] = "Bearer " + tok
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    conn.request(method, path, body=data, headers=headers)
    r = conn.getresponse()
    payload = r.read()
    conn.close()
    try:
        return r.status, json.loads(payload.decode("utf-8"))
    except Exception:
        return r.status, payload[:400]


def clean(text):
    """PDF 抽出来的字里有康熙部首/异体字形，NFKC 归一；顺手压掉多余空格。"""
    t = unicodedata.normalize("NFKC", text)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def read_pdf_text(name):
    import pypdf
    p = Path(r"D:\kendle\Documents\豆皮笔记") / name
    r = pypdf.PdfReader(str(p))
    raw = "\n".join((pg.extract_text() or "") for pg in r.pages)
    return clean(raw)


def cmd_check(name=None):
    tk = token()
    st, data = call("GET", f"{API}/posts?page=0&size=3&sort=metadata.creationTimestamp,desc", tok=tk)
    print("list ->", st, "total=", (data.get("total") if isinstance(data, dict) else data))
    items = data.get("items", []) if isinstance(data, dict) else []
    if items:
        print("item[0] keys:", list(items[0].keys()))
        print(json.dumps(items[0], ensure_ascii=False, indent=2)[:900])
    target = name
    if target is None and items:
        first = items[0]
        target = (first.get("metadata") or {}).get("name") or first.get("name")
    if target:
        st2, post = call("GET", f"{CONTENT}/posts/{target}", tok=tk)
        print("\npost ->", st2)
        print(json.dumps(post, ensure_ascii=False, indent=2)[:1600])
        st3, cont = call("GET", f"{CONTENT}/posts/{target}/content", tok=tk)
        if isinstance(cont, dict):
            print("\ncontent fields:", list(cont.keys()), "rawType=", cont.get("rawType"),
                  "raw_len=", len(cont.get("raw") or ""))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        cmd_check(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        print("unknown cmd", cmd)
