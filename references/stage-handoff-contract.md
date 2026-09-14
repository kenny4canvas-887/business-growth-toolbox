# 阶段交接契约

## 用途

诊断 Skill 与一个 K0—S7 行动 Skill 之间只传递一份版本化交接对象。公共事实只保存一次；阶段专属内容放入 `stage_payload`。缺失值写“待验证”，不得为满足字段而补造。

## 公共字段

| 字段 | 含义 |
|---|---|
| `schema_version` | 契约版本；当前为 `1.0` |
| `scope` | 产品/服务 × 国家/地区 × 实际渠道或经营主体 |
| `context_stage` | 公司或存量业务背景阶段；只能为 `K0`—`K4`、`S5`—`S7` 或“待复核”，未知时为待复核；解释写入 `decision` 或 `stage_payload` |
| `action_stage` | 当前项目行动阶段；只由诊断 Skill 设置或修改 |
| `decision` | 本轮唯一经营决策 |
| `business_type` | `to_b`、`to_c`、`mixed` 或 `unknown` |
| `work_mode` | `owner` 或 `internal_consultant` |
| `confirmed_facts` | 可追溯的已发生事实，包含已发生的客户行动 |
| `working_assumptions` | 尚待验证、可被推翻的解释 |
| `evidence_gaps` | 会影响阶段或建议的缺失证据 |
| `target_30d` | 30 天内要改变的可观察状态 |
| `stage_payload` | 当前行动阶段专属字段，不复制公共字段 |
| `recommended_review` | 行动 Skill 返回的保持、回退、停止或建议复核 |

## 最小对象

```yaml
schema_version: "1.0"
scope: "产品/服务 × 国家/地区 × 实际渠道或经营主体"
context_stage: "待复核"
action_stage: "K0-S7"
decision: "本轮唯一经营决策"
business_type: "unknown"
work_mode: "owner"
confirmed_facts: []
working_assumptions: []
evidence_gaps: []
target_30d: "待验证"
stage_payload: {}
recommended_review: "待行动 Skill 回传"
```

## S5 阶段字段

S5 只在 `stage_payload` 中传递 `replication_unit`、`profit_engine`、`proven_results`、`standard_core`、`local_variations`、`target_replication`、`capacity_constraints`、`flywheel_loop` 和 `defensibility_signals`。其中盈利、飞轮和防御性都必须保留证据状态与替代解释，不得由诊断层补造。

## S6 阶段字段

S6 只在 `stage_payload` 中传递 `portfolio_unit`、`comparison_slices`、`customer_value_signals`、`profit_quality`、`working_capital`、`return_metrics`、`break_even`、`financial_statements` 和 `management_constraints`。各字段保留已确认事实、工作假设或证据缺口；缺失数据不补造。行动 Skill 可以回传证据和 `recommended_review`，不得自行修改已确认的 `action_stage`。

## S7 阶段字段

S7 只在 `stage_payload` 中传递 `legacy_business_unit`、`failure_signals`、`reusable_assets`、`transition_hypotheses`、`transition_constraints` 和 `evidence_gaps`。只有旧模式失效或必须重构的已发生证据可进入；趋势、管理意图或集团规模不能替代失效或新曲线成立证据。公司背景为 S7、当前项目仍待验证时，保持 `context_stage=S7` 与 `action_stage=K0`，不得由 S7 抢占 K0。行动 Skill 可以回传证据和 `recommended_review`，不得自行修改已确认的 `action_stage`。

## 交接与回传

1. 诊断 Skill 锁定 `scope` 和 `action_stage`，每轮只选择一个行动 Skill。
2. 行动 Skill 校验入口，只读取公共字段和自己的 `stage_payload`。
3. 行动 Skill 可以追加事实、推翻假设、补充缺口并写入 `recommended_review`，但不得覆盖 `action_stage`，也不得调用其他行动 Skill。
4. 诊断 Skill 合并回传证据后，才决定保持、回退、停止或改判。
5. 如需证据索引，只传脱敏编号；不在对象中嵌入客户名单、合同全文、账号、密钥或私人原始材料。
