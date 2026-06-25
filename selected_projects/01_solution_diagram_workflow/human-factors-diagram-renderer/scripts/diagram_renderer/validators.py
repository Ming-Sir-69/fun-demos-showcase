"""DSL, XML, and renderer validation helpers."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
import xml.etree.ElementTree as ET

from .icons import ICON_SIMILARITY_THRESHOLD, ICON_SVG_BODY, icon_similarity
from .spacing import LEGEND_CONTENT_GAP
from .styles import EDGE_SEMANTICS, NODE_SPECS, edge_visual_family


RAG_LANE_SAFE_X = 20.0
RAG_LANE_SAFE_Y = 16.0
SWIMLANE_SAFE_X = 16.0
SWIMLANE_SAFE_Y = 16.0
LANE_TITLE_FONT_SIZE = "fontSize=15"


def collect_declared_ids(dsl: Dict[str, Any]) -> Dict[str, str]:
    ids: Dict[str, str] = {}
    dtype = dsl.get("diagram_type", "layered_architecture")
    if dtype == "layered_architecture":
        for layer in dsl.get("layers", []):
            ids[f"layer_{layer['id']}_bg"] = "generated_layer_bg"
            ids[f"layer_{layer['id']}_rail"] = "generated_layer_rail"
            for node in layer.get("nodes", []):
                ids[node["id"]] = node["type"]
            for group in layer.get("groups", []):
                ids[group["id"]] = group["type"]
                for node in group.get("nodes", []):
                    ids[node["id"]] = node["type"]
        for label in dsl.get("labels", []):
            ids[label["id"]] = label["type"]
    else:
        for node in dsl.get("nodes", []):
            ids[node["id"]] = node["type"]
    return ids


def iter_icon_assignments(dsl: Dict[str, Any]) -> List[Dict[str, str]]:
    assignments: List[Dict[str, str]] = []

    def add_node(node: Dict[str, Any]):
        node_type = node.get("type")
        spec = NODE_SPECS.get(node_type, {})
        icon = node.get("icon") or spec.get("icon")
        if icon:
            assignments.append({
                "id": node.get("id", ""),
                "title": node.get("title", ""),
                "type": node_type or "",
                "icon": icon,
                "semantic": node.get("semantic", node.get("subtitle", node.get("title", ""))),
            })

    if dsl.get("diagram_type", "layered_architecture") == "layered_architecture":
        for layer in dsl.get("layers", []):
            for node in layer.get("nodes", []):
                add_node(node)
            for group in layer.get("groups", []):
                for node in group.get("nodes", []):
                    add_node(node)
    else:
        for node in dsl.get("nodes", []):
            add_node(node)
    return assignments


def validate_icon_governance(dsl: Dict[str, Any]) -> List[Tuple[str, bool, str]]:
    """Scripted version of the guide's icon de-dup check plus SVG-similarity screening."""
    results: List[Tuple[str, bool, str]] = []
    assignments = iter_icon_assignments(dsl)

    unknown = sorted({a["icon"] for a in assignments if a["icon"] not in ICON_SVG_BODY})
    results.append(("Icon keys exist in local SVG registry", not unknown, f"unknown={unknown}"))

    by_icon: Dict[str, List[Dict[str, str]]] = {}
    for a in assignments:
        by_icon.setdefault(a["icon"], []).append(a)
    exact_reuse = {icon: [(a["id"], a["title"], a["type"]) for a in uses] for icon, uses in by_icon.items() if len(uses) > 1}
    results.append(("No exact icon reuse across rendered nodes", not exact_reuse, f"reuse={exact_reuse}"))

    used_icons = sorted(by_icon.keys())
    similar_pairs = []
    for i, icon_a in enumerate(used_icons):
        for icon_b in used_icons[i + 1:]:
            score = icon_similarity(icon_a, icon_b)
            if score >= ICON_SIMILARITY_THRESHOLD:
                users_a = [(a["id"], a["title"]) for a in by_icon[icon_a]]
                users_b = [(a["id"], a["title"]) for a in by_icon[icon_b]]
                similar_pairs.append((icon_a, icon_b, round(score, 3), users_a, users_b))
    results.append((
        f"No near-duplicate SVG icons above {ICON_SIMILARITY_THRESHOLD}",
        not similar_pairs,
        f"similar_pairs={similar_pairs}",
    ))

    return results


def validate_dsl(dsl: Dict[str, Any]) -> List[Tuple[str, bool, str]]:
    results: List[Tuple[str, bool, str]] = []
    results.extend(validate_icon_governance(dsl))
    ids = collect_declared_ids(dsl)
    dtype = dsl.get("diagram_type", "layered_architecture")

    node_types = [kind for kind in ids.values() if not kind.startswith("generated_") and not kind.startswith("group_")]
    unknown_node_types = sorted({t for t in node_types if t not in NODE_SPECS})
    results.append(("DSL node types known", not unknown_node_types, f"unknown={unknown_node_types}"))

    unknown_edge_types = sorted({e.get("type") for e in dsl.get("edges", []) if e.get("type") not in EDGE_SEMANTICS})
    results.append(("DSL edge types known", not unknown_edge_types, f"unknown={unknown_edge_types}"))
    missing = []
    for idx, e in enumerate(dsl.get("edges", []), 1):
        if e.get("source") not in ids:
            missing.append((idx, "source", e.get("source")))
        if e.get("target") not in ids:
            missing.append((idx, "target", e.get("target")))
    results.append(("DSL edge endpoints declared", not missing, f"missing={missing}"))

    if dtype == "layered_architecture":
        labels = {l["id"]: l for l in dsl.get("labels", [])}
        label_mismatch = []
        for e in dsl.get("edges", []):
            target = e.get("target")
            if target in labels:
                expected = labels[target].get("visual_family")
                actual = edge_visual_family(e["type"]) if e.get("type") in EDGE_SEMANTICS else None
                policy = EDGE_SEMANTICS.get(e.get("type"), {}).get("arrow_policy")
                if policy != "label_ingress" or expected != actual:
                    label_mismatch.append((target, e.get("type"), expected, actual, policy))
        results.append(("Label ingress uses label visual family", not label_mismatch, f"mismatch={label_mismatch}"))

        platform_ids = {n["id"] for layer in dsl.get("layers", []) if layer.get("id") == "platform" for n in layer.get("nodes", [])}
        platform_types = sorted({e.get("type") for e in dsl.get("edges", []) if e.get("target") in platform_ids})
        results.append(("Platform-target edges use platform_support", platform_types == ["platform_support"], f"types={platform_types}"))

        legend_types = [item.get("edge_type") for item in dsl.get("legend", [])]
        legend_unknown = [t for t in legend_types if t not in EDGE_SEMANTICS]
        legend_families = [edge_visual_family(t) for t in legend_types if t in EDGE_SEMANTICS]
        results.append(("Legend edge types known", not legend_unknown, f"unknown={legend_unknown}"))
        results.append(("Legend visual families unique", len(legend_families) == len(set(legend_families)), f"families={legend_families}"))
    else:
        rows = dsl.get("rows", [])
        row_ids = [nid for row in rows for nid in row.get("node_ids", [])]
        missing_row_nodes = [nid for nid in row_ids if nid not in ids]
        results.append(("Flow rows reference declared nodes", not missing_row_nodes, f"missing={missing_row_nodes}"))
        duplicate_row_nodes = sorted({nid for nid in row_ids if row_ids.count(nid) > 1})
        results.append(("Flow rows do not duplicate nodes", not duplicate_row_nodes, f"duplicates={duplicate_row_nodes}"))
        edge_labels = [e.get("label", "") for e in dsl.get("edges", []) if e.get("label")]
        results.append(("Decision edges can carry labels", True, f"labeled_edges={len(edge_labels)}"))
        condition_edges = [e for e in dsl.get("edges", []) if e.get("type", "").startswith("label_ingress")]
        condition_nodes = [n.get("id") for n in dsl.get("nodes", []) if n.get("type") == "flow_condition"]
        if condition_edges:
            results.append(("Decision conditions are explicit movable nodes", bool(condition_nodes), f"condition_nodes={condition_nodes}"))
        else:
            results.append(("Decision conditions are explicit movable nodes", True, "not applicable: no label_ingress condition branches"))

    dsl_text = repr(dsl)
    forbidden = ["fillColor=", "strokeColor=", "mxCell", "mxGeometry", "exitX=", "entryX=", "dashPattern="]
    leaked = [token for token in forbidden if token in dsl_text]
    results.append(("DSL has no raw draw.io style leakage", not leaked, f"leaked={leaked}"))
    return results


def validate_xml(xml_text: str) -> List[Tuple[str, bool, str]]:
    results: List[Tuple[str, bool, str]] = []
    root = ET.fromstring(xml_text)
    results.append(("XML parse", True, "XML can be parsed"))
    diagrams = root.findall("diagram")
    page_count = root.get("pages")
    expected_pages = str(len(diagrams))
    results.append(("Single draw.io files declare page count", page_count == expected_pages, f"pages={page_count}, diagrams={len(diagrams)}"))
    page_name_issues = []
    for index, diagram in enumerate(diagrams, 1):
        name = (diagram.get("name") or "").strip()
        if not name or re.fullmatch(r"(Page|第)\s*-?\s*\d+\s*(页)?", name, flags=re.IGNORECASE):
            page_name_issues.append((index, name))
    results.append((
        "Draw.io page tabs have explicit names",
        not page_name_issues,
        f"issues={page_name_issues}" if page_name_issues else "all diagram tabs have semantic names",
    ))

    cells = root.findall(".//*[@id]")
    last_vertex = max((i for i, c in enumerate(cells) if c.get("vertex") == "1"), default=-1)
    first_edge = min((i for i, c in enumerate(cells) if c.get("edge") == "1"), default=-1)
    results.append(("Layer order: all edges after vertices", first_edge > last_vertex, f"first_edge={first_edge}, last_vertex={last_vertex}"))

    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+",
        flags=re.UNICODE,
    )
    has_emoji = bool(emoji_pattern.search(xml_text))
    results.append(("Emoji zero-use", not has_emoji, "no emoji found" if not has_emoji else "emoji found"))

    png_icons = xml_text.count("data:image/png;base64")
    svg_icons = xml_text.count("data:image/svg+xml;base64")
    results.append((
        "Rendered node icons use vector SVG data URIs",
        png_icons == 0,
        f"png_icons={png_icons}, svg_icons={svg_icons}",
    ))

    ids = {c.get("id") for c in cells}
    missing = []
    for c in root.findall(".//*[@edge='1']"):
        src, tgt = c.get("source"), c.get("target")
        if src and src not in ids:
            missing.append((c.get("id"), "source", src))
        if tgt and tgt not in ids:
            missing.append((c.get("id"), "target", tgt))
    results.append(("XML edge endpoint existence", not missing, "all source/target ids exist" if not missing else str(missing)))
    return results


def validate_renderer(renderer: Any) -> List[Tuple[str, bool, str]]:
    results: List[Tuple[str, bool, str]] = []
    grouped: Dict[Tuple[str, str], Dict[str, set]] = {}

    for rec in renderer.port_records:
        grouped.setdefault((rec["source"], rec["src_side"]), {}).setdefault(rec["family"], set()).add(rec["source_port"])
        grouped.setdefault((rec["target"], rec["tgt_side"]), {}).setdefault(rec["family"], set()).add(rec["target_port"])

    unstable = []
    collisions = []
    multi_family_cases = []
    for key, fam_ports in grouped.items():
        for fam, ports in fam_ports.items():
            if len(ports) != 1:
                unstable.append((key, fam, sorted(ports)))
        if len(fam_ports) > 1:
            multi_family_cases.append((key, sorted(fam_ports)))
            used = {}
            for fam, ports in fam_ports.items():
                for port in ports:
                    if port in used:
                        collisions.append((key, port, used[port], fam))
                    used[port] = fam

    if renderer.dsl.get("diagram_type", "layered_architecture") == "layered_architecture":
        results.append(("Same-family same-side ports are shared", not unstable, f"unstable={unstable}"))
    else:
        branch_splits = [rec for rec in renderer.port_records if renderer.node_type_by_id(rec["source"]) == "flow_decision"]
        results.append(("Flowchart decision branches may split same-family ports", True, f"decision_branch_edges={len(branch_splits)}"))
    results.append(("Different visual families use distinct same-side ports", not collisions, f"collisions={collisions}; multi_family_cases={multi_family_cases}"))

    compact_over = []
    for v in renderer.vertices:
        if v.id.startswith("label_") and v.box.w > 186:
            compact_over.append((v.id, v.box.w))
    results.append(("Compact annotation labels stay within max width", len(compact_over) == 0, f"oversized={compact_over}" if compact_over else "all compact labels within 186px"))

    legend_box = renderer.boxes.get("legend_box")
    if legend_box:
        legend_overflow = []
        for v in renderer.vertices:
            if v.id.startswith("legend_text_"):
                left_pad = v.box.x - legend_box.x
                right_pad = (legend_box.x + legend_box.w) - (v.box.x + v.box.w)
                if left_pad < 20 or right_pad < 20:
                    legend_overflow.append((v.id, round(left_pad, 1), round(right_pad, 1)))
        results.append(("Legend text keeps breathing room inside legend box", len(legend_overflow) == 0, f"issues={legend_overflow}" if legend_overflow else "all legend texts keep >=20px box padding"))

        legend_center_issues = []
        content_lefts = []
        content_rights = []
        for e in renderer.edges:
            if e.id.startswith("legend_line_") and e.points:
                content_lefts.append(e.points[0][0])
                content_rights.append(e.points[1][0])
        for v in renderer.vertices:
            if v.id.startswith("legend_text_"):
                content_lefts.append(v.box.x)
                content_rights.append(v.box.x + v.box.w)
            if v.id.startswith("legend_swatch_"):
                content_lefts.append(v.box.x)
                content_rights.append(v.box.x + v.box.w)
        if content_lefts and content_rights:
            content_left = min(content_lefts)
            content_right = max(content_rights)
            left_margin = content_left - legend_box.x
            right_margin = (legend_box.x + legend_box.w) - content_right
            if abs(left_margin - right_margin) > 2:
                legend_center_issues.append((round(left_margin, 1), round(right_margin, 1)))
        results.append(("Legend content is centered inside legend box", len(legend_center_issues) == 0, f"margins={legend_center_issues}" if legend_center_issues else "left/right content margins balanced within 2px"))

        legend_gap_issues = []
        if renderer.dsl.get("layout", {}).get("mode") in {"decision_tree_bus", "stage_gated_swimlane", "rag_sequence_flow"}:
            content_boxes = _main_content_boxes_for_legend_gap(renderer)
            if content_boxes:
                content_bottom = max(box.y + box.h for box in content_boxes.values())
                gap = legend_box.y - content_bottom
                if gap + 0.1 < LEGEND_CONTENT_GAP:
                    legend_gap_issues.append((round(gap, 1), LEGEND_CONTENT_GAP))
        results.append(("Legend keeps breathing room from main content", len(legend_gap_issues) == 0, f"issues={legend_gap_issues}" if legend_gap_issues else f"gap >= {LEGEND_CONTENT_GAP}px or not required"))
    else:
        results.append(("Legend text keeps breathing room inside legend box", True, "no legend in this diagram type"))
        results.append(("Legend content is centered inside legend box", True, "no legend in this diagram type"))
        results.append(("Legend keeps breathing room from main content", True, "no legend in this diagram type"))

    routed_segment_hits = []
    foreground = _foreground_boxes(renderer)
    for edge in renderer.edges:
        if not edge.points:
            continue
        p1, p2 = edge.points
        for node_id, box in foreground.items():
            if _segment_hits_box(p1, p2, box, padding=2):
                routed_segment_hits.append((edge.id, node_id))
    results.append(("Explicit routed segments avoid foreground nodes", not routed_segment_hits, f"hits={routed_segment_hits}"))

    if renderer.dsl.get("diagram_type") == "rag_sequence_flow" or renderer.dsl.get("layout", {}).get("mode") == "rag_sequence_flow":
        results.extend(_validate_lane_visual_guards(renderer, "rag_lane", _rag_node_lane_id, RAG_LANE_SAFE_X, RAG_LANE_SAFE_Y, "RAG"))
    if renderer.dsl.get("layout", {}).get("mode") == "stage_gated_swimlane":
        results.extend(_validate_lane_visual_guards(renderer, "swimlane", _stage_node_lane_id, SWIMLANE_SAFE_X, SWIMLANE_SAFE_Y, "Swimlane"))
    return results


def _validate_lane_visual_guards(renderer: Any, prefix: str, lane_id_for_node: Any, safe_x: float, safe_y: float, label: str) -> List[Tuple[str, bool, str]]:
    results: List[Tuple[str, bool, str]] = []
    lane_issues = []
    text_issues = []
    lane_title_issues = []
    lane_width_issues = []
    nodes = {node.get("id"): node for node in renderer.dsl.get("nodes", [])}

    for node_id, node in nodes.items():
        lane_key = lane_id_for_node(node)
        if not lane_key:
            continue
        lane_id = f"{prefix}_{lane_key}_bg"
        if lane_id not in renderer.boxes or node_id not in renderer.boxes:
            continue
        box = renderer.boxes[node_id]
        lane = renderer.boxes[lane_id]
        left = box.x - lane.x
        right = lane.x + lane.w - (box.x + box.w)
        top = box.y - lane.y
        bottom = lane.y + lane.h - (box.y + box.h)
        if min(left, right) < safe_x or min(top, bottom) < safe_y:
            lane_issues.append((node_id, lane_key, round(left, 1), round(right, 1), round(top, 1), round(bottom, 1)))

        needed_h = _estimated_node_content_height(node)
        if box.h + 0.1 < needed_h:
            text_issues.append((node_id, node.get("type"), round(box.h, 1), round(needed_h, 1)))

    lane_widths = [box.w for node_id, box in renderer.boxes.items() if node_id.startswith(f"{prefix}_") and node_id.endswith("_bg")]
    if lane_widths and max(lane_widths) - min(lane_widths) > 2:
        lane_width_issues.append([round(w, 1) for w in lane_widths])

    for vertex_id, box in renderer.boxes.items():
        if not vertex_id.startswith(f"{prefix}_") or not vertex_id.endswith("_title"):
            continue
        lane_id = vertex_id.replace("_title", "_bg")
        lane = renderer.boxes.get(lane_id)
        if not lane:
            continue
        center_delta = abs(box.cx - lane.cx)
        style = next((v.style for v in renderer.vertices if v.id == vertex_id), "")
        if center_delta > 1 or box.w < lane.w * 0.75 or "align=center" not in style or LANE_TITLE_FONT_SIZE not in style or "fontStyle=1" not in style:
            lane_title_issues.append((vertex_id, round(center_delta, 1), round(box.w, 1), round(lane.w, 1), style))

    results.append((
        f"{label} nodes stay inside lane safe margins",
        not lane_issues,
        f"issues={lane_issues}" if lane_issues else f"safe_x={safe_x}, safe_y={safe_y}",
    ))
    results.append((
        f"{label} node boxes fit estimated text height",
        not text_issues,
        f"issues={text_issues}" if text_issues else f"all {label} node content fits estimated height",
    ))
    results.append((
        f"{label} lane titles are prominent and centered",
        not lane_title_issues,
        f"issues={lane_title_issues}" if lane_title_issues else f"all {label} lane titles centered and prominent",
    ))
    results.append((
        f"{label} lane widths are coordinated",
        not lane_width_issues,
        f"issues={lane_width_issues}" if lane_width_issues else f"all {label} lane widths balanced",
    ))
    return results


def _rag_node_lane_id(node: Dict[str, Any]) -> str:
    return node.get("layout_hint", {}).get("participant", "")


def _stage_node_lane_id(node: Dict[str, Any]) -> str:
    return node.get("lane", "")


def _estimated_node_content_height(node: Dict[str, Any]) -> float:
    node_type = node.get("type", "")
    spec = NODE_SPECS.get(node_type, {})
    icon_name = node.get("icon") or spec.get("icon")
    text_lines = 1
    if node.get("subtitle"):
        text_lines += 1
    text_lines += len(node.get("lines", []))
    icon_h = 26.0 if icon_name else 0.0
    title_h = 18.0
    body_h = max(0, text_lines - 1) * 15.0
    vertical_padding = 16.0
    return icon_h + title_h + body_h + vertical_padding


def _foreground_boxes(renderer: Any) -> Dict[str, Any]:
    ignored_prefixes = (
        "canvas_",
        "layer_",
        "swimlane_",
        "legend_box",
        "bus_",
    )
    return {
        node_id: box
        for node_id, box in renderer.boxes.items()
        if not node_id.startswith(ignored_prefixes)
    }


def _main_content_boxes_for_legend_gap(renderer: Any) -> Dict[str, Any]:
    ignored_prefixes = (
        "canvas_",
        "legend_",
        "bus_",
    )
    ignored_suffixes = (
        "_title",
    )
    return {
        node_id: box
        for node_id, box in renderer.boxes.items()
        if not node_id.startswith(ignored_prefixes) and not node_id.endswith(ignored_suffixes)
    }


def _segment_hits_box(p1: Tuple[float, float], p2: Tuple[float, float], box: Any, padding: float = 0) -> bool:
    x1, y1 = p1
    x2, y2 = p2
    left = box.x - padding
    right = box.x + box.w + padding
    top = box.y - padding
    bottom = box.y + box.h + padding
    if y1 == y2:
        if not (top <= y1 <= bottom):
            return False
        return max(min(x1, x2), left) <= min(max(x1, x2), right)
    if x1 == x2:
        if not (left <= x1 <= right):
            return False
        return max(min(y1, y2), top) <= min(max(y1, y2), bottom)
    return False


def run_validations(dsl: Dict[str, Any], xml_text: str, renderer: Any) -> bool:
    all_results = validate_dsl(dsl) + validate_xml(xml_text) + validate_renderer(renderer)
    ok_all = True
    for name, ok, msg in all_results:
        status = "PASS" if ok else "FAIL"
        if not ok:
            ok_all = False
        print(f"[{status}] {name}: {msg}")
    return ok_all
