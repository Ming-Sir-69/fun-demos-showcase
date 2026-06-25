# Demo Exit Criteria — POC Speed With NPI Discipline

本文件定义 `solution-diagram-workflow-mvp` 什么时候算 Demo 收口。

核心判断：当前阶段仍是 POC/MVP，不追求一次做成完整产品；但验收方式必须采用 NPI 思路，用明确门禁证明它可复用、可迁移、可继续迭代。

## 1. POC 目标

POC 证明“这条路能走”。

通过标准：

- JSON DSL 可以表达业务图结构。
- Python renderer 可以稳定输出 `.drawio`。
- 四张代表图可以回归生成。
- draw.io / diagrams.net 可以打开并人工验收。
- Skill 可以安装到全局并在其他会话触发。

当前状态：基本通过。

## 2. NPI 验收思想

NPI 关注“能不能真实导入使用”，不是只看实验成功。

套用到本项目，验收重点是：

- 输入是否受控。
- 生成是否稳定。
- 输出是否可编辑。
- 质量门禁是否明确。
- 失败是否可记录和反哺。
- 新场景是否能按规则扩展。

## 3. DFM 标准：可稳定制造

这里的“制造”指批量生成图。

通过标准：

- JSON 只写业务语义，不写坐标、style、`mxCell`、`mxGeometry`。
- C0 schema 验证在 renderer 前执行，坏输入不得进入 XML 生成。
- renderer 统一负责布局、颜色、线条、图标、页签、图例。
- 四个 bundled examples 可以一键回归。
- 生成结果不依赖手工拖线、手工调框、手工改 XML。
- 全局 Skill 路径下也能独立运行。

## 4. DFA 标准：可顺利组装

这里的“组装”指从用户输入到最终图的完整链路。

通过标准：

- Mermaid、文字流程、人工结构草稿可以被转成受控 JSON DSL。
- JSON DSL 能清楚表达节点、连线、语义类型、图类型和布局模式。
- renderer 能把 DSL 组装成 `.drawio`。
- 用户能在 diagrams.net/draw.io 中打开、编辑、保存。
- 用户反馈的问题可以记录到 `logs/`，包含文字和截图。
- 问题能反哺到 JSON、prompt、renderer、validators 或文档，而不是只修单张图。

## 5. Demo 收口门禁

Demo 只有同时通过这些门，才算阶段性关闭。

| Gate | 名称 | 通过标准 |
|------|------|----------|
| C0 | 输入门 | `scripts/validate_dsl.py --input <json>` 通过，且 render 前自动执行 C0 |
| C1 | 渲染门 | 四张已验收图全部能生成 `.drawio` |
| C2 | 质量门 | validators 全通过，包括端点、图标、style 泄漏、图层顺序、容器越界、图例间距、页签名 |
| C3 | 可迁移门 | 全局 Skill 路径下可独立跑通四图回归 |
| C4 | 文档门 | `SKILL.md`、`README.md`、`Index.md`、`references/` 能说明怎么用、边界是什么、禁止什么 |
| C5 | 问题闭环门 | `scripts/log_issue.py` 可记录问题，且文档说明应修哪一层 |
| C6 | 边界门 | 明确暂不做 Mermaid parser、大型布局依赖、官方 draw.io CLI 稳定化、无限扩展 diagram_type |

## 6. 当前不进入 Demo 收口的事项

这些事项重要，但不阻塞当前 Demo：

- Mermaid 自动 parser。
- 大型自动布局算法，例如 A*、Hanan Grid、libavoid。
- draw.io Desktop CLI 导出稳定化。
- 更多 diagram_type 的泛化设计。
- GUI 或 Web UI。
- 自动视觉截图验收。

## 7. 后续扩展规则

新增能力必须按这个顺序推进：

1. 先确认是内容问题、模板问题、布局问题、校验问题，还是新图族问题。
2. 如果现有 `diagram_type` + `layout.mode` 能表达，优先扩展 profile。
3. 如果不能表达，再新增 top-level `diagram_type`。
4. 新增 diagram family 必须同时补 schema、example、renderer、validators、docs、回归用例。
5. 没有验收门禁的能力不能标为 `✅ Available`。
