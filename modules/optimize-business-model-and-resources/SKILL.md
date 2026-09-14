# K4 提效配资源（optimize-business-model-and-resources）

> 这是 BMI 业务增长工具箱的八个阶段模块之一，回答「哪个收入、成本、交付或资源瓶颈最先限制放大」。
> 前置：只有根 `SKILL.md`（业务体检）已确认 `action_stage=K4` 时，才由它加载本模块。本模块不重新诊断阶段，不自行修改 `action_stage`，不调用其他阶段模块。
> 收口：给出方案后回传业务体检，复核是否进入 S5 或 S7。

## 阶段1目标

先确认是否真正进入 K4，锁定本轮唯一诊断对象，并形成可交接的输入输出契约。只有 `action_stage=K4` 已由业务体检 确认，且用户请求本轮经营分析、完整报告或正式测试时，才使用本模块。

用户明确请求优先于默认流程与展示偏好。以下阶段1至7是内部处理顺序，不是逐步审批点；完整请求在证据允许时连续执行至交付，复用已有字段。每阶段末尾的“不输出”只限制该中间步骤，不禁止后续阶段按契约完成报告。参考资料仅在进入对应步骤时读取，已读取且未变更的不重复加载。发布、部署和全局同步须另获授权。若本模块规则导致暂停或偏离请求，链接具体规则并说明原因。

本模块不重新诊断阶段，不自行修改 `action_stage`。阶段1不填写商业模式画布，阶段1不计算收入成本对比，阶段1不给出资源配置方案。

## 显性专业价值

K4 必须追问：**哪一个约束正在吞掉经营结果**。缺少会改变主约束判断的证据时，先说明为什么不能直接判断，并只问一个决定性问题；不以集团总量、行业均值或臆测财务数字代替经营单元证据。

K4 的顾问论点是：**收入增长可能掩盖经营约束**。必须在收入质量、成本到服务、交付容量与关键资源中找出正在吞掉结果的一个主约束，再决定优化什么和停止什么。

只有某个视角会改变主约束或资源取舍时，才读取[顾问视角](modules/optimize-business-model-and-resources/references/consultant-lenses.md)；每轮最多选择一个。客户增长是否可重复属于 K3，系统复制与飞轮属于 S5，集团级利润、资本配置和完整财务报表诊断属于 S6；K4 不与它们竞争阶段权限。

完整输出保留通用顾问语义：`核心判断`、`关键机制`、`为什么不是另一个常见答案`、`改判证据`。行动 HTML 首屏将其收紧为 `consultant_insight`：`真正吞掉结果的约束`、`本轮明确不优化`、`改判证据`。三项分别对应 `contrarian`、`do_not_do`、`reversal_evidence`，每项必须以 `[已确认]`、`[假设]` 或 `[缺口]` 标记证据状态。结论要鲜明，证据状态要诚实；不寻常来自机制洞察，不来自冒犯性标签。

## 客户可感知的阶段决策闭环

完整输出时，在任何方法名称或画布之前先放置“阶段决策卡”。卡片固定写明：

- 本阶段唯一决策：哪个资源效率瓶颈应先处理。
- 为什么暂不进入相邻阶段：重复增长证据不足时，返回 K3；需求、价值或交付边界被推翻时，返回 K1 或 K2；只有旧模式失效证据成立时才建议诊断层复核 S7。
- 30 天最小证据闭环：只验证一个经营单位中会改变主约束判断的一项收入、成本、交付或资源证据。
- 什么新证据会推翻当前建议：保持事实、假设和缺口分层，不用公司总量、单体报表、行业均值或画布完成度代替可比经营证据。

画布只用于使经营约束和杠杆可扫描，不能替代财务审计、资源配置决定或阶段复核。

## 输入契约

优先消费业务体检 按公共交接契约传入的对象，缺失字段标记“待验证”，不得补造：

- `schema_version`：当前契约版本，固定为 `1.0`。
- `scope`、`context_stage`、`action_stage`、`business_type`
- `confirmed_facts`、`working_assumptions`、`evidence_gaps`
- `target_30d`：本轮 30 天内要形成的最小经营证据闭环。
- `stage_payload`：承载 K4 专属字段，包括 `growth_unit`、`baseline_scope`、`validated_value`、`delivery_boundary`、`repeatable_growth_evidence`、`revenue_sources`、`cost_signals`、`delivery_capacity`、`key_resources` 和 `key_dependencies`。

## K4 准入闸门

1. 当同一 `growth_unit` 尚无可追溯的重复获客、使用、续约、复购、扩展或收入证据时，返回 K3。公司整体规模不能代替当前增长单元证据；品牌、流量、融资、计划或单一大客户也不能单独证明可重复增长。
   增长单元不等于客户群：它也可以是边界稳定的产品线或业务分部。若该单元在连续可比周期已有可追溯的确认收入或使用证据，可将 `entry_decision=进入 K4` 并标记为“有条件准入”，但公开汇总证据只能支持产品线经营比较，不能支持客户级单位经济；单一周期、公司总收入或无法固定边界的数据仍返回 K3。
2. 当已验证价值或最小交付边界失效、频繁变动时，返回 K2；当优先客户、使用场景或需求被新证据推翻时，返回 K1。
3. 只有当重复增长证据已出现，且主要约束转为收入结构、成本结构、交付效率、承接能力、关键人依赖或资源调用时，才进入 K4。
4. 当商业模式与资源承接已有重复证据，当前问题是跨区域、团队或组织复制时，建议复核 S5。
5. 输入不足时，先给出可纠正的准入初判，只补充最多一个决定性问题，不启动长问卷。

## 诊断对象

每轮只固定一个诊断对象：一个可比较的业务单元、产品组合或增长单元。必须记录客户、价值、渠道、客户关系、收入方式及对应时间和业务口径。公司背景可作为上下文，但不得与当前诊断对象混在同一证据结论中。

## 阶段1输出契约

固定输出：

- `entry_decision`：进入 K4 / 返回 K3 / 返回 K2 / 返回 K1 / 停止 / 建议复核 S5。
- `diagnostic_scope`：唯一诊断对象及可比较口径。
- `confirmed_facts`、`working_assumptions`、`evidence_gaps`：分开记录三类证据状态。
- `constraint_signal`：当前是否已出现商业模式、收入成本、交付承接或资源依赖信号。
- `decisive_question`：仅在会改变准入结论时提出，最多一个。
- `entry_stop_line`：触发退回、暂停或停止的已知信号，不编造数字门槛。
- `recommended_review`：交由业务体检 复核的阶段建议。

## 阶段2商业模式诊断

只有 `entry_decision=进入 K4` 时才进入本阶段。沿用用户已有的商业模式画布，以“商业模式画布 + 收入成本对比 + 资源与能力承接”形成一条约束判断链；不要把三者分别做成互不相关的清单。具体按[方法参考](modules/optimize-business-model-and-resources/references/methods.md)执行。

1. 固定阶段1的 `diagnostic_scope`，所有收入、成本、交付和资源证据使用同一增长单元及可比较口径。
2. 以“商业模式画布（K4资源与增长效率优化）”为一个核心方法，检查九个模块之间是否匹配；客户与价值结论继承 K1-K3 已确认结果，不在 K4 重做市场定位。
3. 同步形成轻量收入成本对比和资源与能力承接判断；无同口径数据时只标记方向与证据缺口，不补造利润、效率、回收期或行业基准。
4. 从模式错配、收入成本压力、交付承接、资源能力依赖中确定一个主约束、至多一个次约束，并写明会推翻判断的证据。
5. 若资料不足，先给可纠正初判；只有答案会改变主约束时才追问，每轮最多四个问题。

## 阶段2输出契约

- `business_model_snapshot`：九个模块的已确认事实、工作假设和证据缺口。
- `revenue_cost_judgment`：同口径下的收入机制、主要成本驱动、可比性和当前压力信号。
- `resource_capability_judgment`：关键活动、关键资源、关键伙伴、交付承接、关键人依赖和能力缺口。
- `bottleneck_chain`：客户行为与收入如何经过交付、资源和成本形成当前结果。
- `main_constraint`：本轮唯一主约束；证据不足时明确写“待验证”。
- `secondary_constraint`：最多一个次约束，否则为空。
- `reversal_evidence`：什么新增证据会推翻或改写主约束。
- `selected_method`：固定为 K4 资源与增长效率商业模式画布。
- `supporting_method`：仅当会改变主约束判断时选择一个，否则为空。

本阶段只完成诊断框架和方法取舍，不输出资源配置方案、计算器、行动卡、30 天计划或视觉成品。

## 阶段3收入成本与单位经营口径

只有阶段2已形成 `business_model_snapshot`、`bottleneck_chain` 和待检验的 `main_constraint` 时才进入本阶段。按[单位经营参考](modules/optimize-business-model-and-resources/references/unit-economics.md)锁定唯一经营单位、收入状态、成本层级和计算条件，用可比较数据检验主约束，不把本阶段当作财务审计。

1. 固定 `economic_scope`：一个增长单元、一个经营单位、一个时间范围和一套确认规则；公司总量只能作为背景。
2. 建立 `revenue_bridge`，区分合同额或订单额、已确认收入、开票金额和实际回款，不互相替代。
3. 建立 `cost_stack`，区分直接变动成本、承接与半变动成本、固定与共享成本、获客投入；没有归集规则时保留缺口。
4. 先判断 `data_readiness`，只有分子、分母、周期和定义均可比时才形成 `unit_economics`；否则只输出方向性比较。
5. 用 `comparison_result` 回看阶段2的 `main_constraint`。若结果不支持原判断，更新为工作假设并记录 `reversal_evidence`，不静默改写事实。

## 阶段3输出契约

- `economic_scope`：增长单元、经营单位、客户或合同边界、时间范围、币种及确认规则。
- `data_readiness`：可计算 / 仅可方向判断 / 数据不可得，并说明原因。
- `revenue_bridge`：各收入状态的数值、来源、日期和不可比项。
- `cost_stack`：四层成本及其可追溯、需分摊或待确认状态。
- `unit_economics`：仅列已满足条件的指标、公式口径、结果和限制；不满足条件的指标写“不可计算”。
- `comparison_result`：内部同周期、分群或有来源外部基准的比较结论。
- `calculation_guardrails`：本轮允许计算和禁止推导的边界。
- `economics_stop_line`：混合口径、关键分母缺失或确认规则冲突时暂停计算的条件。

本阶段不输出资源比例、裁撤或招聘结论，不制作行动卡和视觉成品，也不把经营分析结论表述为法定会计意见。

## 阶段4资源与能力约束判断

只有阶段2的 `main_constraint` 已形成、阶段3已输出 `economic_scope`、`data_readiness` 与 `comparison_result` 时才进入本阶段。按[资源约束参考](modules/optimize-business-model-and-resources/references/resource-constraints.md)，在同一经营单位内把交付边界、容量、关键人、流程与伙伴依赖串回主约束和经济结果；没有直接证据时只保留工作假设。

1. 固定 `economic_scope` 与交付边界，列出增长必须经过的关键活动、输入、输出和责任边界。
2. 区分容量不足、关键人依赖、流程与能力缺口、伙伴依赖和资源错配；不把岗位数量、成本金额或主观紧迫感直接当作资源约束。
3. 仅确定一个 `resource_constraint`、最多一个 `secondary_resource_constraint`，并说明其如何连接阶段2 `main_constraint` 与阶段3经济结果。
4. 记录能推翻该判断的 `resource_reversal_evidence`。若需求、价值或单位经营口径本身未成立，按停止线退回对应阶段复核，不静默转为资源问题。
5. 只有一个辅助方法会改变资源约束判断时才填写 `resource_supporting_method`；否则为空。

## 阶段4输出契约

- `delivery_system_snapshot`：同一经营单位内的关键活动、输入、输出、责任与交付边界。
- `capacity_signal`：可用、已用或排队、时效、质量、返工和成本的已确认信号；没有测量时明确缺口。
- `dependency_map`：关键人、关键流程与伙伴的不可替代性、替代路径及证据状态。
- `resource_constraint`：本轮唯一主资源约束；证据不足时明确写“待验证”。
- `secondary_resource_constraint`：最多一个次约束，否则为空。
- `constraint_priority_reason`：主资源约束与 `main_constraint`、`comparison_result` 的可追溯连接。
- `resource_reversal_evidence`：什么新增证据会推翻或改变资源约束。
- `resource_supporting_method`：最多一个会改变判断的辅助方法，否则为空。
- `resource_stop_line`：不能定位资源约束或应退回复核的条件。

本阶段不做人员编制、不设资源比例、不推荐裁撤或招聘、不生成行动卡、资源配置方案、30 天计划或视觉成品。

## 阶段5经营杠杆与方案取舍

只有阶段2至4已经形成同一 `economic_scope` 下的 `main_constraint`、`comparison_result` 和 `resource_constraint` 时才进入本阶段。按[经营杠杆参考](modules/optimize-business-model-and-resources/references/operating-levers.md)，将利润压力先拆回可比较的经营单元，再提出可检验的经营杠杆与取舍；不把公司整体利润、管理意图或单次异常直接当作商业模式失效。

1. 当成熟主业与新业务或新品类共同影响利润时，先输出 `operating_scope_split`，分别记录其收入、成本、资源占用与证据状态；不能拆分时停止在数据补证，不把两者混作同一结论。
2. 用 `profit_pressure_triage` 依次判断增长是否仍成立、压力是否可被同口径收入成本解释、资源约束是否已连接经济结果；每条结论标记事实、假设或缺口。
3. 围绕已确认的主约束和主资源约束，提出最多三个 `operating_levers`；每项必须写明作用机制、前提、主要代价及停止或调整条件，不默认裁撤、降价、压缩研发或关闭新业务。
4. 以 `option_tradeoffs` 比较保留、优化、收缩或新曲线验证等选择；只选一个 `priority_validation` 在 30 天内补足或推翻关键证据，不用行业均值或无依据数字设门槛。
5. `model_rebuild_review` 只能输出“继续 K4 / 建议业务体检 复核 S7 / 证据不足”。只有旧模式失效证据成立时才建议业务体检 复核 S7；本模块不自行判定或写入 S7。

## 阶段5输出契约

- `operating_scope_split`：同一公司内须分开的成熟主业、新业务或新品类，以及各自证据口径。
- `profit_pressure_triage`：增长、收入成本、资源约束与利润压力之间的可追溯判断。
- `operating_levers`：最多三个、均有机制、前提、代价与停止或调整条件的经营杠杆。
- `option_tradeoffs`：主方案与最多两个备选的适用条件和相对取舍。
- `priority_validation`：唯一优先验证、所需数据与 30 天复盘边界。
- `model_rebuild_review`：继续 K4、建议业务体检 复核 S7 或证据不足，以及对应证据。
- `operating_stop_line`：无法分开经营单元、关键口径不可比或前提被推翻时的暂停与复核条件。

本阶段不制定预算、编制、裁撤、涨降价、供应商替换或组织重组方案。

## 阶段6可视化交付

只有阶段2至5字段已经形成、`operating_scope_split` 能区分成熟主业与新业务或新品类，且至少有一个符合证据边界的 `operating_levers` 时才进入本阶段。按[可视化输出规范](modules/optimize-business-model-and-resources/references/visual-frameworks.md)执行，图文使用同一组事实，不另起一套判断。

1. 默认生成并显示一张“K4 经营模型与资源优化图”，不机械重画九宫格，也不默认拆成多张图。
2. 图中固定包含商业模式与经营结果链、成熟主业、新业务或新品类、收入成本判断、资源约束、商业模式重构复核、最多三个经营杠杆、30 天优先验证和停止线。
3. 图内必须保留已确认事实、工作假设和证据缺口的区分；没有可计算数据时只写方向判断，不补造利润、占比、回收期或行业阈值。
4. 完整交付使用 `modules/optimize-business-model-and-resources/scripts/render_k4_operating_model.py` 输出 `.html`，生成 K4 HTML 行动报告并内嵌经营模型图；只需单独画布时仍可输出 `.svg`。以绝对路径显示给用户；若无法生成文件，降级为紧凑 Markdown 框架并说明原因，不声称已生成 HTML。
5. 图表只负责把阶段2至5的结论变得可扫描，不替代文字证据、阶段诊断、财务审计或管理决策。

## 阶段6输出契约

- `visual_artifact`：完整报告为 HTML 的绝对路径；单独画布为 SVG 路径。生成失败时可用 Markdown 说明进展，但正式报告验收仍未完成。仅预览不可用不影响返回已验证存在的 HTML 链接，须说明未做视觉验收。
- `visual_scope`：与 `diagnostic_scope`、`economic_scope` 一致的唯一经营单位和时间口径。
- `visual_evidence_summary`：已确认事实、工作假设、证据缺口的简要计数或标签。
- `visual_stop_line`：沿用 `operating_stop_line`，不得为了图表新增无依据门槛。

本阶段不新增经营结论，不制定预算、编制或组织调整方案，也不自行把 `model_rebuild_review` 改写为 S7 阶段结论。

## 阶段7完工收口

客户任务按下列交付检查收口，不运行整套开发评测。只有迭代或发布验收本模块时才读取[评测案例](modules/optimize-business-model-and-resources/references/evaluation-cases.md)，覆盖 To C、To B、返回 K1、返回 K2、返回 K3、继续 K4、建议复核 S5、建议业务体检 复核 S7、混合经营单元和证据不足；不得把历史评测结果当成本轮客户证据。

1. 准入成立时，交付阶段2至6的同一条证据链；准入不成立时，不生成假装完成 K4 的经营优化图。
2. 返回 K1、K2、K3，或建议复核 S5、S7 时，使用五栏阶段交接框架：当前判断、移交证据、缺失证据、下一步、停止线。
3. 阶段交接只回传新增证据和 `recommended_review`，不自行修改 `action_stage`，不得调用其他阶段模块，不自行写入 S5 或 S7，也不越过业务体检 宣称转型或规模复制成立。
4. 完工只表示结构、代表行为、视觉和回归测试达到本轮合同，不证明真实企业经营结果、利润改善或资源调整已发生。

## 最小示例

若只有“公司收入上升”，但无法说明是否来自同一增长单元的重复客户行为，则 `entry_decision=返回 K3`，不进入成本或资源分析。
