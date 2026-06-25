# Excel Intelligent Translation

## 这是什么

这是一个经过裁剪后的对外副本。

它展示的不是“一个可以直接分发的软件包”，而是一个工业级 Excel 智能翻译 Demo 如何被设计成更稳定、更省成本、也更容易在真实业务里推行。

这个项目的重点有四个：

1. 复杂格式保护
2. 本地词典与线上模型双路并行
3. 成本、稳定性和复用价值之间的平衡
4. 从脚本到可打包工具的产品化思路

## 建议怎么读

### 快速阅读

如果只想快速判断这个项目的价值，建议按这个顺序读：

1. `project_context/01_project_overview.md`
2. `project_context/05_Architecture_Evolution_Whitepaper.md`
3. `project_context/项目复盘与架构思想总结.md`
4. `project_context/04_Classification_Audit_Report.md`

### 深入阅读

如果想判断这个项目的落地能力和取舍逻辑，再继续读：

1. `project_context/07_Architecture_Refactoring_and_GUI_Preparation.md`
2. `project_context/08_GUI_Architecture_and_Future_Optimizations.md`
3. `src/core/`
4. `src/gui/`
5. `data/original_excel_doc/L9FHS003&04-DT-R 检验规范(SIP).xlsx`

## 这个副本保留了什么

这个副本只保留四类内容：

1. 架构演进、审计和复盘文档
2. 核心源码
3. 单一测试样本
4. 与打包思路相关的入口文件

## 怎么理解这里的上下文

这个项目的原始 Session 记录不完整。

因此，这里的主要证据不是逐轮原始对话，而是已经沉淀下来的项目概览、架构白皮书、审计报告、复盘文档和源码结构。

换句话说，这个副本更适合用来判断：

1. 这个 Demo 是否真的能落地
2. 设计取舍是否清楚
3. 产品化推进思路是否完整

而不是还原每一步最早的原始对话。

如果需要分析作者本人更原始的一手工作材料，应优先阅读 `Solution Diagram Workflow` 副本中的 `transcripts/`。这个 Excel 项目更适合承担“完整度、稳定性与产品化能力”的证据角色。

## 当前边界

这个副本不用于对外提供可直接运行的软件。

它不包含真实 API 密钥，也不附带可直接分发的应用本体。这里保留的是开发思路、系统设计和可运行 Demo 的证据，而不是交付给外部直接试用的安装包。

## 文件提示

- `app.py`、`run.sh`、`build_mac.sh`、`ExcelIntelligentTranslator.spec` 主要用于说明这个项目如何从 Demo 走向可打包工具。
- `src/core/llm_translator.py` 中的密钥已经改为占位符。
- 这里保留虚拟环境与打包思路的叙述，是因为“降低部署门槛”本身就是这个项目的产品化考虑之一。
