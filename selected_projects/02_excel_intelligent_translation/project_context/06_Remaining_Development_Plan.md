# Excel Intelligent Translation - 后续开发规划与验收大纲

> 本文档记录了 Excel 智能翻译项目从当前阶段到最终交付的剩余核心开发框架。

## 1. 后续大框架流程规划

1. **可选文件及工作簿 (Selectable File & Sheet)**
   - 目标：摆脱硬编码的文件路径和索引，利用跨平台方案（如 `tkinter`）弹出系统原生文件选择器，让用户选择待翻译的 Excel 文件。
   - 工作簿选择：后台读取所选文件的 Sheet 列表，提供轻量级交互让用户选择具体翻译哪个工作簿。

2. **跨系统平台适配 (Cross-Platform Compatibility)**
   - 目标：确保方案在 macOS 和 Windows 系统下表现一致。
   - 评估由于系统差异（如 `xlwings` 在 Mac 依赖 AppleScript，在 Win 依赖 COM）导致的权限和渲染问题，提供双版本或通用适配方案。
   - **执行策略变更 (2026-04-09)**：当前所有开发均以 macOS 环境为主线。待 macOS 版本（含 GUI 与打包）彻底跑通并验证后，再将代码迁移至真实 Windows 环境，解决 COM 接口与文件锁等特定问题，衍生出一个专属的 Windows 分支版本。

3. **UI 可视化图形交互界面 (GUI)**
   - 目标：为项目穿上一层正式的图形界面外衣。
   - 整合文件选择、工作表选择、源语言/目标语言选择、进度条和控制台日志输出到一个完整的 GUI 窗口中，彻底告别终端黑框。
   - **无障碍说明**：此部分使用 `tkinter`，高度跨平台，在 macOS 下可无缝开发与测试。

4. **打包与发布 (Packaging)**
   - 目标：将 Python 代码与依赖环境（虚拟环境）打包为独立的可执行文件（macOS 下为 `.app`，Windows 下为 `.exe`）。
   - 使用 PyInstaller 或 Nuitka 等工具，实现用户的“开箱即用”。
   - **架构定律**：由于打包工具不支持跨平台编译（无法在 Mac 上直接生成 `.exe`），且项目强依赖宿主环境的 Excel 应用，打包动作必须分别在 macOS 和 Windows 原生系统中各自执行。

---
*注：本次开发迭代（当前阶段）仅专注于**阶段 1**（可选文件及工作簿）的开发、测试与验收。*

## 2. 2026-04-09 架构回退与未来规划 (Architecture Revert & Future Plan)

由于之前的字典污染和 UI 交互不一致等混乱问题，项目已回退至版本 `15b6fc9`（基础 GUI 阶段），以舍弃不稳定的代码并重新进行干净的实现。接下来的核心开发任务如下：

1. **Core Translation Pipeline Integration (核心翻译管道集成)**：将 GUI 的 `run_btn`（运行按钮）与 `src/main.py` 的核心处理逻辑打通桥接。
2. **Newline Split Fix (换行符拆分修复)**：在文本分类器的循环中实现 `re.split(r'(\r?\n| {2,}|\t+)')`，确保带有换行或多个连续空格的单元格文本能被正确切分和保留格式。
3. **Persistent User Dictionary (持久化用户词典)**：将本地用户词典路径硬编码为 `~/Library/Application Support/ExcelIntelligentTranslator/local_dict_mapping.txt`。若该路径下未找到词典，则从打包环境 `sys._MEIPASS` 中复制默认词典过去，保证词典的持久化与用户可编辑性。
4. **Error Correction Pre-processing (纠错预处理)**：规划并实现一个预处理模块，在将文本发送给 LLM 翻译前，扫描并自动修复源文本中的常见拼写错误（例如将 "Lizhen" 修正为 "Luxshare"）。