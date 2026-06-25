"""Style tokens and style string helpers for the draw.io renderer."""

from __future__ import annotations


COLORS = {
    "canvas_bg": "#F8F6F0",
    "layer_bg": "#F2F2F2",
    "role_fill": "#F3E8D5",
    "role_stroke": "#D2C7B8",
    "ai_fill": "#3F6EA8",
    "ai_stroke": "#2E5585",
    "system_fill": "#D6E4F0",
    "system_stroke": "#8BA5BD",
    "knowledge_fill": "#DDE9DB",
    "knowledge_stroke": "#9DB88E",
    "request_fill": "#D6E4F0",
    "request_stroke": "#8BA5BD",
    "filter_fill": "#F6EBDD",
    "filter_stroke": "#CDBA9B",
    "platform_fill": "#4B5259",
    "platform_stroke": "#4B5259",
    "rail_fill": "#D2C7B8",
    "text_dark": "#2C3E50",
    "text_soft": "#4D4D4D",
    "edge_dark": "#3F4447",
    "edge_soft": "#64748B",
    "label_stroke": "#DADDE0",
}

LAYER_BACKGROUND_MODE = "unified"  # unified | tiered
LAYER_TIERED_FILLS = {
    "role": "#F3E8D5",
    "ai": "#EEF2F6",
    "business": "#F2F2F2",
    "platform": "#ECEFF2",
}

NODE_SPECS = {
    "role": {"w": 150, "h": 90, "icon": "user", "fill": "role_fill", "stroke": "role_stroke", "font": "text_dark", "arc": 12, "shape": "rounded"},
    "ai_core": {"w": 270, "h": 78, "icon": "cpu", "fill": "ai_fill", "stroke": "ai_stroke", "font": "#FFFFFF", "arc": 10, "shape": "rounded"},
    "system": {"w": 215, "h": 55, "icon": "app", "fill": "system_fill", "stroke": "system_stroke", "font": "text_dark", "arc": 12, "shape": "rounded"},
    "knowledge": {"w": 155, "h": 55, "icon": "database", "fill": "knowledge_fill", "stroke": "knowledge_stroke", "font": "text_dark", "arc": 12, "shape": "rounded"},
    "knowledge_wide": {"w": 205, "h": 55, "icon": "database", "fill": "knowledge_fill", "stroke": "knowledge_stroke", "font": "text_dark", "arc": 12, "shape": "rounded"},
    "platform": {"w": 350, "h": 65, "icon": "stack", "fill": "platform_fill", "stroke": "platform_stroke", "font": "#FFFFFF", "arc": 8, "shape": "rounded"},
    "edge_label": {"w": 160, "h": 30, "icon": None, "fill": "#FFFFFF", "stroke": "label_stroke", "font": "text_dark", "arc": 50, "shape": "rounded"},
    "flow_start": {"w": 260, "h": 58, "icon": "alert", "fill": "#D6E4F0", "stroke": "ai_stroke", "font": "text_dark", "arc": 16, "shape": "rounded"},
    "flow_process": {"w": 230, "h": 62, "icon": None, "fill": "#D6E4F0", "stroke": "system_stroke", "font": "text_dark", "arc": 12, "shape": "rounded"},
    "flow_decision": {"w": 330, "h": 120, "icon": "brain", "fill": "#F3E8D5", "stroke": "role_stroke", "font": "text_dark", "arc": 0, "shape": "rhombus"},
    "flow_condition": {"w": 220, "h": 50, "icon": None, "fill": "#FFFFFF", "stroke": "label_stroke", "font": "text_dark", "arc": 50, "shape": "rounded"},
    "flow_request": {"w": 230, "h": 62, "icon": "search", "fill": "request_fill", "stroke": "request_stroke", "font": "text_dark", "arc": 12, "shape": "rounded"},
    "flow_filter": {"w": 245, "h": 76, "icon": "filter", "fill": "filter_fill", "stroke": "filter_stroke", "font": "text_dark", "arc": 18, "shape": "rounded"},
    "flow_data": {"w": 245, "h": 72, "icon": "book", "fill": "knowledge_fill", "stroke": "knowledge_stroke", "font": "text_dark", "arc": 12, "shape": "rounded"},
    "flow_result": {"w": 245, "h": 72, "icon": None, "fill": "#DDE9DB", "stroke": "knowledge_stroke", "font": "text_dark", "arc": 12, "shape": "rounded"},
    "flow_output": {"w": 230, "h": 62, "icon": "code", "fill": "platform_fill", "stroke": "platform_stroke", "font": "#FFFFFF", "arc": 12, "shape": "rounded"},
}

VISUAL_FAMILIES = {
    "solid_main": {
        "stroke": COLORS["edge_dark"],
        "stroke_width": 1.5,
        "dash": None,
        "arrow": "block",
        "end_fill": 1,
    },
    "dashed_agent": {
        "stroke": COLORS["edge_dark"],
        "stroke_width": 1.5,
        "dash": "8 6",
        "arrow": "block",
        "end_fill": 1,
    },
    "dotted_knowledge": {
        "stroke": COLORS["edge_soft"],
        "stroke_width": 1.0,
        "dash": "2 2",
        "arrow": "open",
        "end_fill": 0,
    },
}

EDGE_SEMANTICS = {
    "control_flow": {"visual_family": "solid_main", "arrow_policy": "normal"},
    "system_interface": {"visual_family": "solid_main", "arrow_policy": "normal"},
    "platform_support": {"visual_family": "solid_main", "arrow_policy": "normal"},
    "agent_flow": {"visual_family": "dashed_agent", "arrow_policy": "normal"},
    "knowledge_flow": {"visual_family": "dotted_knowledge", "arrow_policy": "normal"},
    "label_ingress_solid": {"visual_family": "solid_main", "arrow_policy": "label_ingress"},
    "label_ingress_knowledge": {"visual_family": "dotted_knowledge", "arrow_policy": "label_ingress"},
}

VISUAL_FAMILY_PRIORITY = {
    "solid_main": 10,
    "dashed_agent": 20,
    "dotted_knowledge": 30,
}

BASE_NODE_STYLE = (
    "rounded=1;whiteSpace=wrap;html=1;strokeWidth=1.5;"
    "fontFamily=Segoe UI, PingFang SC, Microsoft YaHei, Arial, sans-serif;"
    "align=center;verticalAlign=middle;spacing=6;"
)

BASE_EDGE_STYLE = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;labelBackgroundColor=#FFFFFF;fontSize=11;align=center;verticalAlign=middle;"

LAYOUT_PROFILE = {
    "layer_x": 70,
    "layer_w": 1460,
    "rail_x": 90,
    "rail_w": 92,
    "top_y": 90,
    "legend_y": 919,
}


def resolve_color(value: str) -> str:
    return COLORS.get(value, value)


def node_style(node_type: str) -> str:
    spec = NODE_SPECS[node_type]
    shape = spec.get("shape", "rounded")
    if shape == "rhombus":
        return (
            "shape=rhombus;perimeter=rhombusPerimeter;whiteSpace=wrap;html=1;rounded=0;"
            + f"fillColor={resolve_color(spec['fill'])};"
            + f"strokeColor={resolve_color(spec['stroke'])};strokeWidth=1.5;"
            + f"fontColor={resolve_color(spec['font'])};fontSize=12;align=center;verticalAlign=middle;"
            + "fontFamily=Segoe UI, PingFang SC, Microsoft YaHei, Arial, sans-serif;spacing=4;"
        )
    return (
        BASE_NODE_STYLE
        + f"arcSize={spec['arc']};"
        + f"fillColor={resolve_color(spec['fill'])};"
        + f"strokeColor={resolve_color(spec['stroke'])};"
        + f"fontColor={resolve_color(spec['font'])};fontSize=12;"
    )


def group_style(group_type: str) -> str:
    if group_type == "group_existing":
        stroke = COLORS["system_stroke"]
    elif group_type == "group_infra":
        stroke = COLORS["knowledge_stroke"]
    else:
        stroke = COLORS["role_stroke"]
    return (
        BASE_NODE_STYLE
        + f"arcSize=8;fillColor={COLORS['layer_bg']};strokeColor={stroke};"
        + f"fontColor={COLORS['text_dark']};fontStyle=1;fontSize=13;verticalAlign=top;spacingTop=8;"
    )


def layer_bg_style(fill: str) -> str:
    return f"rounded=1;whiteSpace=wrap;html=1;arcSize=6;fillColor={fill};strokeColor={COLORS['role_stroke']};strokeWidth=1;"


def rail_style() -> str:
    return (
        f"rounded=1;whiteSpace=wrap;html=1;arcSize=12;fillColor={COLORS['rail_fill']};"
        f"strokeColor={COLORS['rail_fill']};fontColor={COLORS['text_dark']};fontSize=14;fontStyle=1;"
        "fontFamily=Segoe UI, PingFang SC, Microsoft YaHei, Arial, sans-serif;align=center;verticalAlign=middle;"
    )


def text_style(font_size: int = 11, bold: bool = False) -> str:
    return (
        f"text;html=1;strokeColor=none;fillColor=none;fontColor={COLORS['text_dark']};fontSize={font_size};"
        f"fontStyle={1 if bold else 0};fontFamily=Segoe UI, PingFang SC, Microsoft YaHei, Arial, sans-serif;"
        "align=center;verticalAlign=middle;"
    )


def edge_style(edge_type: str, include_endpoint_style: str = "") -> str:
    sem = EDGE_SEMANTICS[edge_type]
    family = VISUAL_FAMILIES[sem["visual_family"]]
    dash = f"dashed=1;dashPattern={family['dash']};" if family["dash"] else ""
    if sem["arrow_policy"] == "label_ingress":
        arrow = "endArrow=none;endFill=0;"
    else:
        arrow = f"endArrow={family['arrow']};endFill={family['end_fill']};"
    return (
        BASE_EDGE_STYLE
        + dash
        + arrow
        + f"strokeWidth={family['stroke_width']};strokeColor={family['stroke']};"
        + include_endpoint_style
    )


def edge_visual_family(edge_type: str) -> str:
    return EDGE_SEMANTICS[edge_type]["visual_family"]


def layer_fill_for(layer_id: str) -> str:
    if LAYER_BACKGROUND_MODE == "tiered":
        return LAYER_TIERED_FILLS.get(layer_id, COLORS["layer_bg"])
    return COLORS["layer_bg"]


def estimate_text_width(text: str) -> float:
    width = 0.0
    for ch in text:
        if ch.isspace():
            width += 4.0
        elif ord(ch) > 127:
            width += 10.5
        else:
            width += 6.8
    return width
