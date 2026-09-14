# K0 交付与回传

## 阶段五文字交付

当前版本固定输出：

1. **当前方向结论**：`优先进入`、`有条件进入`、`调整方向`、`暂停或停止` 之一。
2. **判断依据**：`opportunity_window`、`alternative_matrix`、`ecosystem_position_hypothesis`，以及 `[已确认]`、`[假设]`、`[缺口]`。
3. **探索对象与情境**：按业务类型输出 `priority_exploration_target`、`trigger_scene_hypothesis` 和角色边界。
4. **候选方向取舍**：默认 2 至 3 个候选、一个优先方向，以及不选方向和理由。
5. **证据行动**：机会证据卡、替代与生态卡、K1 信号卡三张按依赖排序的行动卡。
6. **30 天决策闭环**：30 天目标、前两周证据冲刺、后两周决策分支和 `triggered_stop_line`。
7. **K0 回传证据包**：保持 `action_stage=K0`，列明 `recommended_review`。

正文、行动卡、回传包和 SVG 图文使用同一组事实。

完整行动报告在画布前先显示一个 `consultant_insight` 对象，且只允许一个主视角：

- `contrarian`：为什么现在值得进入。
- `do_not_do`：本轮明确排除。
- `reversal_evidence`：什么新证据会改变当前判断。

三个字段都必须以 `[已确认]`、`[假设]` 或 `[缺口]` 开头。旧版输入缺少 `consultant_insight` 时，渲染器分别复用 `direction_judgment`、首项 `exclusions` 和首项 `stop_line` 形成兼容卡片，不改变原有方向判断。

## 默认 SVG 交付合同

完整交付默认把 UTF-8 JSON 传给 `scripts/render_k0_opportunity_canvas.py` 输出 K0 HTML 行动报告，报告内嵌 1600×1100 方向机会画布；单独画布可输出 SVG。以绝对路径显示产物。

输入必须包含 `title`、`stage`、`decision`、带证据标签的 `direction_judgment`，以及六个且仅六个 sections：`window`、`alternatives`、`target`、`ecosystem_position`、`direction_choice`、`evidence`。每条 section 内容都以 `[已确认]`、`[假设]` 或 `[缺口]` 开头；新版 HTML 可传入三字段 `consultant_insight`；`evidence_sprint` 恰好 3 项；`exclusions` 和 `stop_line` 均为非空字符串数组。

只有环境不能生成或显示 SVG 时，才降级为紧凑 Markdown 画布并说明原因。降级不能删除证据标签、三步证据冲刺、明确不做或停止线。

## 完整回传证据包

逐项回传 `scope`、`context_stage`、`action_stage=K0`、`business_type`、`decision`、`direction_judgment`、`priority_direction`、`rejected_directions`、`priority_exploration_target`、`trigger_scene_hypothesis`、`current_alternatives`、`ecosystem_position_hypothesis`、`confirmed_facts`、`working_assumptions`、`evidence_gaps`、`completed_actions`、`new_behavior_signals`、`triggered_stop_line` 和 `recommended_review`。

`recommended_review` 只能建议诊断层继续 K0、调整、停止或复核 K1；K0 Skill 不自行修改阶段。

每项新证据必须可追溯到用户回答、公开来源或实际验证材料。画布完成、内部批准和行动计划本身不算客户证据；未知字段保持 `[缺口]`，不得用建议内容冒充已完成行动。
