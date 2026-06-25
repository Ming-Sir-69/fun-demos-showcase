# Excel Intelligent Translation - 模块化重构与 GUI 准备演进白皮书

> 本文档记录了在尝试开发 macOS 可视化图形交互界面 (GUI) 过程中遭遇挫折、回退后，重新进行的底层模块化重构及架构演进思路。

## 1. 架构演进背景 (Background)
在 2026-04-10 的开发中，为了满足项目“摆脱硬编码的文件路径，利用跨平台方案弹出原生选择器”的需求，我们最初尝试直接在 `main.py` 的单体架构上强行套壳 `tkinter` 的 GUI。但这导致了两个致命后果：
1. **线程死锁与假死**：单体脚本中的终端进度条（`live_timer`）、`time.sleep` 等与 UI 线程强耦合，导致 GUI 在执行长耗时的翻译任务时彻底卡死无响应。
2. **逻辑打架与修改困难**：随着错误处理、字典去重、换行拆分修复等逻辑在 `main.py` 中不断膨胀，任何对 UI 交互的微调都会牵一发而动全身，导致核心翻译功能（如 JSON 解析回退）连带失效。

为了彻底解决这一痛点，我们执行了 Git 回退，并改变了策略：**先拆分底层逻辑，再开发表层 UI。**

## 2. 核心模块化剥离 (Modular Decomposition)
我们将原本臃肿的 `main.py` 强行拆解为高内聚、低耦合的多个子模块，所有模块统一放置在 `src/core/` 及其子目录下，彻底剥离了控制流与业务流：

- **`src/utils/timer.py`**：
  剥离了终端特有的 `live_timer` 后台计时器线程和 `StageTimer` 上下文管理器。这确保了未来在 GUI 中，我们可以自由选择是否引入终端打印，而不会影响核心逻辑的执行。
- **`src/core/dictionary_manager.py`**：
  将所有的字典加载 (`load_local_dictionary`)、归一化 (`normalize_text`) 以及写入 (`append_to_local_dictionary`) 收口到单一模块。这保证了无论多少个界面或脚本调用字典，其清洗规则（全角转半角、剔除动态参数、中英双语位置反转）都是绝对一致且安全的。
- **`src/core/pipeline.py`**：
  将长达 300 行的 `run_pipeline` 完整抽离，并重构了其函数签名：`run_pipeline(original_file, test_file, sheet_name=None, mode="zh_to_en_bilingual")`。它不再内部硬编码找文件，而是作为一个纯粹的执行引擎，等待外部传入明确的路径指令。
- **`src/main.py` (降级为 CLI Entry Point)**：
  现在的 `main.py` 仅仅是一个 30 多行的终端测试入口。它的唯一职责就是提供默认的硬编码参数，然后调用 `core.pipeline.run_pipeline`。

## 3. 持久化存储规范确立 (Persistent Storage Specification)
在为 GUI 打包（PyInstaller `.app`）做前置规划时，我们彻底解决了打包后字典读写失效的隐患：
- 废弃了基于相对路径 `data/dictionary/local_dict_mapping.txt` 的存储方式。
- 将本地用户字典强制硬编码指向 macOS 官方标准的应用数据支持目录：`~/Library/Application Support/ExcelIntelligentTranslator/local_dict_mapping.txt`。
- **防呆自建**：在 `dictionary_manager.py` 中加入了目录探针，若新电脑上没有该目录，系统将在启动瞬间自动层级创建并推入带注释的初始化空字典，保障了打包应用在任何目标机上的绝对读写权限。

## 4. 后续 GUI 开发灵感与思路 (Future GUI Ideas)
通过本次的模块化拆分与持久化路径重构，我们为明天的 GUI 交互设计打开了全新的思路：
1. **无痛接入**：明天的 `gui.py` 只需要简单地导入 `from core.pipeline import run_pipeline`，在用户点击“运行”按钮时，开一个后台线程把选择好的 `file_path` 丢给它即可，底层翻译业务零修改。
2. **“一键修典”交互体验**：由于字典已经被存放在了标准的用户支持目录下，我们可以在 UI 面板上设计一个“打开本地字典”的按钮。当用户点击时，直接调用系统命令 `os.system("open '~/Library/Application Support/ExcelIntelligentTranslator'")` 唤起 Finder。这不仅解决了打包后包内文件无法修改的痛点，更提供了一种极其优雅的“用户手动介入矫正”体验。