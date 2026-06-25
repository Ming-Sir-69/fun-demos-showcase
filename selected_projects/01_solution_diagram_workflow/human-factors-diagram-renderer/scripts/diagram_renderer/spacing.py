"""Reusable spacing rules for layout profiles."""

from __future__ import annotations


BASE_GAP = 50
LINE_WEIGHT = 25
UNLABELED_DISCOUNT = 12
BUS_COMPENSATION = 8
LEGEND_BOTTOM_MARGIN = 26
LEGEND_CONTENT_GAP = 44
LEGEND_ROW_HEIGHT = 28
LEGEND_BOX_PAD_Y = 10


def layered_gap(line_count: int, labeled_count: int = 0) -> float:
    """Return the validated layered-architecture gap formula."""
    if line_count < 0 or labeled_count < 0 or labeled_count > line_count:
        raise ValueError("Invalid line/labeled counts for gap calculation")
    return BASE_GAP + line_count * LINE_WEIGHT - (line_count - labeled_count) * UNLABELED_DISCOUNT


def decision_tree_bus_gap(branch_count: int, labeled_count: int = 0) -> float:
    """Return the minimum vertical corridor for a split/merge bus."""
    return layered_gap(branch_count, labeled_count) + BUS_COMPENSATION


def legend_box_height(edge_count: int = 0, node_color_count: int = 0, has_lane_note: bool = False) -> float:
    """Return legend box height based on visible legend rows."""
    row_count = int(edge_count > 0) + int(node_color_count > 0) + int(has_lane_note)
    if row_count <= 0:
        return 0
    return max(34, LEGEND_BOX_PAD_Y + row_count * LEGEND_ROW_HEIGHT)


def legend_reserved_height(edge_count: int = 0, node_color_count: int = 0, has_lane_note: bool = False) -> float:
    """Return the full bottom reserve: content gap + legend box + bottom margin."""
    box_h = legend_box_height(edge_count, node_color_count, has_lane_note)
    if box_h <= 0:
        return 0
    return LEGEND_CONTENT_GAP + box_h + LEGEND_BOTTOM_MARGIN


def legend_top_y(canvas_height: float, edge_count: int = 0, node_color_count: int = 0, has_lane_note: bool = False) -> float:
    """Return legend box top y for a bottom-anchored legend."""
    return canvas_height - legend_box_height(edge_count, node_color_count, has_lane_note) - LEGEND_BOTTOM_MARGIN


def content_bottom_before_legend(canvas_height: float, edge_count: int = 0, node_color_count: int = 0, has_lane_note: bool = False) -> float:
    """Return the lowest y where main content may end before the legend zone."""
    return canvas_height - legend_reserved_height(edge_count, node_color_count, has_lane_note)
