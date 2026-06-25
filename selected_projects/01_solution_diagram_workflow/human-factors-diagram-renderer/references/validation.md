# 04 — 自检验收（C1-C6）

> 强制步骤。每项不通过 → 修复 → 重检 → 全部通过才算闭环。

---

## C0 — DSL 白名单与 schema 验证

验证方法：先检查 JSON 是否符合 DSL 边界，再进入 XML 生成。

```bash
python scripts/validate_dsl.py --input assets/examples/json/chart04_rag_sequence_flow_r01.json
```

- 顶层字段是否只来自 `diagram_dsl_v0_1_spec.md`
- `diagram_type` 是否为当前 renderer 已支持图型
- `flowchart_decision_tree` 是否使用 `rows + nodes + edges`
- 判断树条件是否落成显式 `flow_condition` 节点，而不是边标签

**通过标准**：DSL 结构、字段和图型全部合法；不通过则不得进入 C1-C6。

---

## C1 — 间距公式验证

验证方法：对每层间隙，计算实际间距并与公式值对比。

```python
import xml.etree.ElementTree as ET

def check_spacing(xml_text, gaps):
    """gaps: [(gap_name, top_y, bottom_y, N, M), ...]"""
    root = ET.fromstring(xml_text)
    mxgraph = root.find(".//mxGraphModel")
    for name, top_y, bottom_y, N, M in gaps:
        G_formula = 50 + N * 25 - (N - M) * 12
        G_actual = bottom_y - top_y
        if G_actual < G_formula:
            print(f"❌ {name}: 实际{G_actual}px < 公式{G_formula}px (N={N}, M={M})")
        else:
            print(f"✅ {name}: 实际{G_actual}px ≥ 公式{G_formula}px")

# 使用示例（以 chart1 为例）：
# gaps = [
#     ("层3(编排)→层2(专家)", 260, 330, 8, 0),  # N=8条线, M=0条有标签
#     ("人审→层1(知识库)", 640, 690, 1, 0),      # N=1条线, M=0条有标签
# ]
```

**通过标准**：每层间隙实际值 ≥ 公式值。不通过 → 增大 pageHeight，下移下层。

---

## C2 — 图标去重检查

验证方法：统计每个图标的使用次数和用户列表，检查同图标是否用于**不同职能**的节点。

```python
from collections import Counter

# 列出所有节点及使用的图标名
NODE_ICONS = {
    "user": ("users", "工程师用户"),
    "main_agent": ("cpu", "主控Agent"),
    "task_split": ("layers", "任务拆解与路由"),
    # ... 继续补充
}

icon_usage = Counter(icon for icon, _ in NODE_ICONS.values())
for icon, count in icon_usage.items():
    if count > 1:
        users = [nid for nid, (ic, _) in NODE_ICONS.items() if ic == icon]
        print(f"⚠️ 图标 '{icon}' 被 {count} 个节点共用: {users}")
        print(f"   检查这些节点是否属于同一职能类别")
```

**通过标准**：不同职能节点使用不同图标。如果共用图标，必须确认职能相同。

---

## C3 — 标签存在性检查

验证方法：检查关键标签节点的 value 是否非空。

```python
def check_labels(xml_text, label_ids):
    root = ET.fromstring(xml_text)
    for lid in label_ids:
        cell = root.find(f".//*[@id='{lid}']")
        value = cell.get("value", "") if cell is not None else ""
        if value.strip():
            print(f"✅ 标签 {lid} 存在且有内容")
        else:
            print(f"❌ 标签 {lid} 缺失或为空")

# 使用示例：
# check_labels(xml, ["label_dispatch", "label_return", "human_check"])
```

**通过标准**：所有预期标签的 value 非空。

---

## C3.5 — 判断树条件节点检查

验证方法：对 `flowchart_decision_tree` 额外检查：

- 是否存在 `flow_condition` 节点
- `q1` 等判断节点的每个分支是否都连接到独立条件节点
- 条件文字是否错误挂在 edge label 上

**通过标准**：条件 A/B/C/D 均为显式节点，且分支一一对应。

---

## C4 — 包围盒重叠检测

验证方法：检查关键元素对之间是否有交集。

```python
def boxes_overlap(a, b):
    """a, b: (x, y, w, h)"""
    return not (a[0] + a[2] <= b[0] or b[0] + b[2] <= a[0]
                or a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1])

def check_overlaps(xml_text, pairs):
    """pairs: [(id_a, id_b, label), ...]"""
    for a_id, b_id, label in pairs:
        # 从 XML 中提取坐标
        a = get_cell_geometry(xml_text, a_id)
        b = get_cell_geometry(xml_text, b_id)
        if a and b and boxes_overlap(a, b):
            print(f"❌ {label}: {a_id}({a}) 与 {b_id}({b}) 重叠")
        else:
            print(f"✅ {label}: 无重叠")
```

**通过标准**：无任何关键元素重叠。

---

## C5 — XML 合法性 + emoji 零使用

```python
import re

def check_xml_and_emoji(xml_text):
    # 1) XML 合法性
    try:
        ET.fromstring(xml_text)
        print("✅ XML 解析正常")
    except ET.ParseError as e:
        print(f"❌ XML 解析失败: {e}")
        return False

    # 2) emoji 检查（常见 emoji 范围）
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # 表情符号
        "\U0001F300-\U0001F5FF"  # 符号 & 象形文字
        "\U0001F680-\U0001F6FF"  # 交通 & 地图
        "\U0001F1E0-\U0001F1FF"  # 国旗
        "\U00002702-\U000027B0"  # 其他符号
        "\U000024C2-\U0001F251"  # 其他
        "]+", flags=re.UNICODE)

    values = re.findall(r'value="([^"]*)"', xml_text)
    for v in values:
        emojis = emoji_pattern.findall(v)
        if emojis:
            print(f"❌ value 中含 emoji: {emojis} 在...{v[:50]}...")
            return False

    print("✅ 无 emoji 使用")
    return True
```

**通过标准**：XML 可解析；所有 value 中无 emoji 字符。

---

## C6 — 线型一致性检查

验证方法：同语义的连线是否全图使用相同的 style 参数。

```python
def check_line_consistency(xml_text):
    root = ET.fromstring(xml_text)
    edges = root.findall(".//*[@edge='1']")

    # 按语义分组检查 style 一致性
    # 语义约定来自命名约定或 source/target
    # ...
    
    print("✅ 线型一致性检查完成（需逐项确认）")
```

**人工辅助**：
- 查看所有 `endArrow=block;endFill=1` 的实线条：style 中 `strokeWidth` 和 `strokeColor` 是否一致
- 查看所有 `dashed=1;dashPattern=8 6` 的虚线条：dashPattern、样式是否一致
- 查看所有 `dashPattern=2 2` 的点线条：是否全图统一

**通过标准**：同一语义的连线在全图使用完全相同的 style 参数。

---

## C7 — 图层顺序检查（防止箭头被覆盖）

验证方法：XML 中所有 `edge="1"` 必须在最后一个 `vertex="1"` 之后。

```python
def check_layer_order(xml_text):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_text)
    cells = root.findall(".//*[@id]")
    last_vertex = -1
    first_edge = -1
    for i, cell in enumerate(cells):
        if cell.get("vertex") == "1":
            last_vertex = i
        if cell.get("edge") == "1" and first_edge == -1:
            first_edge = i
    if first_edge > last_vertex:
        print("✅ 所有边在所有节点之后，箭头应可见")
    else:
        print(f"❌ 第一条边(#{first_edge}) 在最后一个节点(#{last_vertex}) 之前，箭头可能被节点填充色覆盖")
        print("   修复：将所有 edge=1 的 mxCell 移到最后声明的区域内")
```

**通过标准**：第一个 edge 的索引 > 最后一个 vertex 的索引。

---

## C7.5 — draw.io 工作簿页签检查

验证方法：检查最终写出的 `.drawio` 文件，而不只检查内存中的即时渲染结果。

必检项：

- 根节点 `mxfile` 的 `pages` 是否等于实际 `<diagram>` 数量
- 单图交付是否只有一个 `<diagram>`
- `<diagram name="...">` 是否等于 JSON 的 `page_name`
- `<diagram id="...">` 是否为稳定页 id，不允许继续使用 `dsl_demo`

**通过标准**：每个单图文件打开后，diagrams.net 底部页签显示语义图名，而不是默认的 `Page-1` / `第 1 页`。

---

## C7.6 — 图例语义歧义检查

适用于同时存在泳道/分层背景和节点颜色图例的图。

必检项：

- 连线图例和节点颜色图例是否分组显示
- 分组标题是否明确，例如 `连线含义`、`节点颜色`
- 节点颜色图例是否使用小型圆角节点缩略框，而不是普通色块
- 泳道背景是否足够浅，不能比节点色更抢眼
- 如果泳道已有标题说明责任主体，不再额外写 `泳道底色 = ...` 这类说明文字

**通过标准**：用户能一眼看出颜色图例解释的是“节点类型”，而不是泳道/大容器背景。

---

## C8 — 连线入口点检测（防止悬浮未连接）

验证方法：每条边的最后方式点必须在目标节点的包围盒内。

```python
import re

def check_entry_points(xml_text):
    """检查所有带方式点的边，最后方式点是否落在目标框内"""
    # 提取 vertex 坐标
    vc = {}
    for m in re.finditer(r'<mxCell[^>]*id="(\w+)"[^>]*vertex="1"[^>]*>.*?<mxGeometry\s+[^>]*x="([\d.]+)"\s+y="([\d.]+)"\s+width="([\d.]+)"\s+height="([\d.]+)"', xml_text, re.DOTALL):
        vc[m.group(1)] = tuple(float(g) for g in m.groups()[1:])

    bad = 0
    for m in re.finditer(r'<mxCell[^>]*id="(\w+)"[^>]*edge="1"[^>]*source="(\w+)"[^>]*target="(\w+)"[^>]*>(.*?)</mxCell>', xml_text, re.DOTALL):
        eid, src, tgt, inner = m.group(1), m.group(2), m.group(3), m.group(4)
        tgt_box = vc.get(tgt)
        wps = [(float(x),float(y)) for x,y in re.findall(r'<mxPoint\s+x="([\d.]+)"\s+y="([\d.]+)"', inner)]
        if not wps or not tgt_box:
            continue
        lx, ly = wps[-1]
        tx, ty, tw, th = tgt_box
        inside = (tx <= lx <= tx + tw) and (ty <= ly <= ty + th)
        if not inside:
            print(f"❌ {eid}({src}→{tgt}): 入口({lx:.0f},{ly:.0f}) 不在目标框[{tx:.0f},{tx+tw:.0f}]×[{ty:.0f},{ty+th:.0f}]内")
            bad += 1

    if bad == 0:
        print("✅ 所有边入口在目标框内")
    return bad
```

**通过标准**：所有带方式点的边，最后方式点都落在目标节点的 (x, y, w, h) 范围内。不通过 → 调整最后方式点的坐标使其进入目标框。

---

## C9 — 线重叠检测（防止多线共路径）

验证方法：检查所有方式点是否被多条边共享，超过 1 条即视为重叠。

```python
from collections import Counter

def check_line_overlap(xml_text):
    """检测是否有不同边共享同一个方式点"""
    wps_counter = Counter()
    edge_wps = {}  # eid -> [(x,y), ...]

    for m in re.finditer(r'<mxCell[^>]*id="(\w+)"[^>]*edge="1"(.*?)>(.*?)</mxCell>', xml_text, re.DOTALL):
        eid = m.group(1)
        inner = m.group(3)
        wps = [(int(float(x)), int(float(y))) for x,y in re.findall(r'<mxPoint\s+x="([\d.]+)"\s+y="([\d.]+)"', inner)]
        if wps:
            edge_wps[eid] = wps
            for wp in wps:
                wps_counter[wp] += 1

    found = False
    for pt, cnt in wps_counter.most_common():
        if cnt > 1:
            shared_by = [eid for eid, wps in edge_wps.items() if pt in wps]
            print(f"⚠️  点({pt[0]},{pt[1]}) 被 {cnt} 条边共享: {shared_by}")
            found = True

    if not found:
        print("✅ 无线重叠")
    return found
```

**通过标准**：没有方式点被 2 条以上的边共享。如果出现共享：
- 若共享边的源节点都相同或目的节点都相同 → 这是总线模式，可以接受
- 若共享边来自不同源、去往不同目标 → 路径规划错误，需重新路由

---

## 验收总表

```
C1 间距公式:   □ 通过  □ 不通过
C2 图标去重:   □ 通过  □ 不通过
C3 标签存在:   □ 通过  □ 不通过
C4 包围盒:     □ 通过  □ 不通过
C5 XML/emoji:  □ 通过  □ 不通过
C6 线型一致:   □ 通过  □ 不通过
C7 图层顺序:   □ 通过  □ 不通过
C8 入口点:     □ 通过  □ 不通过
C9 线重叠:     □ 通过  □ 不通过
```

**全部通过 → 可以交付。**
**任意不通过 → 修复后重检。**
