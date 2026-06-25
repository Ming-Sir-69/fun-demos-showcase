# 08_GUI_Architecture_and_Future_Optimizations

## 当前 GUI 架构总结 (Current Architecture)

在彻底抛弃了早期将终端倒计时、轮询逻辑和业务逻辑高度耦合的单体架构后，我们为 `Excel Intelligent Translation` 构建了一套现代化的、线程安全的 macOS 专属图形用户界面 (GUI)。

### 1. 核心模块与入口解耦
- **`app.py`**：作为全局统一入口，负责环境路径的挂载（解决 PyInstaller 打包后的模块检索偏移问题）并拉起主窗口。
- **`src/gui/main_window.py`**：封装了 `MainWindow` 类，彻底将表现层 (Presentation Layer) 与底层的 `core.pipeline` (业务逻辑层) 剥离。

### 2. Apple HIG 浅色主题与响应式布局
- **绝对视觉一致性**：严禁深色模式混用。统一背景底色 `#F5F5F7` 与卡片底色 `#FFFFFF`，搭配高对比度字体 `#1D1D1F` 和亮色点缀 `#007AFF`。
- **圆角卡片模拟**：由于 `ttk.Frame` 不支持 `border-radius`，采用 `tk.Canvas.create_polygon(..., smooth=True)` 绘制圆角背景，完美模拟出 macOS 原生悬浮卡片的质感。
- **响应式网格 (Responsive Grid)**：采用 `pack(expand=True, fill=tk.BOTH)` 与 `rowconfigure/columnconfigure(weight=1)` 相结合的布局策略，取代僵硬的绝对像素定位。窗口可自由拉伸，所有内部组件均等比例自适应，并配置了 `minsize` 防挤压。

### 3. 双标签页控制台 (Dual-Tab Dashboard)
使用 `ttk.Notebook` 构建，将用户视线分离为两层：
- **实时进度 (Dashboard)**：面向小白用户，提供极简的参数配置面板（原生文件选择器、模式下拉框）、实时动态指标卡片（命中率/处理条数）、以及三态看板流水灯（⚪️/🟡/🟢）。
- **运行日志 (Console)**：面向极客或排障需求，提供原汁原味的底层运行日志。

### 4. 终极防假死机制 (Anti-Freeze & Threading)
- **业务守护线程**：将极度耗时的 `run_pipeline` 抛入 `threading.Thread(daemon=True)` 中执行，彻底解放主线程 (`mainloop`)，保证窗口始终可拖拽。
- **Stdout 重定向与队列通信**：自定义 `StdoutRedirector` 拦截底层所有的 `print` 输出并压入 `queue.Queue`。主线程利用 `root.after` 轮询消费队列。
- **UI 动画复刻与滚动防呆**：
  - 在插入 UI 文本框前，通过正则彻底剥离 ANSI 颜色转义符。
  - 通过探测 `\r` 字符，在 UI 中删行重写，完美复刻原终端的倒计时动画。
  - 智能滚动逻辑：仅当滚动条触底（`yview()[1] >= 0.99`）时才自动跟随 `see(tk.END)`，防止用户向上查阅历史时发生严重拉扯假死。

---

## 2026-04-11 最新架构升级 (GUI Architecture Evolution)

### 1. 彻底消灭原生边框与材质重塑 (Borderless & Materials)
- **消除黑边**：移除了所有由 `RoundedFrame` 和 `tk.Entry` 产生的默认黑色轮廓线 (`outline=''`)，通过纯白 (`#FFFFFF`) 与浅灰 (`#F5F5F7`) 的色差来划分层级，大幅削弱了 Tkinter 的第三方软件感。
- **侧边栏架构 (Sidebar Layout)**：废弃了顶部的 `ttk.Notebook` 标签页，引入 macOS 经典的“左侧边栏 + 右侧主内容区”结构。侧边栏使用 `#EAEBEE` 底色，选中的导航按钮呈现 `#D1D1D6` 下压态，右侧内容区保持纯白，纵深感显著提升。
- **统一按钮层级**：所有辅助操作按钮（如打开字典、所在目录）降级为浅灰色 (`#E5E5EA`) 的 `ModernButton`，仅保留“开始翻译”为 Apple Blue (`#007AFF`)，使 Call-To-Action (CTA) 更加聚焦。

### 2. 全局动态缩放引擎 (Global Zoom Engine)
为了解决高分辨率屏幕下字体过小、拉伸窗口时内容无法等比放大的痛点，引入了系统级 `Cmd +/-` 缩放机制：
- **字体驱动引擎 (Text-Driven Scaling)**：构建了全局字体池 (`self.fonts`)。缩放指令首先改变基准字号，Tkinter 原生组件感知字体变化后会自动撑开。
- **Canvas 重绘联动 (Box Gap Scaling)**：自定义绘制的组件（如 `ModernButton` 和 `CircularProgress`）加入了 `recalculate_size` 机制，按比例放大内部间隙 (`padding_x/y`) 和线条粗细 (`thickness`) 并重新计算 `winfo_reqwidth()` 触发重绘。
- **窗口屏障智能贴合 (Smart Window Geometry)**：
  - 将基础分辨率锁定在 `1150x700`。
  - **缩小策略 (`Cmd -`)**：强制重置窗口的物理大小 `geometry` 以贴合缩小后的内容。
  - **放大策略 (`Cmd +`)**：仅推高 `minsize`。如果当前窗口（如全屏态）已经大于需要的尺寸，则不改变物理窗口大小，仅让内部元素膨胀，避免了全屏状态下放大字体导致窗口突然回缩的割裂感。

---

## 后续 UI 优化方向与规划预留 (Future Optimizations)

### 1. 更丰富的动画与微交互 (Micro-interactions)
- **Hover 反馈**：Tkinter 默认对鼠标悬停的视觉反馈较弱，后续可通过绑定 `<Enter>` 和 `<Leave>` 事件，在按钮和配置卡片上模拟出阴影加深或颜色渐变的动效。（*部分已在 `ModernButton` 中实现*）
- **加载态阻断**：在 `openpyxl` 读取工作表名称等短暂 I/O 操作时，加入微小的 Loading 动画，防止用户在此期间多次点击。

### 2. 数据可视化升维 (Data Visualization)
- **图表接入**：如果需要进一步增强工业高级感，可以考虑将目前的纯文字“指标卡片”替换为轻量级的图表。例如，利用 Python 的绘图库将“字典命中率”和“API 调用量”渲染成动态的环形图或柱状图嵌入 Dashboard 中。（*已使用 `CircularProgress` 实现*）

### 3. 跨平台打包与资源内联准备 (Packaging Preparedness)
- 虽然当前代码已经做了针对 Mac 的路径防呆（`~/Library/Application Support/...` 的字典初始化逻辑），但在后续使用 PyInstaller 或 `py2app` 正式构建 `.app` 时，仍需：
  - 确保所有的静态图片资源（如果有 logo、icon）使用 `sys._MEIPASS` 动态定位。（*已通过全局 `resource_path` 函数实现*）
  - 在 `.spec` 文件中显式注入 `NSAppleEventsUsageDescription`，以防止 `xlwings` 触发 macOS 安全拦截报错。