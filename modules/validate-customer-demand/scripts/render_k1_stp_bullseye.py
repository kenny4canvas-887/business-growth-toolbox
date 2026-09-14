#!/usr/bin/env python3
"""Render one evidence-bounded K1 STP bullseye canvas as SVG."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any


EVIDENCE_LABELS = ("[已确认]", "[假设]", "[缺口]")
CRITERIA = (
    ("measurable", "可衡量"),
    ("substantial", "足够价值"),
    ("accessible", "可触达"),
    ("differentiable", "可区分"),
    ("actionable", "可行动"),
)
POSITIONING = (
    ("context_job", "情境与任务"),
    ("current_alternative", "当前替代"),
    ("difference", "差异理由"),
    ("reason_to_believe", "可信依据"),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a K1 STP bullseye from JSON.")
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 JSON input")
    parser.add_argument("--output", required=True, type=Path, help="SVG or HTML output path")
    return parser.parse_args()


def _text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _labelled(payload: dict[str, Any], key: str) -> str:
    value = _text(payload, key)
    if not value.startswith(EVIDENCE_LABELS):
        raise ValueError(f"{key} must start with an evidence label")
    return value


def _labelled_list(payload: dict[str, Any], key: str) -> list[str]:
    values = payload.get(key)
    if not isinstance(values, list) or not values:
        raise ValueError(f"{key} must be a non-empty list")
    cleaned: list[str] = []
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key}[{index}] must be a non-empty string")
        value = value.strip()
        if not value.startswith(EVIDENCE_LABELS):
            raise ValueError(f"{key}[{index}] must start with an evidence label")
        cleaned.append(value)
    return cleaned


def _short(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _wrap(value: str, width: int, max_lines: int) -> list[str]:
    compact = " ".join(value.split())
    lines = [compact[index : index + width] for index in range(0, len(compact), width)]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = _short(lines[-1], max(2, width - 1))
    return lines


def _svg_text(
    value: str,
    x: int,
    y: int,
    *,
    width: int,
    max_lines: int,
    css: str = "body",
    line_height: int = 26,
    anchor: str = "start",
) -> str:
    return "\n".join(
        f'<text x="{x}" y="{y + index * line_height}" class="{css}" '
        f'text-anchor="{anchor}">{html.escape(line)}</text>'
        for index, line in enumerate(_wrap(value, width, max_lines))
    )


def _validate_to_c_label(label: str, field: str) -> None:
    if len(label) > 10:
        raise ValueError(f"{field} must contain no more than 10 characters for To C")
    if re.search(r"[\s，,、；;：:（）()]", label):
        raise ValueError(f"{field} must be one compact To C label")


def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
    business_type = _text(payload, "business_type")
    if business_type not in {"To B", "To C", "混合业务"}:
        raise ValueError("business_type must be To B, To C, or 混合业务")

    segments = payload.get("segments")
    if not isinstance(segments, list) or not 2 <= len(segments) <= 4:
        raise ValueError("segments must contain 2 to 4 candidates")
    normalized_segments = []
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise ValueError(f"segments[{index}] must be an object")
        label = _text(segment, "label")
        basis = _labelled(segment, "basis")
        if business_type == "To C":
            _validate_to_c_label(label, f"segments[{index}].label")
        normalized_segments.append({"label": label, "basis": basis})

    target = payload.get("target")
    if not isinstance(target, dict):
        raise ValueError("target must be an object")
    target_label = _text(target, "label")
    if business_type == "To C":
        _validate_to_c_label(target_label, "target.label")
    why_selected = _labelled(target, "why_selected")
    criteria = target.get("criteria")
    if not isinstance(criteria, dict) or set(criteria) != {key for key, _ in CRITERIA}:
        raise ValueError("target.criteria must contain exactly the five STP target gates")
    normalized_criteria = {key: _labelled(criteria, key) for key, _ in CRITERIA}

    positioning = payload.get("positioning")
    if not isinstance(positioning, dict) or set(positioning) != {
        key for key, _ in POSITIONING
    }:
        raise ValueError("positioning must contain exactly the four K1 positioning fields")
    normalized_positioning = {
        key: _labelled(positioning, key) for key, _ in POSITIONING
    }

    consultant_insight = payload.get("consultant_insight")
    if consultant_insight is None:
        normalized_insight = {
            "contrarian": f"[假设] {_text(payload, 'decision')}",
            "do_not_do": _labelled_list(payload, "non_targets")[0],
            "reversal_evidence": _labelled_list(payload, "stop_line")[0],
        }
    else:
        if not isinstance(consultant_insight, dict) or set(consultant_insight) != {
            "contrarian",
            "do_not_do",
            "reversal_evidence",
        }:
            raise ValueError(
                "consultant_insight must contain exactly contrarian, do_not_do, and reversal_evidence"
            )
        normalized_insight = {
            key: _labelled(consultant_insight, key)
            for key in ("contrarian", "do_not_do", "reversal_evidence")
        }

    return {
        "title": _text(payload, "title"),
        "stage": _text(payload, "stage"),
        "business_type": business_type,
        "decision": _text(payload, "decision"),
        "market_boundary": _labelled(payload, "market_boundary"),
        "segments": normalized_segments,
        "target_label": target_label,
        "why_selected": why_selected,
        "criteria": normalized_criteria,
        "positioning": normalized_positioning,
        "non_targets": _labelled_list(payload, "non_targets")[:2],
        "next_evidence": _labelled_list(payload, "next_evidence")[:2],
        "stop_line": _labelled_list(payload, "stop_line")[:2],
        "consultant_insight": normalized_insight,
    }


def render(payload: dict[str, Any]) -> str:
    data = _normalize(payload)
    segment_labels = " / ".join(item["label"] for item in data["segments"])
    segment_basis = "；".join(item["basis"] for item in data["segments"])

    gate_cards: list[str] = []
    for index, (key, label) in enumerate(CRITERIA):
        column = index % 2
        row = index // 2
        x = 700 + column * 425
        y = 310 + row * 112
        width = 400 if index < 4 else 825
        gate_cards.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="92" rx="16" class="card"/>'
        )
        gate_cards.append(f'<text x="{x + 20}" y="{y + 31}" class="label">{label}</text>')
        gate_cards.append(
            _svg_text(
                data["criteria"][key],
                x + 20,
                y + 61,
                width=19 if width < 500 else 42,
                max_lines=2,
                line_height=22,
            )
        )

    position_cards: list[str] = []
    for index, (key, label) in enumerate(POSITIONING):
        column = index % 2
        row = index // 2
        x = 700 + column * 425
        y = 700 + row * 112
        position_cards.append(
            f'<rect x="{x}" y="{y}" width="400" height="92" rx="16" class="position"/>'
        )
        position_cards.append(f'<text x="{x + 20}" y="{y + 31}" class="label">{label}</text>')
        position_cards.append(
            _svg_text(
                data["positioning"][key],
                x + 20,
                y + 61,
                width=19,
                max_lines=2,
                line_height=22,
            )
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1100" viewBox="0 0 1600 1100">
  <style>
    .title {{ font: 700 40px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #172238; }}
    .brand {{ font: 600 23px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #fff; }}
    .stage {{ font: 600 22px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #14645a; }}
    .heading {{ font: 700 27px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #27354d; }}
    .label {{ font: 700 21px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #172238; }}
    .body {{ font: 400 19px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #34425a; }}
    .ring-label {{ font: 600 18px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #27354d; }}
    .target {{ font: 700 25px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #fff; }}
    .card {{ fill: #fff; stroke: #d9e0ec; stroke-width: 2; }}
    .position {{ fill: #eef1ff; stroke: #bec8f4; stroke-width: 2; }}
  </style>
  <rect width="1600" height="1100" fill="#f3f6fa"/>
  <rect width="1600" height="90" fill="#172238"/>
  <text x="60" y="58" class="brand">BMI 兴远咨询 · K1 STP 客群收窄画布</text>
  <text x="1540" y="58" text-anchor="end" class="brand">BMI Kenny</text>
  <text x="60" y="145" class="title">{html.escape(_short(data['title'], 24))}</text>
  <rect x="1110" y="112" width="430" height="54" rx="27" fill="#dff3ee"/>
  <text x="1325" y="147" text-anchor="middle" class="stage">{html.escape(_short(data['stage'] + ' · ' + data['business_type'], 32))}</text>
  <rect x="60" y="180" width="1480" height="64" rx="18" fill="#fff1cf"/>
  {_svg_text(f"核心判断｜{data['decision']}", 90, 221, width=67, max_lines=1)}

  <text x="60" y="286" class="heading">同心收窄图</text>
  <circle cx="360" cy="565" r="250" fill="#dfe8f7"/>
  <circle cx="360" cy="565" r="185" fill="#cbd9ef"/>
  <circle cx="360" cy="565" r="120" fill="#aabfe5"/>
  <circle cx="360" cy="565" r="64" fill="#4c6fff"/>
  <text x="360" y="347" class="ring-label" text-anchor="middle">S · 市场边界</text>
  {_svg_text(data['market_boundary'], 360, 381, width=30, max_lines=2, css='body', anchor='middle')}
  <text x="360" y="438" class="ring-label" text-anchor="middle">S · 需求/行为候选群</text>
  {_svg_text(segment_labels, 360, 470, width=28, max_lines=2, css='body', anchor='middle')}
  <text x="360" y="514" class="ring-label" text-anchor="middle">T · 五项闸门收窄</text>
  {_svg_text(data['target_label'], 360, 545, width=14, max_lines=2, css='target', line_height=27, anchor='middle')}
  <text x="360" y="610" class="target" text-anchor="middle">优先 Target</text>
  <rect x="60" y="840" width="600" height="112" rx="18" fill="#fff" stroke="#d9e0ec" stroke-width="2"/>
  <text x="84" y="878" class="label">选择依据</text>
  {_svg_text(data['why_selected'], 84, 910, width=48, max_lines=2)}
  <text x="60" y="985" class="label">候选证据</text>
  {_svg_text(segment_basis, 60, 1017, width=52, max_lines=2)}

  <text x="700" y="286" class="heading">T · 有效细分五项闸门</text>
  {''.join(gate_cards)}
  <text x="700" y="674" class="heading">P · 客户问题定位假设</text>
  {''.join(position_cards)}

  <rect x="700" y="940" width="260" height="112" rx="16" fill="#fff1cf"/>
  <text x="720" y="976" class="label">非目标客户</text>
  {_svg_text('；'.join(data['non_targets']), 720, 1008, width=19, max_lines=2)}
  <rect x="980" y="940" width="280" height="112" rx="16" fill="#e6f3ee"/>
  <text x="1000" y="976" class="label">下一证据</text>
  {_svg_text('；'.join(data['next_evidence']), 1000, 1008, width=21, max_lines=2)}
  <rect x="1280" y="940" width="260" height="112" rx="16" fill="#ffe5e5"/>
  <text x="1300" y="976" class="label">停止线</text>
  {_svg_text('；'.join(data['stop_line']), 1300, 1008, width=19, max_lines=2)}
  <text x="60" y="1082" class="body">STP 是决策主线；同心图只呈现收窄过程。图文必须复用同一组 [已确认] [假设] [缺口]。</text>
</svg>'''


def render_html(payload: dict[str, Any]) -> str:
    data = _normalize(payload)
    svg = render(payload)
    diagnosis_href = html.escape(
        str(payload.get("diagnosis_report_href", "stage-diagnosis-report.html")),
        quote=True,
    )
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>K1 客户需求行动报告</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#f3f6fa;color:#172238;font:15px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}main{{max-width:1660px;margin:auto;padding:24px}}header{{margin-bottom:18px}}h1{{margin:0}}p{{color:#52627a}}section{{background:#fff;border:1px solid #d9e0ec;border-radius:16px;padding:14px;overflow:auto}}.insight-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px}}.insight-card{{border-radius:12px;padding:16px;background:#f7f9fc}}.insight-card h2{{font-size:17px;margin:0 0 8px}}.insight-card p{{margin:0;color:#27354d}}svg{{display:block;width:100%;height:auto}}@media(max-width:760px){{main{{padding:12px}}.insight-grid{{grid-template-columns:1fr}}}}@media print{{body{{background:#fff}}main{{padding:0}}section{{border:0}}}}</style>
</head><body><main data-report="k1-action"><header><h1>K1 客户需求行动报告</h1><p>回答应该优先服务哪类客户；不是阶段诊断页。</p></header><section data-section="consultant-insight" class="insight-grid"><article class="insight-card"><h2>关键反常识</h2><p>{html.escape(data['consultant_insight']['contrarian'])}</p></article><article class="insight-card"><h2>本轮明确不做</h2><p>{html.escape(data['consultant_insight']['do_not_do'])}</p></article><article class="insight-card"><h2>改判证据</h2><p>{html.escape(data['consultant_insight']['reversal_evidence'])}</p></article></section><section data-section="stage-method">{svg}</section><p><a href="{diagnosis_href}">返回阶段诊断报告</a></p></main></body></html>'''


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
        raise SystemExit(f"render failed: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
