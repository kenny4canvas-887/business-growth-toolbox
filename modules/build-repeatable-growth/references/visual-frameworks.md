# K3 视觉框架

## 1. 默认四域增长诊断图

每次完成 K3 主路径取舍后，完整交付默认生成并显示一张 K3 HTML 行动报告页面并内嵌 1600×1100 四域图；单独画布可输出 SVG。调用：

```bash
python scripts/render_k3_growth_diagnosis.py --input /绝对路径/k3-growth.json --output /绝对路径/k3-growth.html
```

输入固定包含：`title`、`stage`、`decision`、`growth_unit`、`main_bottleneck`、`main_path`、`lifecycle_judgment`、`domains`、`actions`、`stop_line`、`recommended_review`。其中：

- `lifecycle_judgment` 必须且只能包含 `get`、`keep`、`grow`、`benefit_cost`、`main_break`。图中以“生命周期概览”紧凑显示；这是轻量判断栏，不是完整客户经营画布。
- `domains` 必须且只能包含 `segment`、`channel`、`relationship`、`revenue`；每域包含 `judgment`、`evidence`、`gap`、`action`。
- `actions` 恰好 3 项；每项包含 `title`、`action`、`done`。
- 图文使用同一组事实；图中不引入新的数字、阶段判断或建议。
- 输出后返回 HTML 的绝对路径链接；单独画布才显示 SVG。

生成失败可降级为紧凑 Markdown 框架，按相同字段说明进展，但不算正式报告验收完成。仅预览不可用时保留已验证存在的 HTML 交付并说明未做视觉验收。

## 2. 阶段交接框架

若入口判断要求返回 K1/K2、停止或建议复核 K4，不生成四域增长诊断图，改用下列紧凑 Markdown 表格：

| 已确认事实 | 工作假设 | 证据缺口 | 下一步补证 | 停止线/阶段建议 |
|---|---|---|---|---|
| 只写已发生事实 | 可被证伪的当前解释 | 最可能改变阶段判断的未知项 | 一项最小原始证据动作 | 本阶段不再继续什么，以及建议流向 |

表格只压缩本次交接结论，不代替 K1、K2 或 K4 执行，也不新增角色、数量、指标、阈值或经营判断。表格后仍可补充一个决定性问题，但不得用长问卷延迟初判。

## 3. 现有客户经营画布调用边界

原画布位于：`/Users/kennyleung/Desktop/常讲课程/design canvas/公司画布/中文版 16：9/客户经营画布.jpg`。

- Get、Keep、Grow 是画布核心。
- Benefit、Cost 补充收益与成本观察。
- 只在客户关系或客户经营成为主瓶颈时调用。
- 直接复用原画布，不复制、不重画、不改名，也不把默认四域增长诊断图改造成另一张客户经营画布。
- 默认图中的“生命周期概览”只同步 `lifecycle_judgment` 的轻量结果；它不触发、替换或冒充完整客户经营画布。
- 原画布只补充客户关系域，不能替代客户细分、渠道通路、客户关系和收入扩大四域扫描。
