"""诊断：打印候选口令各段的「长度/字符类型」，不输出任何口令原文。"""
import re

MEM = (r"C:\Users\kendle\.qoder-cn\projects"
       r"\C--Users-kendle-Documents-Qoder-2026-09-21-5e6cb6a5"
       r"\memory\reference-wenlv-deploy.md")

TICK = chr(96)
txt = open(MEM, encoding="utf-8").read()
print("文件字节数:", len(txt.encode("utf-8")), " 行数:", txt.count(chr(10)) + 1)
runs = re.findall(TICK + "([^" + TICK + "]+)" + TICK, txt)
print("反引号包裹段数:", len(runs))
for i, r in enumerate(runs[:8]):
    kinds = sorted({("digit" if c.isdigit() else "alpha" if c.isalpha() else "sym") for c in r})
    print(f"  #{i} len={len(r)} kinds={kinds} endswith_bang={r.endswith('!')}")

# 也打印前 16 行里含反引号的「行号 + 每段长度」（不输出内容）
for idx, line in enumerate(txt.split(chr(10))[:16]):
    if TICK in line:
        lens = [len(p) for p in line.split(TICK)]
        print(f"  line#{idx} 段长={lens}")
