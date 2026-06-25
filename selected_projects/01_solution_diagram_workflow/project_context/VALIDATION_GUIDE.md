# VALIDATION_GUIDE

> 说明：本文档记录的是项目内验收方法。文中引用的部分源项目路径和历史输出目录，主要用于解释当时如何验收；当前对外副本请优先以 `human-factors-diagram-renderer/assets/examples/` 作为样例入口。

> 验收对象：b010 package 化 renderer 的 draw.io 生成结果  
> 项目路径：`/Users/eric-mingle-69/Documents/trae/item_fille/solution-diagram-workflow-mvp`
> 当前状态：chart01 / chart02 / chart03 已在 2026-06-21 11:09 完成人工视觉验收，通过。

## 0. 当前验收方向

chart04 暴露的问题不按“单张图修图”处理，而是按“通用规则缺口”处理。

本轮已完成第一轮通用规则修复：

- chart04 已使用独立 `rag_sequence_flow` 图类型。
- 请求、过滤器、知识返回已拆成 `flow_request`、`flow_filter`、`flow_data` 三类语义节点。
- RAG 跨参与者连线已改为优先左右端口，同参与者内部步骤仍上下连接。
- 四张图已重渲染，26 个自动测试通过。

本轮已完成第二轮视觉门禁修复：

- 图标已改为 SVG data URI，不再使用 22px 手工 PNG。
- chart04 节点已自动缩入泳道，横向至少保留 20px 安全边距。
- chart04 节点高度已按内容自动增加，过滤器等多行节点不应再文字超框。
- chart04 泳道标题已改为居中、加粗、15px。
- chart04 画布高度已按内容自动下延，底部输出节点不应再压出泳道。

下一轮验收目标：

- 验证通用视觉语义层是否成立。
- 验证模板路由器能不能把数据流 / RAG / sequence-like 场景和流程图、判断树区分开。
- 验证通用兜底模板在匹配不到专用模板时，是否仍然清楚、可读、不乱。
- 验证 drawio skill 只作为导出和生态适配能力，不反过来改变本项目的 JSON DSL-first 主路线。
- 每个单图 `.drawio` 文件现在都会写入 `pages=1` 和独立页签名。
- chart03 和 chart04 的泳道 / 大容器已经走同一套标题、宽度和边距规则。

## 1. 铭哥需要打开验收的文件

优先打开这四个文件：

| 图号 | draw.io 文件 | 你要看什么 |
|------|------|------|
| chart01 | `/Users/eric-mingle-69/Documents/trae/item_fille/solution-diagram-workflow-mvp/outputs/drawio/generated/chart01_layered_architecture_r01.drawio` | 分层架构图是否还像原来验收过的图；层、角色、AI、业务系统、平台、图例是否正常 |
| chart02 | `/Users/eric-mingle-69/Documents/trae/item_fille/solution-diagram-workflow-mvp/outputs/drawio/generated/chart02_decision_tree_r02.drawio` | 判断树是否清楚；Q1 是否先向下引出再用一根横线分流到条件 A-D；条件和结果是否按列对齐；R1-R3 是否先用一根横线合流再进 Final |
| chart03 | `/Users/eric-mingle-69/Documents/trae/item_fille/solution-diagram-workflow-mvp/outputs/drawio/generated/chart03_human_boundary_8d_flow_r01.drawio` | 图表 3：人机边界与 8D 阶段流转；重点看单图页签名、纵向泳道、泳道标题是否居中加粗醒目、各泳道宽度是否协调、D1-D8 主流程基线、人工审核列、状态胶囊列、底部图例 |
| chart04 | `/Users/eric-mingle-69/Documents/trae/item_fille/solution-diagram-workflow-mvp/outputs/drawio/generated/chart04_rag_sequence_flow_r01.drawio` | 图表 4：隔离式知识检索 RAG 数据流；重点看单图页签名、语义颜色、左右端口、过滤器真实节点、检索返回链路、泳道标题和边距是否与 chart03 规则一致 |

`outputs/drawio/generated/` 现在只保留当前版本图。`pre_refactor` 过程快照已经删除，避免验收时误打开旧图。

注意：本项目实际交付不使用多页工作簿。每张图都必须作为独立 `.drawio` 文件验收。

## 2. 对应输入 JSON

这些是 renderer 的输入，不是你主要验收对象；如果图不对，可以回头对照它们。

| 图号 | JSON 输入 |
|------|------|
| chart01 | `/Users/eric-mingle-69/Documents/trae/item_fille/solution-diagram-workflow-mvp/experiments/chart01_layered_architecture_r01.json` |
| chart02 | `/Users/eric-mingle-69/Documents/trae/item_fille/solution-diagram-workflow-mvp/experiments/chart02_decision_tree_r02.json` |
| chart03 | `/Users/eric-mingle-69/Documents/trae/item_fille/solution-diagram-workflow-mvp/experiments/chart03_human_boundary_8d_flow_r01.json` |
| chart04 | `/Users/eric-mingle-69/Documents/trae/item_fille/solution-diagram-workflow-mvp/experiments/chart04_rag_sequence_flow_r01.json` |

## 3. 当前真实流程

现在已经跑通的是：

```text
JSON DSL -> Python package renderer -> draw.io XML -> validators -> .drawio 文件
```

当前没有生成、也不纳入本轮验收的是：

```text
暂无。
```

图表 4 已单独进入 generated，用于验证 RAG / 数据流 / 请求响应类模板。

## 4. 你怎么验收

1. 用 draw.io / diagrams.net 打开 generated 文件。
2. 先看 chart01、chart02 是否保持原来验收过的视觉效果和结构。
3. 再看 chart03 的 8D 阶段流转和人机边界。
4. 反馈时不用看代码，只要按下面格式告诉我：

```text
chart01：通过 / 不通过，问题是……
chart02：通过 / 不通过，问题是……
chart03：通过 / 不通过，问题是……
chart04：通过 / 不通过，问题是……
```

## 5. 你重点挑这些问题

- 是否有线压住节点或文字。
- 是否有箭头方向看起来不对。
- 判断树的条件节点是否清楚。
- 图表 2 的 Q1 四分支是否使用分流横线，而不是从菱形硬挤四根线。
- 图表 2 的分流横线和合流横线是否像一根干净河流，不再出现局部变粗、线段错位。
- 图表 2 的条件 A-D 和结果 R1-R4 是否竖向对齐，避免小 Z 字折弯。
- 图表 2 的 R1/R2/R3 是否先合流，再用一根线进入 `写入 8D 结构化 JSON`。
- 图表 2 的 R4 是否保持为“触发 Agent 重新调研”，没有擅自补回流。
- 8D 阶段是否按 D1 到 D8 清楚纵向流转，不再是一条横向大长条。
- D1-D8 主流程节点是否形成同一条垂直基线。
- D4、D5、D7、人工终审是否形成右侧同一列人工关卡。
- “签字通过”和“入库”是否形成状态胶囊列。
- “人工签字通过”和“入库”是否是独立胶囊节点，而不是挂在线上的文字。
- 图例是否居中、是否还能读。
- 节点文字是否溢出。
- 整体是否还像“企业咨询报告风格”，不是普通流程图草稿。
- 图表 4 是否能从左到右看出用户、主控 Agent、PQE Agent、隔离向量库四个参与者。
- 图表 4 的过滤器是否是独立节点，不是线上的附着文字。
- 图表 4 的请求、检索、返回、综合输出是否能从上到下顺着读。
- 图表 4 的颜色是否能看出语义规律，而不是每个框随机一个颜色。
- 图表 4 的横向线是否优先从右边出、左边入，而不是从下边出、上边入。
- 图表 4 的过滤器 / 约束 / 权限 / 审核状态是否作为真实语义节点表达，而不是借用判断树条件节点。
- 图表 4 的请求节点是否像请求，过滤器节点是否像约束，知识返回节点是否像数据/证据。
- 图表 4 暴露的问题是否已经沉淀为通用规则，而不是只修这张图。
- 图表 4 的所有节点是否都在各自泳道内部，不贴边、不越界。
- 图表 4 的 `过滤器注入` 是否文字完整，不再压出框。
- 图表 3 和图表 4 的泳道标题是否都居中、加粗、明显像分区标题。
- 图表 3 和图表 4 的同组泳道宽度是否协调，不像临时拼出来的七巧板。
- 图表 3 和图表 4 的节点是否都留有容器安全边距，不贴边、不越界。
- 图表 1-4 的图标是否比上一版更清晰、更像统一 SVG 线条图标。
- 每个单图文件打开后，底部页签是否显示该图自己的独立图名，不带 `Chart 01` 这类排序前缀。

## 5.1 本轮自动门禁已经覆盖

这些问题不需要铭哥肉眼兜底，renderer 已经会自动拦截：

- draw.io 输出里出现 PNG 图标。
- 单图使用默认页名或固定 `dsl_demo` 页面 id。
- 单图缺少 `pages=1` 页数声明。
- RAG 节点超出泳道或贴边。
- RAG 节点高度小于估算文字高度。
- RAG 泳道标题不居中、不够醒目。
- chart03 这类阶段泳道图的节点超出泳道或贴边。
- chart03 这类阶段泳道图的标题不居中、不加粗、不醒目。
- chart03 和 chart04 这类泳道图宽度不协调。

铭哥本轮主要做“单图真实场景验收”：只打开四个独立 `.drawio` 文件，看页签、泳道、连线和整体阅读感，不需要看多页文件。

## 6. chart03 本轮重点验收动作

打开 chart03 后，建议铭哥直接做两个拖动验证：

1. 拖动 `签字通过` / `入库` 胶囊节点，看它是否作为独立框图存在。
2. 拖动 `强制人工签字` / `人工终审` 这些人工审核节点，看相关连线是否跟随节点移动。
3. 看四条泳道标题是否清楚：`8D 阶段 / AI 自动处理`、`人工审核 / 签字`、`状态`、`知识沉淀`。

如果它们只是线上的文字，说明模板规则失败；如果它们是可移动的小框，说明“标签节点化”规则已经生效。

## 7. chart04 图例与间距验收

本轮已将 chart04 图例 v2 接入 renderer 和自动门禁。

已固化规则：

- 保留框图语义颜色图例，用于解释同色框跨泳道的含义。
- 不为泳道背景展开完整色块图例，也不额外加说明文字；泳道标题已经承担说明作用。
- 连线图例和节点颜色图例必须分组显示，标题为 `连线含义`、`节点颜色`。
- 节点颜色图例必须使用“小型圆角节点缩略框”，不能退回普通色块。
- 泳道背景必须比节点色更浅，视觉上只做责任主体分区。
- 图例和主图主体之间必须留出呼吸感，当前自动门禁要求至少 44px。
- chart03 / chart04 的泳道底部会随图例预留区自动下延，不能再把节点压到泳道底部。

明早人工重点看：

- chart04 底部图例是否离主图有足够呼吸感。
- chart04 框图颜色图例是否能解释节点颜色语义，且不会被误认为泳道背景说明。
- chart04 是否只保留必要的框图颜色图例，没有多余泳道说明文字。
- chart03 是否没有因为统一间距规则而变得过空或压底。

## 8. 如果要验证 Mermaid 输入

如果要验证 Mermaid 输入层，优先使用 `project_context/30_chart_definitions.md` 中的图表 3。下一步会单独做：

```text
Mermaid 草图 -> 受控 JSON DSL -> package renderer -> draw.io
```

但这一步会作为输入转换层，不会让 JSON 直接带 draw.io style、坐标、mxCell 或 mxGeometry。
