# Excel Intelligent Translation 保留清单

> 状态：第二轮收缩后版本
> 原则：只保留足以展示完整度、稳定性、成本意识和产品化思路的内容。

## 1. 保留目标

对外副本只保留四类内容：

1. 能说明项目问题、架构演进和关键取舍的高密度文档
2. 能说明它是如何跑通和如何推行的核心实现材料
3. 少量足够证明 Demo 存在的样本与入口文件
4. 能说明边界和局限的补充上下文

## 2. 当前确定保留

### 入口层

1. `README.md`
2. `app.py`
3. `run.sh`
4. `build_mac.sh`
5. `ExcelIntelligentTranslator.spec`
6. `Excel智能翻译器_项目介绍.pptx`

### Project Context 层

1. `project_context/00_Global_Dialogue_Transcript.md`
2. `project_context/01_project_overview.md`
3. `project_context/02_auth_and_xlwings_test.md`
4. `project_context/03_xlwings_refactor_and_ui_upgrade_20260408.md`
5. `project_context/04_Classification_Audit_Report.md`
6. `project_context/05_Architecture_Evolution_Whitepaper.md`
7. `project_context/06_Remaining_Development_Plan.md`
8. `project_context/07_Architecture_Refactoring_and_GUI_Preparation.md`
9. `project_context/08_GUI_Architecture_and_Future_Optimizations.md`
10. `project_context/项目复盘与架构思想总结.md`

### 实现层

1. `src/`

### 样本层

1. `data/original_excel_doc/L9FHS003&04-DT-R 检验规范(SIP).xlsx`

## 3. 当前已知需要后续处理的敏感点

1. API Key
2. 测试 Excel 样本数量过多，只保留一个 `L9FHS003&04-DT-R 检验规范(SIP)` 相关样本
3. 已打包的 macOS App 不作为对外测试交付

## 4. 当前执行策略

1. 只保留一个统一的 `README.md` 作为入口
2. 以白皮书、审计、复盘和核心源码作为主证据
3. 将 `00_Global_Dialogue_Transcript.md` 视为补充上下文，而不是原始 Session 证据
4. 原项目保持不变
