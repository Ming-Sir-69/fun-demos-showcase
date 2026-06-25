# 01 — 绘制流程

> 从蓝图到可交付 draw.io 文件的六步流程。
> 每步包含：做什么 → 参考文件 → 输出 → 自检。

---

## 概览

```
Step -1: 已知失败模式预读
Step 0: 生成 / 校验 JSON DSL
Step 1: 确认蓝图结构
Step 2: 布局与坐标
Step 3: 生成 XML
Step 4: 嵌入图标
Step 5: 自检验收
```

---

## Step -1 — 已知失败模式预读

**做什么**：新图型、布局调整、连线调整、导出异常、视觉验收不通过时，先读 `references/pitfalls.md`。

**目的**：避免重复踩已经记录过的坑，例如 JSON 写 draw.io style、边标签挂错层、非官方预览误判、图例贴近主图、容器越界、页签名丢失。

**输出**：确认这次问题是否已经有历史失败模式；如果有，按已有预防规则处理。

**自检**：
- [ ] 已确认问题不属于 `references/pitfalls.md` 中已有的失败模式，或已按对应规则处理。

---

## Step 0 — 生成 / 校验 JSON DSL

**做什么**：先把输入内容转成受控 JSON DSL，再交给 renderer。输入可以是 Mermaid、文字流程、业务说明或人工结构草稿。

**核心约束**：

- AI 不直接输出 draw.io XML
- AI 不输出 `mxCell`、`mxGeometry`、style 字符串、waypoint、base64 图标
- JSON 只描述业务结构和语义，表现层全部交给 renderer
- DSL 必须先通过 schema 和 renderer validators，之后才允许进入 XML 生成
- C0 使用 `scripts/validate_dsl.py --input <json>`；`scripts/render_diagram.py` 也会在渲染前自动执行 C0

**参考文件**：

| 文件 | 用途 |
|------|------|
| `references/diagram_dsl_v0_1_spec.md` | DSL 设计边界 |
| `references/diagram_dsl_v0_1_schema.json` | 顶层字段、枚举和值域白名单 |
| `references/ai_to_dsl_prompt_v0_1.md` | AI 生成 DSL 的提示模板 |
| `scripts/validate_dsl.py` | C0 schema 验证入口 |
| `scripts/render_diagram.py` | 当前稳定渲染入口 |
| `scripts/diagram_renderer/` | 当前可执行 renderer package |

**图型规则**：

- `layered_architecture`：允许 `layers`、`groups`、`labels`、`legend`
- `flowchart_decision_tree`：使用 `rows`、`nodes`、`edges`
- 判断树中的条件 A/B/C/D 不使用 draw.io 原生 edge label，而转成显式 `flow_condition` 节点

**输出**：一份可校验的 JSON DSL 文件。

**自检**：

- [ ] JSON 顶层字段只来自 DSL 白名单
- [ ] `diagram_type` 与当前图型一致
- [ ] 所有 edge 的 `source/target` 都能在 nodes 中找到
- [ ] 判断树条件已落成显式节点，而不是边上的文本

---

## Step 1 — 确认蓝图结构

**做什么**：读取蓝图文件，了解目标图的层级结构、节点类型、连线语义。

**参考文件**：

| 文件 | 用途 |
|------|------|
| `assets/examples/json/` | 已验收 JSON DSL 样例 |
| `assets/examples/drawio/` | 已验收 draw.io 输出样例 |
| `references/ai_to_dsl_prompt_v0_1.md` | Mermaid / 文字流程转 DSL 的提示模板 |

**输出**：确认以下信息清单：
- 共有几层？从顶到底的顺序是什么？
- 每层有哪些节点？节点名称、颜色含义？
- 节点之间的连线语义（实线=数据流，虚线=协同流，点线=沉淀流）？
- 特殊节点（人审门菱形、数据库存储）？
- 判断树场景下，每一行有哪些节点、哪些条件节点需要 fan-out？

**自检**：
- [ ] 蓝图结构确认后，写一段结构描述（例如："3层，第1层为编排层含主控Agent+任务拆解…"）并验证正确性
- [ ] 连线语义已分类：主数据流/协同流/沉淀流
- [ ] 若为判断树，条件节点已经和结果节点一一配对

---

## Step 2 — 布局与坐标计算

**做什么**：确定画布尺寸、每层位置、节点位置、间距。

**参考文件**：

| 文件 | 用途 |
|------|------|
| `02_风格参考.md` | 颜色 hex、间距公式、字体层级 |
| `03_避坑手册.md` | 已知失败模式（尤其是 N 计数法） |

### 步骤 2a — 计算层间距

适用减法公式（详见 `02_风格参考.md §间距公式`）：

```
G = 50 + N × 25 − (N − M) × 12
```

其中：
- **N** = 穿过该间隙的**全部连线数**（不管有没有标签）
- **M** = 有标签的连线数

**务必注意：N 不等于 M！** 初次绘制时最容易踩的坑就是只看标签框数量、漏算裸线。

### 步骤 2b — 确定画布尺寸

- 默认 1600×900（16:9）
- 根据内容自然比例调整
- 层数多、间距大时增加 pageHeight
- 所有坐标从左上角 (0,0) 开始正向计算

### 步骤 2c — 计算节点坐标

- 节点之间水平间距：≥20px
- 节点到层边框内边距：≥12px
- 层背景到画布左右内边距：≥70px
- `flowchart_decision_tree` 的分支节点必须 fan-out，不把多个条件全部压到同一端口

### 步骤 2d — 计算 Rail 高度

Rail 的高度必须等于层背景的高度，底部对齐。不能短 1px 也不能短 10px。

示例：
```
bg_l3: y=96,  h=150  → 底部 246
rail_l3: y=96, h=150  → 底部 246  ✅ 对齐
```
而不是：
```
bg_l3: y=96,  h=150  → 底部 246
rail_l3: y=106, h=130  → 底部 236  ❌ 悬空 10px
```

**输出**：坐标清单，包含所有元素（背景/rail/节点/标签/图例）的 (x,y,w,h)。

**自检**：
- [ ] 每层间隙都用了减法公式验算
- [ ] 同层内节点间无重叠
- [ ] 相邻层间无布局重叠
- [ ] Rail 与层背景底部完全对齐
- [ ] 判断树的条件节点宽度紧凑，未错误占满整行

---

## Step 3 — 生成 XML

**做什么**：根据坐标清单和风格参考，生成完整的 draw.io XML。

**参考文件**：

| 文件 | 用途 |
|------|------|
| `02_风格参考.md` | 所有 style 参数（颜色/线型/圆角/字号） |
| `03_避坑手册.md` | 已知的 XML 生成坑（颜色误用、渲染顺序等） |

**补充要求**：

- 业务语义先映射到 `edge.type`
- `edge.type` 再映射到视觉家族 `visual_family`
- 判断树条件文字不落在 edge label 上，而是以 `flow_condition` 节点呈现
- 同图中同一 `visual_family` 的 style 必须完全一致

### draw.io XML 结构模板

```xml
<?xml version='1.0' encoding='utf-8'?>
<mxfile host="app.diagrams.net" modified="2026-06-20T00:00:00.000Z" version="24.7.17" type="device">
  <diagram id="chart1" name="图表名称">
    <mxGraphModel dx="1307" dy="762" grid="1" gridSize="10" guides="1"
                  pageWidth="1600" pageHeight="940" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- 画布背景 -->
        <mxCell id="bg" vertex="1" parent="1"
          style="rounded=0;whiteSpace=wrap;html=1;strokeColor=none;fillColor=#F8F6F0;">
          <mxGeometry width="1600" height="940" as="geometry" />
        </mxCell>
        <!-- 标题 -->
        <!-- 层背景 + rail -->
        <!-- 节点 -->
        <!-- 连线 + 标签 -->
        <!-- 图例 -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

### 节点 style 模板

```
# 编排层核心（深蓝底白字）
fillColor=#3F6EA8;strokeColor=#2E5585;fontColor=#FFFFFF;fontSize=12;rounded=1;arcSize=10;spacing=8

# 专家层节点（浅米色深色字）
fillColor=#F3E8D5;strokeColor=#D2C7B8;fontColor=#2C3E50;fontSize=12;rounded=1;arcSize=12;spacing=6

# 人审门（菱形，深红底白字）
shape=diamond;fillColor=#B25D5D;strokeColor=#8B3E3E;fontColor=#FFFFFF;fontSize=12;spacing=6

# 知识库节点（浅绿底深色字）
fillColor=#DDE9DB;strokeColor=#9DB88E;fontColor=#2C3E50;fontSize=12;rounded=1;arcSize=12;spacing=8

# 层背景（浅灰底）
fillColor=#F2F2F2;strokeColor=#D2C7B8;strokeWidth=1;rounded=1;arcSize=6

# 层 rail（左轨，中和灰底深色字）
fillColor=#D2C7B8;strokeColor=#D2C7B8;fontColor=#2C3E50;fontSize=14;rounded=1;arcSize=12

# 胶囊标签（白底灰边框）
fillColor=#FFFFFF;strokeColor=#DADDE0;fontColor=#2C3E50;fontSize=11;rounded=1;arcSize=50
```

### 连线 style 模板

| 语义 | style 参数 |
|------|-----------|
| 主数据/控制流 | `endArrow=block;endFill=1;strokeWidth=1.5;strokeColor=#3F4447;` |
| 协同/辩论流 | `dashed=1;dashPattern=8 6;endArrow=block;endFill=1;strokeWidth=1.5;strokeColor=#3F4447;` |
| 经验沉淀/审计流 | `dashed=1;dashPattern=2 2;endArrow=open;endFill=0;strokeWidth=1;strokeColor=#64748B;` |

### ⚠️ 关键：XML 声明顺序（决定箭头是否可见）

draw.io 渲染规则：**后声明的元素在上层**。

正确顺序：
```
1. 画布背景（bg）
2. 所有层背景（bg_l3, bg_l2, bg_l1）
3. 所有层轨（rail_l3, rail_l2, rail_l1）
4. 所有节点/卡片/标签/图例文字         ← vertex 元素
5. 所有边（edge=1 的 mxCell）           ← ✅ 所有边在最后，箭头不被遮挡
```

**箭头不见是最常见的图层问题**——如果边声明在其目标节点之前，节点的填充色会覆盖箭头。

自检：XML 中最后一个 `vertex="1"` 必须在第一个 `edge="1"` 之前。

---

### ⚠️ 关键：标签箭头规则

标签（胶囊型边注释、id 含 `label_`）是注释，不是流程目标节点。**入标签的边不能有箭头**。

```python
if "label_" in target_id:
    style += ";endArrow=none;endFill=0;"  # 入标签无箭头
else:
    style += ";endArrow=block;endFill=1;"  # 入节点有箭头
```

---

### ⚠️ 关键：出口方向选择（避免绕远路）

基于源和目标中心点的相对位置选择最优出口：

```python
dx = target_cx - source_cx
dy = target_cy - source_cy

if abs(dx) < 30 and dy > 0:        # 正下方
    exit_side = "下"; entry_side = "上"; bends = 0
elif abs(dx) < 30 and dy < 0:      # 正上方
    exit_side = "上"; entry_side = "下"; bends = 0
elif dx >= 0 and dy >= 0:           # 右下
    exit_side = "右"; entry_side = "上"; bends = 1
elif dx < 0 and dy >= 0:            # 左下
    exit_side = "左"; entry_side = "上"; bends = 1
elif dx >= 0 and dy < 0:            # 右上
    exit_side = "右"; entry_side = "下"; bends = 1
elif dx < 0 and dy < 0:             # 左上
    exit_side = "左"; entry_side = "下"; bends = 1
```

---

### ⚠️ 关键：总线检测（避免线重叠）

当多条路径在同一区域内共享方向时，合并为一条总线：

```python
# 如果多条边从同一 y 区域出发到同一 y 区域的多个目标
# 且源/目标的 x 范围在 200px 内 → 合并
if len(targets) >= 3 and all(top(src) < bottom(targets[0]) for t in targets):
    # 创建总线（垂直段，无箭头）
    bus_edge = create_bus(x=bus_x, y_start=label_bottom, y_end=target_area_top, arrow="none")
    # 从总线引出水平分支到各 target
    for t in targets:
        branch = edge(source=bus, target=t, ...)
```

---

**自检**：
- [ ] 所有节点 style 参数正确
- [ ] 连线语义与 style 对应正确
- [ ] 入标签的边无箭头（endArrow=none）
- [ ] 出口方向按相对位置选择，不走回头路
- [ ] 有 3+ 条并行线时已合并为总线
- [ ] 所有 value 中的 HTML 已做实体编码（`<`→`&lt;`，`>`→`&gt;`）
- [ ] 无 emoji 使用

---

## Step 4 — 嵌入图标

**做什么**：为节点添加 Feather Icons 风格的 SVG 线条图标。

**参考文件**：

| 文件 | 用途 |
|------|------|
| `assets/icons/` | SVG 源文件（21 个 Feather Icons） |
| `03_避坑手册.md §图标嵌入` | 已验证的嵌入方法 |

### 唯一可行的嵌入方式

```xml
&lt;img src=&quot;data:image/png;base64,iVBOR...&quot; width=&quot;22&quot; height=&quot;22&quot; style=&quot;vertical-align:middle;margin-right:6px;&quot;/&gt;
```

### 转换步骤

```bash
# 1. SVG → PNG（28×28px）
rsvg-convert -w 28 -h 28 input.svg -o output.png

# 2. PNG → base64
base64 -i output.png

# 3. 拼入 value 属性
value="&lt;img src=&quot;data:image/png;base64,<base64内容>&quot; width=&quot;22&quot; height=&quot;22&quot; style=&quot;vertical-align:middle;&quot;/&gt;&lt;br&gt;&lt;b&gt;标题&lt;/b&gt;"
```

### 图标颜色规则

- **浅色卡片**（#F3E8D5 / #D6E4F0 / #F8F6F0 等背景）：图标 stroke → `#1A1A1A`
- **深色卡片**（#3F6EA8 / #4B5259 等背景）：图标 stroke → `#FFFFFF`
- 每个节点的图标放在自己居中的一行，标题和描述在下方

### 图标去重检查

```
同一图标不应被不同职能的多个节点使用。
如果必须重复，使用前确认两个节点的职能是否相同。
```

**自检**：
- [ ] 所有节点均有图标
- [ ] 图标使用 HTML `<img>` 标签，非 `shape=image`
- [ ] 图标颜色与卡片文字颜色一致
- [ ] 无图标语义重复（不同职能节点用不同图标）
- [ ] 图标 base64 不为空，可渲染

---

## Step 5 — 自检验收

**做什么**：对生成的 draw.io 文件执行 C1-C6 全面自检。

**参考文件**：`04_自检验收.md`

**强制检查顺序**：

```
1. C1 — 间距公式验证：每层间隙的 G 值是否 ≥ 公式计算结果
2. C2 — 图标去重：不同职能节点是否用了不同图标
3. C3 — 标签存在性：所有预期标签是否有非空 value
4. C4 — 包围盒重叠：有无节点/标签/层之间重叠
5. C5 — XML 合法性 + emoji 零使用
6. C6 — 线型一致性：同语义连线是否全图一致
```

**任意一项不通过 → 修复 → 重新自检 → 全部通过后才算闭环**。

---

## 全流程速查清单

```
【Step 1 蓝图确认】
□ 读取 dqe-L6-human-factors.mmd
□ 确认层数、节点类型、连线语义
□ 输出结构描述文档

【Step 2 布局】
□ 公式计算每层间距
□ 确定画布尺寸
□ 计算所有节点坐标
□ Rail 与背景对齐

【Step 3 XML 生成】
□ 按模板生成完整 XML
□ 检查 style 参数与 02_风格参考.md 一致
□ 跨层边声明顺序正确
□ HTML 实体编码

【Step 4 图标嵌入】
□ 21 个图标源文件在 assets/icons/
□ SVG → PNG → base64 嵌入
□ 图标颜色按卡片类型区分

【Step 5 自检验收】
□ C1-C6 逐项通过
□ 不通过则修复→重检→闭环
```
