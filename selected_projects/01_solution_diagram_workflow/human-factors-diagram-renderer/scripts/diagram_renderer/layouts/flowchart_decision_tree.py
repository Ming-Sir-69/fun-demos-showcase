"""Flowchart decision tree layout profile."""

from __future__ import annotations

from typing import Any, Dict, List

from ..drawio_xml import Box, label_value
from ..spacing import content_bottom_before_legend, decision_tree_bus_gap, legend_box_height, legend_reserved_height, legend_top_y
from ..styles import COLORS, NODE_SPECS, estimate_text_width, node_style, resolve_color, text_style
from .layered_architecture import add_canvas_and_title


SWIMLANES = [
    {"id": "stage", "title": "8D 阶段 / AI 自动处理", "fill": "#EEF4F8"},
    {"id": "human", "title": "人工审核 / 签字", "fill": "#F6EBDD"},
    {"id": "status", "title": "状态", "fill": "#FFFFFF"},
    {"id": "knowledge", "title": "知识沉淀", "fill": "#EDF5EA"},
]

RAG_LANES = [
    {"id": "user", "title": "用户", "fill": "#F7FAFC"},
    {"id": "main", "title": "主控 Agent", "fill": "#F7F9FB"},
    {"id": "pqe", "title": "PQE Agent", "fill": "#FBF4EA"},
    {"id": "db", "title": "隔离向量库", "fill": "#F5FBF3"},
]

LANE_TITLE_FONT_SIZE = 15
LANE_SAFE_X = 16
RAG_LANE_PAD_X = 20
RAG_LANE_PAD_BOTTOM = 16


def layout_flowchart_decision_tree(renderer: Any) -> None:
    rows: List[List[Dict[str, Any]]] = renderer.dsl.get("rows", [])
    node_map: Dict[str, Dict[str, Any]] = {n["id"]: n for n in renderer.dsl.get("nodes", [])}
    layout = renderer.dsl.get("layout", {})
    mode = layout.get("mode", "row_grid")
    if mode == "rag_sequence_flow":
        _expand_rag_canvas_if_needed(renderer, rows, node_map)
    if mode == "stage_gated_swimlane":
        _expand_stage_canvas_if_needed(renderer, rows, node_map)
    add_canvas_and_title(renderer)
    if mode == "stage_gated_swimlane":
        layout_stage_gated_swimlane(renderer, rows, node_map)
        return
    if mode == "decision_tree_bus":
        layout_decision_tree_bus(renderer, rows, node_map)
        return
    if mode == "rag_sequence_flow":
        layout_rag_sequence_flow(renderer, rows, node_map)
        return
    top_y = layout.get("top_y", 130 if mode == "stage_gated_snake" else 110)
    row_gap = layout.get("row_gap", 62)
    default_col_gap = layout.get("col_gap", 34)
    current_y = top_y
    stage_width = _stage_width(renderer, rows, node_map, default_col_gap) if mode == "stage_gated_snake" else None
    for row_index, row in enumerate(rows):
        row_nodes = [node_map[nid] for nid in row.get("node_ids", [])]
        if not row_nodes:
            continue
        gap = row.get("gap", default_col_gap)
        widths = [NODE_SPECS[n["type"]]["w"] for n in row_nodes]
        heights = [NODE_SPECS[n["type"]]["h"] for n in row_nodes]
        total_w = sum(widths) + gap * max(0, len(widths) - 1)
        direction = row.get("direction", _default_stage_direction(row_index) if mode == "stage_gated_snake" else "ltr")
        visual_nodes = row_nodes if direction == "ltr" else list(reversed(row_nodes))
        visual_widths = widths if direction == "ltr" else list(reversed(widths))
        visual_heights = heights if direction == "ltr" else list(reversed(heights))
        x = _row_start_x(renderer, rows, row_index, direction, total_w, stage_width) if mode == "stage_gated_snake" else (renderer.width - total_w) / 2
        y = current_y
        for node, w, h in zip(visual_nodes, visual_widths, visual_heights):
            renderer.add_vertex(node["id"], label_value(node, node["type"]), node_style(node["type"]), Box(x, y, w, h))
            x += w + gap
        current_y += max(heights) + row_gap

    layout_flow_legend(renderer)
    endpoint_overrides = renderer.compute_endpoint_overrides(renderer.dsl.get("edges", []))
    for idx, edge in enumerate(renderer.dsl.get("edges", []), 1):
        renderer.add_edge(edge["source"], edge["target"], edge["type"], eid=f"e_{idx:03d}", endpoint_style_override=endpoint_overrides.get(idx), value=edge.get("label", ""))


def layout_decision_tree_bus(renderer: Any, rows: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]]) -> None:
    layout = renderer.dsl.get("layout", {})
    top_y = layout.get("top_y", 110)
    row_gap = layout.get("row_gap", 54)
    default_col_gap = layout.get("col_gap", 36)
    aligned_rows = _aligned_condition_result_rows(rows, node_map)
    aligned_columns = _aligned_column_centers(renderer, rows, node_map, default_col_gap, aligned_rows)
    row_gaps = _decision_tree_row_gaps(renderer, rows, node_map, row_gap)

    current_y = top_y
    for row_index, row in enumerate(rows):
        row_nodes = [node_map[nid] for nid in row.get("node_ids", []) if nid in node_map]
        if not row_nodes:
            continue
        gap = row.get("gap", default_col_gap)
        heights = [NODE_SPECS[n["type"]]["h"] for n in row_nodes]
        y = current_y
        if row_index in aligned_rows and aligned_columns:
            for col_index, node in enumerate(row_nodes):
                spec = NODE_SPECS[node["type"]]
                x = aligned_columns[col_index] - spec["w"] / 2
                renderer.add_vertex(node["id"], label_value(node, node["type"]), node_style(node["type"]), Box(x, y, spec["w"], spec["h"]))
        else:
            widths = [NODE_SPECS[n["type"]]["w"] for n in row_nodes]
            total_w = sum(widths) + gap * max(0, len(widths) - 1)
            x = (renderer.width - total_w) / 2
            for node, w, h in zip(row_nodes, widths, heights):
                renderer.add_vertex(node["id"], label_value(node, node["type"]), node_style(node["type"]), Box(x, y, w, h))
                x += w + gap
        current_y += max(heights) + row_gaps[row_index]

    layout_flow_legend(renderer)
    _add_decision_tree_bus_edges(renderer)


def layout_rag_sequence_flow(renderer: Any, rows: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]]) -> None:
    layout = renderer.dsl.get("layout", {})
    top_y = layout.get("top_y", 138)
    row_gap = layout.get("row_gap", 34)
    lane_top = top_y - 48
    lane_bottom = _main_content_bottom(renderer)
    lane_h = lane_bottom - lane_top
    lanes = _balanced_lanes(renderer, RAG_LANES, side_margin=50, gap=30)
    lane_lookup = {lane["id"]: lane for lane in lanes}

    _add_lanes(renderer, lanes, "rag_lane", lane_top, lane_h)

    current_y = top_y
    for row in rows:
        row_nodes = [node_map[nid] for nid in row.get("node_ids", []) if nid in node_map]
        if not row_nodes:
            continue
        row_dimensions = {node["id"]: _rag_node_dimensions(node, lane_lookup.get(node.get("layout_hint", {}).get("participant", "main"), lane_lookup["main"])) for node in row_nodes}
        row_height = max(dim[1] for dim in row_dimensions.values())
        for node in row_nodes:
            participant = node.get("layout_hint", {}).get("participant", "main")
            lane = lane_lookup.get(participant, lane_lookup["main"])
            w, h = row_dimensions[node["id"]]
            x = lane["x"] + (lane["w"] - w) / 2
            y = current_y + (row_height - h) / 2
            renderer.add_vertex(node["id"], label_value(node, node["type"]), node_style(node["type"]), Box(x, y, w, h))
        current_y += row_height + row_gap

    layout_flow_legend(renderer)
    endpoint_overrides = renderer.compute_endpoint_overrides(renderer.dsl.get("edges", []))
    for idx, edge in enumerate(renderer.dsl.get("edges", []), 1):
        renderer.add_edge(edge["source"], edge["target"], edge["type"], eid=f"e_{idx:03d}", endpoint_style_override=endpoint_overrides.get(idx), value=edge.get("label", ""))


def _rag_lane_title_style() -> str:
    return _lane_title_style()


def _lane_title_style() -> str:
    return (
        f"text;html=1;strokeColor=none;fillColor=none;fontColor={COLORS['text_dark']};fontSize={LANE_TITLE_FONT_SIZE};"
        "fontStyle=1;fontFamily=Segoe UI, PingFang SC, Microsoft YaHei, Arial, sans-serif;"
        "align=center;verticalAlign=middle;"
    )


def _balanced_lanes(renderer: Any, lane_defs: List[Dict[str, Any]], side_margin: float, gap: float) -> List[Dict[str, Any]]:
    lane_count = len(lane_defs)
    lane_w = (renderer.width - side_margin * 2 - gap * max(0, lane_count - 1)) / lane_count
    lanes = []
    x = side_margin
    for lane in lane_defs:
        item = dict(lane)
        item["x"] = x
        item["w"] = lane_w
        lanes.append(item)
        x += lane_w + gap
    return lanes


def _add_lanes(renderer: Any, lanes: List[Dict[str, Any]], prefix: str, lane_top: float, lane_h: float) -> None:
    for lane in lanes:
        renderer.add_vertex(
            f"{prefix}_{lane['id']}_bg",
            "",
            f"rounded=1;whiteSpace=wrap;html=1;arcSize=6;fillColor={lane['fill']};strokeColor={COLORS['role_stroke']};strokeWidth=1;",
            Box(lane["x"], lane_top, lane["w"], lane_h),
        )
        renderer.add_vertex(
            f"{prefix}_{lane['id']}_title",
            lane["title"],
            _lane_title_style(),
            Box(lane["x"] + 16, lane_top + 14, lane["w"] - 32, 26),
        )


def _rag_node_dimensions(node: Dict[str, Any], lane: Dict[str, Any]) -> tuple[float, float]:
    spec = NODE_SPECS[node["type"]]
    max_w = lane["w"] - RAG_LANE_PAD_X * 2
    width = min(float(spec["w"]), float(max_w))
    return width, max(float(spec["h"]), _estimated_rag_content_height(node))


def _estimated_rag_content_height(node: Dict[str, Any]) -> float:
    spec = NODE_SPECS[node["type"]]
    icon_name = node.get("icon") or spec.get("icon")
    text_lines = 1
    if node.get("subtitle"):
        text_lines += 1
    text_lines += len(node.get("lines", []))
    return (26.0 if icon_name else 0.0) + 18.0 + max(0, text_lines - 1) * 15.0 + 16.0


def _expand_rag_canvas_if_needed(renderer: Any, rows: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]]) -> None:
    layout = renderer.dsl.get("layout", {})
    top_y = layout.get("top_y", 138)
    row_gap = layout.get("row_gap", 34)
    lane_lookup = {lane["id"]: lane for lane in _balanced_lanes(renderer, RAG_LANES, side_margin=50, gap=30)}
    current_y = top_y
    for row in rows:
        row_nodes = [node_map[nid] for nid in row.get("node_ids", []) if nid in node_map]
        if not row_nodes:
            continue
        current_y += max(_rag_node_dimensions(node, lane_lookup.get(node.get("layout_hint", {}).get("participant", "main"), lane_lookup["main"]))[1] for node in row_nodes) + row_gap
    content_bottom = current_y - row_gap
    required_height = int(content_bottom + RAG_LANE_PAD_BOTTOM + _legend_reserved_height(renderer))
    if required_height > renderer.height:
        renderer.height = required_height


def _expand_stage_canvas_if_needed(renderer: Any, rows: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]]) -> None:
    layout = renderer.dsl.get("layout", {})
    top_y = layout.get("top_y", 148)
    row_gap = layout.get("row_gap", 34)
    lane_lookup = {lane["id"]: lane for lane in _balanced_lanes(renderer, SWIMLANES, side_margin=48, gap=36)}
    current_y = top_y
    for row in rows:
        row_nodes = [node_map[nid] for nid in row.get("node_ids", []) if nid in node_map]
        if not row_nodes:
            continue
        current_y += max(_stage_node_dimensions(node, lane_lookup.get(node.get("lane", "stage"), lane_lookup["stage"]))[1] for node in row_nodes) + row_gap
    content_bottom = current_y - row_gap
    required_height = int(content_bottom + RAG_LANE_PAD_BOTTOM + _legend_reserved_height(renderer))
    if required_height > renderer.height:
        renderer.height = required_height


def _aligned_condition_result_rows(rows: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]]) -> set[int]:
    aligned: set[int] = set()
    for idx in range(len(rows) - 1):
        upper = [node_map[nid] for nid in rows[idx].get("node_ids", []) if nid in node_map]
        lower = [node_map[nid] for nid in rows[idx + 1].get("node_ids", []) if nid in node_map]
        if not upper or len(upper) != len(lower):
            continue
        if {n["type"] for n in upper} == {"flow_condition"} and {n["type"] for n in lower} == {"flow_result"}:
            aligned.update({idx, idx + 1})
    return aligned


def _aligned_column_centers(renderer: Any, rows: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]], default_gap: float, aligned_rows: set[int]) -> List[float]:
    if not aligned_rows:
        return []
    aligned_row_list = sorted(aligned_rows)
    node_rows = [[node_map[nid] for nid in rows[idx].get("node_ids", []) if nid in node_map] for idx in aligned_row_list]
    col_count = min((len(row) for row in node_rows), default=0)
    if col_count == 0:
        return []
    gap = max(rows[idx].get("gap", default_gap) for idx in aligned_row_list)
    col_widths = []
    for col_index in range(col_count):
        col_widths.append(max(NODE_SPECS[row[col_index]["type"]]["w"] for row in node_rows))
    total_w = sum(col_widths) + gap * max(0, col_count - 1)
    x = (renderer.width - total_w) / 2
    centers = []
    for width in col_widths:
        centers.append(x + width / 2)
        x += width + gap
    return centers


def _decision_tree_row_gaps(renderer: Any, rows: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]], default_gap: float) -> List[float]:
    gaps = [default_gap for _ in rows]
    row_by_node: Dict[str, int] = {}
    for row_index, row in enumerate(rows):
        for node_id in row.get("node_ids", []):
            row_by_node[node_id] = row_index

    split_counts: Dict[int, int] = {}
    merge_counts: Dict[int, int] = {}
    for edge in renderer.dsl.get("edges", []):
        source = edge.get("source")
        target = edge.get("target")
        if source not in node_map or target not in node_map:
            continue
        source_row = row_by_node.get(source)
        target_row = row_by_node.get(target)
        if source_row is None or target_row is None or target_row != source_row + 1:
            continue
        source_type = node_map[source]["type"]
        target_type = node_map[target]["type"]
        if source_type == "flow_decision" and target_type == "flow_condition":
            split_counts[source_row] = split_counts.get(source_row, 0) + 1
        if source_type == "flow_result" and target_type == "flow_output":
            merge_counts[source_row] = merge_counts.get(source_row, 0) + 1

    for row_index, count in split_counts.items():
        if count >= 4:
            gaps[row_index] = max(gaps[row_index], decision_tree_bus_gap(count))
    for row_index, count in merge_counts.items():
        if count >= 2:
            gaps[row_index] = max(gaps[row_index], decision_tree_bus_gap(count))
    return gaps


def _hidden_junction_style() -> str:
    return "shape=ellipse;html=1;fillColor=none;strokeColor=none;opacity=0;resizable=0;movable=0;"


def _add_hidden_junction(renderer: Any, jid: str, x: float, y: float) -> None:
    renderer.add_vertex(jid, "", _hidden_junction_style(), Box(x - 1, y - 1, 2, 2))


def _add_decision_tree_bus_edges(renderer: Any) -> None:
    edges = renderer.dsl.get("edges", [])
    split_edges = [edge for edge in edges if edge.get("source") in renderer.boxes and edge.get("target") in renderer.boxes and renderer.node_type_by_id(edge["source"]) == "flow_decision" and renderer.node_type_by_id(edge["target"]) == "flow_condition"]
    merge_edges = [edge for edge in edges if edge.get("source") in renderer.boxes and edge.get("target") in renderer.boxes and renderer.node_type_by_id(edge["source"]) == "flow_result" and renderer.node_type_by_id(edge["target"]) == "flow_output"]
    skip = {(edge["source"], edge["target"], edge["type"]) for edge in split_edges + merge_edges}

    for idx, edge in enumerate(edges, 1):
        key = (edge["source"], edge["target"], edge["type"])
        if key in skip:
            continue
        renderer.add_edge(edge["source"], edge["target"], edge["type"], eid=f"e_{idx:03d}", value=edge.get("label", ""))

    if split_edges:
        _add_split_bus(renderer, split_edges)
    if merge_edges:
        _add_merge_bus(renderer, merge_edges)


def _add_split_bus(renderer: Any, split_edges: List[Dict[str, Any]]) -> None:
    source = split_edges[0]["source"]
    source_box = renderer.boxes[source]
    target_boxes = [renderer.boxes[edge["target"]] for edge in split_edges]
    bus_y = source_box.y + source_box.h + max(28, (min(box.y for box in target_boxes) - (source_box.y + source_box.h)) * 0.42)
    center_id = "bus_split_center"
    _add_hidden_junction(renderer, center_id, source_box.cx, bus_y)
    renderer.add_edge(source, center_id, "label_ingress_solid", eid="bus_split_in")

    branch_ids = []
    for idx, edge in enumerate(split_edges, 1):
        target_box = renderer.boxes[edge["target"]]
        branch_id = f"bus_split_branch_{idx}"
        branch_ids.append(branch_id)
        _add_hidden_junction(renderer, branch_id, target_box.cx, bus_y)
        renderer.add_edge(branch_id, edge["target"], edge["type"], eid=f"bus_split_down_{idx}")

    x_values = [renderer.boxes[jid].cx for jid in [center_id] + branch_ids]
    renderer.add_edge(None, None, "label_ingress_solid", points=((min(x_values), bus_y), (max(x_values), bus_y)), eid="bus_split_h")


def _add_merge_bus(renderer: Any, merge_edges: List[Dict[str, Any]]) -> None:
    target = merge_edges[0]["target"]
    target_box = renderer.boxes[target]
    source_boxes = [renderer.boxes[edge["source"]] for edge in merge_edges]
    bus_y = max(box.y + box.h for box in source_boxes) + max(26, (target_box.y - max(box.y + box.h for box in source_boxes)) * 0.45)
    center_id = "bus_merge_center"
    _add_hidden_junction(renderer, center_id, target_box.cx, bus_y)
    renderer.add_edge(center_id, target, "control_flow", eid="bus_merge_out")

    branch_ids = []
    for idx, edge in enumerate(merge_edges, 1):
        source_box = renderer.boxes[edge["source"]]
        branch_id = f"bus_merge_branch_{idx}"
        branch_ids.append(branch_id)
        _add_hidden_junction(renderer, branch_id, source_box.cx, bus_y)
        renderer.add_edge(edge["source"], branch_id, "label_ingress_solid", eid=f"bus_merge_up_{idx}")

    x_values = [renderer.boxes[jid].cx for jid in branch_ids + [center_id]]
    renderer.add_edge(None, None, "label_ingress_solid", points=((min(x_values), bus_y), (max(x_values), bus_y)), eid="bus_merge_h")


def layout_stage_gated_swimlane(renderer: Any, rows: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]]) -> None:
    layout = renderer.dsl.get("layout", {})
    top_y = layout.get("top_y", 148)
    row_gap = layout.get("row_gap", 34)
    lane_top = top_y - 46
    lane_bottom = _main_content_bottom(renderer)
    lane_h = lane_bottom - lane_top
    lanes = _balanced_lanes(renderer, SWIMLANES, side_margin=48, gap=36)

    _add_lanes(renderer, lanes, "swimlane", lane_top, lane_h)

    lane_lookup = {lane["id"]: lane for lane in lanes}
    current_y = top_y
    for row in rows:
        row_nodes = [node_map[nid] for nid in row.get("node_ids", []) if nid in node_map]
        if not row_nodes:
            continue
        row_dimensions = {
            node["id"]: _stage_node_dimensions(node, lane_lookup.get(node.get("lane", "stage"), lane_lookup["stage"]))
            for node in row_nodes
        }
        row_height = max(dim[1] for dim in row_dimensions.values())
        for node in row_nodes:
            lane_id = node.get("lane", "stage")
            lane = lane_lookup.get(lane_id, lane_lookup["stage"])
            w, h = row_dimensions[node["id"]]
            x = lane["x"] + (lane["w"] - w) / 2
            y = current_y + (row_height - h) / 2
            renderer.add_vertex(node["id"], label_value(node, node["type"]), node_style(node["type"]), Box(x, y, w, h))
        current_y += row_height + row_gap

    layout_flow_legend(renderer)
    endpoint_overrides = renderer.compute_endpoint_overrides(renderer.dsl.get("edges", []))
    for idx, edge in enumerate(renderer.dsl.get("edges", []), 1):
        renderer.add_edge(edge["source"], edge["target"], edge["type"], eid=f"e_{idx:03d}", endpoint_style_override=endpoint_overrides.get(idx), value=edge.get("label", ""))


def _stage_node_dimensions(node: Dict[str, Any], lane: Dict[str, Any]) -> tuple[float, float]:
    spec = NODE_SPECS[node["type"]]
    max_w = lane["w"] - LANE_SAFE_X * 2
    width = min(float(spec["w"]), float(max_w))
    return width, max(float(spec["h"]), _estimated_rag_content_height(node))


def _default_stage_direction(row_index: int) -> str:
    return "ltr" if row_index % 2 == 0 else "rtl"


def _row_width(row: Dict[str, Any], node_map: Dict[str, Dict[str, Any]], default_gap: float) -> float:
    nodes = [node_map[nid] for nid in row.get("node_ids", []) if nid in node_map]
    if not nodes:
        return 0
    gap = row.get("gap", default_gap)
    widths = [NODE_SPECS[n["type"]]["w"] for n in nodes]
    return sum(widths) + gap * max(0, len(widths) - 1)


def _stage_width(renderer: Any, rows: List[Dict[str, Any]], node_map: Dict[str, Dict[str, Any]], default_gap: float) -> float:
    max_row_width = max((_row_width(row, node_map, default_gap) for row in rows), default=0)
    return min(max_row_width, renderer.width - 160)


def _next_direction(rows: List[Dict[str, Any]], row_index: int) -> str:
    if row_index + 1 >= len(rows):
        return _default_stage_direction(row_index + 1)
    return rows[row_index + 1].get("direction", _default_stage_direction(row_index + 1))


def _row_start_x(renderer: Any, rows: List[Dict[str, Any]], row_index: int, direction: str, total_w: float, stage_width: float | None) -> float:
    if stage_width is None:
        return (renderer.width - total_w) / 2
    stage_left = (renderer.width - stage_width) / 2
    stage_right = stage_left + stage_width
    if direction == "rtl":
        return stage_right - total_w
    if row_index == 0 and _next_direction(rows, row_index) == "rtl":
        return stage_right - total_w
    return stage_left


def layout_flow_legend(renderer: Any) -> None:
    edge_items = list(renderer.dsl.get("legend", []))
    node_items = _node_color_legend_items(renderer)
    lane_note = _lane_note_text(renderer)
    if not edge_items and not node_items and not lane_note:
        return

    legend_h = legend_box_height(len(edge_items), len(node_items), bool(lane_note))
    y = legend_top_y(renderer.height, len(edge_items), len(node_items), bool(lane_note))
    legend_w = min(1120, renderer.width - 240)
    legend_x = (renderer.width - legend_w) / 2
    renderer.add_vertex("legend_box", "", f"rounded=1;whiteSpace=wrap;html=1;arcSize=12;fillColor=#FFFFFF;strokeColor={COLORS['role_stroke']};strokeWidth=1;", Box(legend_x, y, legend_w, legend_h))

    show_group_titles = bool(node_items)
    row_y = y + 7
    if edge_items:
        _layout_edge_legend_row(renderer, edge_items, legend_x, legend_w, row_y, show_group_title=show_group_titles)
        row_y += 28
    if node_items:
        _layout_node_color_legend_row(renderer, node_items, legend_x, legend_w, row_y, show_group_title=show_group_titles)
        row_y += 28
    if lane_note:
        renderer.add_vertex("legend_text_lane_note", lane_note, text_style(11), Box(legend_x + 20, row_y + 1, legend_w - 40, 20))


def _legend_group_title_style() -> str:
    return text_style(11, bold=True)


def _layout_edge_legend_row(renderer: Any, items: List[Dict[str, Any]], legend_x: float, legend_w: float, y: float, show_group_title: bool = False) -> None:
    line_len = 44
    gap_after_line = 18
    item_gap = 84
    text_extra = 8
    title_w = 82 if show_group_title else 0
    if show_group_title:
        renderer.add_vertex("legend_title_edges", "连线含义", _legend_group_title_style(), Box(legend_x + 28, y, title_w, 20))
    item_widths: List[float] = []
    for item in items:
        text_w = estimate_text_width(item["label"]) + text_extra
        item_widths.append(line_len + gap_after_line + text_w)
    total_content_w = sum(item_widths) + item_gap * max(0, len(items) - 1)
    content_x = legend_x + max(20, (legend_w - total_content_w) / 2)
    cursor = content_x
    for idx, item in enumerate(items):
        text_w = item_widths[idx] - line_len - gap_after_line
        line_x = cursor
        text_x = line_x + line_len + gap_after_line
        renderer.add_vertex(f"legend_text_{idx + 1}", item["label"], text_style(11), Box(text_x, y, text_w, 20))
        renderer.add_edge(None, None, item["edge_type"], points=((line_x, y + 12), (line_x + line_len, y + 12)), eid=f"legend_line_{idx + 1}")
        cursor += item_widths[idx] + item_gap


def _layout_node_color_legend_row(renderer: Any, items: List[Dict[str, Any]], legend_x: float, legend_w: float, y: float, show_group_title: bool = False) -> None:
    swatch_w = 46
    swatch_h = 18
    gap_after_swatch = 10
    item_gap = 28
    text_extra = 8
    title_w = 82 if show_group_title else 0
    if show_group_title:
        renderer.add_vertex("legend_title_nodes", "节点颜色", _legend_group_title_style(), Box(legend_x + 28, y, title_w, 20))
    item_widths = [swatch_w + gap_after_swatch + estimate_text_width(item["label"]) + text_extra for item in items]
    total_content_w = sum(item_widths) + item_gap * max(0, len(items) - 1)
    cursor = legend_x + max(20, (legend_w - total_content_w) / 2)
    for idx, item in enumerate(items):
        spec = NODE_SPECS[item["node_type"]]
        swatch_x = cursor
        text_x = swatch_x + swatch_w + gap_after_swatch
        text_w = item_widths[idx] - swatch_w - gap_after_swatch
        renderer.add_vertex(
            f"legend_swatch_{idx + 1}",
            "",
            "rounded=1;whiteSpace=wrap;html=1;arcSize=30;"
            f"fillColor={resolve_color(spec['fill'])};strokeColor={resolve_color(spec['stroke'])};strokeWidth=1.2;",
            Box(swatch_x, y + 1, swatch_w, swatch_h),
        )
        renderer.add_vertex(f"legend_text_node_{idx + 1}", item["label"], text_style(11), Box(text_x, y, text_w, 20))
        cursor += item_widths[idx] + item_gap


def _node_color_legend_items(renderer: Any) -> List[Dict[str, str]]:
    mode = renderer.dsl.get("layout", {}).get("mode")
    if mode != "rag_sequence_flow":
        return []
    return [
        {"node_type": "flow_request", "label": "请求输入"},
        {"node_type": "ai_core", "label": "Agent 执行"},
        {"node_type": "flow_filter", "label": "过滤约束"},
        {"node_type": "flow_data", "label": "知识证据"},
        {"node_type": "flow_output", "label": "最终输出"},
    ]


def _lane_note_text(renderer: Any) -> str:
    return ""


def _main_content_bottom(renderer: Any) -> float:
    edge_count = len(renderer.dsl.get("legend", []))
    node_count = len(_node_color_legend_items(renderer))
    has_lane_note = bool(_lane_note_text(renderer))
    bottom = content_bottom_before_legend(renderer.height, edge_count, node_count, has_lane_note)
    return bottom if bottom > 0 else renderer.height - 92


def _legend_reserved_height(renderer: Any) -> float:
    return legend_reserved_height(
        len(renderer.dsl.get("legend", [])),
        len(_node_color_legend_items(renderer)),
        bool(_lane_note_text(renderer)),
    )
