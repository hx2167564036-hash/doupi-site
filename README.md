# doupi-site

个人站点 [doupi123.top](https://doupi123.top) 的主题与工具：一个 Halo 2.x 主题（`theme-doupi`），
加上把 492 篇每日记录整理成「档案」的那套脚本。

## 这不是一个普通博客

站点的主线是 **一份持续了 492 天的个人档案**：每天一篇记录（同时导出 PDF 存档）、课程与课件索引、
项目与能力清单。所以主题的第一屏不是文章列表，而是一张「档案卡」，往下依次是项目、能力、课程、
资料柜、记录、视频。

![首页](https://cdn.jsdelivr.net/gh/hx2167564036-hash/doupi-site@main/docs/shot-home.png)

<p align="center"><i>首屏不是文章列表，而是一张「档案卡」：492 篇记录、476 天有字、3,046 张图，天气与时间实时。</i></p>

### 另外两个二级页与滚动区

| 课程 | 记录 |
| --- | --- |
| ![课程页](https://cdn.jsdelivr.net/gh/hx2167564036-hash/doupi-site@main/docs/shot-courses.png) | ![记录](https://cdn.jsdelivr.net/gh/hx2167564036-hash/doupi-site@main/docs/shot-journal.png) |
| 5 个学期 / 57 门课 / 163 条章节 / 课件下载 | 数字随滚动 0→492，热力图逐列点亮 |

| 时间轴 |
| --- |
| ![时间轴](https://cdn.jsdelivr.net/gh/hx2167564036-hash/doupi-site@main/docs/shot-daily.png) |
| 一天一行，断更处插「留白 N 天」分隔 |

## 结构

```
theme-doupi/          Halo 2.x 主题（可直接打包上传）
  theme.yaml          customTemplates: page = default / daily / courses
  templates/          index / page / post / archives / categories / tags / error
  assets/css|js|data  样式、交互脚本、构建期生成的静态数据
probe/                运维脚本（截图、部署、数据生成、发布）
notes/                设计过程记录（每一轮为什么这么改）
```

## 几个技术点

- **图片与主题资源**：Halo 对自制主题的 `/themes/<name>/assets/*` 会 404，所以 `probe/serve_assets.py`
  把 assets 同步到宿主机目录，由 openresty 用 `location ^~ /themes/theme-doupi/assets/` 直接供文件。
- **活数据**：首页的数字（篇数 / 有字的天 / 留白天 / 图片数）不是写死的，`assets/js/live.js` 通过
  公开内容 API 拉全部文章后现算，带 30 分钟 sessionStorage 缓存。
- **滚动动效**：`assets/js/home.js` 用 IntersectionObserver + `requestAnimationFrame` 做遮罩上浮、
  逐字点亮、以及记录区 280vh 的滚动驱动计数器；`prefers-reduced-motion` 下全部降级为静态。
- **两个二级页**：`/daily`（按天的时间轴，含 76 周热力条与「留白 N 天」）与 `/courses`
  （5 个学期 / 57 门课 / 章节结构 / 课件下载）。都由页面 slug 分流到不同模板。

## 部署

```bash
python probe/deploy_theme.py upload      # 模板上传到服务器 themes/ 目录
python probe/serve_assets.py upload      # CSS/JS/图片同步到静态目录
python probe/activate_theme.py restart   # 改模板后必须重启 Halo（不支持热加载）
```

服务器口令只从环境变量读，仓库里没有任何密码。

## 许可

主题代码 MIT；`notes/` 里的文字与站点截图归作者所有。

> 截图走 jsDelivr CDN（国内可直连）。若仍加载不出来，仓库里的 `docs/` 目录有同样的原文件。
