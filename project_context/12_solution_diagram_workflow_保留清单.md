# Solution Diagram Workflow 保留清单

> 状态：第二轮收缩后版本
> 原则：以最终可复用 Skill 为中心反推，只保留支撑其成立的必要证据。

## 1. 保留目标

对外副本只保留三类内容：

1. 最终收口成型的 Skill 成品
2. 能说明目标、决策、验收和关键错误的高密度文档
3. 原项目中已经沉淀的原始对话与上下文记录

## 2. 当前确定保留

### 入口层

1. `README.md`
2. `Index.md`

### Project Context 层

1. `project_context/00_Key_Decisions.md`
2. `project_context/01_mvp_goal.md`
3. `project_context/05_error_index.md`
4. `project_context/35_skill_maturity_assessment.md`
5. `project_context/DEMO_EXIT_CRITERIA.md`
6. `project_context/VALIDATION_GUIDE.md`

### 原始上下文层

1. `transcripts/`

### Skill 成品层

1. `human-factors-diagram-renderer/`

## 3. 第二轮已从副本移出的内容

以下内容在第一批复制后，已经从副本中主动移出：

1. `guides/`
2. `specs/`
3. `templates/`
4. `src/`
5. `tests/`
6. `outputs/`
7. 与最终 Skill 无直接支撑关系的阶段性交接和局部实验文档

## 4. 当前执行策略

1. 以 `human-factors-diagram-renderer/` 作为主阅读对象
2. 用 `project_context/` 补足目标、决策、验收和错误证据
3. 用 `transcripts/` 保留原始上下文
4. 原项目保持不变
