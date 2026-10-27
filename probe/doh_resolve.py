"""用阿里 DoH 取真实 IP（本机 DNS 被 fake-ip 污染，别信 getaddrinfo）。"""
import json
import sys
import ssl
import urllib.request

DOH = "https://dns.alidns.com/resolve?name={name}&type=A"


def resolve(name):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(DOH.format(name=name),
                                 headers={"accept": "application/dns-json"})
    with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
        data = json.loads(r.read().decode())
    return [a["data"] for a in data.get("Answer", []) if a.get("type") == 1]


if __name__ == "__main__":
    for n in (sys.argv[1:] or ["doupi123.top", "www.doupi123.top"]):
        print(n, "->", ", ".join(resolve(n)) or "(无 A 记录)")
