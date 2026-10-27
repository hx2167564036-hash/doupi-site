"""首屏档案卡接真天气：地点改杭州·拱墅，天气/时间由 weather.js 现取。

- 模板：两行改带 data-* 的 span，并加载 weather.js；
- serve_assets.py 白名单需要包含 .json（早已加），weather.js 是 .js 会自动传。
"""
import pathlib

root = pathlib.Path(__file__).resolve().parent.parent
tpl = root / "theme-doupi/templates/index.html"
s = tpl.read_text(encoding="utf-8")

old = """        <div><dt>现在</dt><dd>北京 · 海淀</dd></div>
        <div><dt>天气</dt><dd>阴 14°C · 15:10</dd></div>"""
new = """        <div><dt>现在</dt><dd><span data-city>杭州 · 拱墅</span></dd></div>
        <div><dt>天气</dt><dd><span data-weather>— · --°C</span> · <span data-clock>--:--</span></dd></div>"""
if old not in s:
    raise SystemExit("档案卡天气锚点没匹配到")
s = s.replace(old, new, 1)

# 载入 weather.js（放在 live.js 之前，互不依赖）
if 'assets/js/weather.js' not in s:
    s = s.replace('<script th:src="@{/assets/js/live.js}"></script>',
                  '<script th:src="@{/assets/js/weather.js}"></script>\n'
                  '<script th:src="@{/assets/js/live.js}"></script>', 1)
    if 'assets/js/weather.js' not in s:   # 没有 live.js 的写法就退回 body 末尾
        s = s.replace('</body>', '<script th:src="@{/assets/js/weather.js}"></script>\n</body>', 1)

tpl.write_text(s, encoding="utf-8")
print("模板已更新；weather.js 已挂:", 'assets/js/weather.js' in s)

# 页脚也挂一份（可选，保持时间一致）：先只做首屏
