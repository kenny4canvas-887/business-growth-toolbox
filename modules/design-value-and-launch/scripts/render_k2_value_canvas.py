#!/usr/bin/env python3
"""Render one evidence-bounded K2 value proposition canvas as SVG."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


EVIDENCE_LABELS = ("[已确认]", "[假设]", "[缺口]")
SECTION_LAYOUT = (
    ("target", "目标客户", 60, 300, 430, 145),
    ("scene_job", "场景与任务", 60, 465, 430, 165),
    ("pain_outcome", "痛点与好结果", 60, 650, 430, 165),
    ("offering", "产品或服务载体", 1110, 300, 430, 145),
    ("pain_relief", "痛点缓解", 1110, 465, 430, 165),
    ("gain_creation", "收益创造", 1110, 650, 430, 165),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a BMI K2 value proposition canvas from JSON."
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


def _require_text_list(
    payload: dict[str, Any], key: str, *, count: int | None = None
) -> list[str]:
    values = payload.get(key)
    if not isinstance(values, list) or not values:
        raise ValueError(f"{key} must be a non-empty list")
    cleaned = [item.strip() for item in values if isinstance(item, str) and item.strip()]
    if len(cleaned) != len(values):
        raise ValueError(f"{key} must contain non-empty strings")
    if count is not None and len(cleaned) != count:
        raise ValueError(f"{key} must contain exactly {count} items")
    return cleaned


def _normalize_sections(payload: dict[str, Any]) -> dict[str, list[str]]:
    raw = payload.get("sections")
    if not isinstance(raw, dict):
        raise ValueError("sections must be an object")

    expected = {key for key, *_ in SECTION_LAYOUT} | {"evidence"}
    if set(raw) != expected:
        raise ValueError("sections must contain exactly the seven K2 canvas sections")

    sections: dict[str, list[str]] = {}
    for key in expected:
        lines = _require_text_list(raw, key)
        for line in lines:
            if not line.startswith(EVIDENCE_LABELS):
                raise ValueError(f"sections.{key} must start each line with an evidence label")
        sections[key] = lines[:3]
    return sections


def _with_evidence_label(value: str, label: str) -> str:
    return value if value.startswith(EVIDENCE_LABELS) else f"{label} {value}"


def _normalize_consultant_insight(
    payload: dict[str, Any],
    value_proposition: str,
    exclusions: list[str],
    stop_line: list[str],
) -> dict[str, str]:
    raw = payload.get("consultant_insight")
    if raw is None:
        return {
            "contrarian": value_proposition,
            "do_not_do": _with_evidence_label(exclusions[0], "[假设]"),
            "reversal_evidence": _with_evidence_label(stop_line[0], "[缺口]"),
        }
    if not isinstance(raw, dict) or set(raw) != {
        "contrarian",
        "do_not_do",
        "reversal_evidence",
    }:
        raise ValueError("consultant_insight must contain exactly three K2 fields")
    return {
        key: _require_labelled_text(raw, key)
        for key in ("contrarian", "do_not_do", "reversal_evidence")
    }


def _shorten(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _wrap_text(value: str, width: int) -> list[str]:
    compact = " ".join(value.split())
    return [compact[index : index + width] for index in range(0, len(compact), width)]


def _svg_text(
    lines: list[str],
    x: int,
    y: int,
    *,
    width: int,
    max_lines: int,
    line_height: int = 29,
    css_class: str = "body",
) -> str:
    wrapped: list[str] = []
    for line in lines:
        wrapped.extend(_wrap_text(line, width))
    if len(wrapped) > max_lines:
        wrapped = wrapped[:max_lines]
        wrapped[-1] = _shorten(wrapped[-1], max(2, width - 1))

    return "\n".join(
        f'<text x="{x}" y="{y + index * line_height}" class="{css_class}">'
        f"{html.escape(line)}</text>"
        for index, line in enumerate(wrapped)
    )


def render(payload: dict[str, Any]) -> str:
    title = _require_text(payload, "title")
    stage = _require_text(payload, "stage")
    decision = _require_text(payload, "decision")
    value_proposition = _require_labelled_text(payload, "value_proposition")
    sections = _normalize_sections(payload)
    flow = _require_text_list(payload, "minimum_value_flow", count=5)
    exclusions = _require_text_list(payload, "exclusions")[:2]
    stop_line = _require_text_list(payload, "stop_line")[:2]

    cards: list[str] = []
    for key, label, x, y, width, height in SECTION_LAYOUT:
        cards.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="20" class="card"/>'
        )
        cards.append(f'<text x="{x + 24}" y="{y + 42}" class="label">{label}</text>')
        cards.append(
            _svg_text(
                sections[key],
                x + 24,
                y + 82,
                width=22,
                max_lines=3,
            )
        )

    evidence_text = _svg_text(
        sections["evidence"], 620, 565, width=24, max_lines=6, line_height=31
    )
    proposition_text = _svg_text(
        [value_proposition], 620, 385, width=24, max_lines=4, line_height=33
    )

    flow_nodes: list[str] = []
    for index, item in enumerate(flow):
        x = 80 + index * 300
        flow_nodes.append(
            f'<rect x="{x}" y="875" width="230" height="72" rx="18" class="flow"/>'
        )
        flow_nodes.append(
            _svg_text([item], x + 20, 916, width=12, max_lines=2, css_class="flow-text")
        )
        if index < len(flow) - 1:
            flow_nodes.append(
                f'<path d="M {x + 230} 911 H {x + 285}" class="arrow" marker-end="url(#arrow)"/>'
            )

    safe_title = html.escape(_shorten(title, 24))
    safe_stage = html.escape(_shorten(stage, 30))
    decision_text = _svg_text([f"核心判断｜{decision}"], 90, 223, width=57, max_lines=1)
    exclusion_text = html.escape(_shorten("；".join(exclusions), 42))
    stop_text = html.escape(_shorten("；".join(stop_line), 42))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1100" viewBox="0 0 1600 1100">
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" fill="#4c6fff"/>
    </marker>
  </defs>
  <style>
    .title {{ font: 700 42px -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; fill: #172238; }}
    .brand {{ font: 600 23px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #ffffff; }}
    .stage {{ font: 600 24px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #14645a; }}
    .column {{ font: 700 28px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #46536b; }}
    .label {{ font: 700 24px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #172238; }}
    .body {{ font: 400 21px -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; fill: #27354d; }}
    .flow-text {{ font: 600 20px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #27354d; }}
    .card {{ fill: #ffffff; stroke: #d7dfeb; stroke-width: 2; }}
    .match {{ fill: #eef2ff; stroke: #9cacf9; stroke-width: 2; }}
    .flow {{ fill: #ffffff; stroke: #9cacf9; stroke-width: 2; }}
    .arrow {{ stroke: #4c6fff; stroke-width: 4; fill: none; }}
  </style>
  <rect width="1600" height="1100" fill="#f3f6fa"/>
  <rect width="1600" height="90" fill="#172238"/>
  <text x="60" y="58" class="brand">BMI 兴远咨询 · K2 价值主张设计画布</text>
  <text x="1540" y="58" text-anchor="end" class="brand">BMI Kenny</text>
  <text x="60" y="145" class="title">{safe_title}</text>
  <rect x="1110" y="112" width="430" height="54" rx="27" fill="#dff3ee"/>
  <text x="1325" y="148" text-anchor="middle" class="stage">{safe_stage}</text>
  <rect x="60" y="180" width="1480" height="64" rx="18" fill="#fff1cf"/>
  {decision_text}
  <text x="60" y="282" class="column">客户侧</text>
  <text x="585" y="282" class="column">价值匹配</text>
  <text x="1110" y="282" class="column">产品与服务侧</text>
  {''.join(cards)}
  <path d="M 505 555 H 570" class="arrow" marker-end="url(#arrow)"/>
  <path d="M 1095 555 H 1030" class="arrow" marker-end="url(#arrow)"/>
  <rect x="585" y="300" width="430" height="515" rx="24" class="match"/>
  <text x="620" y="350" class="label">优先价值主张</text>
  {proposition_text}
  <line x1="620" y1="510" x2="980" y2="510" stroke="#bac5f5" stroke-width="2"/>
  <text x="620" y="545" class="label">价值匹配证据</text>
  {evidence_text}
  <text x="60" y="855" class="column">最小价值闭环</text>
  {''.join(flow_nodes)}
  <rect x="60" y="980" width="720" height="64" rx="16" fill="#fff1cf"/>
  <text x="84" y="1021" class="body">排除范围：{exclusion_text}</text>
  <rect x="800" y="980" width="740" height="64" rx="16" fill="#ffe5e5"/>
  <text x="824" y="1021" class="body">停止线：{stop_text}</text>
  <text x="60" y="1080" class="body">图中 [已确认] [假设] [缺口] 必须与文字结论使用同一组事实。</text>
</svg>'''


def render_html(payload: dict[str, Any]) -> str:
    svg = render(payload)
    value_proposition = _require_labelled_text(payload, "value_proposition")
    exclusions = _require_text_list(payload, "exclusions")[:2]
    stop_line = _require_text_list(payload, "stop_line")[:2]
    insight = _normalize_consultant_insight(
        payload, value_proposition, exclusions, stop_line
    )
    insight_cards = "".join(
        f'<article><h2>{heading}</h2><p>{html.escape(insight[key])}</p></article>'
        for key, heading in (
            ("contrarian", "客户为何改变"),
            ("do_not_do", "本轮明确删掉"),
            ("reversal_evidence", "改判证据"),
        )
    )
    diagnosis_href = html.escape(
        str(payload.get("diagnosis_report_href", "stage-diagnosis-report.html")),
        quote=True,
    )
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>K2 价值设计行动报告</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#f3f6fa;color:#172238;font:15px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}main{{max-width:1660px;margin:auto;padding:24px}}header{{margin-bottom:18px}}h1{{margin:0}}p{{color:#52627a}}section{{background:#fff;border:1px solid #d9e0ec;border-radius:16px;padding:14px;overflow:auto}}.insights{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:18px;background:transparent;border:0;padding:0}}.insights article{{background:#fff;border:1px solid #d9e0ec;border-top:5px solid #4c6fff;border-radius:14px;padding:16px}}.insights h2{{margin:0 0 8px;font-size:18px}}.insights p{{margin:0}}svg{{display:block;width:100%;height:auto}}@media(max-width:760px){{main{{padding:12px}}.insights{{grid-template-columns:1fr}}}}@media print{{body{{background:#fff}}main{{padding:0}}section{{border:0}}}}</style>
</head><body><main data-report="k2-action"><header><h1>K2 价值设计行动报告</h1><p>回答最小价值闭环是否成立；不是阶段诊断页。</p></header><section class="insights" data-section="consultant-insight">{insight_cards}</section><section data-section="stage-method">{svg}</section><p><a href="{diagnosis_href}">返回阶段诊断报告</a></p></main></body></html>'''


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
