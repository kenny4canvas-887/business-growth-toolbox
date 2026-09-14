#!/usr/bin/env python3
"""Render a deterministic, evidence-bounded S6 business trade-off report."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_METRIC_FIELDS = {
    "scope",
    "period",
    "currency",
    "numerator",
    "denominator",
    "source",
    "evidence_status",
}

ALLOWED_EVIDENCE_STATUS = {"确认事实", "工作假设", "证据缺口", "数据不可得"}
CALCULABLE_EVIDENCE_STATUS = {"确认事实", "工作假设"}
ALLOWED_REFERENCE_KINDS = {"公开同业参照", "教学算例"}
REFERENCE_FIELDS = (
    "kind",
    "title",
    "observation",
    "source",
    "comparability",
    "lesson",
)
FINANCIAL_METRIC_ERROR = (
    "financial metric requires scope, period, currency, numerator, denominator, "
    "source and confirmed or assumed evidence status"
)
PLACEHOLDER_DENOMINATOR_ERROR = (
    "financial metric requires a substantive denominator; "
    "report absolute amounts as evidence signals when no denominator applies"
)

FINANCIAL_STATEMENT_FIELDS = (
    "income_statement",
    "balance_sheet",
    "cash_flow_statement",
    "reconciliation_gap",
)

MANAGEMENT_CONSTRAINT_FIELDS = (
    "constraints",
    "counterevidence",
    "completion_signal",
    "recommended_review",
)

EVIDENCE_CLASSES = (
    ("customer_value_signals", "客户价值"),
    ("profit_quality", "利润质量"),
    ("working_capital", "营运资金"),
    ("return_metrics", "资本回报"),
    ("break_even", "盈亏平衡"),
)

COMPARISON_FIELDS = (
    ("customer_value", "客户价值"),
    ("profit_quality", "利润质量"),
    ("working_capital", "营运资金"),
    ("capital_return", "资本回报"),
    ("break_even", "盈亏平衡"),
)

STATUS_CLASS = {
    "确认事实": "confirmed",
    "工作假设": "assumption",
    "证据缺口": "gap",
    "数据不可得": "unavailable",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 JSON 渲染 S6 经营取舍报告")
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 JSON 输入")
    parser.add_argument("--output", required=True, type=Path, help="HTML 输出")
    return parser.parse_args()


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _is_placeholder_denominator(value: str) -> bool:
    normalized = re.sub(r"[\s（）()/_-]", "", value).casefold()
    return (
        not normalized
        or normalized in {"na", "无", "notapplicable"}
        or normalized.startswith("不适用")
    )


def _safe_html_href(payload: dict[str, Any]) -> str:
    href = payload.get("diagnosis_report_href")
    if not isinstance(href, str) or not href.strip():
        raise ValueError(
            "diagnosis_report_href must reference one local HTML report"
        )
    href = href.strip()
    if (
        not re.fullmatch(r"[^/%\\?#:]+\.html", href, flags=re.IGNORECASE)
        or Path(href).name != href
        or ".." in Path(href).parts
    ):
        raise ValueError(
            "diagnosis_report_href must reference one local HTML report"
        )
    return href


def _normalize_item(item: Any, label: str) -> dict[str, str]:
    if not isinstance(item, dict):
        raise ValueError(f"{label} must be an object")
    if "value" in item:
        required = REQUIRED_METRIC_FIELDS | {"metric", "value"}
        if (
            not required.issubset(item)
            or not isinstance(item.get("evidence_status"), str)
            or item["evidence_status"] not in CALCULABLE_EVIDENCE_STATUS
            or any(
                not isinstance(item.get(field), str) or not item[field].strip()
                for field in required
            )
        ):
            raise ValueError(FINANCIAL_METRIC_ERROR)
        if _is_placeholder_denominator(item["denominator"]):
            raise ValueError(PLACEHOLDER_DENOMINATOR_ERROR)
    status = item.get("evidence_status")
    if status not in ALLOWED_EVIDENCE_STATUS:
        raise ValueError(f"{label}.evidence_status is invalid")
    if not any(
        isinstance(item.get(field), str) and item[field].strip()
        for field in ("metric", "signal")
    ):
        raise ValueError(f"{label} requires metric or signal")
    return {
        key: _require_text(value, f"{label}.{key}")
        for key, value in item.items()
    }


def _require_items(payload: dict[str, Any], key: str) -> list[dict[str, str]]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} must be a non-empty list")
    return [
        _normalize_item(item, f"{key}[{index}]")
        for index, item in enumerate(value)
    ]


def _require_text_object(
    payload: dict[str, Any], key: str, fields: tuple[str, ...]
) -> dict[str, str]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return {
        field: _require_text(value.get(field), f"{key}.{field}")
        for field in fields
    }


def _normalize_comparisons(payload: dict[str, Any]) -> list[dict[str, str]]:
    value = payload.get("comparison_slices")
    required = {"option", "evidence_status"} | {
        field for field, _ in COMPARISON_FIELDS
    }
    if not isinstance(value, list) or not value:
        raise ValueError("comparison_slices must be a non-empty list")
    slices: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict) or not required.issubset(item):
            raise ValueError(f"comparison_slices[{index}] is incomplete")
        normalized = {
            field: _require_text(item[field], f"comparison_slices[{index}].{field}")
            for field in required
        }
        if normalized["evidence_status"] not in ALLOWED_EVIDENCE_STATUS:
            raise ValueError(
                f"comparison_slices[{index}].evidence_status is invalid"
            )
        slices.append(normalized)
    return slices


def _normalize_reference_examples(payload: dict[str, Any]) -> list[dict[str, str]]:
    value = payload.get("reference_examples", [])
    if not isinstance(value, list):
        raise ValueError("reference_examples must be a list")
    examples: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"reference_examples[{index}] must be an object")
        normalized = {
            field: _require_text(item.get(field), f"reference_examples[{index}].{field}")
            for field in REFERENCE_FIELDS
        }
        if normalized["kind"] not in ALLOWED_REFERENCE_KINDS:
            raise ValueError(f"reference_examples[{index}].kind is invalid")
        examples.append(normalized)
    return examples


def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
    data: dict[str, Any] = {
        key: _require_text(payload.get(key), key)
        for key in (
            "title",
            "stage",
            "decision",
            "portfolio_unit",
            "recommendation",
            "validation_30d",
            "stop_line",
        )
    }
    if data["stage"] != "S6":
        raise ValueError("stage must be S6")
    data["comparison_slices"] = _normalize_comparisons(payload)
    for key, _ in EVIDENCE_CLASSES:
        data[key] = _require_items(payload, key)
    data["financial_statements"] = _require_text_object(
        payload, "financial_statements", FINANCIAL_STATEMENT_FIELDS
    )
    data["management_constraints"] = _require_text_object(
        payload, "management_constraints", MANAGEMENT_CONSTRAINT_FIELDS
    )
    data["reference_examples"] = _normalize_reference_examples(payload)
    data["diagnosis_report_href"] = _safe_html_href(payload)
    return data


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _status_badge(status: str) -> str:
    return (
        f'<span class="status status-{STATUS_CLASS[status]}">'
        f'{_escape(status)}</span>'
    )


def _comparison_cards(data: dict[str, Any]) -> str:
    cards: list[str] = []
    for item in data["comparison_slices"]:
        rows = "".join(
            f'<div class="matrix-row"><strong>{label}</strong>'
            f'<span>{_escape(item[field])}</span></div>'
            for field, label in COMPARISON_FIELDS
        )
        cards.append(
            '<article class="matrix-card">'
            f'<header><h3>{_escape(item["option"])}</h3>'
            f'{_status_badge(item["evidence_status"])}</header>{rows}</article>'
        )
    return "".join(cards)


def _metric_value(item: dict[str, str]) -> str:
    return item.get("value", "数据不可得")


def _metric_label(item: dict[str, str], fallback: str = "数据不可得") -> str:
    return item.get("metric", item.get("signal", fallback))


def _finance_bridge(data: dict[str, Any]) -> str:
    profit = data["profit_quality"][0]
    cash = data["working_capital"][0]
    returns = "；".join(
        f'{_metric_label(item, "资本回报")} {_metric_value(item)}'
        for item in data["return_metrics"]
    )
    break_even = data["break_even"][0]
    return f'''<svg viewBox="0 0 1200 330" role="img" aria-labelledby="bridge-title bridge-desc">
<title id="bridge-title">利润—现金—资本回报桥</title>
<desc id="bridge-desc">从利润质量，经由营运资金和资本回报，到盈亏平衡的口径桥。</desc>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#2f6b61"/></marker></defs>
<rect x="20" y="60" width="245" height="190" rx="20" class="bridge-card"/>
<rect x="325" y="60" width="245" height="190" rx="20" class="bridge-card"/>
<rect x="630" y="60" width="245" height="190" rx="20" class="bridge-card"/>
<rect x="935" y="60" width="245" height="190" rx="20" class="bridge-card"/>
<path d="M265 155 H315 M570 155 H620 M875 155 H925" class="bridge-arrow"/>
<text x="142" y="105" text-anchor="middle" class="bridge-heading">利润质量</text>
<text x="142" y="145" text-anchor="middle" class="bridge-value">{_escape(_metric_label(profit))}</text>
<text x="142" y="182" text-anchor="middle" class="bridge-copy">{_escape(_metric_value(profit))}</text>
<text x="447" y="105" text-anchor="middle" class="bridge-heading">营运资金</text>
<text x="447" y="145" text-anchor="middle" class="bridge-value">{_escape(_metric_label(cash))}</text>
<text x="447" y="182" text-anchor="middle" class="bridge-copy">{_escape(_metric_value(cash))}</text>
<text x="752" y="105" text-anchor="middle" class="bridge-heading">资本回报</text>
<foreignObject x="650" y="125" width="205" height="95"><div xmlns="http://www.w3.org/1999/xhtml" class="bridge-html">{_escape(returns)}</div></foreignObject>
<text x="1057" y="105" text-anchor="middle" class="bridge-heading">盈亏平衡</text>
<text x="1057" y="145" text-anchor="middle" class="bridge-value">{_escape(_metric_label(break_even))}</text>
<text x="1057" y="182" text-anchor="middle" class="bridge-copy">{_escape(_metric_value(break_even))}</text>
</svg>'''


def _evidence_card(item: dict[str, str], *, financial: bool) -> str:
    name = item.get("metric", item.get("signal", ""))
    detail_parts = [
        ("口径", item.get("scope")),
        ("期间", item.get("period")),
        ("币种", item.get("currency")),
        ("分子", item.get("numerator")),
        ("分母", item.get("denominator")),
        ("来源", item.get("source")),
        ("证据", item.get("evidence")),
    ]
    details = "".join(
        f'<li><strong>{label}</strong><span>{_escape(value)}</span></li>'
        for label, value in detail_parts
        if value is not None
    )
    value = (
        f'<p class="metric-value">{_escape(_metric_value(item))}</p>'
        if financial
        else ""
    )
    return (
        '<article class="evidence-card">'
        f'<header><h3>{_escape(name)}</h3>{_status_badge(item["evidence_status"])}</header>'
        f'{value}<ul>{details}</ul></article>'
    )


def _evidence_sections(data: dict[str, Any]) -> str:
    sections: list[str] = []
    for key, title in EVIDENCE_CLASSES:
        cards = "".join(
            _evidence_card(item, financial=key != "customer_value_signals")
            for item in data[key]
        )
        sections.append(
            f'<section data-evidence-class="{key}"><h2>{title}</h2>'
            f'<div class="evidence-grid">{cards}</div></section>'
        )
    return "".join(sections)


def _evidence_boundaries(data: dict[str, Any]) -> str:
    groups = {"确认事实": [], "工作假设": [], "证据缺口": []}
    for key, _ in EVIDENCE_CLASSES:
        for item in data[key]:
            status = item["evidence_status"]
            target = "证据缺口" if status == "数据不可得" else status
            name = item.get("metric", item.get("signal", ""))
            evidence = item.get("value", item.get("evidence", "数据不可得"))
            groups[target].append(f"{name}：{evidence}")
    cards = "".join(
        '<article class="boundary-card">'
        f'<h3>{title}</h3><ul>'
        + "".join(f'<li>{_escape(item)}</li>' for item in groups[title])
        + "</ul></article>"
        for title in ("确认事实", "工作假设", "证据缺口")
    )
    return (
        '<section data-section="evidence-boundary"><h2>证据边界</h2>'
        f'<div class="boundary-grid">{cards}</div></section>'
    )


def _reference_examples(data: dict[str, Any]) -> str:
    if not data["reference_examples"]:
        return ""
    cards = "".join(
        '<article class="reference-card">'
        f'<header><h3>{_escape(item["title"])}</h3>'
        f'<span class="reference-kind">{_escape(item["kind"])}</span></header>'
        f'<p>{_escape(item["observation"])}</p><ul>'
        f'<li><strong>来源</strong><span>{_escape(item["source"])}</span></li>'
        f'<li><strong>可比边界</strong><span>{_escape(item["comparability"])}</span></li>'
        f'<li><strong>可借鉴动作</strong><span>{_escape(item["lesson"])}</span></li>'
        '</ul></article>'
        for item in data["reference_examples"]
    )
    return (
        '<section data-section="reference-examples"><h2>同业参照与教学示例</h2>'
        '<p class="reference-boundary">以下内容不代表客户表现，不参与客户指标计算；'
        '只用于解释可比经验、计算口径和补数方向。</p>'
        f'<div class="reference-grid">{cards}</div></section>'
    )


def _governance_sections(data: dict[str, Any]) -> str:
    statement_labels = (
        ("income_statement", "利润表可用范围"),
        ("balance_sheet", "资产负债表可用范围"),
        ("cash_flow_statement", "现金流量表可用范围"),
        ("reconciliation_gap", "勾稽缺口"),
    )
    constraint_labels = (
        ("constraints", "管理约束"),
        ("counterevidence", "反证"),
        ("completion_signal", "完成信号"),
        ("recommended_review", "建议复核"),
    )

    def rows(values: dict[str, str], labels: tuple[tuple[str, str], ...]) -> str:
        return "".join(
            f'<li><strong>{label}</strong><span>{_escape(values[key])}</span></li>'
            for key, label in labels
        )

    return (
        '<section data-section="financial-statements">'
        '<h2>三张报表可用范围与勾稽缺口</h2><ul class="detail-list">'
        f'{rows(data["financial_statements"], statement_labels)}</ul></section>'
        '<section data-section="management-constraints">'
        '<h2>管理约束与复核信号</h2><ul class="detail-list">'
        f'{rows(data["management_constraints"], constraint_labels)}</ul></section>'
    )


def render_html(payload: dict[str, Any]) -> str:
    data = _normalize(payload)
    href = _escape(data["diagnosis_report_href"])
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_escape(data["title"])}</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f2f5f1;color:#17322d;font:15px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}}main{{width:min(100%,1440px);margin:auto;padding:24px}}header,section,footer{{min-width:0}}.hero{{padding:32px;border-radius:24px;background:#17322d;color:#fff}}.eyebrow{{margin:0 0 8px;color:#b8dfd1;font-weight:700}}h1,h2,h3,p{{overflow-wrap:anywhere}}h1{{margin:.1em 0;font-size:clamp(2rem,5vw,3.6rem);line-height:1.08}}h2{{margin:0 0 14px}}h3{{margin:0;font-size:1rem}}.unit{{color:#d5e8e1}}.decision,.recommendation{{margin:16px 0 0;padding:16px 18px;border-left:5px solid #f3c969;background:#24473f;border-radius:10px}}section{{margin:18px 0;padding:20px;background:#fff;border:1px solid #d9e3de;border-radius:20px;overflow:hidden}}.matrix-grid,.reference-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,20rem),1fr));gap:14px}}.matrix-card,.evidence-card,.boundary-card,.reference-card{{min-width:0;border:1px solid #d7e0dc;border-radius:16px;padding:16px;background:#fbfcfb}}.matrix-card>header,.evidence-card>header,.reference-card>header{{display:flex;gap:10px;align-items:flex-start;justify-content:space-between}}.matrix-row{{display:grid;grid-template-columns:minmax(5.5rem,.36fr) minmax(0,1fr);gap:10px;padding:10px 0;border-top:1px solid #e2e9e5}}.matrix-row:first-of-type{{margin-top:12px}}.matrix-row span{{min-width:0;overflow-wrap:anywhere}}.status,.reference-kind{{display:inline-flex;flex:0 0 auto;padding:3px 9px;border-radius:999px;font-size:.78rem;font-weight:800}}.reference-kind{{background:#e8e0f4;color:#593d78}}.reference-boundary{{padding:12px 14px;border-left:4px solid #7b5b99;background:#f5f0fa;border-radius:8px}}.reference-card li{{display:grid;grid-template-columns:5rem minmax(0,1fr);gap:8px;margin:5px 0}}.status-confirmed{{background:#d8efe7;color:#155f51}}.status-assumption{{background:#fff0c9;color:#855c00}}.status-gap{{background:#f8dddd;color:#8a3037}}.status-unavailable{{background:#e7edf2;color:#385063}}.bridge-wrap svg{{display:block;width:100%;height:auto}}.bridge-card{{fill:#edf5f1;stroke:#9dbeb2;stroke-width:2}}.bridge-arrow{{stroke:#2f6b61;stroke-width:5;fill:none;marker-end:url(#arrow)}}.bridge-heading{{font-size:23px;font-weight:800;fill:#17322d}}.bridge-value{{font-size:18px;font-weight:700;fill:#2f6b61}}.bridge-copy{{font-size:17px;fill:#3e5f57}}.bridge-html{{height:100%;display:grid;place-items:center;text-align:center;overflow-wrap:anywhere;font:700 17px/1.45 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;color:#2f6b61}}.evidence-grid,.boundary-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,17rem),1fr));gap:12px}}.metric-value{{font-size:1.5rem;font-weight:800;color:#2f6b61}}ul{{padding-left:20px}}li{{overflow-wrap:anywhere}}.evidence-card li{{display:grid;grid-template-columns:3.2rem minmax(0,1fr);gap:8px;margin:5px 0}}.action-strip{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}.action-strip article{{min-width:0;padding:18px;border-radius:16px;background:#eef5f2}}.action-strip .stop{{background:#f9e7e7}}a{{color:#175f53;font-weight:800}}@media(max-width:700px){{main{{padding:10px}}.hero,section{{padding:16px}}.action-strip{{grid-template-columns:1fr}}.bridge-wrap{{overflow-x:auto}}.bridge-wrap svg{{min-width:700px}}.matrix-row,.reference-card li{{grid-template-columns:1fr}}}}@media print{{body{{background:#fff}}main{{width:100%;padding:0}}section{{break-inside:avoid}}}}
 .detail-list li{{display:grid;grid-template-columns:5.5rem minmax(0,1fr);gap:8px;margin:5px 0}}@media(max-width:700px){{.detail-list li{{grid-template-columns:1fr}}}}
</style></head><body><main data-report="s6-action">
<header class="hero"><p class="eyebrow">S6 成熟期经营取舍</p><h1>{_escape(data["title"])}</h1><p class="unit">经营单元｜{_escape(data["portfolio_unit"])}</p><p class="decision"><strong>核心判断｜</strong>{_escape(data["decision"])}</p><p class="recommendation"><strong>业务建议｜</strong>{_escape(data["recommendation"])}</p></header>
<section data-section="tradeoff-matrix"><h2>经营取舍矩阵</h2><div class="matrix-grid">{_comparison_cards(data)}</div></section>
{_reference_examples(data)}
<section data-section="finance-bridge"><h2>利润—现金—资本回报桥</h2><div class="bridge-wrap">{_finance_bridge(data)}</div></section>
{_governance_sections(data)}
{_evidence_sections(data)}
{_evidence_boundaries(data)}
<section data-section="next-step"><h2>30 天最小证据闭环</h2><div class="action-strip"><article><h3>30 天验证</h3><p>{_escape(data["validation_30d"])}</p></article><article class="stop"><h3>停止线</h3><p>{_escape(data["stop_line"])}</p></article></div></section>
<footer><a href="{href}">返回阶段诊断报告</a></footer>
</main></body></html>'''


def main() -> int:
    args = _parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        artifact = render_html(payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(artifact, encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(str(exc) + "\n")
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\"></head>"
                f"<body><h1>渲染未成功</h1><p>原因：{html.escape(str(exc))}</p>"
                "<p>这是降级提示页；完整判断以对话文本为准。</p></body></html>",
                encoding="utf-8",
            )
        except Exception:
            pass
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
