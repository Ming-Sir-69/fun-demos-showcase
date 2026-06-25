# JSON DSL v0.1 — Controlled Diagram Spec

> 目标：让 AI 只输出稳定、受控、可校验的图表语义 JSON；Python renderer 负责布局、样式、端口、连线、图标、draw.io XML 与自检。

## 1. 设计边界

### AI 可以输出
- 图表标题与副标题
- 图表类型 `diagram_type`
- 层、分组、节点、标签、连线、图例
- 判断树 / 阶段流程的节点行 `rows`、阅读方向与受控间距 `layout`
- 节点语义类型 `node.type`
- 连线业务语义 `edge.type`
- 图标语义 `icon`
- 少量受控布局提示 `layout_hint`

### AI 禁止输出
- draw.io XML、`mxCell`、`mxGeometry`
- 原生 draw.io style 字符串
- `fillColor`、`strokeColor`、`fontSize`、`arcSize`
- 普通节点的绝对坐标 `x/y/w/h`
- 连线 waypoint、入口点、出口点
- base64 图标
- Mermaid 原生语法作为最终输入

例外：`labels` 中的补充说明标签 v0.1 暂时允许 `x/y/w/h`，因为当前 renderer 中它们属于“连线注释胶囊”，不是主体节点。后续可升级为自动定位。

## 2. 顶层结构

```json
{
  "diagram_type": "layered_architecture",
  "title": "8D Flow 多智能体质量协同系统架构图",
  "page_name": "8D Flow 多智能体质量协同系统架构图",
  "subtitle": "Multi-Agent Quality Collaboration System",
  "style_profile": "enterprise_consulting_v10",
  "canvas": {"width": 1600, "height": 989},
  "layers": [],
  "labels": [],
  "edges": [],
  "legend": []
}
```

## 3. diagram_type

v0.1 当前稳定支持：

| 值 | 说明 | 当前状态 |
|---|---|---|
| `layered_architecture` | 分层企业架构图，例如 V10 | 已支持 |
| `flowchart_decision_tree` | 判断树 / 多条件分支流程图 | 已支持 |
| `decision_tree` | `flowchart_decision_tree` 的兼容别名 | 已支持 |
| `rag_sequence_flow` | RAG / 数据流 / 请求响应类分栏流程 | 已支持 |

当前 renderer 的主能力是 `layered_architecture`、`flowchart_decision_tree` 和 `rag_sequence_flow`。新增类型必须先进入 renderer、schema、测试和验收文档，不能只在 JSON 里临时发明。

## 3.1 page_name

`page_name` 是 diagrams.net / draw.io 工作簿里的页面页签名，不是画布标题。

规则：

- 推荐使用独立图名，例如 `8D Flow 多智能体质量协同系统架构图`。
- 不要为了排序给页签增加 `Chart 01` 这类前缀；排序由文件名或外部文件管理完成。
- `title` 继续用于画布内的大标题。
- `page_name` 用于 draw.io XML 的 `<diagram name="...">`。
- 如果不写 `page_name`，renderer 会退回使用 `title`。
- renderer 会根据 `page_name` 生成稳定唯一的页面 id，避免多个图插入同一个工作簿时都叫 `dsl_demo`。

示例：

```json
{
  "diagram_type": "rag_sequence_flow",
  "title": "隔离式知识检索 RAG 数据流",
  "page_name": "隔离式知识检索 RAG 数据流",
  "subtitle": "Role / Product / Human-Reviewed Filtered Retrieval Flow"
}
```

## 4. style_profile

v0.1 支持：

| 值 | 说明 |
|---|---|
| `enterprise_consulting_v10` | 暖白背景、低饱和、圆角卡片、左侧 rail、正交连线、底部图例 |

AI 不应该发明新的 profile。新增 profile 需要 renderer 先注册。

## 5. layers

### 5.1 普通层

```json
{
  "id": "role",
  "index": 1,
  "title": "岗位层",
  "height": 135,
  "gap_after": 30,
  "nodes": []
}
```

字段说明：

| 字段 | 必填 | 说明 |
|---|---:|---|
| `id` | 是 | 稳定业务 id，不使用中文，不使用空格 |
| `index` | 是 | 从上到下 1,2,3... |
| `title` | 是 | 左侧 rail 显示标题 |
| `height` | v0.1 是 | 当前仍由 fixture 指定；后续可自动计算 |
| `gap_after` | v0.1 是 | 当前仍由 fixture 指定；后续接入间距公式自动计算 |
| `nodes` | 条件 | 简单横向层使用 |
| `groups` | 条件 | 分组层使用 |

### 5.2 分组层

```json
{
  "id": "business",
  "index": 3,
  "title": "业务系统层",
  "height": 230,
  "gap_after": 50,
  "groups": []
}
```

## 6. groups

```json
{
  "id": "existing_systems",
  "type": "system_group",
  "title": "现有系统与客户端",
  "nodes": []
}
```

| 字段 | 必填 | 说明 |
|---|---:|---|
| `id` | 是 | 稳定业务 id |
| `type` | 是 | 分组类型，目前支持 `system_group`、`agent_infra_group` |
| `title` | 是 | 分组标题 |
| `nodes` | 是 | 分组内节点 |

## 7. nodes

### 7.1 普通节点

```json
{
  "id": "dqe",
  "type": "role",
  "title": "DQE",
  "subtitle": "质量主责",
  "icon": "target"
}
```

### 7.2 多行节点

```json
{
  "id": "main_agent",
  "type": "ai_core",
  "title": "主控 Agent",
  "lines": ["任务分解、辩论协调", "人机协同控制"],
  "icon": "brain"
}
```

### 7.3 node.type 白名单

| node.type | 用途 | 视觉映射 |
|---|---|---|
| `role` | 角色、岗位、入口 | 浅米色卡片 |
| `ai_core` | AI 协同核心模块 | 深蓝卡片 |
| `system` | 业务系统、客户端、接口系统 | 浅蓝卡片 |
| `knowledge` | 知识、审计、工作流、小型基建节点 | 浅绿卡片 |
| `knowledge_wide` | 宽版知识节点 | 浅绿宽卡片 |
| `platform` | 平台底座、治理、安全 | 深灰卡片 |
| `edge_label` | 胶囊型连线注释 | 白底胶囊 |
| `flow_start` | 判断树起点/异常触发 | 浅蓝起点卡片 |
| `flow_process` | 判断树过程/报告节点 | 浅蓝过程卡片 |
| `flow_decision` | 判断树核心判断节点 | 菱形判断节点 |
| `flow_condition` | 判断树显式条件节点 | 白底条件胶囊 |
| `flow_request` | 请求、查询、检索发起 | 浅蓝请求卡片 |
| `flow_filter` | 过滤器、权限、约束、审核状态 | 浅棕约束卡片 |
| `flow_data` | 知识返回、证据、历史经验 | 浅绿数据卡片 |
| `flow_result` | 判断树结果节点 | 浅绿结果卡片 |
| `flow_output` | 判断树最终输出节点 | 深灰输出卡片 |

AI 不允许发明新的 `node.type`。新增类型必须先注册到 renderer。

## 8. icon

### 8.1 规则

- 每个主体节点应该指定 `icon`。
- 图标 key 必须存在于 renderer 的本地图标注册表。
- 不同职能节点不能重复使用同一 icon。
- 图标相似度超过阈值时，validator 应提示疑似近似重复。

### 8.2 当前可用 icon key

```text
target, message, activity, truck, bar_chart, tool, package, check_circle,
brain, users, debate, dollar, smartphone, database_local, code, server,
layers, vector, search, book, filter, plug, key, shield,
alert, user, cpu, app, database, stack
```

## 8.3 判断树与阶段流程结构

`flowchart_decision_tree`、`rag_sequence_flow` 不使用 `layers`，而使用顶层 `nodes`、`rows`、`layout` 和 `edges`。

```json
{
  "diagram_type": "flowchart_decision_tree",
  "title": "多 Agent 复合根因判断树",
  "style_profile": "enterprise_consulting_v10",
  "canvas": {"width": 1600, "height": 980},
  "layout": {"mode": "row_grid", "row_gap": 54, "col_gap": 36},
  "nodes": [],
  "rows": [],
  "edges": []
}
```

`layout.mode` 当前支持：

| 值 | 用途 |
|---|---|
| `row_grid` | 默认行网格，适合判断树、短流程 |
| `decision_tree_bus` | 判断树分流/合流总线，适合 4 个以上条件分支 |
| `stage_gated_snake` | 阶段闸门 S 型流程，适合 8D、审批流、人工签字流 |
| `stage_gated_swimlane` | 阶段闸门泳道图，适合强调 AI 自动处理与人工审核边界 |
| `rag_sequence_flow` | RAG / 数据流 / 请求响应流程，适合角色隔离、过滤器、检索返回链路 |

`rows` 决定从上到下的逻辑行，每行只引用已声明的 `node.id`：

```json
{
  "node_ids": ["cA", "cB", "cC", "cD"],
  "gap": 28,
  "direction": "ltr"
}
```

`rows.direction` 当前支持：

| 值 | 用途 |
|---|---|
| `ltr` | 本行从左到右阅读 |
| `rtl` | 本行从右到左阅读，常用于 S 型折返 |

判断树条件、人工签字、入库、发布等关键状态必须用显式 `flow_condition` 节点表达，不要把它们只写成 edge label。renderer 会根据 `rows` 自动计算坐标，并对 `flow_decision` fan-out 做端口分离。

当 `layout.mode = decision_tree_bus` 时：

- 4 个及以上条件分支优先从判断节点引出一条主线，再用分流横线展开到条件节点。
- 条件行和结果行若是一一对应关系，应按列中心线对齐。
- 多个同类结果指向同一个输出节点时，优先先合流，再用一根主线进入输出节点。
- renderer 不补业务回流；回流必须在 Mermaid 或 JSON 中显式写出。

当 `layout.mode = stage_gated_swimlane` 时，节点可以增加 `lane` 字段：

| lane | 用途 |
|---|---|
| `stage` | 主流程阶段 / AI 自动处理 |
| `human` | 人工审核 / 签字 / 终审 |
| `status` | 签字通过、入库、发布等胶囊状态 |
| `knowledge` | 知识库、归档、沉淀结果 |

泳道图仍然不允许节点写坐标。AI 只表达节点属于哪个泳道，Python renderer 负责统一基线、列对齐和连线。

当 `layout.mode = rag_sequence_flow` 时，节点可以在 `layout_hint.participant` 中表达参与者列：

| participant | 用途 |
|---|---|
| `user` | 用户输入 / 输出 |
| `main` | 主控 Agent / 编排节点 |
| `pqe` | 岗位 Agent / 专家节点 |
| `db` | 向量库 / 过滤器 / 历史经验 |

RAG 数据流中的过滤器、审核状态、权限边界必须升级为真实节点，例如 `flow_condition`，不要只挂在线条标签上。
RAG 数据流中的过滤器、审核状态、权限边界优先使用 `flow_filter`，请求/检索发起优先使用 `flow_request`，知识返回/证据优先使用 `flow_data`。这些节点仍然只表达语义，不能写 draw.io 样式或坐标。

## 9. labels

用于放置补充说明类胶囊标签，例如边注释。

```json
{
  "id": "label_knowledge",
  "type": "edge_label",
  "title": "知识 / 编排 / 审计支撑",
  "visual_family": "dotted_knowledge",
  "x": 710,
  "y": 420,
  "w": 210,
  "h": 30,
  "compact": true,
  "max_w": 180
}
```

字段说明：

| 字段 | 必填 | 说明 |
|---|---:|---|
| `id` | 是 | 必须以 `label_` 开头 |
| `type` | 是 | 固定 `edge_label` |
| `title` | 是 | 标签文本 |
| `visual_family` | 是 | 标签所属视觉线型家族 |
| `x/y/w/h` | v0.1 是 | 临时允许，后续自动定位 |
| `compact` | 否 | 是否根据文本自动收窄 |
| `max_w` | 否 | 紧凑标签最大宽度 |

## 10. edges

### 10.1 基本结构

```json
{
  "source": "dqe",
  "target": "main_agent",
  "type": "control_flow"
}
```

### 10.2 edge.type 白名单

| edge.type | 业务语义 | visual_family | 箭头策略 |
|---|---|---|---|
| `control_flow` | 主数据 / 控制流 | `solid_main` | 正常实心箭头 |
| `system_interface` | 系统接口 / 业务系统关系 | `solid_main` | 正常或按规则无箭头 |
| `platform_support` | 到平台底座的支撑关系 | `solid_main` | 正常实心箭头 |
| `agent_flow` | Agent 协同 / 调度流 | `dashed_agent` | 正常实心箭头 |
| `knowledge_flow` | 知识 / 审计支撑流 | `dotted_knowledge` | 空心箭头 |
| `label_ingress_solid` | 进入普通/实线标签或条件节点 | `solid_main` | 无箭头 |
| `label_ingress_knowledge` | 进入知识类标签 | `dotted_knowledge` | 无箭头 |

关键规则：

- `target` 是 `label_` 时，入标签端默认不带箭头。
- `target` 是判断树 `flow_condition` 时，可使用 `label_ingress_solid` 表达无箭头条件入口。
- 标签入线与标签出线必须属于同一 `visual_family`。
- 到平台底座层的支撑关系默认使用 `platform_support`，不要混用点线。
- 同节点同边框不同 `visual_family` 必须端口分离。

## 11. legend

```json
{
  "edge_type": "control_flow",
  "label": "主要数据 / 控制流"
}
```

规则：

- `legend.edge_type` 必须存在于 `edge.type` 白名单。
- 每个图例项对应一个唯一 `visual_family`。
- 图例内容由 renderer 自动整体居中。

## 12. layout_hint

v0.1 暂时保留字段，但不强依赖。

允许：

```json
"layout_hint": {
  "row": 1,
  "priority": "left",
  "span": 2
}
```

禁止：

```json
"layout_hint": {
  "x": 123,
  "y": 456,
  "waypoints": [[1,2],[3,4]]
}
```

## 13. validator 必须检查

v0.1 至少包含：

| 检查 | 说明 |
|---|---|
| 节点类型白名单 | 未注册 `node.type` 必须 fail |
| 连线类型白名单 | 未注册 `edge.type` 必须 fail |
| 端点存在性 | edge source/target 必须已声明 |
| 禁止 style 泄漏 | JSON 中不得出现 draw.io style 字段 |
| 图标存在性 | icon key 必须在注册表中 |
| 图标重复 | 不同职能节点不得复用同一 icon |
| SVG 近似重复 | 超阈值提示疑似重复 |
| 标签入线一致 | 入标签线与出标签线视觉家族一致 |
| 平台支撑一致 | 到平台底座层的线型语义一致 |
| 图例视觉唯一 | 图例项不重复表达同一 visual_family |
| XML 合法 | draw.io XML 可解析 |
| 图层顺序 | edge 必须在 vertex 之后 |
| emoji 零使用 | value 中不使用 emoji |
| 端口分离 | 同节点同边框不同 visual_family 分端口 |
| 紧凑标签宽度 | 补充说明标签不过宽 |
| 图例居中 | 图例整体内容居中且保留呼吸感 |

## 14. 最小示例

```json
{
  "diagram_type": "layered_architecture",
  "title": "示例架构图",
  "subtitle": "Example Architecture Diagram",
  "style_profile": "enterprise_consulting_v10",
  "canvas": {"width": 1600, "height": 900},
  "layers": [
    {
      "id": "role",
      "index": 1,
      "title": "角色层",
      "height": 135,
      "gap_after": 30,
      "nodes": [
        {"id": "user", "type": "role", "title": "用户", "subtitle": "业务输入", "icon": "message"}
      ]
    },
    {
      "id": "ai",
      "index": 2,
      "title": "AI 层",
      "height": 120,
      "gap_after": 50,
      "nodes": [
        {"id": "agent", "type": "ai_core", "title": "主控 Agent", "lines": ["任务分解", "工具调用"], "icon": "brain"}
      ]
    }
  ],
  "labels": [],
  "edges": [
    {"source": "user", "target": "agent", "type": "control_flow"}
  ],
  "legend": [
    {"edge_type": "control_flow", "label": "主要数据 / 控制流"}
  ]
}
```
