---
name: human-factors-diagram-renderer
description: Render clean, human-readable solution diagrams from controlled JSON DSL into validated draw.io files. Use when the user asks to create, improve, validate, package, or troubleshoot architecture diagrams, decision trees, swimlane flows, RAG/data flows, 8D/process diagrams, Mermaid-to-JSON diagram workflows, draw.io visual QA, diagram style consistency, or reusable diagram-generation demos. This is not the official drawio skill; it is a human-factors renderer that outputs draw.io.
---

# Human Factors Diagram Renderer

Status: demo-stable skill package. The renderer is usable for the bundled examples and for controlled JSON DSL inputs that follow the included schema. Treat new visual families as profile extensions, not as ad hoc draw.io edits.

Use this skill to turn semantic diagram content into readable, validated `.drawio` diagrams. The core idea is:

```text
controlled JSON DSL -> deterministic renderer -> draw.io file -> validation -> human visual review
```

Keep AI responsible for content logic. Keep layout, style, connection routing, icons, draw.io XML, and validation inside the renderer.

## Core Rules

- Do not ask the AI to write draw.io XML, `mxCell`, `mxGeometry`, style strings, base64 icons, or waypoint coordinates.
- Do not redesign the DSL casually. If a new diagram type is needed, first decide whether it is a layout profile, a semantic node/edge extension, or a true new `diagram_type`.
- Treat `.drawio` as the primary deliverable. PNG/PDF export is optional and should use official draw.io Desktop when available.
- Do not trust non-official preview renderers for final visual acceptance. If preview output differs from diagrams.net/draw.io, trust draw.io.
- When a user reports a visual or semantic issue, log it with `scripts/log_issue.py` before or during the fix so future iterations compound.
- Prefer the bundled rules over the official draw.io skill when the goal is this project's human-factors diagram style. Use draw.io Desktop only as an export adapter.

## Quick Start

Run C0 schema validation before rendering:

```bash
python scripts/validate_dsl.py \
  --input assets/examples/json/chart04_rag_sequence_flow_r01.json
```

Render one JSON file:

```bash
python scripts/render_diagram.py \
  --input assets/examples/json/chart04_rag_sequence_flow_r01.json \
  --output /tmp/chart04_rag_sequence_flow_r01.drawio
```

Validate all bundled examples:

```bash
python scripts/validate_examples.py
```

Log a reported issue:

```bash
python scripts/log_issue.py \
  --title "Chart04 legend too close to main content" \
  --chart chart04 \
  --description "User reports the legend lacks breathing room." \
  --screenshot /absolute/path/to/screenshot.png
```

Try official draw.io Desktop export, if installed:

```bash
python scripts/export_drawio_desktop.py \
  --input /tmp/chart04_rag_sequence_flow_r01.drawio \
  --format png \
  --output /tmp/chart04_rag_sequence_flow_r01.png
```

## Workflow

0. Read `references/pitfalls.md` when creating a new chart family, debugging a visual issue, changing routing/layout logic, or seeing a repeated failure.
1. Read or create the JSON DSL.
2. Run C0 schema validation with `scripts/validate_dsl.py`.
3. Check `references/diagram_dsl_v0_1_spec.md` and `references/diagram_dsl_v0_1_schema.json` if fields or diagram types are unclear.
4. Render with `scripts/render_diagram.py`. Rendering also runs C0 before XML generation.
5. Run validation. Rendering already runs built-in validators unless `--skip-validation` is passed.
6. Ask the user to open the `.drawio` in diagrams.net/draw.io for final visual review.
7. If the user reports an issue, record it with `scripts/log_issue.py`, then fix the lowest responsible layer:
   - Content wording issue: update JSON.
   - Style/spacing/connection issue: update renderer or style rules.
   - New diagram family: extend profile rules after preserving existing examples.
8. Re-run `scripts/validate_examples.py` before claiming the skill is stable.

## Bundled Resources

Use progressive disclosure. Load only the files needed for the current task.

| Path | Purpose |
|------|---------|
| `scripts/diagram_renderer/` | Self-contained Python renderer package |
| `scripts/validate_dsl.py` | C0 JSON DSL schema validation wrapper |
| `scripts/render_diagram.py` | Stable JSON-to-drawio wrapper |
| `scripts/validate_examples.py` | Regression check for bundled examples |
| `scripts/export_drawio_desktop.py` | Optional official draw.io Desktop PNG/PDF export |
| `scripts/log_issue.py` | Append issue reports and copy screenshots into `logs/` |
| `references/workflow.md` | End-to-end drawing process |
| `references/style_rules.md` | Visual style, color, typography, icon, legend rules |
| `references/validation.md` | Automated and human acceptance checks |
| `references/pitfalls.md` | Known failure modes and prevention rules |
| `references/diagram_dsl_v0_1_spec.md` | DSL contract |
| `references/diagram_dsl_v0_1_schema.json` | JSON schema boundary |
| `references/ai_to_dsl_prompt_v0_1.md` | Prompt template for AI-to-DSL conversion |
| `assets/examples/json/` | Accepted JSON examples |
| `assets/examples/drawio/` | Accepted draw.io outputs |
| `logs/` | Issue log and screenshots collected during real use |

## Current Diagram Types

Do not mix up top-level `diagram_type` and `layout.mode`.

| Capability | How to select it | Status | Use when |
|------------|------------------|--------|----------|
| Layered architecture | `diagram_type: layered_architecture` | ✅ Available, regression-covered | Layered system or solution architecture |
| Decision tree flowchart | `diagram_type: flowchart_decision_tree` or `decision_tree` | ✅ Available, regression-covered | Explicit condition-node decision tree |
| RAG sequence flow | `diagram_type: rag_sequence_flow` or `layout.mode: rag_sequence_flow` | ✅ Available, regression-covered; layout lives in the flowchart module | Swimlane RAG/data retrieval flow |
| Stage-gated swimlane | `layout.mode: stage_gated_swimlane` | ✅ Available as a layout profile, regression-covered | 8D or stage-gated human/AI boundary flow |
| Stage-gated snake | `layout.mode: stage_gated_snake` | 🔶 Partial visual acceptance; available but less validated | Dense top-to-bottom process flows |
| New top-level diagram families | Add schema, examples, validators, and docs first | ❌ Planned only after acceptance criteria exist | New chart families that existing profiles cannot express |

If a requested chart does not match these capabilities, first try the closest layout profile and record the mismatch. Only promote it to a new top-level `diagram_type` after adding schema, examples, validators, and regression coverage.

## Acceptance Standard

Before handing output to a user:

- C0: Run `scripts/validate_dsl.py --input <json>` or confirm `scripts/render_diagram.py` passed its built-in C0 schema gate.
- Run the renderer without validation failures.
- Confirm `.drawio` has exactly one page unless the user explicitly requests a workbook.
- Confirm the draw.io page tab has a semantic name.
- Confirm no raw draw.io style leaks into JSON.
- Confirm icons are vector SVG data URIs, not low-resolution PNGs.
- Confirm nodes fit within containers/lanes and text has breathing room.
- Confirm edge endpoints exist and edge routing avoids foreground nodes.
- Keep final visual acceptance with the user in diagrams.net/draw.io.

## Draw.io Export Policy

Use official draw.io Desktop only as an optional export adapter for PNG/PDF. If it fails, keep `.drawio` as the deliverable and log the export problem. Do not use unofficial previews as visual truth.

## Runtime Dependencies

- Core rendering: Python 3, standard library only.
- Optional PNG/PDF export: official draw.io Desktop.
- Optional skill package validation: PyYAML may be needed by external skill-creator validators, but it is not required by the renderer itself.
