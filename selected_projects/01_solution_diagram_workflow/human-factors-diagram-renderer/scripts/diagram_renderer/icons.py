"""Local icon registry, rasterization, and icon governance helpers."""

from __future__ import annotations

import base64
import difflib
import re
import struct
import zlib
from typing import Dict, List, Tuple


ICON_SVG_BODY: Dict[str, str] = {
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    "alert": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="7" x2="12" y2="13"/><line x1="12" y1="17" x2="12" y2="17"/>',
    "message": '<path d="M21 15a4 4 0 0 1-4 4H7l-4 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z"/>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "truck": '<rect x="1" y="6" width="13" height="10" rx="2"/><path d="M14 9h4l4 4v3h-8z"/><circle cx="6" cy="18" r="2"/><circle cx="18" cy="18" r="2"/>',
    "bar_chart": '<line x1="6" y1="20" x2="6" y2="12"/><line x1="12" y1="20" x2="12" y2="6"/><line x1="18" y1="20" x2="18" y2="10"/>',
    "tool": '<path d="M14.7 6.3l3 3 3.7-3.7a6 6 0 0 1-7.9 7.9L6.6 20.4a2 2 0 1 1-2.8-2.8l6.9-6.9a6 6 0 0 1 4-4.4z"/>',
    "package": '<path d="M21 16V8l-9-5-9 5v8l9 5z"/><polyline points="3.3 7.5 12 12.5 20.7 7.5"/><line x1="12" y1="22" x2="12" y2="12"/>',
    "check_circle": '<circle cx="12" cy="12" r="10"/><polyline points="8 12 11 15 16 9"/>',
    "brain": '<path d="M9.5 3A3 3 0 0 1 12 6v13a3 3 0 0 1-5.5 1.5A3.5 3.5 0 0 1 4 14a3.5 3.5 0 0 1 1-6.5A3 3 0 0 1 9.5 3z"/><path d="M14.5 3A3 3 0 0 0 12 6v13a3 3 0 0 0 5.5 1.5A3.5 3.5 0 0 0 20 14a3.5 3.5 0 0 0-1-6.5A3 3 0 0 0 14.5 3z"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.9"/><path d="M16 3.1a4 4 0 0 1 0 7.8"/>',
    "debate": '<path d="M4 4h11a3 3 0 0 1 3 3v5a3 3 0 0 1-3 3H9l-5 4v-4a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3z"/><path d="M9 8h5"/><path d="M9 11h3"/>',
    "dollar": '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7H14a3.5 3.5 0 0 1 0 7H6"/>',
    "smartphone": '<rect x="7" y="2" width="10" height="20" rx="2"/><line x1="11" y1="18" x2="13" y2="18"/>',
    "database_local": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "code": '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
    "server": '<rect x="3" y="4" width="18" height="6" rx="2"/><rect x="3" y="14" width="18" height="6" rx="2"/><line x1="7" y1="7" x2="7" y2="7"/><line x1="7" y1="17" x2="7" y2="17"/>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 12 12 17 22 12"/><polyline points="2 17 12 22 22 17"/>',
    "vector": '<circle cx="5" cy="5" r="3"/><circle cx="19" cy="5" r="3"/><circle cx="12" cy="19" r="3"/><path d="M8 6.5l8 0"/><path d="M6.5 8l4 8"/><path d="M17.5 8l-4 8"/>',
    "search": '<circle cx="11" cy="11" r="7"/><line x1="16" y1="16" x2="22" y2="22"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H21"/><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H21v20H6.5A2.5 2.5 0 0 1 4 19.5z"/>',
    "filter": '<polygon points="22 3 2 3 10 12 10 19 14 21 14 12 22 3"/>',
    "plug": '<path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/><path d="M6 8h12v4a6 6 0 0 1-12 0z"/>',
    "key": '<circle cx="7" cy="14" r="4"/><path d="M10 14h12"/><path d="M16 14v4"/><path d="M20 14v3"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-5"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 22a8 8 0 0 1 16 0"/>',
    "cpu": '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="15" x2="23" y2="15"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="15" x2="4" y2="15"/>',
    "app": '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5"/><path d="M3 12c0 1.7 4 3 9 3s9-1.3 9-3"/>',
    "stack": '<rect x="4" y="4" width="16" height="4" rx="1"/><rect x="4" y="10" width="16" height="4" rx="1"/><rect x="4" y="16" width="16" height="4" rx="1"/>',
}

ICON_SIMILARITY_THRESHOLD = 0.82


class TinyIcon:
    def __init__(self, size: int = 22, color: Tuple[int, int, int, int] = (26, 26, 26, 255)):
        self.size = size
        self.color = color
        self.pixels = bytearray([0, 0, 0, 0] * size * size)

    def set_px(self, x: int, y: int):
        if 0 <= x < self.size and 0 <= y < self.size:
            i = (y * self.size + x) * 4
            self.pixels[i:i + 4] = bytes(self.color)

    def line(self, x1: int, y1: int, x2: int, y2: int, thickness: int = 1):
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        x, y = x1, y1
        while True:
            for ox in range(-(thickness // 2), thickness // 2 + 1):
                for oy in range(-(thickness // 2), thickness // 2 + 1):
                    self.set_px(x + ox, y + oy)
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def rect(self, x: int, y: int, w: int, h: int):
        self.line(x, y, x + w, y)
        self.line(x + w, y, x + w, y + h)
        self.line(x + w, y + h, x, y + h)
        self.line(x, y + h, x, y)

    def circle(self, cx: int, cy: int, r: int):
        x, y = r, 0
        err = 0
        while x >= y:
            for px, py in [
                (cx + x, cy + y), (cx + y, cy + x), (cx - y, cy + x), (cx - x, cy + y),
                (cx - x, cy - y), (cx - y, cy - x), (cx + y, cy - x), (cx + x, cy - y),
            ]:
                self.set_px(px, py)
            y += 1
            if err <= 0:
                err += 2 * y + 1
            if err > 0:
                x -= 1
                err -= 2 * x + 1

    def ellipse(self, cx: int, cy: int, rx: int, ry: int):
        for deg in range(0, 360, 4):
            import math
            x = int(round(cx + rx * math.cos(math.radians(deg))))
            y = int(round(cy + ry * math.sin(math.radians(deg))))
            self.set_px(x, y)

    def polyline(self, pts: List[Tuple[int, int]], closed: bool = False):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1])
        if closed and len(pts) > 2:
            self.line(pts[-1][0], pts[-1][1], pts[0][0], pts[0][1])

    def png_base64(self) -> str:
        def chunk(tag: bytes, data: bytes) -> bytes:
            return struct.pack("!I", len(data)) + tag + data + struct.pack("!I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        raw = b"".join(b"\x00" + self.pixels[y * self.size * 4:(y + 1) * self.size * 4] for y in range(self.size))
        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack("!IIBBBBB", self.size, self.size, 8, 6, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(raw, 9))
        png += chunk(b"IEND", b"")
        return base64.b64encode(png).decode("ascii")


def draw_named_icon(ic: TinyIcon, name: str):
    # Hand-rasterized 22px versions. They only need to be visually distinct at small size;
    # semantic similarity is checked from ICON_SVG_BODY instead.
    if name == "target":
        ic.circle(11, 11, 9); ic.circle(11, 11, 5); ic.circle(11, 11, 1)
    elif name == "message":
        ic.rect(3, 4, 16, 11); ic.line(7, 15, 4, 19); ic.line(7, 15, 11, 15)
    elif name == "activity":
        ic.polyline([(1,11),(5,11),(8,4),(13,19),(16,11),(21,11)])
    elif name == "truck":
        ic.rect(1, 7, 11, 7); ic.line(12,9,17,9); ic.line(17,9,21,13); ic.line(21,13,21,14); ic.line(12,14,21,14); ic.circle(6,17,2); ic.circle(17,17,2)
    elif name == "bar_chart":
        ic.line(5,18,5,12,2); ic.line(11,18,11,6,2); ic.line(17,18,17,10,2)
    elif name == "tool":
        ic.line(5,17,16,6,2); ic.circle(5,17,2); ic.polyline([(14,4),(18,8),(20,5)])
    elif name == "package":
        ic.polyline([(11,2),(20,7),(20,15),(11,20),(2,15),(2,7),(11,2)], True); ic.line(2,7,11,12); ic.line(20,7,11,12); ic.line(11,12,11,20)
    elif name == "check_circle":
        ic.circle(11,11,9); ic.polyline([(7,11),(10,14),(16,8)])
    elif name == "brain":
        ic.circle(8,8,4); ic.circle(14,8,4); ic.circle(8,14,4); ic.circle(14,14,4); ic.line(11,5,11,18)
    elif name == "users":
        ic.circle(8,7,3); ic.circle(15,8,2); ic.polyline([(2,19),(4,15),(12,15),(14,19)]); ic.polyline([(14,16),(18,16),(20,19)])
    elif name == "debate":
        ic.rect(3,4,15,10); ic.line(7,14,4,18); ic.line(8,8,14,8); ic.line(8,11,12,11)
    elif name == "dollar":
        ic.line(11,2,11,20); ic.polyline([(16,5),(8,5),(7,9),(15,12),(15,17),(6,17)])
    elif name == "smartphone":
        ic.rect(7,2,8,18); ic.line(10,17,12,17)
    elif name in {"database_local", "database"}:
        ic.ellipse(11,5,8,3); ic.rect(3,5,16,13); ic.line(3,11,19,11); ic.line(3,16,19,16)
    elif name == "code":
        ic.polyline([(8,6),(2,11),(8,16)]); ic.polyline([(14,6),(20,11),(14,16)])
    elif name == "server":
        ic.rect(3,4,16,5); ic.rect(3,13,16,5); ic.set_px(7,6); ic.set_px(7,15)
    elif name == "layers":
        ic.polyline([(11,2),(2,7),(11,12),(20,7),(11,2)], True); ic.polyline([(2,12),(11,17),(20,12)]); ic.polyline([(2,16),(11,21),(20,16)])
    elif name == "vector":
        ic.circle(5,5,2); ic.circle(17,5,2); ic.circle(11,17,2); ic.line(7,5,15,5); ic.line(6,7,10,15); ic.line(16,7,12,15)
    elif name == "search":
        ic.circle(10,10,6); ic.line(15,15,20,20)
    elif name == "book":
        ic.rect(5,3,13,17); ic.line(8,3,8,20); ic.line(5,17,18,17)
    elif name == "filter":
        ic.polyline([(2,4),(20,4),(13,12),(13,19),(9,17),(9,12),(2,4)], True)
    elif name == "plug":
        ic.line(8,2,8,8); ic.line(14,2,14,8); ic.rect(6,8,10,6); ic.line(11,14,11,20)
    elif name == "key":
        ic.circle(7,13,4); ic.line(11,13,21,13); ic.line(16,13,16,17); ic.line(20,13,20,16)
    elif name == "shield":
        ic.polyline([(11,2),(19,5),(19,11),(16,17),(11,21),(6,17),(3,11),(3,5),(11,2)], True); ic.polyline([(7,11),(10,14),(15,8)])
    elif name == "user":
        ic.circle(11,7,4); ic.polyline([(4,20),(7,15),(15,15),(18,20)])
    elif name == "cpu":
        ic.rect(5,5,12,12); ic.rect(9,9,4,4)
        for p in [4,8,14,18]:
            ic.line(p,3,p,5); ic.line(p,17,p,19); ic.line(3,p,5,p); ic.line(17,p,19,p)
    elif name == "app":
        ic.rect(3,3,16,16); ic.line(3,8,19,8); ic.line(8,8,8,19)
    elif name == "stack":
        ic.rect(4,4,14,3); ic.rect(4,10,14,3); ic.rect(4,16,14,3)
    else:
        ic.rect(5,5,12,12)


def make_icon_base64(icon_name: str, font_color: str) -> str:
    rgba = (255, 255, 255, 255) if font_color.upper() == "#FFFFFF" else (26, 26, 26, 255)
    ic = TinyIcon(22, rgba)
    draw_named_icon(ic, icon_name)
    return ic.png_base64()


def full_svg(icon_name: str, stroke_color: str = "currentColor") -> str:
    body = ICON_SVG_BODY[icon_name]
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{stroke_color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{body}</svg>'


def make_icon_data_uri(icon_name: str, font_color: str) -> str:
    stroke_color = "#FFFFFF" if font_color.upper() == "#FFFFFF" else "#1A1A1A"
    svg = full_svg(icon_name, stroke_color)
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def canonicalize_svg(svg: str) -> str:
    """Normalize SVG enough for approximate duplicate detection."""
    svg = svg.lower()
    svg = re.sub(r'#[0-9a-f]{3,8}|currentcolor|none|round', '', svg)
    svg = re.sub(r'\s+', ' ', svg)
    svg = re.sub(r'\d+\.\d+', lambda m: str(round(float(m.group(0)), 1)), svg)
    return svg.strip()


def icon_similarity(icon_a: str, icon_b: str) -> float:
    # Compare icon bodies only; the shared <svg ...> wrapper would otherwise
    # create false positives because all icons intentionally share style grammar.
    a = canonicalize_svg(ICON_SVG_BODY[icon_a])
    b = canonicalize_svg(ICON_SVG_BODY[icon_b])
    seq = difflib.SequenceMatcher(None, a, b).ratio()
    tags_a = set(re.findall(r'<(path|line|circle|rect|ellipse|polyline|polygon)\b', a))
    tags_b = set(re.findall(r'<(path|line|circle|rect|ellipse|polyline|polygon)\b', b))
    tag_jaccard = len(tags_a & tags_b) / len(tags_a | tags_b) if tags_a | tags_b else 1.0
    return round(0.75 * seq + 0.25 * tag_jaccard, 3)
