"""Command-line interface for rendering and validating diagrams."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from .drawio_xml import DrawioRenderer
from .schema import load_dsl_from_json, validate_dsl_schema
from .validators import run_validations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Controlled JSON DSL -> draw.io renderer.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render", help="Render a JSON DSL file to draw.io XML.")
    render_parser.add_argument("--input", "-i", required=True, help="Path to input JSON DSL.")
    render_parser.add_argument("--output", "-o", required=True, help="Path to output .drawio file.")
    render_parser.add_argument("--schema", help="Optional schema path for C0 DSL validation.")
    render_parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Write output without running DSL/XML/renderer validators.",
    )

    validate_parser = subparsers.add_parser("validate", help="Run C0 JSON DSL schema validation.")
    validate_parser.add_argument("--input", "-i", required=True, help="Path to input JSON DSL.")
    validate_parser.add_argument("--schema", help="Optional schema path for C0 DSL validation.")

    return parser


def validate_command(args: argparse.Namespace) -> int:
    dsl = load_dsl_from_json(args.input)
    errors = validate_dsl_schema(dsl, getattr(args, "schema", None))
    if errors:
        print("[FAIL] C0 schema validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("[PASS] C0 schema validation passed.")
    return 0


def render_command(args: argparse.Namespace) -> int:
    dsl = load_dsl_from_json(args.input)
    schema_errors = validate_dsl_schema(dsl, getattr(args, "schema", None))
    if schema_errors:
        print("[FAIL] C0 schema validation failed:")
        for error in schema_errors:
            print(f"- {error}")
        return 1

    renderer = DrawioRenderer(dsl)
    xml_text = renderer.to_xml()

    if not args.skip_validation:
        if not run_validations(dsl, xml_text, renderer):
            return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(xml_text, encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"Vertices: {len(renderer.vertices)}")
    print(f"Edges: {len(renderer.edges)}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "render":
        return render_command(args)
    if args.command == "validate":
        return validate_command(args)
    parser.error(f"Unsupported command: {args.command}")
    return 2
