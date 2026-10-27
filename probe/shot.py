"""用 Chrome DevTools Protocol 截精确视口宽度的截图（桌面 + 手机）。

CLI 示例：
  python probe/shot.py mockups/v1/index.html mockups/v1/shots/desktop.png --width 1440 --dsf 1
  python probe/shot.py mockups/v1/index.html mockups/v1/shots/mobile.png  --width 390 --mobile --dsf 2 -H 844
本地文件路径会转成 file:// URL；也可以直接传 http(s) URL。
"""
import argparse
import base64
import json
import os
import pathlib
import socket
import subprocess
import sys
import time
import urllib.request

import websocket

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def to_url(target):
    if "://" in target:
        return target
    frag = ""
    if "#" in target:
        target, _, frag = target.partition("#")
        frag = "#" + frag
    p = pathlib.Path(target).resolve()
    return p.as_uri() + frag


class CDP:
    def __init__(self, ws):
        self.ws = ws
        self.n = 0

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(f"{method} -> {msg['error']}")
                return msg.get("result", {})

    def eval(self, expr, await_promise=False):
        r = self.call("Runtime.evaluate", expression=expr, returnByValue=True,
                      awaitPromise=await_promise)
        return r.get("result", {}).get("value")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=900)
    ap.add_argument("--dsf", type=float, default=1.0)
    ap.add_argument("--mobile", action="store_true")
    ap.add_argument("--settle", type=float, default=0.8, help="静置秒数，让字体/动效落定")
    ap.add_argument("--viewport-only", action="store_true", help="只截一屏，不截整页")
    ap.add_argument("--eval", dest="js", default=None, help="截图前在页面里跑一段 JS 并打印结果")
    ap.add_argument("--scroll", type=float, default=None, help="截图前滚动到指定 Y 像素")
    ap.add_argument("--at", default=None, help="滚动到元素位置，形如 '#journal@0.5'（0=顶部，1=底部）")
    args = ap.parse_args()

    port = free_port()
    profile = pathlib.Path(os.environ.get("TEMP", ".")) / f"chrome-cdp-{port}"
    proc = subprocess.Popen([
        CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--disable-crash-reporter", "--disable-breakpad", "--hide-scrollbars",
        "--no-first-run", "--no-default-browser-check", "--force-color-profile=srgb",
        "--disable-extensions", "--disable-background-networking",
        f"--remote-debugging-port={port}", "--remote-allow-origins=*",
        f"--user-data-dir={profile}", "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws_url = None
    for _ in range(80):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=1) as r:
                for t in json.loads(r.read()):
                    if t.get("type") == "page":
                        ws_url = t["webSocketDebuggerUrl"]
                        break
            if ws_url:
                break
        except Exception:
            pass
        time.sleep(0.15)
    if not ws_url:
        proc.kill()
        sys.exit("Chrome DevTools 没起来")

    ws = websocket.create_connection(ws_url, timeout=60)
    cdp = CDP(ws)
    try:
        cdp.call("Page.enable")
        cdp.call("Emulation.setDeviceMetricsOverride", width=args.width, height=args.height,
                 deviceScaleFactor=args.dsf, mobile=args.mobile)
        if args.mobile:
            cdp.call("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)
        cdp.call("Page.navigate", url=to_url(args.target))

        for _ in range(200):
            if cdp.eval("document.readyState") == "complete":
                break
            time.sleep(0.1)
        cdp.eval("document.fonts ? document.fonts.ready.then(()=>1) : 1", await_promise=True)
        time.sleep(args.settle)

        # 让懒入场动画全部落定（直接关掉 transition，避免截到半透明）
        cdp.eval("document.querySelectorAll('.rv').forEach(function(e){"
                 "e.style.transition='none'; e.classList.add('in');}); 1")
        time.sleep(args.settle)

        if args.at:
            sel, _, frac = args.at.partition("@")
            frac = float(frac or 0)
            js = (
                "(function(){document.documentElement.style.scrollBehavior='auto';"
                "var el=document.querySelector(%r);if(!el)return 'no-el';"
                "var top=el.getBoundingClientRect().top+window.scrollY;"
                "var h=el.offsetHeight-window.innerHeight;"
                "window.scrollTo(0, top+Math.max(0,h)*%f);return window.scrollY;})()"
            ) % (sel, frac)
            print("SCROLL ->", cdp.eval(js))
            time.sleep(args.settle)
        elif args.scroll is not None:
            print("SCROLL ->", cdp.eval(f"document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,{args.scroll}); window.scrollY"))
            time.sleep(args.settle)

        if args.js:
            print("EVAL:", cdp.eval(args.js))

        full_h = cdp.eval("Math.max(document.documentElement.scrollHeight, document.body.scrollHeight,"
                          " document.documentElement.offsetHeight)")
        scroll_w = cdp.eval("document.documentElement.scrollWidth")
        params = {"format": "png", "captureBeyondViewport": not args.viewport_only}
        if not args.viewport_only:
            params["clip"] = {"x": 0, "y": 0, "width": args.width,
                              "height": max(int(full_h), args.height), "scale": 1}
        data = cdp.call("Page.captureScreenshot", **params)["data"]
        out = pathlib.Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(data))
        print(f"OK {out} {args.width}x{int(full_h)} dsf={args.dsf} mobile={args.mobile} "
              f"scrollWidth={scroll_w} (viewport {args.width})")
        if scroll_w and scroll_w > args.width + 1:
            print(f"  !! 横向溢出 {scroll_w - args.width}px")
    finally:
        try:
            ws.close()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
