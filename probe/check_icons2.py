"""按真实 URL（/themes/theme-doupi/assets/...）检查图标与 manifest，并回显 <head> 里的图标标签。"""
import sys

sys.path.insert(0, "probe")
from deploy_theme import ssh_client  # noqa: E402

c = ssh_client()


def run(cmd, timeout=60):
    _, o, e = c.exec_command(cmd, timeout=timeout)
    return o.read().decode("utf-8", "replace")


R = "--resolve doupi123.top:443:127.0.0.1"
BASE = "https://doupi123.top/themes/theme-doupi/assets"

for p in ["/img/favicon.ico", "/img/favicon-32.png", "/img/apple-touch-icon.png",
          "/img/favicon-192.png", "/img/icon-512.png", "/site.webmanifest"]:
    print(run(f"curl -sk -o /dev/null -w '{p:28s} %{{http_code}}  %{{content_type}}  %{{size_download}}B\\n' "
              f"{R} {BASE}{p}").strip())

html = run(f"curl -sk -A 'Mozilla/5.0' {R} https://doupi123.top/ | head -c 900")
print("\n---- head ----")
print(html)
c.close()
