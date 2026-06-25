"""Layered architecture layout profile."""

from __future__ import annotations

import html
from typing import Any, Dict, List, Tuple

from ..drawio_xml import Box, label_value, layer_rail_value, title_value
from ..spacing import layered_gap
from ..styles import (
    COLORS,
    LAYOUT_PROFILE,
    NODE_SPECS,
    estimate_text_width,
    group_style,
    layer_bg_style,
    layer_fill_for,
    node_style,
    rail_style,
    text_style,
)


def compact_label_geometry(label: Dict[str, Any], spec: Dict[str, Any]) -> Tuple[float, float, float, float]:
    base_w = float(label.get("w", spec["w"]))
    h = float(label.get("h", spec["h"]))
    x = float(label["x"])
    y = float(label["y"])
    if label.get("compact", False):
        min_w = float(label.get("min_w", 132))
        max_w = float(label.get("max_w", 186))
        target_w = estimate_text_width(label.get("title", "")) + 34.0
        w = max(min_w, min(max_w, round(target_w)))
        x = x + max(0.0, (base_w - w) / 2.0)
    else:
        w = base_w
    return x, y, w, h


def add_canvas_and_title(renderer: Any) -> None:
    renderer.add_vertex(
        "canvas_bg",
        "",
        f"rounded=0;whiteSpace=wrap;html=1;strokeColor=none;fillColor={COLORS['canvas_bg']};",
        Box(0, 0, renderer.width, renderer.height),
    )
    renderer.add_vertex(
        "title",
        title_value(renderer.dsl["title"], renderer.dsl.get("subtitle", "")),
        "text;html=1;strokeColor=none;fillColor=none;fontColor=#1A1A1A;fontSize=18;fontStyle=1;align=center;verticalAlign=middle;",
        Box(220, 22, renderer.width - 440, 50),
    )


def layout_layered_architecture(renderer: Any) -> None:
    add_canvas_and_title(renderer)
    current_y = LAYOUT_PROFILE["top_y"]
    layers = renderer.dsl["layers"]
    layer_lookup = _layer_lookup(layers)
    for layer_index, layer in enumerate(layers):
        layer_id = layer["id"]
        h = layer["height"]
        bg_fill = layer_fill_for(layer_id)
        renderer.add_vertex(
            f"layer_{layer_id}_bg",
            "",
            layer_bg_style(bg_fill),
            Box(LAYOUT_PROFILE["layer_x"], current_y, LAYOUT_PROFILE["layer_w"], h),
        )
        renderer.add_vertex(
            f"layer_{layer_id}_rail",
            layer_rail_value(layer["index"], layer["title"]),
            rail_style(),
            Box(LAYOUT_PROFILE["rail_x"], current_y + 10, LAYOUT_PROFILE["rail_w"], h - 20),
        )
        if layer_id in {"role", "ai", "platform"}:
            layout_simple_row(renderer, layer, current_y)
        elif layer_id == "business":
            layout_business_groups(renderer, layer, current_y)
        current_y += h + _gap_after_layer(renderer, layers, layer_lookup, layer_index)

    for lab in renderer.dsl.get("labels", []):
        spec = NODE_SPECS[lab["type"]]
        x, y, w, h = compact_label_geometry(lab, spec)
        renderer.add_vertex(lab["id"], html.escape(lab["title"]), node_style(lab["type"]), Box(x, y, w, h))

    layout_legend(renderer)
    endpoint_overrides = renderer.compute_endpoint_overrides(renderer.dsl["edges"])
    for idx, edge in enumerate(renderer.dsl["edges"], 1):
        renderer.add_edge(edge["source"], edge["target"], edge["type"], eid=f"e_{idx:03d}", endpoint_style_override=endpoint_overrides.get(idx), value=edge.get("label", ""))


def _layer_lookup(layers: List[Dict[str, Any]]) -> Dict[str, int]:
    lookup: Dict[str, int] = {}
    for layer_index, layer in enumerate(layers):
        for node in layer.get("nodes", []):
            lookup[node["id"]] = layer_index
        for group in layer.get("groups", []):
            lookup[group["id"]] = layer_index
            for node in group.get("nodes", []):
                lookup[node["id"]] = layer_index
    return lookup


def _gap_after_layer(renderer: Any, layers: List[Dict[str, Any]], layer_lookup: Dict[str, int], layer_index: int) -> float:
    layer = layers[layer_index]
    if "gap_after" in layer:
        return float(layer["gap_after"])
    if layer_index >= len(layers) - 1:
        return 40.0

    line_count = 0
    labeled_count = 0
    for edge in renderer.dsl.get("edges", []):
        source_layer = layer_lookup.get(edge.get("source"))
        target_layer = layer_lookup.get(edge.get("target"))
        crosses_gap = (
            source_layer is not None
            and target_layer is not None
            and min(source_layer, target_layer) <= layer_index < max(source_layer, target_layer)
        )
        if not crosses_gap:
            continue
        line_count += 1
        if edge.get("label"):
            labeled_count += 1
    if line_count == 0:
        return 40.0
    return layered_gap(line_count, labeled_count)


def layout_simple_row(renderer: Any, layer: Dict[str, Any], layer_y: float) -> None:
    layer_id = layer["id"]
    if layer_id == "role":
        x0, gap, y = 210, 12, layer_y + 22
    elif layer_id == "ai":
        x0, gap, y = 235, 52, layer_y + 20
    else:
        x0, gap, y = 240, 95, layer_y + 25
    for i, node in enumerate(layer["nodes"]):
        spec = NODE_SPECS[node["type"]]
        x = x0 + i * (spec["w"] + gap)
        renderer.add_vertex(node["id"], label_value(node, node["type"]), node_style(node["type"]), Box(x, y, spec["w"], spec["h"]))


def layout_business_groups(renderer: Any, layer: Dict[str, Any], layer_y: float) -> None:
    group_boxes = {
        "existing_systems": Box(220, layer_y + 30, 560, 180),
        "agent_infra": Box(835, layer_y + 30, 600, 180),
    }
    for group in layer["groups"]:
        gbox = group_boxes[group["id"]]
        renderer.add_vertex(group["id"], html.escape(group["title"]), group_style(group["type"]), gbox)
        if group["id"] == "existing_systems":
            coords = [(gbox.x + 30, gbox.y + 40), (gbox.x + 300, gbox.y + 40), (gbox.x + 30, gbox.y + 110), (gbox.x + 300, gbox.y + 110)]
        else:
            coords = [(gbox.x + 30, gbox.y + 40), (gbox.x + 220, gbox.y + 40), (gbox.x + 410, gbox.y + 40), (gbox.x + 70, gbox.y + 110), (gbox.x + 330, gbox.y + 110)]
        for node, (x, y) in zip(group["nodes"], coords):
            spec = NODE_SPECS[node["type"]]
            renderer.add_vertex(node["id"], label_value(node, node["type"]), node_style(node["type"]), Box(x, y, spec["w"], spec["h"]))


def layout_legend(renderer: Any) -> None:
    y = LAYOUT_PROFILE["legend_y"]
    legend_x, legend_w, legend_h = 310, 980, 34
    line_len = 44
    gap_after_line = 18
    item_gap = 84
    text_extra = 8
    items = list(renderer.dsl.get("legend", []))
    item_widths: List[float] = []
    for item in items:
        text_w = estimate_text_width(item["label"]) + text_extra
        item_widths.append(line_len + gap_after_line + text_w)
    total_content_w = sum(item_widths) + item_gap * max(0, len(items) - 1)
    content_x = legend_x + (legend_w - total_content_w) / 2
    renderer.add_vertex("legend_box", "", f"rounded=1;whiteSpace=wrap;html=1;arcSize=12;fillColor=#FFFFFF;strokeColor={COLORS['role_stroke']};strokeWidth=1;", Box(legend_x, y, legend_w, legend_h))
    cursor = content_x
    for idx, item in enumerate(items):
        text_w = item_widths[idx] - line_len - gap_after_line
        line_x = cursor
        text_x = line_x + line_len + gap_after_line
        line_id = f"legend_line_{idx + 1}"
        text_id = f"legend_text_{idx + 1}"
        renderer.add_vertex(text_id, html.escape(item["label"]), text_style(11), Box(text_x, y + 5, text_w, 20))
        renderer.add_edge(None, None, item["edge_type"], points=((line_x, y + 17), (line_x + line_len, y + 17)), eid=line_id)
        cursor += item_widths[idx] + item_gap
