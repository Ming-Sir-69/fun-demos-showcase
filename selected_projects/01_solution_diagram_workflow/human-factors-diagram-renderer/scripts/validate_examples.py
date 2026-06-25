#!/usr/bin/env python3
"""Render all bundled examples into a temporary directory and validate them."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DIR = SKILL_ROOT / "assets" / "examples" / "json"
RENDER_SCRIPT = SKILL_ROOT / "scripts" / "render_diagram.py"


def main() -> int:
    examples = sorted(EXAMPLE_DIR.glob("*.json"))
    if not examples:
        print("No example JSON files found.", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="hfdr_examples_") as tmp:
        tmp_dir = Path(tmp)
        for src in examples:
            out = tmp_dir / f"{src.stem}.drawio"
            cmd = [sys.executable, str(RENDER_SCRIPT), "--input", str(src), "--output", str(out)]
            print(f"Rendering {src.name} -> {out.name}")
            result = subprocess.run(cmd, cwd=SKILL_ROOT)
            if result.returncode != 0:
                print(f"FAILED: {src.name}", file=sys.stderr)
                return result.returncode
            if not out.exists() or out.stat().st_size == 0:
                print(f"FAILED: output missing for {src.name}", file=sys.stderr)
                return 1

    print(f"OK: rendered and validated {len(examples)} examples.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
