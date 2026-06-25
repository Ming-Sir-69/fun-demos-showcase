# Solution Diagram Workflow Index

> 如果你是第一次阅读这个副本，请先看根目录 `README.md`。

这个索引只回答一件事：现在这个副本里，还保留了哪些真正值得看的东西。

## 项目定位

这个副本的中心是 `human-factors-diagram-renderer/`。

也就是说，这里不是为了展示“我试过多少路线”，而是为了展示“我最后把什么东西做成了可以复用的 Skill”，以及这个 Skill 背后有哪些必要证据。

## 顶层结构

| 路径 | 作用 |
|---|---|
| `human-factors-diagram-renderer/` | 最终成品。包含 Skill 入口、渲染脚本、规则、示例和日志机制。 |
| `project_context/` | 支撑成品成立的关键决策、目标、验收方式和错误索引。 |
| `transcripts/` | 原始上下文记录，用于保留真实推进过程。 |

## 关键文件

### `human-factors-diagram-renderer/`

| 文件/目录 | 作用 |
|---|---|
| `SKILL.md` | Skill 入口，定义能力边界、工作流和验收方式。 |
| `README.md` | 人类快速入口。 |
| `scripts/` | 渲染、校验、导出、问题记录等核心脚本。 |
| `references/` | 规则、规范、验收和避坑文档。 |
| `assets/examples/` | 成品级示例输入与输出。 |

### `project_context/`

| 文件 | 作用 |
|---|---|
| `00_Key_Decisions.md` | 关键决策与原因。 |
| `01_mvp_goal.md` | 项目目标定义。 |
| `05_error_index.md` | 关键错误与修复路径。 |
| `DEMO_EXIT_CRITERIA.md` | Demo 收口标准。 |
| `VALIDATION_GUIDE.md` | 自检和人工验收方法。 |
| `35_skill_maturity_assessment.md` | 对当前 Skill 成熟度的阶段性评估。 |

## 推荐阅读顺序

1. `README.md`
2. `human-factors-diagram-renderer/SKILL.md`
3. `project_context/01_mvp_goal.md`
4. `project_context/DEMO_EXIT_CRITERIA.md`
5. `project_context/00_Key_Decisions.md`
6. `project_context/05_error_index.md`
7. `transcripts/`

## 备注

- 旧版输出产物和重复实现已经从这个副本移出。
- 当前真正对外可复用的部分，是 `human-factors-diagram-renderer/`。
