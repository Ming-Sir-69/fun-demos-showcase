#!/usr/bin/env python3
"""Render a controlled JSON DSL file to a validated draw.io file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from diagram_renderer.cli import render_command  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Render JSON DSL to draw.io.")
    parser.add_argument("--input", "-i", required=True, help="Input JSON DSL path.")
    parser.add_argument("--output", "-o", required=True, help="Output .drawio path.")
    parser.add_argument("--skip-validation", action="store_true", help="Skip validation checks.")
    args = parser.parse_args()

    class RenderArgs:
        input = args.input
        output = args.output
        skip_validation = args.skip_validation

    return render_command(RenderArgs)


if __name__ == "__main__":
    raise SystemExit(main())
