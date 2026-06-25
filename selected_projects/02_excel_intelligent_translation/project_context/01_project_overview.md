# Excel Intelligent Translation - 项目概览与核心防线

## 核心目标
实现一个**格式与图片零损耗**的 Excel 工业文档（SIP 检验规范）智能翻译工具（商业级 MVP）。

## 核心痛点与防线
1. **零格式损耗**：由于目标文档包含排版、合并单元格和重要图片，绝对禁止使用会重写全表的破坏性库（如纯 openpyxl 写操作会丢失图片）。必须使用原生/AppleScript/xlwings 方案进行单元格级别覆写。
2. **防呆机制（Poka-Yoke）**：任何写操作前，必须在同级目录生成带有 `_translated_test` 后缀的副本。**绝对禁止触碰或修改原文件**。
3. **并发与限流预警**：需预留架构位，包含：
   - 读取
   - 本地缓存查重（Cache/Dict）
   - 防限流休眠（Exponential Backoff）
   - 断点续写

## 开发阶段划分
- **阶段一（当前）**：现有组件评估与 MVP 测试。通过 AppleScript 或其他原生方式读取、翻译表头、正文多文本和尾部格式，并写回副本。
- **阶段二**：引入 `Translation Memory` (本地字典防重翻译) 和 `Rate Limit Retry` (防 API 限流报错) 中间件。
- **阶段三**：剥离测试环境，封装为标准执行模块。

## 已完成的测试与决策
1. `excel-reader` (基于 openpyxl read_only)：无法完美解析合并单元格，无法作为主引擎。
2. `excel-editor` (基于 AppleScript)：方向正确，但遇到了 macOS 权限拦截（-10004）。目前正在进行权限授权调试，等待系统级放行。
3. 最终决定抛弃破坏格式的工具，坚定走 AppleScript/xlwings/原生的方案。
