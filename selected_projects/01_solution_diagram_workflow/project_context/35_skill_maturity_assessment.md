# Human-Factors Diagram Renderer — Skill 成熟度评估与优化路线报告

> 说明：本文件是阶段性成熟度评估，保留了当时对父项目结构的判断。若文中出现已被收缩移出的目录，请将其视为历史结构说明，而不是当前副本必须保留的内容。

> 用途：本文件面向后续继续开发此 Skill 的 AI Agent（无论 Claude Code / Codex / 其他）。
> 读完本文件后，Agent 应能明确当前 Skill 的阶段、缺口、优先修复顺序与可独立推进的决策边界。
> 
> 最后更新：2026-06-22

---

## 一、一句话定位

**Human-Factors Diagram Renderer** 不是 draw.io 的通用封装，而是一个**将"画架构图"这个 AI 做不好的事拆成两层**的工程路线：

```
AI 层（决策）：输出受控 JSON DSL → 脚本层（确定性渲染）：执行全部布局/样式/路由/验收 → 吐出 .drawio
```

本 Skill 是这个工程路线的代码封装。

---

## 二、项目历史决定的能力边界

本项目经历了**三条工具路线（Route A/B/C）的全量探索**，26+ 个已知错误模式（E1-E42 详见 `../project_context/05_error_index.md`），最终在 2026-06-20 确定了当前架构。这些历史教训决定了 Skill 的**隐性约束**：

| 历史教训 | 对 Skill 的约束 |
|---------|----------------|
| Route A（draw.io）手动加过多约束压制了自动能力 → 最终改为"受控 DSL + 脚本渲染" | JSON DSL 禁止写 draw.io style/坐标/图标/waypoint |
| Route B（飞书 whiteboard CLI）接口可调用≠方法已掌握 | 当前 renderer 不支持随意新增 diagram_type，必须先进 schema/spec/测试 |
| Route C（Visio Web）根本性阻断：Web UI 工具不可被 AI 编程操控 | 本 Skill 只输出 .drawio，不承诺 PNG/PDF 自动化导出 |
| chart1 验证 5 轮仍出出口方向错误、线重叠 | AI 不写坐标和方式点——renderer 负责全部几何计算 |
| E32：SVG base64 通过 shape=image 全部不渲染 | 图标使用 HTML `<img>` 标签嵌入，shape=image 已被禁用 |
| E39/E41：图层顺序和 XML 实体编码反复出错 | renderer 使用 xml.etree.ElementTree 生成 XML，避免字符串拼接 |

---

## 三、当前 Skill 结构总览

```
human-factors-diagram-renderer/
├── SKILL.md                              ← 技能定义（被 Claude Code / Codex 调用时加载）
├── agents/openai.yaml                    ← Codex 集成配置（5 行骨架）
│
├── scripts/                              ← 执行层（342 行 Python）
│   ├── render_diagram.py                 ← 主入口：JSON → draw.io
│   ├── validate_examples.py              ← 集成测试：渲染所有内置样例
│   ├── export_drawio_desktop.py          ← 官方 draw.io Desktop 导出适配器
│   ├── log_issue.py                      ← 视觉问题记录工具
│   └── diagram_renderer/                 ← 核心渲染器包（11 模块，≈ 1950 行）
│       ├── cli.py                        │ CLI 路由
│       ├── drawio_xml.py                 │ 核心数据结构 + XML 生成 + 端口计算
│       ├── styles.py                     │ 颜色/字体/形状/连线语义映射（210 行）
│       ├── spacing.py                    │ 减法间距公式（51 行）
│       ├── icons.py                      │ SVG 图标数据 URI 生成（228 行）
│       ├── schema.py                     │ JSON Schema 加载
│       ├── validators.py                 │ C0-C9 自动验收门禁（470 行）
│       └── layouts/
│           ├── layered_architecture.py   │ 分层架构布局引擎（✅ 可用，230 行）
│           └── flowchart_decision_tree.py│ 判断树布局引擎（✅ 可用，570 行）
│
├── references/                           ← 参考层（7 文件，≈ 1800 行）
│   ├── project_overview.md               ← -> ⚠️ 引用路径碎片化（见下文 §4.1）
│   ├── workflow.md                       ← 六步绘制流程 + 各步自检
│   ├── style_rules.md                    ← 颜色/间距/连线语义速查
│   ├── validation.md                     ← C1-C9 验收标准与 Python 代码
│   ├── pitfalls.md                       ← 已知失败模式（13 条）
│   ├── diagram_dsl_v0_1_spec.md          ← JSON DSL 设计边界
│   ├── diagram_dsl_v0_1_schema.json      ← JSON Schema 白名单
│   └── ai_to_dsl_prompt_v0_1.md          ← AI 生成 DSL 的提示模板
│
├── assets/examples/                      ← 验收样例（4 组）
│   ├── json/                             ← 输入 JSON DSL
│   └── drawio/                           ← 输出 .drawio 对比标尺
│
└── logs/                                 ← 问题记录
    └── screenshots/                      ← 截图存放
```

---

## 四、成熟度评估

### 4.1 已实现且稳定的部分（可以直接信赖）

| 维度 | 状态 | 说明 |
|------|:----:|------|
| `layered_architecture` 布局引擎 | ✅ 可用 | 含标题/画布/层背景/节点/分组/标签/图例/边缘端口分配 |
| `flowchart_decision_tree` 布局引擎 | ✅ 可用 | 含行布局/菱形节点/条件节点/结果节点/fan-out |
| DSL 约束层（schema + spec + prompt） | ✅ 完整 | 白名单、禁止项、字段边界 |
| C1-C9 验收门禁 | ✅ 完整 | 间距公式/图标去重/标签存在/包围盒/XML 合法性/emoji 零用/线型一致/图层顺序/入口点/线重叠 |
| 端到端回归 | ✅ 可用 | `validate_examples.py` 4 个案例全部通过 |
| 自定义 SVG 图标系统 | ✅ 可用 | 228 行 icons.py，含 SVG → data URI + 去重/相似度检测 |
| 间距减法公式 | ✅ 经过 8 轮正交实验验证 | `references/style_rules.md` §间距公式 |

### 4.2 标题写着"支持"但实际不完全的部分（⚠️ 伪支持标记）

| 声明 | 实际状态 | 风险 |
|------|---------|------|
| `rag_sequence_flow` | `cli.py` 中走 `flowchart_decision_tree` 布局 fallback，没有独立泳道/分栏布局引擎 | 用户选了会得到一个"能跑但布局不对"的结果 |
| `stage_gated_swimlane` | SKILL.md Workflow §Current Diagram Types 列出但无法选择——schema 中 enum 未包含，cli.py 无路由 | 选了直接报错 |
| `export_drawio_desktop.py` | 代码存在，但要求本机安装 draw.io Desktop | 本机没装，用户用了会静默返回 exit code 2，不可用 |

**Agent 行为建议**：在 SKILL.md 和 CLI `--help` 中明确标注 diagram_type 状态（✅ 可用 / 🔶 partial / ❌ planned）。

### 4.3 路径碎片化——`references/project_overview.md` 引用了父项目路径

这是**当前最隐蔽的坑**。`project_overview.md` 中多处引用：

```
guides/                        ← 实际在 ../project_context 同级（不在 skill 内）
specs/                         ← 同上
templates/ai_to_dsl_prompt_*   ← 同上（虽然 skill 里也有一份拷贝）
experiments/chart01_*.json     ← 同上
outputs/drawio/samples/        ← 同上
outputs/drawio/baseline/       ← 同上
assets/mermaid-references/     ← 同上
assets/style-guides/           ← 同上
```

这些路径在项目工作区（`solution-diagram-workflow-mvp/`）中是有效的，但在 Skill 自己内部（被某个 AI Agent 单独拉到 `.codex/skills/` 或 `~/.claude/skills/` 后）全部断链。

**修复方案**（选一种）：
- **方案 A（推荐）**：将本 Skill 的 `references/` 设计为**自包含**，把真正需要的上下文引用全部拷贝到 `references/` 内，删除 `project_overview.md` 中指向父项目的链接。
- **方案 B**：在 `project_overview.md` 开头加红字说明："以下路径在 skill 独立部署时不可用，仅供项目开发环境下阅读"。

---

## 五、10 个缺口及修复优先级

| # | 缺口 | 优先级 | 影响 | 修复工作量 |
|:--:|------|:------:|------|:---------:|
| ① | **无 README.md** | 🔴 高 | 外部用户（GitHub 拉到本地的人）不知道这 project 是干啥的，不知道怎么装、怎么跑、有哪些能力 | 30 分钟 |
| ② | **无 install.sh** | 🔴 高 | 无法一键部署到 `~/.claude/skills/` 或 `.codex/skills/`；用户必须手动复制文件 | 20 分钟 |
| ③ | **无版本/阶段声明** | 🟡 中 | 新 Session 的 Agent 把 Demo 当完整产品用，踩了 `rag_sequence_flow` 伪支持的坑才意识到 | 15 分钟（文件头加一行） |
| ④ | **路径碎片化（§4.3）** | 🟡 中 | 按 `project_overview.md` 的流程走到 Step 1 就迷路了 | 45 分钟（整理+拷贝） |
| ⑤ | **diagram_type 真实状态未标注** | 🟡 中 | Agent 选了 `rag_sequence_flow` → 走错了布局引擎 → 用户看到不对的图 → 信誉损失 | 10 分钟（改 enum + 注释） |
| ⑥ | **"两层路线"哲学未显性化** | 🟢 低 | Agent 不理解这个 skill 和通用 drawio-skill 的核心区别，容易用错模式（比如直接写 draw.io XML） | 10 分钟（改 SKILL.md 头部） |
| ⑦ | **C0 验证器存在但 SKILL.md 未提** | 🟢 低 | 验证链条不完整——Agent 只跑了 C1-C9 但跳过了 DSL schema 校验 | 5 分钟（加一行到 Acceptance Standard） |
| ⑧ | **无环境依赖声明** | 🟢 低 | `export_drawio_desktop.py` 需要 draw.io Desktop 但不提示；`validate_examples.py` 对外部依赖不声明（E42 经验） | 10 分钟 |
| ⑨ | **`agents/openai.yaml` 过薄** | 🟢 低 | Codex 用户用它时得不到足够的行为约束，Agent 容易溢出"输出 draw.io XML"这条红线 | 15 分钟 |
| ⑩ | **已知失败模式入口缺失** | 🟢 低 | `references/pitfalls.md` 存在但 SKILL.md 没有索引入口，新 Agent 不知道要先读它 | 5 分钟（加一句链接） |

---

## 六、Agent 可自主推进的优化路径

以下按编号给出具体操作路径。Agent 可根据当前会话的预算和时间约束选择相应路径执行。

### 路径 1：外部开发者体验（优先级最高，约 1.5 小时）

完整修复后，用户可从 GitHub clone → `bash install.sh` → 直接跑。

```
TODO:
[ ] 创建 README.md
    - 一句话定位 + 项目背景（300 字以内概述 Route A/B/C 结论和"两层路线"哲学）
    - 5 秒上手：clone + install.sh + 跑一个 example
    - 能力矩阵表（支持的 diagram_type + 状态）
    - 文件结构速览 + 各目录用途
    - 已知限制（无 diagram Desktop 时 PNG/PDF 不可用）
    - 与通用 drawio-skill 的关系

[ ] 创建 install.sh
    - ~/.claude/skills/human-factors-diagram-renderer/ 完整部署
    - `.codex/skills/` 兼容路径（可选）

[ ] CLI --help 补充
    - 输出中标注各 diagram_type 状态（available / partial / planned）
    - 环境依赖提示（draw.io Desktop 可选）
```

### 路径 2：Skill 定义强化（约 1 小时）

让 SKILL.md 的调用方（Claude Code / Codex 的 AI Agent）在第一次使用时就能准确判断可用能力。

```
TODO:
[ ] SKILL.md 头部补充"两层路线"哲学（四句话以内）
    - 核心区别：这个 skill 不是通用画图，而是"AI 输出 DSL → 渲染器出图"
    - AI 禁止直接输出 draw.io XML / style / 坐标 / 图标 base64

[ ] SKILL.md Current Diagram Types 表格增加"真实状态"列
    - layared_architecture → ✅ 可用
    - flowchart_decision_tree → ✅ 可用
    - rag_sequence_flow → 🔶 partial（共享 flowchart 布局引擎，无独立泳道）
    - stage_gated_swimlane → ❌ planned（schema 未包含、cli.py 无路由）

[ ] SKILL.md Acceptance Standard 增加 C0 步骤
    - "运行 renderer 前先确认 DSL 通过 schema 验证"
    - 引用 scripts/diagram_renderer/schema.py

[ ] SKILL.md 增加"环境依赖"章节
    - Python 3.8+（标准库）
    - 可选：draw.io Desktop（仅 PNG/PDF 导出用）
    - YAML 依赖（仅 quick_validate，非核心渲染所需）

[ ] 更新 agents/openai.yaml
    - 增加 behavior 约束段落（禁止输出 draw.io XML / style / 坐标）
    - 增加输出格式约束（只输出 JSON DSL，不写 Markdown 解释）
```

### 路径 3：引用路径修复（约 45 分钟）

```
TODO:
[ ] 选择方案（自包含 vs 标记父项目引用）
    - 推荐方案 A：将 references/ 设计为自包含

[ ] 若选 A：
    - 将 `project_overview.md` 中所有 `guides/`/`specs/`/等父项目路径
      替换为 skill 内的对应文件引用
    - 删除或重定向所有无法自包含的链接（如 mermaid-references/）

[ ] 若选 B：
    - 在 `project_overview.md` 文件头加红字警告
    - 列出所有断裂路径和它们的真实位置
```

### 路径 4：diagram_type 真实化（约 30 分钟）

```
TODO:
[ ] 评估要不要把 rag_sequence_flow 做成独立布局引擎
    - 判断标准：新 SQL / RAG / 数据流的图数量是否值得独立编码
    - 如果值得：参考 chart04 的 JSON 样例，新增 layouts/rag_sequence_flow.py
    - 如果不值得：从 schema enum 和 SKILL.md 移除，标记为 planned

[ ] stage_gated_swimlane：3 选 1
    (a) 删掉 SKILL.md 中的声明
    (b) 补 schema enum + cli.py 路由 → 复用 flowchart 布局
    (c) 标记为 planned 不动代码
```

### 路径 5：已知失败模式前置化（约 15 分钟）

```
TODO:
[ ] SKILL.md 中 Workflow Step 0 增加"先读 pitfalls.md"的步骤
[ ] 确保 references/pitfalls.md 的第一条是"可复用入口索引"
    - 不要只列坑，要告诉 Agent"动手前先确认自己有没有陷入以下模式"
```

---

## 七、不可自主决策的边界

以下事项涉及架构方向或功能承诺，Agent 不应自主决定，必须留待铭哥确认：

| 事项 | 为什么不可自主决策 |
|------|-------------------|
| 新增 diagram_type（如独立的 `rag_sequence_flow` 布局引擎） | 牵涉 schema/验收套件/四图回归/文档更新，且父项目路线图有"Layer 1 验证通过才进 Layer 2"的守则 |
| 是否放弃对 PNG/PDF 导出的支持承诺 | 涉及 Skill 定位——是"只出 draw.io"还是"可交付完整资产" |
| 是否将 Skill 部署到 `~/.claude/skills/` 全局 | 需要铭哥确认是否接受全局 skill 注册（影响命名空间和自动触发） |
| 删除 vs 保留 `project_overview.md` 的碎片链接 | 涉及项目文档风格偏好 |
| 是否投入开发独立的泳道/分栏布局 | 需要从铭哥确认业务价值——目前 4 张验证图里需要泳道的场景是否足够 |

---

## 八、快速检查清单

**每次优化完成后执行：**

```bash
# 1. 回归测试
python3 human-factors-diagram-renderer/scripts/validate_examples.py

# 2. 快速渲染检查
python3 human-factors-diagram-renderer/scripts/render_diagram.py \
  --input human-factors-diagram-renderer/assets/examples/json/chart01_layered_architecture_r01.json \
  --output /tmp/test_chart01.drawio

# 3. 检查标记
diff <(grep "diagram_type" human-factors-diagram-renderer/references/diagram_dsl_v0_1_schema.json) \
     <(echo "    \"rag_sequence_flow\" # 🔶 partial — 共享 flowchart 布局引擎")
# 如果还写了不带标记的 enum，说明 schema 未更新

# 4. 确认 SKILL.md 头部包含"两层路线"说明
head -30 human-factors-diagram-renderer/SKILL.md | grep -q "JSON DSL.*renderer" \
  || echo "⚠️ 缺少两层路线哲学说明"
```

---

## 九、参考源索引

| 参考源 | 路径 | 内容 |
|--------|------|------|
| MVP 目标与三层路线图 | `project_context/01_mvp_goal.md` | Layer 1→2→3 演进策略 |
| 关键架构决策（06-20 转折） | `project_context/00_Key_Decisions.md` | 2026-06-20 条目（双层分离） |
| 完整错误索引 E1-E42 | `project_context/05_error_index.md` | Route A/B/C 全部踩坑记录 |
| 4 张验证图定义 | `project_context/30_chart_definitions.md` | chart1~4 的 Mermaid 蓝图 |
| DRAWIO 风格参考 | `references/style_rules.md` | 颜色字典 / 间距公式 / 连线语义 |
| 验收 C1-C9 完整规范 | `references/validation.md` | 每项的 Python 验证代码 |
| 已知失败模式 13 条 | `references/pitfalls.md` | 症状+根因+正确做法 |
| DSL 白名单 | `references/diagram_dsl_v0_1_spec.md` | AI 允许/禁止输出的字段 |
| AI 生成 DSL 的 Prompt | `references/ai_to_dsl_prompt_v0_1.md` | 强制 JSON 输出 + 字段白名单 |
