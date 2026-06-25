"""draw.io XML data structures and label value helpers."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import html
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

from .icons import make_icon_data_uri
from .styles import (
    EDGE_SEMANTICS,
    NODE_SPECS,
    VISUAL_FAMILY_PRIORITY,
    edge_style,
    edge_visual_family,
    resolve_color,
)


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


@dataclass
class Vertex:
    id: str
    value: str
    style: str
    box: Box


@dataclass
class Edge:
    id: str
    source: Optional[str]
    target: Optional[str]
    style: str
    points: Optional[Tuple[Tuple[float, float], Tuple[float, float]]] = None
    value: str = ""


def label_value(node: Dict[str, Any], node_type: str) -> str:
    spec = NODE_SPECS[node_type]
    parts = []
    font_color = resolve_color(spec["font"])
    icon_name = node.get("icon") or spec.get("icon")
    if icon_name:
        icon_uri = make_icon_data_uri(icon_name, font_color)
        parts.append(f'<img src="{icon_uri}" width="22" height="22" style="vertical-align:middle;"/>')
        parts.append("<br>")
    parts.append(f"<b>{html.escape(node.get('title', ''))}</b>")
    if node.get("subtitle"):
        parts.append(f'<br><font style="font-size:11px">{html.escape(node["subtitle"])}</font>')
    for line in node.get("lines", []):
        parts.append(f'<br><font style="font-size:11px">{html.escape(line)}</font>')
    return "".join(parts)


def layer_rail_value(index: int, title: str) -> str:
    return f"<b>{index}</b><br>{html.escape(title)}"


def title_value(title: str, subtitle: str) -> str:
    return f'<b>{html.escape(title)}</b><br><font style="font-size:13px;color:#4D4D4D">{html.escape(subtitle)}</font>'


def diagram_page_name(dsl: Dict[str, Any]) -> str:
    return str(dsl.get("page_name") or dsl.get("title") or "DSL Demo")


def diagram_page_id(dsl: Dict[str, Any]) -> str:
    name = diagram_page_name(dsl)
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()[:32] or "diagram"
    digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:10]
    return f"page_{slug}_{digest}"


class DrawioRenderer:
    def __init__(self, dsl: Dict[str, Any]):
        self.dsl = dsl
        self.width = int(dsl.get("canvas", {}).get("width", 1600))
        self.height = int(dsl.get("canvas", {}).get("height", 989))
        self.vertices: List[Vertex] = []
        self.edges: List[Edge] = []
        self.boxes: Dict[str, Box] = {}
        self.edge_counter = 1
        self.port_records: List[Dict[str, Any]] = []

    def add_vertex(self, vid: str, value: str, style: str, box: Box):
        if vid in self.boxes:
            raise ValueError(f"Duplicate vertex id: {vid}")
        self.vertices.append(Vertex(vid, value, style, box))
        self.boxes[vid] = box

    def add_edge(
        self,
        source: Optional[str],
        target: Optional[str],
        edge_type: str,
        points=None,
        eid: Optional[str] = None,
        endpoint_style_override: Optional[str] = None,
        value: str = "",
    ):
        eid = eid or f"e_{self.edge_counter:03d}"
        self.edge_counter += 1
        ep = endpoint_style_override or ""
        if not ep and source and target and source in self.boxes and target in self.boxes:
            src_side, tgt_side = self.choose_sides_for_edge(source, target)
            ep = self.port_style_for_sides(src_side, 0.5, tgt_side, 0.5)
        self.edges.append(Edge(eid, source, target, edge_style(edge_type, ep), points, html.escape(value).replace("\n", "<br>") if value else ""))

    @staticmethod
    def choose_sides(src: Box, tgt: Box) -> Tuple[str, str]:
        dx = tgt.cx - src.cx
        dy = tgt.cy - src.cy
        if abs(dy) < 20 and dx >= 0:
            return "right", "left"
        if abs(dy) < 20 and dx < 0:
            return "left", "right"
        if dy > 0:
            return "bottom", "top"
        return "top", "bottom"

    def choose_sides_for_edge(self, source_id: str, target_id: str) -> Tuple[str, str]:
        if self.dsl.get("diagram_type") == "rag_sequence_flow" or self.dsl.get("layout", {}).get("mode") == "rag_sequence_flow":
            source_participant = self.node_participant_by_id(source_id)
            target_participant = self.node_participant_by_id(target_id)
            if source_participant and target_participant and source_participant != target_participant:
                dx = self.boxes[target_id].cx - self.boxes[source_id].cx
                if dx >= 0:
                    return "right", "left"
                return "left", "right"
        return self.choose_sides(self.boxes[source_id], self.boxes[target_id])

    @staticmethod
    def side_port(side: str, fraction: float) -> Tuple[float, float]:
        if side == "top":
            return fraction, 0.0
        if side == "bottom":
            return fraction, 1.0
        if side == "left":
            return 0.0, fraction
        if side == "right":
            return 1.0, fraction
        raise ValueError(f"Unknown side: {side}")

    @staticmethod
    def fmt_port(v: float) -> str:
        return f"{v:.3f}".rstrip("0").rstrip(".")

    @classmethod
    def port_style_for_sides(cls, src_side: str, src_fraction: float, tgt_side: str, tgt_fraction: float) -> str:
        exit_x, exit_y = cls.side_port(src_side, src_fraction)
        entry_x, entry_y = cls.side_port(tgt_side, tgt_fraction)
        return (
            f"exitX={cls.fmt_port(exit_x)};exitY={cls.fmt_port(exit_y)};"
            f"entryX={cls.fmt_port(entry_x)};entryY={cls.fmt_port(entry_y)};"
        )

    def node_type_by_id(self, node_id: str) -> Optional[str]:
        dtype = self.dsl.get("diagram_type", "layered_architecture")
        if dtype == "layered_architecture":
            for layer in self.dsl.get("layers", []):
                for node in layer.get("nodes", []):
                    if node.get("id") == node_id:
                        return node.get("type")
                for group in layer.get("groups", []):
                    if group.get("id") == node_id:
                        return group.get("type")
                    for node in group.get("nodes", []):
                        if node.get("id") == node_id:
                            return node.get("type")
            for label in self.dsl.get("labels", []):
                if label.get("id") == node_id:
                    return label.get("type")
        else:
            for node in self.dsl.get("nodes", []):
                if node.get("id") == node_id:
                    return node.get("type")
        return None

    def node_participant_by_id(self, node_id: str) -> Optional[str]:
        for node in self.dsl.get("nodes", []):
            if node.get("id") == node_id:
                return node.get("layout_hint", {}).get("participant")
        return None

    def compute_endpoint_overrides(self, edge_specs: List[Dict[str, Any]]) -> Dict[int, str]:
        records: Dict[int, Dict[str, Any]] = {}
        usage: Dict[Tuple[str, str], List[Tuple[int, str, float]]] = {}
        dtype = self.dsl.get("diagram_type", "layered_architecture")

        for idx, e in enumerate(edge_specs, 1):
            src_id, tgt_id = e.get("source"), e.get("target")
            if src_id not in self.boxes or tgt_id not in self.boxes or e.get("type") not in EDGE_SEMANTICS:
                continue
            src, tgt = self.boxes[src_id], self.boxes[tgt_id]
            src_side, tgt_side = self.choose_sides_for_edge(src_id, tgt_id)
            family = edge_visual_family(e["type"])
            src_group = family
            tgt_group = family
            if dtype in {"flowchart_decision_tree", "decision_tree"}:
                if self.node_type_by_id(src_id) == "flow_decision":
                    src_group = f"{family}:{tgt_id}"
                if self.node_type_by_id(tgt_id) == "flow_output":
                    tgt_group = f"{family}:{src_id}"
            src_opposite_coord = tgt.cy if src_side in {"left", "right"} else tgt.cx
            tgt_opposite_coord = src.cy if tgt_side in {"left", "right"} else src.cx
            usage.setdefault((src_id, src_side), []).append((idx, src_group, src_opposite_coord))
            usage.setdefault((tgt_id, tgt_side), []).append((idx, tgt_group, tgt_opposite_coord))
            records[idx] = {
                "source": src_id, "target": tgt_id, "type": e["type"], "family": family,
                "src_group": src_group, "tgt_group": tgt_group,
                "src_side": src_side, "tgt_side": tgt_side,
            }

        port_lookup: Dict[Tuple[str, str, str], float] = {}
        for (node_id, side), items in usage.items():
            group_coords: Dict[str, List[float]] = {}
            for _, group, coord in items:
                group_coords.setdefault(group, []).append(coord)
            ordered = sorted(
                group_coords,
                key=lambda grp: (sum(group_coords[grp]) / len(group_coords[grp]), VISUAL_FAMILY_PRIORITY.get(grp.split(":")[0], 999), grp),
            )
            k = len(ordered)
            for rank, group in enumerate(ordered, 1):
                port_lookup[(node_id, side, group)] = rank / (k + 1)

        overrides: Dict[int, str] = {}
        self.port_records = []
        for idx, rec in records.items():
            sf = port_lookup[(rec["source"], rec["src_side"], rec["src_group"])]
            tf = port_lookup[(rec["target"], rec["tgt_side"], rec["tgt_group"])]
            overrides[idx] = self.port_style_for_sides(rec["src_side"], sf, rec["tgt_side"], tf)
            rec = dict(rec)
            rec["source_port_fraction"] = sf
            rec["target_port_fraction"] = tf
            rec["source_port"] = self.side_port(rec["src_side"], sf)
            rec["target_port"] = self.side_port(rec["tgt_side"], tf)
            self.port_records.append(rec)
        return overrides

    def layout(self):
        dtype = self.dsl.get("diagram_type", "layered_architecture")
        if dtype == "layered_architecture":
            from .layouts.layered_architecture import layout_layered_architecture
            layout_layered_architecture(self)
        elif dtype in {"flowchart_decision_tree", "decision_tree", "rag_sequence_flow"}:
            from .layouts.flowchart_decision_tree import layout_flowchart_decision_tree
            layout_flowchart_decision_tree(self)
        else:
            raise ValueError(f"Unsupported diagram_type: {dtype}")

    def to_xml(self) -> str:
        self.layout()
        mxfile = ET.Element("mxfile", {
            "host": "app.diagrams.net",
            "modified": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
            "version": "24.7.17",
            "type": "device",
            "pages": "1",
        })
        diagram = ET.SubElement(mxfile, "diagram", {"id": diagram_page_id(self.dsl), "name": diagram_page_name(self.dsl)})
        model = ET.SubElement(diagram, "mxGraphModel", {"dx": "1307", "dy": "762", "grid": "1", "gridSize": "10", "guides": "1", "tooltips": "1", "connect": "1", "arrows": "1", "fold": "1", "page": "1", "pageScale": "1", "pageWidth": str(self.width), "pageHeight": str(self.height), "math": "0", "shadow": "0"})
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", {"id": "0"})
        ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})
        for v in self.vertices:
            cell = ET.SubElement(root, "mxCell", {"id": v.id, "value": v.value, "style": v.style, "vertex": "1", "parent": "1"})
            geo_attrs = {"width": f"{v.box.w:g}", "height": f"{v.box.h:g}", "as": "geometry"}
            if v.box.x != 0:
                geo_attrs["x"] = f"{v.box.x:g}"
            if v.box.y != 0:
                geo_attrs["y"] = f"{v.box.y:g}"
            ET.SubElement(cell, "mxGeometry", geo_attrs)
        for e in self.edges:
            attrs = {"id": e.id, "style": e.style, "edge": "1", "parent": "1"}
            if e.value:
                attrs["value"] = e.value
            if e.source:
                attrs["source"] = e.source
            if e.target:
                attrs["target"] = e.target
            cell = ET.SubElement(root, "mxCell", attrs)
            geo = ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})
            if e.points:
                src, tgt = e.points
                ET.SubElement(geo, "mxPoint", {"x": f"{src[0]:g}", "y": f"{src[1]:g}", "as": "sourcePoint"})
                ET.SubElement(geo, "mxPoint", {"x": f"{tgt[0]:g}", "y": f"{tgt[1]:g}", "as": "targetPoint"})
        return "<?xml version='1.0' encoding='utf-8'?>\n" + ET.tostring(mxfile, encoding="unicode")
