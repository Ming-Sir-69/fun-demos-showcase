#!/usr/bin/env python3
"""Export a draw.io file through official draw.io Desktop when available."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


DEFAULT_MAC_APP = Path("/Applications/draw.io.app/Contents/MacOS/draw.io")


def resolve_drawio(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    if DEFAULT_MAC_APP.exists():
        return str(DEFAULT_MAC_APP)
    return shutil.which("drawio") or shutil.which("draw.io") or shutil.which("diagrams.net")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export .drawio via official draw.io Desktop.")
    parser.add_argument("--input", "-i", required=True, help="Input .drawio file.")
    parser.add_argument("--output", "-o", required=True, help="Output PNG/PDF/SVG/JPG path.")
    parser.add_argument("--format", "-f", choices=["png", "pdf", "svg", "jpg", "jpeg"], required=True)
    parser.add_argument("--drawio-bin", help="Path to draw.io Desktop executable.")
    parser.add_argument("--crop", action="store_true", help="Pass --crop to draw.io Desktop.")
    args = parser.parse_args()

    drawio = resolve_drawio(args.drawio_bin)
    if not drawio:
        print("draw.io Desktop executable not found. Keep .drawio as the primary deliverable.")
        return 2

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [drawio, "--export", "--format", args.format, "--output", str(output)]
    if args.crop:
        cmd.append("--crop")
    cmd.append(args.input)

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"draw.io Desktop export failed with exit code {result.returncode}.")
        print("This is an export-adapter problem, not necessarily a renderer problem.")
        return result.returncode
    if not output.exists() or output.stat().st_size == 0:
        print("draw.io Desktop reported success but no output file was created.")
        return 1
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
