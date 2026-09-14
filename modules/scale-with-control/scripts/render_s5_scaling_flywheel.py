#!/usr/bin/env python3
"""Render an evidence-bounded S5 profitable-scaling flywheel."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


EVIDENCE_STATUSES = {"已确认", "假设", "缺口"}
PROFIT_FIELDS = (
    "evidence_status",
    "scope_period",
    "contribution_profit",
    "operating_cash_boundary",
)
NODE_FIELDS = ("label", "evidence_status", "evidence")
LINK_FIELDS = ("source", "target", "evidence_status", "mechanism")
CONDITION_FIELDS = ("area", "evidence_status", "evidence")
DEFENSIBILITY_FIELDS = (
    "signal",
    "evidence_status",
    "evidence",
    "alternative",
)
NODE_POSITIONS = (
    (800, 275),
    (1170, 430),
    (1070, 735),
    (530, 735),
    (430, 430),
    (800, 845),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render an S5 profitable-scaling flywheel from JSON."
    )
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 JSON input")
    parser.add_argument("--output", required=True, type=Path, help="SVG or HTML output")
    return parser.parse_args()


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def _require_object(
    payload: dict[str, Any], key: str, fields: tuple[str, ...]
) -> dict[str, str]:
    value = payload.get(key)
    if not isinstance(value, dict) or set(value) != set(fields):
        raise ValueError(f"{key} must contain exactly {', '.join(fields)}")
    return {field: _require_text(value[field], f"{key}.{field}") for field in fields}


def _require_items(
    payload: dict[str, Any],
    key: str,
    fields: tuple[str, ...],
    *,
    minimum: int,
    maximum: int,
) -> list[dict[str, str]]:
    value = payload.get(key)
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise ValueError(f"{key} must contain {minimum} to {maximum} items")
    items: list[dict[str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict) or set(item) != set(fields):
            raise ValueError(
                f"{key}[{index}] must contain exactly {', '.join(fields)}"
            )
        normalized = {
            field: _require_text(item[field], f"{key}[{index}].{field}")
            for field in fields
        }
        if "evidence_status" in normalized:
            _require_status(normalized["evidence_status"], f"{key}[{index}]")
        items.append(normalized)
    return items


def _require_status(status: str, label: str) -> None:
    if status not in EVIDENCE_STATUSES:
        raise ValueError(f"{label}.evidence_status must be 已确认, 假设, or 缺口")


def _safe_html_href(payload: dict[str, Any]) -> str:
    href = _require_text(
        payload.get("diagnosis_report_href", "stage-diagnosis-report.html"),
        "diagnosis_report_href",
    )
    path = Path(href)
    unsafe = (
        ":" in href
        or "\\" in href
        or href.startswith(("/", "#"))
        or path.is_absolute()
        or ".." in path.parts
        or path.suffix.lower() != ".html"
    )
    if unsafe:
        raise ValueError("diagnosis_report_href must be a safe local .html path")
    return href


def _shorten(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "…"


def _svg_text(
    value: str,
    x: int,
    y: int,
    *,
    width: int,
    max_lines: int,
    css_class: str = "body",
    anchor: str = "start",
) -> str:
    compact = " ".join(value.split())
    lines = [compact[i : i + width] for i in range(0, len(compact), width)] or [""]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = _shorten(lines[-1], max(2, width - 1))
    return "".join(
        f'<text x="{x}" y="{y + index * 22}" class="{css_class}" '
        f'text-anchor="{anchor}">{html.escape(line)}</text>'
        for index, line in enumerate(lines)
    )


def _label(status: str) -> str:
    return f"[{status}]"


def _normalize(payload: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {
        key: _require_text(payload.get(key), key)
        for key in (
            "title",
            "stage",
            "decision",
            "replication_unit",
            "target_replication",
            "weakest_link",
            "priority_validation",
            "stop_line",
            "evidence_summary",
        )
    }
    if normalized["stage"] != "S5":
        raise ValueError("stage must be S5")

    profit = _require_object(payload, "profit_engine", PROFIT_FIELDS)
    _require_status(profit["evidence_status"], "profit_engine")
    if profit["evidence_status"] != "已确认":
        raise ValueError(
            "confirmed profit evidence is required for an S5 action report"
        )

    nodes = _require_items(
        payload, "flywheel_nodes", NODE_FIELDS, minimum=4, maximum=6
    )
    links = _require_items(
        payload, "flywheel_links", LINK_FIELDS, minimum=4, maximum=6
    )
    labels = {node["label"] for node in nodes}
    if any(link["source"] not in labels or link["target"] not in labels for link in links):
        raise ValueError("flywheel_links must reference existing node labels")

    normalized.update(
        {
            "profit_engine": profit,
            "flywheel_nodes": nodes,
            "flywheel_links": links,
            "replication_conditions": _require_items(
                payload,
                "replication_conditions",
                CONDITION_FIELDS,
                minimum=1,
                maximum=6,
            ),
            "defensibility_signals": _require_items(
                payload,
                "defensibility_signals",
                DEFENSIBILITY_FIELDS,
                minimum=1,
                maximum=4,
            ),
            "diagnosis_report_href": _safe_html_href(payload),
        }
    )
    return normalized


def render(payload: dict[str, Any]) -> str:
    data = _normalize(payload)
    profit = data["profit_engine"]
    nodes = data["flywheel_nodes"]

    node_svg: list[str] = []
    for index, node in enumerate(nodes):
        x, y = NODE_POSITIONS[index]
        node_svg.append(
            f'<circle cx="{x}" cy="{y}" r="112" class="node status-{node["evidence_status"]}"/>'
        )
        node_svg.append(
            _svg_text(node["label"], x, y - 24, width=10, max_lines=1, css_class="node-title", anchor="middle")
        )
        node_svg.append(
            _svg_text(_label(node["evidence_status"]), x, y + 8, width=10, max_lines=1, css_class="status", anchor="middle")
        )
        node_svg.append(
            _svg_text(node["evidence"], x, y + 38, width=12, max_lines=2, css_class="small", anchor="middle")
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1100" viewBox="0 0 1600 1100">
  <style>
    .brand {{ font: 600 22px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif; fill:#fff; }}
    .title {{ font: 700 38px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif; fill:#172238; }}
    .body {{ font: 400 17px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif; fill:#27354d; }}
    .small {{ font: 500 14px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif; fill:#526176; }}
    .node-title {{ font: 700 21px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif; fill:#172238; }}
    .status {{ font: 700 15px -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif; fill:#27354d; }}
    .node {{ stroke-width:4; }}
    .status-已确认 {{ fill:#dff3ee; stroke:#16826f; }}
    .status-假设 {{ fill:#fff1cf; stroke:#d88324; }}
    .status-缺口 {{ fill:#ffe5e5; stroke:#c94b55; stroke-dasharray:10 7; }}
  </style>
  <defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#536aa3"/></marker></defs>
  <rect width="1600" height="1100" fill="#f3f6fa"/>
  <rect width="1600" height="86" fill="#172238"/>
  <text x="60" y="56" class="brand">BMI 兴远咨询 · S5 盈利复制飞轮</text>
  <text x="1540" y="56" class="brand" text-anchor="end">BMI Kenny</text>
  <text x="60" y="142" class="title">{html.escape(_shorten(data["title"], 34))}</text>
  {_svg_text(f'核心判断｜{data["decision"]}', 60, 184, width=72, max_lines=1)}
  {_svg_text(f'复制单元｜{data["replication_unit"]}', 60, 218, width=72, max_lines=1)}
  <path d="M800 275 C1290 245 1390 780 1070 735 C830 1030 400 920 530 735 C170 570 320 220 800 275" fill="none" stroke="#536aa3" stroke-width="5" marker-end="url(#arrow)" opacity=".65"/>
  {''.join(node_svg)}
  <circle cx="800" cy="545" r="145" fill="#172238"/>
  <text x="800" y="515" class="brand" text-anchor="middle">盈利复制飞轮</text>
  {_svg_text(f'{_label(profit["evidence_status"])} {profit["contribution_profit"]}', 800, 550, width=18, max_lines=3, css_class="brand", anchor="middle")}
  {_svg_text(f'最弱连接｜{data["weakest_link"]}', 800, 635, width=19, max_lines=2, css_class="brand", anchor="middle")}
  <rect x="60" y="940" width="1480" height="62" rx="16" fill="#fff1cf"/>
  {_svg_text(f'目标复制｜{data["target_replication"]}', 82, 968, width=70, max_lines=1)}
  {_svg_text(f'30 天验证｜{data["priority_validation"]}', 82, 994, width=70, max_lines=1)}
  <rect x="60" y="1018" width="1480" height="48" rx="14" fill="#ffe5e5"/>
  {_svg_text(f'停止线｜{data["stop_line"]}', 82, 1048, width=72, max_lines=1)}
</svg>'''


def render_html(payload: dict[str, Any]) -> str:
    data = _normalize(payload)
    svg = render(payload)
    conditions = "".join(
        f'<tr><td>{html.escape(item["area"])}</td><td>{html.escape(_label(item["evidence_status"]))}</td><td>{html.escape(item["evidence"])}</td></tr>'
        for item in data["replication_conditions"]
    )
    defensibility = "".join(
        f'<tr><td>{html.escape(item["signal"])}</td><td>{html.escape(_label(item["evidence_status"]))}</td><td>{html.escape(item["evidence"])}</td><td>{html.escape(item["alternative"])}</td></tr>'
        for item in data["defensibility_signals"]
    )
    flywheel_links = "".join(
        f'<tr><td>{html.escape(link["source"])} → {html.escape(link["target"])}</td>'
        f'<td>{html.escape(_label(link["evidence_status"]))}</td>'
        f'<td>{html.escape(link["mechanism"])}</td></tr>'
        for link in data["flywheel_links"]
    )
    href = html.escape(data["diagnosis_report_href"], quote=True)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>S5 稳步复制行动报告</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#f3f6fa;color:#172238;font:15px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}main{{max-width:1660px;margin:auto;padding:24px}}section{{background:#fff;border:1px solid #d9e0ec;border-radius:16px;padding:14px;margin:14px 0;overflow:auto}}svg{{display:block;width:100%;height:auto}}table{{width:100%;border-collapse:collapse}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #d9e0ec}}th{{background:#eef2f8}}.summary{{color:#52627a}}@media(max-width:600px){{main{{padding:10px}}th,td{{padding:7px}}}}@media print{{body{{background:#fff}}main{{padding:0}}}}</style>
</head><body><main data-report="s5-action"><header><h1>S5 稳步复制行动报告</h1><p class="summary">{html.escape(data["evidence_summary"])}</p></header>
<section data-section="stage-method">{svg}</section>
<section data-section="flywheel-links"><h2>飞轮连接证据</h2><table><thead><tr><th>连接</th><th>状态</th><th>机制与证据</th></tr></thead><tbody>{flywheel_links}</tbody></table></section>
<section data-section="profit-engine"><h2>盈利引擎与口径</h2><table><tbody><tr><th>证据状态</th><td>{html.escape(_label(data["profit_engine"]["evidence_status"]))}</td></tr><tr><th>单元与期间</th><td>{html.escape(data["profit_engine"]["scope_period"])}</td></tr><tr><th>贡献利润</th><td>{html.escape(data["profit_engine"]["contribution_profit"])}</td></tr><tr><th>经营利润与现金边界</th><td>{html.escape(data["profit_engine"]["operating_cash_boundary"])}</td></tr></tbody></table></section>
<section data-section="replication-conditions"><h2>复制条件</h2><table><thead><tr><th>载体</th><th>状态</th><th>证据</th></tr></thead><tbody>{conditions}</tbody></table></section>
<section data-section="defensibility"><h2>护城河或定价权</h2><table><thead><tr><th>信号</th><th>状态</th><th>证据</th><th>替代解释</th></tr></thead><tbody>{defensibility}</tbody></table></section>
<p><a href="{href}">返回阶段诊断报告</a></p></main></body></html>'''


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
