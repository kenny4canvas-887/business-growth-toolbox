# S7 转型建议（guide-business-transition）

> 这是 BMI 业务增长工具箱的八个阶段模块之一，回答「保留什么、停止什么、哪条新曲线假设值得验证」。
> 前置：只有根 `SKILL.md`（业务体检）已确认 `action_stage=S7` 时，才由它加载本模块。本模块不重新诊断阶段，不自行修改 `action_stage`，不调用其他阶段模块。
> 收口：最小验证方案回传业务体检，复核回到 K0、K1、S6 或保持 S7。

仅在业务体检已确认 `action_stage=S7` 时使用。它帮助旧模式已出现可追溯失效信号的经营单元，判断保留什么资产、停止在哪个失效环节继续加码，以及哪一条新曲线假设值得最小验证。

诊断层拥有阶段判断权；本模块不重新诊断阶段，不得修改 `action_stage`，不得调用其他阶段模块。它不做财务预测、组织重组、裁撤、关停、投资决策或系统迁移。

## 显性专业价值

S7 必须追问：**哪些旧优势还能迁移，哪些已经成为包袱**。缺少会改变转型方向的证据时，先说明为什么不能直接判断，并只问一个决定性问题；不把趋势、口号或集团资源当成新曲线成立。

S7 的顾问论点是：**转型不是追趋势**。先分清可迁移的客户关系、技术、渠道或能力，与只应停止追加的沉没成本；新方向仍需作为假设验证，不能靠旧公司的规模背书。

完整输出和行动 HTML 首屏固定写明：`核心判断`、`关键机制`、`为什么不是另一个常见答案`、`改判证据`。结论要鲜明，证据状态要诚实；不寻常来自机制洞察，不来自冒犯性标签。

## 进入闸门与交接

消费 `schema_version=1.0` 公共交接对象。只有存量经营对象、至少一个已发生的失效信号，及可复用资产或待验证转型假设中的至少一项均可追溯时进入；否则回传“暂缓转型判断，先补证”。

`stage_payload` 只读取：`legacy_business_unit`、`failure_signals`、`reusable_assets`、`transition_hypotheses`、`transition_constraints`、`evidence_gaps`。所有内容明确标为确认事实、工作假设或证据缺口；趋势、内部意图或集团规模不能证明新曲线成立。

仅有新项目、趋势或管理意图时，保持“公司背景 S7 + 当前项目 K0”，由 K0 处理新项目验证；旧模式内仍可修复的成熟组合问题建议复核 S6。

## 轻量交付

只输出保留／停止边界、一个推荐假设、至多一个备选、一个 30 天最小验证和 `recommended_review`。验证必须含完成标志、停止线，以及回到 K0、K1、S6 或保持 S7 的复核条件；不得把未发生的客户行动或付费写成确认事实。

完整交付时，使用 `modules/guide-business-transition/scripts/render_s7_business_transition.py --input INPUT.json --output OUTPUT.html` 生成当前阶段的 HTML 行动报告，再由诊断入口以该文件作为 `stage_attachment` 生成诊断 HTML；两页必须使用安全的本地相对链接互链。只生成这一份 S7 行动报告，不生成其他阶段报告。

需要确定转型选择与验证停止线时读取[转型方法](modules/guide-business-transition/references/methods.md)。需要校准 S7 进入门槛及相邻阶段时读取[评测案例](modules/guide-business-transition/references/evaluation-cases.md)。
