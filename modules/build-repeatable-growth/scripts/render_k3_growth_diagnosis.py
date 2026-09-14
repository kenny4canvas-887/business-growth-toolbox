#!/usr/bin/env python3
"""Render one evidence-bounded K3 four-domain growth diagnosis as SVG."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


EVIDENCE_LABELS = ("[已确认]", "[假设]", "[缺口]")
DOMAIN_LAYOUT = (
    ("segment", "客户细分增长", 60, 282),
    ("channel", "渠道通路", 810, 282),
    ("relationship", "客户关系", 60, 492),
    ("revenue", "收入扩大", 810, 492),
)
DOMAIN_FIELDS = (
    ("judgment", "判断"),
    ("evidence", "证据"),
    ("gap", "缺口"),
    ("action", "动作"),
)
ACTION_FIELDS = ("title", "action", "done")
LIFECYCLE_FIELDS = ("get", "keep", "grow", "benefit_cost", "main_break")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a BMI K3 four-domain growth diagnosis from JSON."
    )
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 JSON input")
    parser.add_argument("--output", required=True, type=Path, help="SVG or HTML output path")
    return parser.parse_args()


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _require_labelled_text(payload: dict[str, Any], key: str) -> str:
    value = _require_text(payload, key)
    if not value.startswith(EVIDENCE_LABELS):
        raise ValueError(f"{key} must start with an evidence label")
    return value


def _normalize_consultant_insight(payload: dict[str, Any]) -> dict[str, str]:
    raw = payload.get("consultant_insight")
    if raw is None:
        return {
            "contrarian": f"[假设] {_require_text(payload, 'main_bottleneck')}",
            "do_not_do": f"[假设] {_require_text(payload, 'decision')}",
            "reversal_evidence": f"[缺口] {_require_text(payload, 'stop_line')}",
        }
    if not isinstance(raw, dict) or set(raw) != {
        "contrarian",
        "do_not_do",
        "reversal_evidence",
    }:
        raise ValueError(
            "consultant_insight must contain exactly contrarian, do_not_do, and reversal_evidence"
        )
    return {
        key: _require_labelled_text(raw, key)
        for key in ("contrarian", "do_not_do", "reversal_evidence")
    }


def _normalize_domains(payload: dict[str, Any]) -> dict[str, dict[str, str]]:
    raw = payload.get("domains")
    if not isinstance(raw, dict):
        raise ValueError("domains must be an object")
    expected = {key for key, *_ in DOMAIN_LAYOUT}
    if set(raw) != expected:
        raise ValueError("domains must contain exactly segment, channel, relationship, revenue")

    domains: dict[str, dict[str, str]] = {}
    for domain_key in expected:
        domain = raw[domain_key]
        if not isinstance(domain, dict):
            raise ValueError(f"domains.{domain_key} must be an object")
        normalized: dict[str, str] = {}
        for field, _ in DOMAIN_FIELDS:
            normalized[field] = _require_text(domain, field)
        domains[domain_key] = normalized
    return domains


def _normalize_actions(payload: dict[str, Any]) -> list[dict[str, str]]:
    raw = payload.get("actions")
    if not isinstance(raw, list) or len(raw) != 3:
        raise ValueError("actions must contain exactly 3 items")

    actions: list[dict[str, str]] = []
    for index, action in enumerate(raw):
        if not isinstance(action, dict):
            raise ValueError(f"actions[{index}] must be an object")
        actions.append({field: _require_text(action, field) for field in ACTION_FIELDS})
    return actions


def _normalize_lifecycle(payload: dict[str, Any]) -> dict[str, str]:
    raw = payload.get("lifecycle_judgment")
    if not isinstance(raw, dict):
        raise ValueError("lifecycle_judgment must be an object")
    if set(raw) != set(LIFECYCLE_FIELDS):
        raise ValueError(
            "lifecycle_judgment must contain exactly get, keep, grow, benefit_cost, main_break"
        )
    return {field: _require_text(raw, field) for field in LIFECYCLE_FIELDS}


def _shorten(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _wrap_text(value: str, width: int, max_lines: int) -> list[str]:
    compact = " ".join(value.split())
    lines = [compact[index : index + width] for index in range(0, len(compact), width)]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = _shorten(lines[-1], max(2, width - 1))
    return lines


def _svg_text(
    value: str,
    x: int,
    y: int,
    *,
    width: int,
    max_lines: int,
    line_height: int = 25,
    css_class: str = "body",
    anchor: str | None = None,
) -> str:
    anchor_attr = f' text-anchor="{anchor}"' if anchor else ""
    return "\n".join(
        f'<text x="{x}" y="{y + index * line_height}" class="{css_class}"{anchor_attr}>'
        f"{html.escape(line)}</text>"
        for index, line in enumerate(_wrap_text(value, width, max_lines))
    )


def render(payload: dict[str, Any]) -> str:
    title = _require_text(payload, "title")
    stage = _require_text(payload, "stage")
    decision = _require_text(payload, "decision")
    growth_unit = _require_text(payload, "growth_unit")
    main_bottleneck = _require_text(payload, "main_bottleneck")
    main_path = _require_text(payload, "main_path")
    lifecycle = _normalize_lifecycle(payload)
    domains = _normalize_domains(payload)
    actions = _normalize_actions(payload)
    stop_line = _require_text(payload, "stop_line")
    recommended_review = _require_text(payload, "recommended_review")
    _normalize_consultant_insight(payload)

    domain_nodes: list[str] = []
    for key, label, x, y in DOMAIN_LAYOUT:
        domain_nodes.append(
            f'<rect x="{x}" y="{y}" width="730" height="192" rx="20" class="domain-card"/>'
        )
        domain_nodes.append(f'<text x="{x + 24}" y="{y + 38}" class="domain-title">{label}</text>')
        for index, (field, field_label) in enumerate(DOMAIN_FIELDS):
            content = f"{field_label}｜{domains[key][field]}"
            domain_nodes.append(
                _svg_text(
                    content,
                    x + 24,
                    y + 78 + index * 31,
                    width=33,
                    max_lines=1,
                )
            )

    action_nodes: list[str] = []
    for index, action in enumerate(actions):
        x = 60 + index * 500
        action_nodes.append(
            f'<rect x="{x}" y="802" width="460" height="164" rx="18" class="action-card"/>'
        )
        action_nodes.append(
            f'<circle cx="{x + 38}" cy="838" r="22" class="number"/>'
        )
        action_nodes.append(
            f'<text x="{x + 38}" y="846" text-anchor="middle" class="number-text">{index + 1}</text>'
        )
        action_nodes.append(
            _svg_text(action["title"], x + 75, 844, width=18, max_lines=1, css_class="action-title")
        )
        action_nodes.append(
            _svg_text(f'动作｜{action["action"]}', x + 24, 886, width=21, max_lines=2)
        )
        action_nodes.append(
            _svg_text(f'完成｜{action["done"]}', x + 24, 942, width=21, max_lines=1)
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1100" viewBox="0 0 1600 1100">
  <style>
    .brand {{ font: 600 23px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #ffffff; }}
    .title {{ font: 700 40px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #172238; }}
    .stage {{ font: 600 22px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #14645a; }}
    .domain-title {{ font: 700 24px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #172238; }}
    .body {{ font: 400 19px -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; fill: #27354d; }}
    .summary {{ font: 600 18px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #27354d; }}
    .lifecycle {{ font: 500 17px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #27354d; }}
    .action-title {{ font: 700 21px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #172238; }}
    .number-text {{ font: 700 21px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #ffffff; }}
    .domain-card {{ fill: #ffffff; stroke: #d7dfeb; stroke-width: 2; }}
    .action-card {{ fill: #ffffff; stroke: #9cacf9; stroke-width: 2; }}
    .number {{ fill: #4c6fff; }}
  </style>
  <rect width="1600" height="1100" fill="#f3f6fa"/>
  <rect width="1600" height="90" fill="#172238"/>
  <text x="60" y="58" class="brand">BMI 兴远咨询 · K3 四域增长诊断图</text>
  <text x="1540" y="58" text-anchor="end" class="brand">BMI Kenny</text>
  <text x="60" y="145" class="title">{html.escape(_shorten(title, 28))}</text>
  <rect x="1110" y="112" width="430" height="54" rx="27" fill="#dff3ee"/>
  <text x="1325" y="148" text-anchor="middle" class="stage">{html.escape(_shorten(stage, 30))}</text>
  <rect x="60" y="180" width="1480" height="82" rx="18" fill="#fff1cf"/>
  {_svg_text(f'核心判断｜{decision}', 84, 212, width=66, max_lines=1)}
  {_svg_text(f'增长单元｜{growth_unit}', 84, 244, width=66, max_lines=1)}
  {''.join(domain_nodes)}
  <rect x="60" y="704" width="1480" height="78" rx="16" fill="#e7ecff" class="lifecycle-card"/>
  {_svg_text(f'主瓶颈｜{main_bottleneck}', 76, 728, width=42, max_lines=1, css_class="summary")}
  {_svg_text(f'主路径｜{main_path}', 930, 728, width=26, max_lines=1, css_class="summary")}
  {_svg_text(f'生命周期概览｜Get｜{lifecycle["get"]}', 76, 752, width=27, max_lines=1, css_class="lifecycle")}
  {_svg_text(f'Keep｜{lifecycle["keep"]}', 560, 752, width=25, max_lines=1, css_class="lifecycle")}
  {_svg_text(f'Grow｜{lifecycle["grow"]}', 1044, 752, width=25, max_lines=1, css_class="lifecycle")}
  {_svg_text(f'Benefit、Cost｜{lifecycle["benefit_cost"]}', 76, 776, width=40, max_lines=1, css_class="lifecycle")}
  {_svg_text(f'主断点｜{lifecycle["main_break"]}', 790, 776, width=40, max_lines=1, css_class="lifecycle")}
  {''.join(action_nodes)}
  <rect x="60" y="986" width="920" height="54" rx="16" fill="#ffe5e5"/>
  {_svg_text(f'停止线｜{stop_line}', 84, 1020, width=46, max_lines=1)}
  <rect x="1000" y="986" width="540" height="54" rx="16" fill="#dff3ee"/>
  {_svg_text(f'建议复核｜{recommended_review}', 1024, 1020, width=25, max_lines=1)}
  <text x="60" y="1072" class="body">图文使用同一组事实；增长图只呈现 K3 结论，不替代阶段诊断。</text>
</svg>'''


def render_html(payload: dict[str, Any]) -> str:
    svg = render(payload)
    insight = _normalize_consultant_insight(payload)
    diagnosis_href = html.escape(
        str(payload.get("diagnosis_report_href", "stage-diagnosis-report.html")),
        quote=True,
    )
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>K3 重复增长行动报告</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#f3f6fa;color:#172238;font:15px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}main{{max-width:1660px;margin:auto;padding:24px}}header{{margin-bottom:18px}}h1{{margin:0}}p{{color:#52627a}}section{{background:#fff;border:1px solid #d9e0ec;border-radius:16px;padding:14px;overflow:auto}}.insight-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px}}.insight-card{{border-radius:12px;padding:16px;background:#f7f9fc}}.insight-card h2{{font-size:17px;margin:0 0 8px}}.insight-card p{{margin:0;color:#27354d}}svg{{display:block;width:100%;height:auto}}@media(max-width:760px){{main{{padding:12px}}.insight-grid{{grid-template-columns:1fr}}}}@media print{{body{{background:#fff}}main{{padding:0}}section{{border:0}}}}</style>
</head><body><main data-report="k3-action"><header><h1>K3 重复增长行动报告</h1><p>回答增长瓶颈在哪里以及如何验证重复性；不是阶段诊断页。</p></header><section data-section="consultant-insight" class="insight-grid"><article class="insight-card"><h2>真正增长瓶颈</h2><p>{html.escape(insight['contrarian'])}</p></article><article class="insight-card"><h2>本轮明确不做</h2><p>{html.escape(insight['do_not_do'])}</p></article><article class="insight-card"><h2>改判证据</h2><p>{html.escape(insight['reversal_evidence'])}</p></article></section><section data-section="stage-method">{svg}</section><p><a href="{diagnosis_href}">返回阶段诊断报告</a></p></main></body></html>'''


def main() -> int:
    args = _parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        artifact = render_html(payload) if args.output.suffix.lower() == ".html" else render(payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(artifact, encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
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
        raise SystemExit(f"render failed: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
