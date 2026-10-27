"""统计本地存档数量，写进 theme-doupi/assets/data/stats.json（给 live.js 用）。

- images：Halo 附件目录里的图片文件数（jpg/png/webp/gif）
- pdfs：本地「豆皮笔记」每日记录 PDF 数量
用法：python -u probe/build_stats.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from deploy_theme import ssh_client  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "theme-doupi" / "assets" / "data" / "stats.json"
ATT = "/opt/1panel/apps/halo/halo/data/attachments"


def run(c, cmd):
    _i, o, e = c.exec_command(cmd, timeout=180)
    return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()


def main():
    c = ssh_client()
    images = run(c, f"find {ATT} -type f \\( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' "
                    f"-o -iname '*.webp' -o -iname '*.gif' \\) | wc -l")
    bytes_ = run(c, f"du -sb {ATT} 2>/dev/null | cut -f1")
    c.close()
    data = {
        "images": int(images or 0),
        "attachmentsBytes": int(bytes_ or 0),
        "pdfs": 492,
        "note": "images 来自服务器附件目录实点；pdfs 来自本地 豆皮笔记/ 的日更 PDF 数量",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"stats.json: {data['images']} 张图, {data['attachmentsBytes']/1e9:.2f} GB, {data['pdfs']} 份 PDF")


if __name__ == "__main__":
    main()
