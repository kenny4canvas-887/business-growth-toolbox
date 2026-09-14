#!/usr/bin/env python3
"""Render a deterministic, evidence-bounded S7 transition report."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_EVIDENCE_STATUS = {"确认事实", "工作假设", "证据缺口"}
STATUS_CLASS = {
    "确认事实": "confirmed",
    "工作假设": "assumption",
    "证据缺口": "gap",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 JSON 渲染 S7 转型建议报告")
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 JSON 输入")
    parser.add_argument("--output", required=True, type=Path, help="HTML 输出")
    return parser.parse_args()


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _safe_html_href(value: Any) -> str:
    href = _require_text(value, "diagnosis_report_href")
    if (
        not re.fullmatch(r"[^/%\\?#:]+\.html", href, flags=re.IGNORECASE)
        or Path(href).name != href
        or ".." in Path(href).parts
    ):
        raise ValueError("diagnosis_report_href must reference one local HTML report")
    return href


def _normalize_status(value: Any, label: str) -> str:
    status = _require_text(value, label)
    if status not in ALLOWED_EVIDENCE_STATUS:
        raise ValueError(f"{label} is invalid")
    return status


def _normalize_boundary(value: Any, label: str) -> list[dict[str, str]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    items = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"{label}[{index}] must be an object")
        items.append(
            {
                "item": _require_text(item.get("item"), f"{label}[{index}].item"),
                "reason": _require_text(item.get("reason"), f"{label}[{index}].reason"),
                "evidence_status": _normalize_status(
                    item.get("evidence_status"), f"{label}[{index}].evidence_status"
                ),
            }
        )
    return items


def _normalize_hypothesis(value: Any, label: str, *, alternative: bool) -> dict[str, str] | None:
    if value is None and alternative:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    data = {
        "name": _require_text(value.get("name"), f"{label}.name"),
        "evidence_status": _normalize_status(
            value.get("evidence_status"), f"{label}.evidence_status"
        ),
    }
    if alternative:
        data["tradeoff"] = _require_text(value.get("tradeoff"), f"{label}.tradeoff")
    else:
        data["target"] = _require_text(value.get("target"), f"{label}.target")
        data["value"] = _require_text(value.get("value"), f"{label}.value")
        data["counterevidence"] = _require_text(
            value.get("counterevidence"), f"{label}.counterevidence"
        )
    return data


def _normalize_evidence(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        raise ValueError("evidence_boundary must be an object")
    result: dict[str, list[str]] = {}
    for key in ("confirmed_facts", "working_assumptions", "evidence_gaps"):
        items = value.get(key)
        if not isinstance(items, list) or not items:
            raise ValueError(f"evidence_boundary.{key} must be a non-empty list")
        result[key] = [_require_text(item, f"evidence_boundary.{key}") for item in items]
    return result


def _normalize_validation(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("validation_30d must be an object")
    return {
        field: _require_text(value.get(field), f"validation_30d.{field}")
        for field in ("action", "completion_signal", "stop_line", "recommended_review")
    }


def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("input must be a JSON object")
    data = {
        key: _require_text(payload.get(key), key)
        for key in ("title", "stage", "decision", "legacy_business_unit")
    }
    if data["stage"] != "S7":
        raise ValueError("stage must be S7")
    data["retain_boundary"] = _normalize_boundary(
        payload.get("retain_boundary"), "retain_boundary"
    )
    data["stop_boundary"] = _normalize_boundary(
        payload.get("stop_boundary"), "stop_boundary"
    )
    data["recommended_hypothesis"] = _normalize_hypothesis(
        payload.get("recommended_hypothesis"), "recommended_hypothesis", alternative=False
    )
    data["alternative_hypothesis"] = _normalize_hypothesis(
        payload.get("alternative_hypothesis"), "alternative_hypothesis", alternative=True
    )
    data["evidence_boundary"] = _normalize_evidence(payload.get("evidence_boundary"))
    data["validation_30d"] = _normalize_validation(payload.get("validation_30d"))
    data["diagnosis_report_href"] = _safe_html_href(payload.get("diagnosis_report_href"))
    return data


def _escape(value: str) -> str:
    return html.escape(value, quote=True)


def _status(value: str) -> str:
    return f'<span class="status {STATUS_CLASS[value]}">{_escape(value)}</span>'


def _boundary_cards(items: list[dict[str, str]], label: str) -> str:
    return "".join(
        "<article><h3>{}</h3><p>{}</p>{}</article>".format(
            _escape(item["item"]), _escape(item["reason"]), _status(item["evidence_status"])
        )
        for item in items
    )


def _list(items: list[str]) -> str:
    return "".join(f"<li>{_escape(item)}</li>" for item in items)


def render_html(payload: dict[str, Any]) -> str:
    data = _normalize(payload)
    recommended = data["recommended_hypothesis"]
    alternative = data["alternative_hypothesis"]
    evidence = data["evidence_boundary"]
    validation = data["validation_30d"]
    alternative_html = (
        "<article><h3>备选｜{}</h3><p>{}</p>{}</article>".format(
            _escape(alternative["name"]),
            _escape(alternative["tradeoff"]),
            _status(alternative["evidence_status"]),
        )
        if alternative
        else ""
    )

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>S7 转型建议</title><style>
:root{{--ink:#172b3a;--muted:#5b7083;--line:#d9e2ec;--paper:#f5f7fa;--navy:#102a43;--teal:#0f766e;--fact:#e8f5ee;--hyp:#fff7df;--gap:#fdecec}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}main{{max-width:940px;margin:auto;padding:32px 20px 56px}}header,section{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:22px}}header{{background:var(--navy);color:#fff}}header p{{margin:8px 0 0;color:#d8e6f1}}section{{margin-top:16px}}h1,h2,h3,p{{overflow-wrap:anywhere}}h1{{margin:0;font-size:28px}}h2{{margin:0 0 14px;color:var(--navy);font-size:20px}}h3{{margin:0 0 6px;font-size:16px}}.decision{{border-left:4px solid #5eead4;padding-left:12px}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}article{{min-width:0;border:1px solid var(--line);border-radius:12px;padding:14px;background:#fbfcfd}}.status{{display:inline-block;margin-top:8px;padding:2px 8px;border-radius:999px;font-size:12px;font-weight:700}}.confirmed{{background:var(--fact);color:#17663d}}.assumption{{background:var(--hyp);color:#7a5700}}.gap{{background:var(--gap);color:#8a3037}}.evidence{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}.evidence article:nth-child(1){{background:var(--fact)}}.evidence article:nth-child(2){{background:var(--hyp)}}.evidence article:nth-child(3){{background:var(--gap)}}ul{{margin:6px 0 0;padding-left:20px}}.validation{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}.validation article:last-child{{grid-column:span 2;background:#fff5f5}}a{{color:var(--teal);font-weight:700}}footer{{margin-top:16px;text-align:center}}@media(max-width:640px){{main{{padding:16px 12px 36px}}header,section{{padding:18px}}.grid,.evidence,.validation{{grid-template-columns:1fr}}.validation article:last-child{{grid-column:auto}}}}@media print{{body{{background:#fff}}main{{max-width:none;padding:0}}header,section{{break-inside:avoid}}}}
</style></head><body><main data-report="s7-action">
<header><p>S7 轻量转型建议</p><h1>{_escape(data["title"])}</h1><p>{_escape(data["legacy_business_unit"])}</p><p class="decision"><strong>核心判断｜</strong>{_escape(data["decision"])}</p></header>
<section data-section="retain-stop-boundary"><h2>保留／停止边界</h2><div class="grid"><article><h3>保留</h3>{_boundary_cards(data["retain_boundary"], "保留")}</article><article><h3>停止加码</h3>{_boundary_cards(data["stop_boundary"], "停止")}</article></div></section>
<section data-section="transition-options"><h2>转型选择图</h2><div class="grid"><article><h3>推荐｜{_escape(recommended["name"])}</h3><p>目标对象：{_escape(recommended["target"])}</p><p>待验证价值：{_escape(recommended["value"])}</p><p>关键反证：{_escape(recommended["counterevidence"])}</p>{_status(recommended["evidence_status"])}</article>{alternative_html}</div></section>
<section data-section="evidence-boundary"><h2>证据边界</h2><div class="evidence"><article><h3>已确认事实</h3><ul>{_list(evidence["confirmed_facts"])}</ul></article><article><h3>工作假设</h3><ul>{_list(evidence["working_assumptions"])}</ul></article><article><h3>证据缺口</h3><ul>{_list(evidence["evidence_gaps"])}</ul></article></div></section>
<section data-section="validation-30d"><h2>30 天最小验证</h2><div class="validation"><article><h3>最小动作</h3><p>{_escape(validation["action"])}</p></article><article><h3>完成标志</h3><p>{_escape(validation["completion_signal"])}</p></article><article><h3>停止线与复核</h3><p>{_escape(validation["stop_line"])}</p><p>{_escape(validation["recommended_review"])}</p></article></div></section>
<footer><a href="{_escape(data["diagnosis_report_href"])}">返回阶段诊断报告</a></footer>
</main></body></html>"""


def render_s7_action(output_dir: Path, payload: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "stage-action-s7.html"
    output.write_text(render_html(payload), encoding="utf-8")
    return output


def main() -> int:
    args = _parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        html_output = render_html(payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(html_output, encoding="utf-8")
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
