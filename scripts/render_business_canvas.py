#!/usr/bin/env python3
"""Render a compact BMI business-stage action canvas as SVG."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


SECTION_LAYOUT = (
    ("customer", "客户定位", 60, 250, 480, 230),
    ("value", "价值主张", 560, 250, 480, 230),
    ("activities", "关键活动", 1060, 250, 480, 230),
    ("evidence", "现有证据", 60, 510, 480, 260),
    ("next_step", "下一步验证", 560, 510, 480, 260),
    ("stop_line", "停止线", 1060, 510, 480, 260),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a BMI business-stage action canvas from JSON."
    )
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 JSON input")
    parser.add_argument("--output", required=True, type=Path, help="SVG output path")
    return parser.parse_args()


def _require_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _normalize_sections(payload: dict[str, Any]) -> dict[str, list[str]]:
    raw = payload.get("sections")
    if not isinstance(raw, dict):
        raise ValueError("sections must be an object")

    sections: dict[str, list[str]] = {}
    for key, *_ in SECTION_LAYOUT:
        values = raw.get(key)
        if not isinstance(values, list) or not values:
            raise ValueError(f"sections.{key} must be a non-empty list")
        cleaned = [value.strip() for value in values if isinstance(value, str) and value.strip()]
        if not cleaned:
            raise ValueError(f"sections.{key} must contain text")
        sections[key] = cleaned[:3]
    return sections


def _wrap_text(value: str, width: int = 24) -> list[str]:
    compact = " ".join(value.split())
    return [compact[index : index + width] for index in range(0, len(compact), width)] or ["待验证"]


def _text_lines(
    lines: list[str],
    x: int,
    y: int,
    line_height: int = 35,
    width: int = 17,
    max_lines: int = 5,
) -> str:
    wrapped_lines: list[str] = []
    for line in lines:
        wrapped_lines.extend(_wrap_text(f"• {line}", width=width))
    if len(wrapped_lines) > max_lines:
        wrapped_lines = wrapped_lines[:max_lines]
        wrapped_lines[-1] = wrapped_lines[-1][:-1] + "…"

    parts = []
    current_y = y
    for wrapped in wrapped_lines:
        parts.append(
            f'<text x="{x}" y="{current_y}" class="body">'
            f"{html.escape(wrapped)}"
            "</text>"
        )
        current_y += line_height
    return "\n".join(parts)


def _shorten(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[: limit - 1] + "…"


def render(payload: dict[str, Any]) -> str:
    title = _require_text(payload, "title")
    stage = _require_text(payload, "stage")
    decision = _require_text(payload, "decision")
    sections = _normalize_sections(payload)

    cards = []
    for key, label, x, y, width, height in SECTION_LAYOUT:
        cards.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="24" class="card"/>'
        )
        cards.append(f'<text x="{x + 30}" y="{y + 52}" class="label">{label}</text>')
        cards.append(_text_lines(sections[key], x + 30, y + 105))

    safe_title = html.escape(_shorten(title, 22))
    safe_stage = html.escape(_shorten(stage, 30))
    decision_lines = _text_lines(
        [decision], 90, 207, line_height=38, width=58, max_lines=1
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
  <style>
    .title {{ font: 700 44px -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; fill: #172238; }}
    .brand {{ font: 600 24px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #ffffff; }}
    .stage {{ font: 600 25px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #14645a; }}
    .label {{ font: 700 27px -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; fill: #172238; }}
    .body {{ font: 400 24px -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif; fill: #27354d; }}
    .card {{ fill: #ffffff; stroke: #d7dfeb; stroke-width: 2; }}
  </style>
  <rect width="1600" height="900" fill="#f3f6fa"/>
  <rect width="1600" height="92" fill="#172238"/>
  <text x="60" y="60" class="brand">BMI 兴远咨询 · 商业阶段行动画布</text>
  <text x="1540" y="60" text-anchor="end" class="brand">增长看方向，经营要算账</text>
  <text x="60" y="145" class="title">{safe_title}</text>
  <rect x="1120" y="115" width="420" height="55" rx="27" fill="#dff3ee"/>
  <text x="1330" y="151" text-anchor="middle" class="stage">{safe_stage}</text>
  <rect x="60" y="170" width="1480" height="58" rx="18" fill="#fff1cf"/>
  {decision_lines}
  {''.join(cards)}
  <text x="60" y="842" class="body">当前内容是可纠正初判；“待验证”不等于事实。</text>
  <text x="1540" y="842" text-anchor="end" class="body">BMI Kenny</text>
</svg>'''


def main() -> int:
    args = _parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        svg = render(payload)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(svg, encoding="utf-8")
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
