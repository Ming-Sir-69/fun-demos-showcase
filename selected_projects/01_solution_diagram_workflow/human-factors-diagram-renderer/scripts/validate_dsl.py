#!/usr/bin/env python3
"""Run C0 schema validation for a controlled JSON DSL file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from diagram_renderer.cli import validate_command  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate JSON DSL against the bundled schema.")
    parser.add_argument("--input", "-i", required=True, help="Input JSON DSL path.")
    parser.add_argument("--schema", help="Optional schema path.")
    args = parser.parse_args()

    class ValidateArgs:
        input = args.input
        schema = args.schema

    return validate_command(ValidateArgs)


if __name__ == "__main__":
    raise SystemExit(main())
