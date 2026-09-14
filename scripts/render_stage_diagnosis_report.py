#!/usr/bin/env python3
"""Render one evidence-bounded business-stage diagnosis as static HTML."""

from __future__ import annotations

import argparse
import json
import re
import sys
from html import escape
from pathlib import Path
from typing import Any


UNKNOWN = "待验证"
STAGE_HELP = (
    ("K0", "避免押错方向", "判断机会是否值得进入"),
    ("K1", "避免服务错客户", "锁定会在具体场景中行动的客户"),
    ("K2", "避免做大后无人采用", "验证最小价值与真实结果"),
    ("K3", "找到可重复增长", "验证同一增长单元能否重复"),
    ("K4", "改善利润与交付效率", "找到最先限制放大的经营瓶颈"),
)
ROUTES = {
    "K0": "define-market-opportunity",
    "K1": "validate-customer-demand",
    "K2": "design-value-and-launch",
    "K3": "build-repeatable-growth",
    "K4": "optimize-business-model-and-resources",
    "S5": "scale-with-control",
    "S6": "manage-business-tradeoffs",
    "S7": "guide-business-transition",
}
NEXT_STAGES = {
    "K0": "K1",
    "K1": "K2",
    "K2": "K3",
    "K3": "K4",
    "S5": "S6",
    "S6": "S7",
}
SCOPE_FIELDS = (
    ("product_service", "产品／服务"),
    ("region", "国家／地区"),
    ("channel_operator", "实际渠道／运营主体"),
    ("revenue_owner", "收入归属"),
    ("customer_data_owner", "客户数据持有方"),
    ("fulfillment_owner", "交付／售后责任"),
)


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _normalize_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return [UNKNOWN]
    items = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return items or [UNKNOWN]


def _normalize_scope_boundary(payload: dict[str, Any]) -> dict[str, str]:
    stage_payload = payload.get("stage_payload")
    if not isinstance(stage_payload, dict):
        stage_payload = {}
    boundary = stage_payload.get("scope_boundary")
    if not isinstance(boundary, dict):
        boundary = {}
    return {
        key: value.strip() if isinstance(value, str) and value.strip() else UNKNOWN
        for key, _ in SCOPE_FIELDS
        for value in (boundary.get(key),)
    }


def _normalize_stage_diagnosis(
    stage_payload: dict[str, Any], action_stage: str, decision: str, recommended_review: str
) -> dict[str, Any]:
    diagnosis = stage_payload.get("stage_diagnosis")
    if not isinstance(diagnosis, dict):
        raise ValueError("stage_payload.stage_diagnosis is required")

    def text_value(key: str, fallback: str) -> str:
        value = diagnosis.get(key)
        return value.strip() if isinstance(value, str) and value.strip() else fallback

    questions = []
    raw_questions = diagnosis.get("questions")
    if isinstance(raw_questions, list):
        for item in raw_questions[:5]:
            if not isinstance(item, dict):
                continue
            question = item.get("question")
            if not isinstance(question, str) or not question.strip():
                continue
            answer = item.get("current_answer")
            status = item.get("evidence_status")
            questions.append(
                {
                    "question": question.strip(),
                    "current_answer": answer.strip()
                    if isinstance(answer, str) and answer.strip()
                    else UNKNOWN,
                    "evidence_status": status.strip()
                    if isinstance(status, str) and status.strip()
                    else "证据缺口",
                }
            )
    if not questions:
        raise ValueError("stage_payload.stage_diagnosis.questions is required")
    return {
        "title": text_value("title", f"{action_stage} 阶段诊断"),
        "why_this_stage": text_value("why_this_stage", decision),
        "current_decision": text_value("current_decision", decision),
        "questions": questions,
        "advance_when": text_value("advance_when", recommended_review),
    }


def _list_html(items: list[str]) -> str:
    return "".join(f"<li>{escape(item)}</li>" for item in items)


def _attachment_html(value: Any) -> str:
    error = "stage_attachment must reference one local HTML action report"
    if not isinstance(value, dict):
        raise ValueError(error)
    label = value.get("label")
    href = value.get("href")
    if not isinstance(label, str) or not label.strip():
        label = "阶段附件"
    if not isinstance(href, str) or not href.strip():
        raise ValueError(error)
    href = href.strip()
    if (
        not re.fullmatch(r"[^/%\\?#:]+\.html", href, flags=re.IGNORECASE)
        or Path(href).name != href
        or ".." in Path(href).parts
    ):
        raise ValueError(error)
    return f'<a class="attachment" href="{escape(href, quote=True)}">{escape(label.strip())}</a>'


def render(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    for key in (
        "schema_version",
        "scope",
        "context_stage",
        "action_stage",
        "decision",
        "business_type",
        "work_mode",
        "target_30d",
        "recommended_review",
    ):
        _require_text(payload, key)

    action_stage = _require_text(payload, "action_stage")
    context_stage = _require_text(payload, "context_stage")
    stage_payload = payload.get("stage_payload")
    if not isinstance(stage_payload, dict):
        stage_payload = {}
    confirmed = _normalize_list(payload.get("confirmed_facts"))
    assumptions = _normalize_list(payload.get("working_assumptions"))
    gaps = _normalize_list(payload.get("evidence_gaps"))
    refs = _normalize_list(payload.get("evidence_refs")) if "evidence_refs" in payload else []
    scope_boundary = _normalize_scope_boundary(payload)
    route = ROUTES.get(action_stage, "不调用 K0—S7 行动 Skill")
    next_stage = NEXT_STAGES.get(action_stage, "下一阶段")
    evidence_gate_label = (
        "形成明确经营取舍的证据条件"
        if action_stage == "S6"
        else f"进入 {next_stage} 的证据条件"
    )
    if action_stage == "S7":
        evidence_gate_label = "转型方向成立的证据条件"
    stage_diagnosis = _normalize_stage_diagnosis(
        stage_payload,
        action_stage,
        _require_text(payload, "decision"),
        _require_text(payload, "recommended_review"),
    )
    stop_line = stage_payload.get("stop_line")
    if not isinstance(stop_line, str) or not stop_line.strip():
        stop_line = UNKNOWN

    stage_cards = "".join(
        '<div class="stage{}" data-stage-help="{}"><strong>{} · {}</strong><span>{}</span></div>'.format(
            " active" if code in {action_stage, context_stage} else "",
            escape(code, quote=True),
            escape(code),
            escape(outcome),
            escape(task),
        )
        for code, outcome, task in STAGE_HELP
    )
    scope_rows = "".join(
        f"<tr><th>{escape(label)}</th><td>{escape(scope_boundary[key])}</td></tr>"
        for key, label in SCOPE_FIELDS
    )
    refs_html = (
        f'<div class="evidence refs"><h3>证据索引</h3><ul>{_list_html(refs)}</ul></div>'
        if refs
        else ""
    )
    question_rows = "".join(
        "<tr><th>{}</th><td>{}</td><td><span class=\"status\">{}</span></td></tr>".format(
            escape(item["question"]),
            escape(item["current_answer"]),
            escape(item["evidence_status"]),
        )
        for item in stage_diagnosis["questions"]
    )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BMI 商业阶段诊断</title>
<style>
:root{{--navy:#102a43;--blue:#2457a6;--ink:#243b53;--muted:#627d98;--line:#d9e2ec;--paper:#f5f7fa;--white:#fff;--fact:#e8f5ee;--hyp:#fff7df;--gap:#fdecec}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}} main{{max-width:1120px;margin:auto;padding:36px 24px 64px}} header{{background:var(--navy);color:var(--white);padding:30px;border-radius:18px}} header p{{margin:8px 0 0;color:#d9eaf7}} section{{margin-top:20px;background:var(--white);border:1px solid var(--line);border-radius:16px;padding:22px}} h1,h2,h3,p{{overflow-wrap:anywhere}} h1{{margin:0;font-size:30px}} h2{{margin:0 0 14px;color:var(--navy);font-size:20px}} h3{{margin:0 0 8px;font-size:15px}} .verdict{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} .callout{{padding:16px;border-left:5px solid var(--blue);background:#eef4fb;border-radius:8px}} .stages{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}} .stage{{border:1px solid var(--line);border-radius:10px;padding:12px;display:grid;gap:4px}} .stage span,.muted{{color:var(--muted)}} .stage.active{{border:2px solid var(--blue);background:#eef4fb}} table{{width:100%;border-collapse:collapse}} th,td{{padding:10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}} th{{width:30%;color:var(--navy)}} .evidence-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}} .evidence{{padding:15px;border-radius:10px}} .fact{{background:var(--fact)}} .hyp{{background:var(--hyp)}} .gap{{background:var(--gap)}} ul{{margin:6px 0 0;padding-left:20px}} .route{{display:flex;align-items:center;gap:12px;flex-wrap:wrap}} .node{{padding:12px 16px;border:1px solid var(--line);border-radius:999px;background:#f8fafc}} .arrow{{font-weight:700;color:var(--blue)}} .loop{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}} .loop article{{border-top:4px solid var(--blue);padding:12px;background:#f8fafc}} .attachment{{display:inline-block;color:var(--blue);font-weight:650}}
.stage-summary{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}} .stage-summary article{{padding:14px;background:#f8fafc;border-radius:10px}} .questions th{{width:34%}} .questions td:last-child{{width:16%}} .status{{display:inline-block;padding:2px 8px;border-radius:999px;background:#eef4fb;color:var(--blue);white-space:nowrap}} .advance{{margin-top:14px;padding:14px;border-left:4px solid var(--blue);background:var(--fact)}}
@media(max-width:600px){{main{{padding:16px 12px 36px}} header,section{{padding:18px}} h1{{font-size:24px}} .verdict,.evidence-grid,.loop,.stage-summary{{grid-template-columns:1fr}} .stages{{grid-template-columns:1fr 1fr}} th,td{{display:block;width:100%}} th{{border-bottom:0;padding-bottom:2px}} td{{padding-top:2px}} .questions td:last-child{{width:100%}}}}
@media print{{body{{background:#fff}} main{{max-width:none;padding:0}} header,section{{break-inside:avoid;box-shadow:none}} a{{color:inherit;text-decoration:none}}}}
</style>
</head>
<body><main data-report="stage-diagnosis">
<header><h1>BMI 商业阶段诊断</h1><p>{escape(_require_text(payload, "scope"))}</p></header>
<section data-section="verdict"><h2>核心判断</h2><div class="verdict"><div class="callout"><strong>{escape(context_stage)} 背景 × {escape(action_stage)} 行动</strong><p>{escape(_require_text(payload, "decision"))}</p></div><div><h3>诊断层复核建议</h3><p>{escape(_require_text(payload, "recommended_review"))}</p><p class="muted">这是可纠正判断，不是经营结果保证。</p></div></div></section>
<section data-section="stage-matrix"><h2>K0–K4 如何帮助业务</h2><p class="muted">不是五套方法一起做，而是先判断当前最需要跨过哪一关。</p><div class="stages">{stage_cards}</div></section>
<section data-section="current-stage-diagnosis"><h2>当前阶段诊断：{escape(stage_diagnosis["title"])}</h2><div class="stage-summary"><article><h3>仍处于 {escape(action_stage)} 的原因</h3><p>{escape(stage_diagnosis["why_this_stage"])}</p></article><article><h3>本阶段唯一决策</h3><p>{escape(stage_diagnosis["current_decision"])}</p></article></div><table class="questions"><thead><tr><th>本阶段要回答的问题</th><th>当前答案</th><th>证据状态</th></tr></thead><tbody>{question_rows}</tbody></table><div class="advance"><strong>{escape(evidence_gate_label)}</strong><p>{escape(stage_diagnosis["advance_when"])}</p></div></section>
<section data-section="scope-boundary"><h2>业务范围边界</h2><table>{scope_rows}</table></section>
<section data-section="evidence-boundary"><h2>证据边界</h2><div class="evidence-grid"><div class="evidence fact"><h3>已确认事实</h3><ul>{_list_html(confirmed)}</ul></div><div class="evidence hyp"><h3>工作假设</h3><ul>{_list_html(assumptions)}</ul></div><div class="evidence gap"><h3>证据缺口</h3><ul>{_list_html(gaps)}</ul></div>{refs_html}</div></section>
<section data-section="single-route"><h2>本轮单一路由</h2><div class="route"><span class="node">advise-business-stage</span><span class="arrow">→</span><span class="node">{escape(route)}</span><span class="arrow">→</span><span class="node">诊断层复核</span></div><p class="muted">每轮最多启用一个行动 Skill；行动 Skill 不互调，也不修改阶段。</p></section>
<section data-section="evidence-loop"><h2>30 天证据闭环</h2><div class="loop"><article><h3>改变目标</h3><p>{escape(_require_text(payload, "target_30d"))}</p></article><article><h3>回传判断</h3><p>{escape(_require_text(payload, "recommended_review"))}</p></article><article><h3>停止／改判线</h3><p>{escape(stop_line.strip())}</p></article></div></section>
<section data-section="stage-attachment"><h2>阶段附件</h2>{_attachment_html(payload.get("stage_attachment"))}</section>
</main></body></html>
"""


def _fallback_html(message: str) -> str:
    safe = escape(message)
    return (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        "<title>BMI 商业阶段诊断（降级）</title></head><body>"
        f"<h1>诊断报告未能生成</h1><p>原因：{safe}</p>"
        "<p>这是降级提示页；完整判断以对话文本为准。</p></body></html>"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(render(payload), encoding="utf-8")
    except Exception as exc:
        sys.stderr.write(f"render failed: {exc}\n")
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(_fallback_html(str(exc)), encoding="utf-8")
        except Exception:
            pass
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
