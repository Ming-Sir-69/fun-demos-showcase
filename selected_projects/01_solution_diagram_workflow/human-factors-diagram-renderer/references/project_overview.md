# Project Overview

This skill is a self-contained human-factors diagram renderer. It packages the working renderer, controlled DSL references, accepted examples, validation scripts, and issue logging workflow into one portable folder.

It is not the official draw.io skill. The official draw.io toolchain is useful as an export adapter, but this skill owns the diagram rules: layout, spacing, color, typography, icons, routing, page naming, and validation.

## Core Chain

```text
human or AI process content
-> controlled JSON DSL
-> deterministic Python renderer
-> validated .drawio file
-> human visual acceptance in diagrams.net/draw.io
```

The AI should describe content and intent. It should not handcraft draw.io XML, coordinates, style strings, `mxCell`, `mxGeometry`, or base64 icon data.

## Portable File Map

| Path | Role |
|------|------|
| `SKILL.md` | Skill entry point and operating contract |
| `README.md` | Human-facing GitHub quick start |
| `install.sh` | Optional installer into local Codex or Claude skill folders |
| `scripts/diagram_renderer/` | Self-contained Python renderer package |
| `scripts/validate_dsl.py` | C0 JSON DSL schema validation wrapper |
| `scripts/render_diagram.py` | Single JSON-to-drawio command wrapper |
| `scripts/validate_examples.py` | Regression check for all bundled examples |
| `scripts/export_drawio_desktop.py` | Optional official draw.io Desktop export wrapper |
| `scripts/log_issue.py` | Issue logger with screenshot copying |
| `references/diagram_dsl_v0_1_spec.md` | DSL contract and field meaning |
| `references/diagram_dsl_v0_1_schema.json` | Machine-checkable schema boundary |
| `references/style_rules.md` | Visual style rules and human-factors heuristics |
| `references/validation.md` | Automated and human acceptance rules |
| `references/pitfalls.md` | Known failure modes and prevention rules |
| `assets/examples/json/` | Accepted JSON examples |
| `assets/examples/drawio/` | Accepted draw.io outputs |
| `logs/` | Runtime issue log folder |

All paths above are relative to the skill folder. The skill must not depend on the parent project directory after installation.

## Capability Status

| Capability | Selection | Status |
|------------|-----------|--------|
| Layered architecture | `diagram_type: layered_architecture` | ✅ Available and regression-covered |
| Decision tree flowchart | `diagram_type: flowchart_decision_tree` or `decision_tree` | ✅ Available and regression-covered |
| RAG sequence flow | `diagram_type: rag_sequence_flow` or `layout.mode: rag_sequence_flow` | ✅ Available and regression-covered |
| Stage-gated swimlane | `layout.mode: stage_gated_swimlane` | ✅ Available as a layout profile and regression-covered |
| Stage-gated snake | `layout.mode: stage_gated_snake` | 🔶 Partial visual acceptance |
| New top-level diagram families | Add schema, examples, validators, and docs first | ❌ Planned only after acceptance criteria exist |

Use top-level `diagram_type` for genuinely different diagram families. Use `layout.mode` for different layout profiles inside a related family.

## Quality Bar

A generated diagram is not accepted just because a file exists. It must pass these checks:

- The renderer and validators complete without errors.
- C0 schema validation passes before XML generation.
- The draw.io file has one semantic page name unless a workbook is explicitly requested.
- Node text fits inside visible containers and lanes.
- Lane titles are clear, centered, and visually stronger than ordinary node text.
- Colors encode stable semantic roles, not arbitrary sequence order.
- Edge endpoints exist and routes avoid foreground nodes.
- Legends explain line semantics and only explain node colors when color meaning is not already obvious from labels.
- Final visual acceptance happens in diagrams.net/draw.io, not in unofficial preview renderers.

## Evolution Rule

When a new user chart exposes a weakness, do not patch only that chart. Record the issue, identify the lowest responsible layer, and improve the reusable rule:

- Content wording problem: fix JSON content or AI-to-DSL prompt guidance.
- Visual grammar problem: fix style rules, spacing rules, icon rules, or layout profile.
- Routing problem: fix connection selection, branch/merge logic, or validators.
- New family problem: add schema, examples, validators, regression coverage, then document the new capability.
