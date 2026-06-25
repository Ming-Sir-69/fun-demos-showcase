# Solution Diagram Workflow

## 这是什么

这个副本的展示中心不是“整个流程图项目”，而是最终收口出来的 `Human Factors Diagram Renderer`。

它代表的是一个更具体的结果：

把语义内容、规则约束和确定性渲染封装成一个可复用的 Skill，让图表生成不再依赖临时拼装，而是可以被验证、复查和继续迭代。

## 这个副本保留了什么

这个副本只保留三类内容：

1. 最终可复用的 Skill 成品
2. 支撑这个成品成立的关键决策、验收规则和错误索引
3. 能反映真实推进过程的原始上下文记录

旧路线的输出产物、重复源码和会放大阅读噪音的材料，已经从这个副本里移出。

## 建议怎么读

### 快速阅读

如果只想快速判断这个项目是否有展示价值，建议按这个顺序读：

1. `human-factors-diagram-renderer/SKILL.md`
2. `human-factors-diagram-renderer/README.md`
3. `project_context/01_mvp_goal.md`
4. `project_context/DEMO_EXIT_CRITERIA.md`
5. `project_context/00_Key_Decisions.md`

### 深入阅读

如果想理解这个 Skill 是怎么被做出来的，再继续看：

1. `project_context/05_error_index.md`
2. `project_context/VALIDATION_GUIDE.md`
3. `project_context/35_skill_maturity_assessment.md`
4. `transcripts/`

## 怎么理解这里的上下文

这里保留的上下文，不是为了包装，而是为了保留项目推进过程中真实发生过的判断和拐点。

`transcripts/` 的作用也不只是记录这个 Skill 是怎么被做出来的。

它同时也是分析作者的第一入口：里面保留了未经事后修饰的长文本 Session 对话，适合用来判断真实的问题拆解方式、决策习惯、验证意识、边界感和产品推进风格。

如果你想判断这个项目背后的工作方式，或者进一步分析作者本人是否具备 AI 产品经理所需要的品质与技能，请把 `project_context/` 和 `transcripts/` 当成证据层，让AI来分析，而不是把它们当成附录。

## 当前边界

这个副本不是原项目的完整镜像。

它只保留最终 Skill、关键决策和必要证据，用来降低阅读负担，同时避免旧方案输出对判断造成干扰。
