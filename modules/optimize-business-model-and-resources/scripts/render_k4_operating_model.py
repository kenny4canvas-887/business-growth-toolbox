#!/usr/bin/env python3
"""Render one evidence-bounded K4 operating-model diagnosis as SVG."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


CHAIN_FIELDS = (
    ("customer_value", "客户与价值"),
    ("revenue", "收入机制"),
    ("delivery_resource", "交付与资源"),
    ("operating_result", "经营结果"),
)
ECONOMICS_FIELDS = ("data_readiness", "comparison_result", "main_constraint")
RESOURCE_FIELDS = ("resource_constraint", "priority_reason")
SCOPE_FIELDS = ("mature_business", "new_business")
LEVER_FIELDS = ("title", "mechanism", "tradeoff", "stop")
CONSULTANT_INSIGHT_FIELDS = ("contrarian", "do_not_do", "reversal_evidence")
EVIDENCE_PREFIXES = ("[已确认]", "[假设]", "[缺口]")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a BMI K4 operating-model diagnosis from JSON."
    )
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 JSON input")
    parser.add_argument("--output", required=True, type=Path, help="SVG or HTML output path")
    return parser.parse_args()


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _require_object(
    payload: dict[str, Any], key: str, fields: tuple[str, ...]
) -> dict[str, str]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    if set(value) != set(fields):
        raise ValueError(f"{key} must contain exactly {', '.join(fields)}")
    return {field: _require_text(value, field) for field in fields}


def _normalize_chain(payload: dict[str, Any]) -> dict[str, str]:
    return _require_object(payload, "bottleneck_chain", tuple(key for key, _ in CHAIN_FIELDS))


def _normalize_levers(payload: dict[str, Any]) -> list[dict[str, str]]:
    value = payload.get("operating_levers")
    if not isinstance(value, list) or not 1 <= len(value) <= 3:
        raise ValueError("operating_levers must contain 1 to 3 items")
    levers: list[dict[str, str]] = []
    for index, lever in enumerate(value):
        if not isinstance(lever, dict):
            raise ValueError(f"operating_levers[{index}] must be an object")
        if set(lever) != set(LEVER_FIELDS):
            raise ValueError(
                f"operating_levers[{index}] must contain exactly {', '.join(LEVER_FIELDS)}"
            )
        levers.append({field: _require_text(lever, field) for field in LEVER_FIELDS})
    return levers


def _with_evidence_label(value: str, default: str) -> str:
    return value if value.startswith(EVIDENCE_PREFIXES) else f"{default} {value}"


def _normalize_consultant_insight(payload: dict[str, Any]) -> dict[str, str]:
    value = payload.get("consultant_insight")
    if value is None:
        economics = payload.get("economics")
        main_constraint = (
            economics.get("main_constraint", "主约束待验证")
            if isinstance(economics, dict)
            else "主约束待验证"
        )
        return {
            "contrarian": _with_evidence_label(str(main_constraint), "[假设]"),
            "do_not_do": "[假设] 本轮不同时优化全部收入、成本、交付与资源问题",
            "reversal_evidence": _with_evidence_label(
                str(payload.get("stop_line", "改判证据待补齐")), "[缺口]"
            ),
        }
    insight = _require_object(payload, "consultant_insight", CONSULTANT_INSIGHT_FIELDS)
    for field, text in insight.items():
        if not text.startswith(EVIDENCE_PREFIXES):
            raise ValueError(
                f"consultant_insight.{field} must start with [已确认], [假设], or [缺口]"
            )
    return insight


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
    line_height: int = 24,
    css_class: str = "body",
    anchor: str | None = None,
) -> str:
    anchor_attr = f' text-anchor="{anchor}"' if anchor else ""
    return "".join(
        f'<text x="{x}" y="{y + index * line_height}" class="{css_class}"{anchor_attr}>'
        f"{html.escape(line)}</text>"
        for index, line in enumerate(_wrap_text(value, width, max_lines))
    )


def render(payload: dict[str, Any]) -> str:
    title = _require_text(payload, "title")
    stage = _require_text(payload, "stage")
    diagnostic_scope = _require_text(payload, "diagnostic_scope")
    decision = _require_text(payload, "decision")
    chain = _normalize_chain(payload)
    economics = _require_object(payload, "economics", ECONOMICS_FIELDS)
    resource = _require_object(payload, "resource", RESOURCE_FIELDS)
    scope_split = _require_object(payload, "scope_split", SCOPE_FIELDS)
    model_rebuild_review = _require_text(payload, "model_rebuild_review")
    levers = _normalize_levers(payload)
    priority_validation = _require_text(payload, "priority_validation")
    stop_line = _require_text(payload, "stop_line")
    evidence_summary = _require_text(payload, "evidence_summary")

    chain_nodes: list[str] = []
    for index, (key, label) in enumerate(CHAIN_FIELDS):
        x = 60 + index * 375
        chain_nodes.append(
            f'<rect x="{x}" y="310" width="340" height="130" rx="18" class="chain-card"/>'
        )
        chain_nodes.append(f'<text x="{x + 22}" y="344" class="card-title">{label}</text>')
        chain_nodes.append(
            _svg_text(chain[key], x + 22, 378, width=16, max_lines=3, line_height=22)
        )
        if index < len(CHAIN_FIELDS) - 1:
            chain_nodes.append(
                f'<path d="M {x + 345} 375 L {x + 368} 375" class="arrow"/>'
            )

    lever_nodes: list[str] = []
    lever_width = 460 if len(levers) == 3 else (700 if len(levers) == 2 else 1480)
    lever_gap = 30
    for index, lever in enumerate(levers):
        x = 60 + index * (lever_width + lever_gap)
        lever_nodes.append(
            f'<rect x="{x}" y="750" width="{lever_width}" height="196" rx="18" class="lever-card"/>'
        )
        lever_nodes.append(f'<circle cx="{x + 34}" cy="786" r="20" class="number"/>')
        lever_nodes.append(
            f'<text x="{x + 34}" y="793" text-anchor="middle" class="number-text">{index + 1}</text>'
        )
        lever_nodes.append(
            _svg_text(lever["title"], x + 68, 792, width=16, max_lines=1, css_class="lever-title")
        )
        text_width = 22 if lever_width <= 460 else 36
        lever_nodes.append(
            _svg_text(f'机制｜{lever["mechanism"]}', x + 22, 832, width=text_width, max_lines=2)
        )
        lever_nodes.append(
            _svg_text(f'代价｜{lever["tradeoff"]}', x + 22, 884, width=text_width, max_lines=2)
        )
        lever_nodes.append(
            _svg_text(f'停止｜{lever["stop"]}', x + 22, 932, width=text_width, max_lines=1)
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1100" viewBox="0 0 1600 1100">
  <style>
    .brand {{ font: 600 23px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #ffffff; }}
    .title {{ font: 700 38px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #172238; }}
    .stage {{ font: 600 20px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #14645a; }}
    .section-title {{ font: 700 23px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #172238; }}
    .card-title {{ font: 700 21px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #172238; }}
    .body {{ font: 400 17px -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; fill: #27354d; }}
    .small {{ font: 500 15px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #526176; }}
    .lever-title {{ font: 700 20px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #172238; }}
    .number-text {{ font: 700 19px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #ffffff; }}
    .chain-card {{ fill: #ffffff; stroke: #9cacf9; stroke-width: 2; }}
    .scope-card {{ fill: #ffffff; stroke: #d7dfeb; stroke-width: 2; }}
    .analysis-card {{ fill: #ffffff; stroke: #b9d9d3; stroke-width: 2; }}
    .lever-card {{ fill: #ffffff; stroke: #f0b05b; stroke-width: 2; }}
    .number {{ fill: #d88324; }}
    .arrow {{ fill: none; stroke: #4c6fff; stroke-width: 4; stroke-linecap: round; }}
  </style>
  <rect width="1600" height="1100" fill="#f3f6fa"/>
  <rect width="1600" height="86" fill="#172238"/>
  <text x="60" y="56" class="brand">BMI 兴远咨询 · K4 经营模型与资源优化图</text>
  <text x="1540" y="56" text-anchor="end" class="brand">BMI Kenny</text>
  <text x="60" y="136" class="title">{html.escape(_shorten(title, 30))}</text>
  <rect x="1120" y="105" width="420" height="48" rx="24" fill="#dff3ee"/>
  <text x="1330" y="136" text-anchor="middle" class="stage">{html.escape(_shorten(stage, 30))}</text>
  {_svg_text(f'诊断口径｜{diagnostic_scope}', 60, 174, width=72, max_lines=1)}
  <rect x="60" y="194" width="1480" height="64" rx="16" fill="#fff1cf"/>
  {_svg_text(f'核心判断｜{decision}', 82, 221, width=68, max_lines=1)}
  {_svg_text(f'证据状态｜{evidence_summary}', 82, 247, width=68, max_lines=1, css_class="small")}
  <text x="60" y="294" class="section-title">商业模式与经营结果链</text>
  {''.join(chain_nodes)}
  <rect x="60" y="465" width="350" height="190" rx="18" class="scope-card"/>
  <text x="82" y="500" class="card-title">成熟主业</text>
  {_svg_text(scope_split["mature_business"], 82, 536, width=16, max_lines=5)}
  <rect x="430" y="465" width="350" height="190" rx="18" class="scope-card"/>
  <text x="452" y="500" class="card-title">新业务 / 新品类</text>
  {_svg_text(scope_split["new_business"], 452, 536, width=16, max_lines=5)}
  <rect x="800" y="465" width="350" height="190" rx="18" class="analysis-card"/>
  <text x="822" y="500" class="card-title">收入成本判断</text>
  {_svg_text(f'数据｜{economics["data_readiness"]}', 822, 534, width=17, max_lines=2)}
  {_svg_text(f'比较｜{economics["comparison_result"]}', 822, 580, width=17, max_lines=2)}
  {_svg_text(f'主约束｜{economics["main_constraint"]}', 822, 626, width=17, max_lines=2)}
  <rect x="1170" y="465" width="370" height="190" rx="18" class="analysis-card"/>
  <text x="1192" y="500" class="card-title">资源约束</text>
  {_svg_text(f'约束｜{resource["resource_constraint"]}', 1192, 542, width=18, max_lines=3)}
  {_svg_text(f'优先原因｜{resource["priority_reason"]}', 1192, 614, width=18, max_lines=2)}
  <rect x="60" y="675" width="1480" height="52" rx="16" fill="#e7ecff"/>
  {_svg_text(f'商业模式重构复核｜{model_rebuild_review}', 82, 708, width=70, max_lines=1)}
  <text x="60" y="744" class="section-title">经营杠杆（最多三个）</text>
  {''.join(lever_nodes)}
  <rect x="60" y="968" width="1480" height="54" rx="16" fill="#dff3ee"/>
  {_svg_text(f'30 天优先验证｜{priority_validation}', 82, 1002, width=70, max_lines=1)}
  <rect x="60" y="1036" width="1480" height="44" rx="14" fill="#ffe5e5"/>
  {_svg_text(f'停止线｜{stop_line}', 82, 1065, width=72, max_lines=1)}
</svg>'''


def render_html(payload: dict[str, Any]) -> str:
    svg = render(payload)
    insight = _normalize_consultant_insight(payload)
    diagnosis_href = html.escape(
        str(payload.get("diagnosis_report_href", "stage-diagnosis-report.html")),
        quote=True,
    )
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>K4 经营优化行动报告</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#f3f6fa;color:#172238;font:15px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}main{{max-width:1660px;margin:auto;padding:24px}}header{{margin-bottom:18px}}h1{{margin:0}}p{{color:#52627a}}section{{background:#fff;border:1px solid #d9e0ec;border-radius:16px;padding:14px;overflow:auto}}.insights{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:0 0 16px}}.insight-card{{background:#fff;border:1px solid #d9e0ec;border-top:4px solid #4c6fff;border-radius:14px;padding:16px}}.insight-card h2{{font-size:16px;margin:0 0 8px}}.insight-card p{{margin:0;color:#172238}}svg{{display:block;width:100%;height:auto}}@media(max-width:760px){{main{{padding:12px}}.insights{{grid-template-columns:1fr}}}}@media print{{body{{background:#fff}}main{{padding:0}}section{{border:0}}}}</style>
</head><body><main data-report="k4-action"><header><h1>K4 经营优化行动报告</h1><p>回答哪个资源效率瓶颈应先处理；不是阶段诊断页。</p></header><div class="insights" data-section="consultant-insight"><article class="insight-card"><h2>真正吞掉结果的约束</h2><p>{html.escape(insight["contrarian"])}</p></article><article class="insight-card"><h2>本轮明确不优化</h2><p>{html.escape(insight["do_not_do"])}</p></article><article class="insight-card"><h2>改判证据</h2><p>{html.escape(insight["reversal_evidence"])}</p></article></div><section data-section="stage-method">{svg}</section><p><a href="{diagnosis_href}">返回阶段诊断报告</a></p></main></body></html>'''


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
