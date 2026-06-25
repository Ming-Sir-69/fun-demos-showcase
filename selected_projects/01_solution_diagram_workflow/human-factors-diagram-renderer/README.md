# Human Factors Diagram Renderer

Turn controlled JSON DSL into readable, validated draw.io diagrams.

This folder is a portable Codex skill package. It is intentionally separate from the official draw.io skill: draw.io is the file format and optional export tool; this package owns the human-factors rendering rules.

## Quick Start

Render one bundled example:

```bash
python scripts/validate_dsl.py \
  --input assets/examples/json/chart04_rag_sequence_flow_r01.json

python scripts/render_diagram.py \
  --input assets/examples/json/chart04_rag_sequence_flow_r01.json \
  --output /tmp/chart04_rag_sequence_flow_r01.drawio
```

Validate all examples:

```bash
python scripts/validate_examples.py
```

Log a visual issue:

```bash
python scripts/log_issue.py \
  --title "Legend is too close to content" \
  --chart chart04 \
  --description "The legend needs more breathing room." \
  --screenshot /absolute/path/to/screenshot.png
```

Optional install:

```bash
bash install.sh
```

## What It Supports

| Capability | Selection | Status |
|------------|-----------|--------|
| Layered architecture | `diagram_type: layered_architecture` | ✅ Available |
| Decision tree flowchart | `diagram_type: flowchart_decision_tree` or `decision_tree` | ✅ Available |
| RAG sequence flow | `diagram_type: rag_sequence_flow` or `layout.mode: rag_sequence_flow` | ✅ Available |
| Stage-gated swimlane | `layout.mode: stage_gated_swimlane` | ✅ Available as a layout profile |
| Stage-gated snake | `layout.mode: stage_gated_snake` | 🔶 Partial visual acceptance |

Core rendering uses Python standard library only. Optional PNG/PDF export uses official draw.io Desktop through `scripts/export_drawio_desktop.py`.

## Deliverable Rule

The `.drawio` file is the source of truth. PNG/PDF exports are secondary and should be checked against diagrams.net/draw.io if visual differences appear.
