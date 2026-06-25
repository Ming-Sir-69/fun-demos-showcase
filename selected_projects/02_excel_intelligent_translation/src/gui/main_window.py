import os
import sys
import threading
import queue
import re
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont
import openpyxl


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)

# 兼容 Python 3.14 下 xlwings/appscript 的 pth 路径问题
if sys.platform.startswith("darwin"):
    aeosa_path = os.path.join(sys.prefix, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages", "aeosa")
    if os.path.exists(aeosa_path) and aeosa_path not in sys.path:
        sys.path.append(aeosa_path)

# 确保可以找到 core 模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.pipeline import run_pipeline

# 绘制带有圆角的卡片背景
def create_rounded_rectangle(canvas, x1, y1, x2, y2, r=25, **kwargs):
    points = (x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1)
    if 'outline' not in kwargs:
        kwargs['outline'] = kwargs.get('fill', '')
    return canvas.create_polygon(points, **kwargs, smooth=True)

class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg_color, corner_radius=15, **kwargs):
        tk.Canvas.__init__(self, parent, bg=parent["bg"], highlightthickness=0, **kwargs)
        self.bg_color = bg_color
        self.corner_radius = corner_radius
        self.bind("<Configure>", self._on_resize)
        
    def _on_resize(self, event):
        self.delete("all")
        create_rounded_rectangle(self, 0, 0, event.width, event.height, r=self.corner_radius, fill=self.bg_color)


class ModernButton(tk.Canvas):
    def __init__(self, parent, text, command=None, bg_color="#007AFF", hover_color="#0056b3", click_color="#003d82", text_color="#FFFFFF", font=None, corner_radius=10, padding_x=20, padding_y=10, **kwargs):
        tk.Canvas.__init__(self, parent, bg=parent["bg"], highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.click_color = click_color
        self.text_color = text_color
        self.font = font
        self.corner_radius = corner_radius
        self.text_str = text
        self.state = tk.NORMAL
        
        self.base_padding_x = padding_x
        self.base_padding_y = padding_y
        self.padding_x = padding_x
        self.padding_y = padding_y
        
        self.bind("<Configure>", self._on_resize)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)
        
        self.recalculate_size()
        
    def recalculate_size(self):
        dummy = tk.Label(font=self.font, text=self.text_str)
        req_width = dummy.winfo_reqwidth() + self.padding_x * 2
        req_height = dummy.winfo_reqheight() + self.padding_y * 2
        self.config(width=req_width, height=req_height)
        self.after(10, lambda: self._draw(self.bg_color if self.state == tk.NORMAL else "#A2A2A2"))
        
    def _draw(self, color):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10: return
        create_rounded_rectangle(self, 0, 0, w, h, r=self.corner_radius, fill=color)
        self.create_text(w/2, h/2, text=self.text_str, fill=self.text_color, font=self.font)
        
    def _on_resize(self, event):
        self._draw(self.bg_color if self.state == tk.NORMAL else "#A2A2A2")
        
    def _on_enter(self, event):
        if self.state == tk.NORMAL:
            self._draw(self.hover_color)
            self.config(cursor="hand2")
            
    def _on_leave(self, event):
        if self.state == tk.NORMAL:
            self._draw(self.bg_color)
            self.config(cursor="")
            
    def _on_click(self, event):
        if self.state == tk.NORMAL:
            self._draw(self.click_color)
            
    def _on_release(self, event):
        if self.state == tk.NORMAL:
            x, y = event.x, event.y
            if 0 <= x <= self.winfo_width() and 0 <= y <= self.winfo_height():
                self._draw(self.hover_color)
                if self.command:
                    self.command()
            else:
                self._draw(self.bg_color)
                
    def config_state(self, state):
        self.state = state
        if state == tk.DISABLED:
            self._draw("#A2A2A2")
            self.config(cursor="")
        else:
            self._draw(self.bg_color)

class CircularProgress(tk.Canvas):
    def __init__(self, parent, size=130, thickness=12, bg_color="#E5E5EA", fg_color="#007AFF", text_color="#1D1D1F", title="", number_font=None, title_font=None, **kwargs):
        tk.Canvas.__init__(self, parent, width=size, height=size, bg=parent["bg"], highlightthickness=0, **kwargs)
        self.base_size = size
        self.size = size
        self.base_thickness = thickness
        self.thickness = thickness
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.text_color = text_color
        self.value = 0
        self.title = title
        self.max_value = 100
        self.number_font = number_font
        self.title_font = title_font
        
        self.bind("<Configure>", lambda e: self._draw())
        
    def recalculate_size(self, scale_factor):
        self.size = int(self.base_size * scale_factor)
        self.thickness = max(1, int(self.base_thickness * scale_factor))
        self.config(width=self.size, height=self.size)
        self.after(10, self._draw)

    def set_value(self, value, max_value=None):
        self.value = int(value)
        if max_value is not None:
            self.max_value = int(max_value) if int(max_value) > 0 else 1
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            w, h = self.size, self.size
            
        pad = self.thickness + 2
        x0 = (w - self.size) / 2 + pad
        y0 = (h - self.size) / 2 + pad
        x1 = x0 + self.size - pad * 2
        y1 = y0 + self.size - pad * 2
        
        self.create_oval(x0, y0, x1, y1, outline=self.bg_color, width=self.thickness)
        
        if self.max_value > 0 and self.value > 0:
            fraction = self.value / self.max_value
            if fraction > 1: fraction = 1
            extent = -fraction * 359.99 
            self.create_arc(x0, y0, x1, y1, start=90, extent=extent, outline=self.fg_color, width=self.thickness, style=tk.ARC)
        
        self.create_text(w/2, h/2 - 10 * (self.size / self.base_size), text=str(self.value), fill=self.text_color, font=self.number_font)
        self.create_text(w/2, h/2 + 18 * (self.size / self.base_size), text=self.title, fill="#86868B", font=self.title_font)

class StdoutRedirector:
    def __init__(self, msg_queue):
        self.msg_queue = msg_queue

    def write(self, string):
        self.msg_queue.put(string)

    def flush(self):
        pass

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Excel Intelligent Translator")
        self.root.geometry("1150x700")
        self.root.minsize(1150, 700)
        
        self.scale_factor = 1.0
        self.base_minsize = (1150, 700)
        self.base_sidebar_width = 180
        self.scalable_widgets = []
        
        # 统一全局字体配置
        self.fonts = {
            "normal": tkfont.Font(family="San Francisco", size=13),
            "bold": tkfont.Font(family="San Francisco", size=13, weight="bold"),
            "title": tkfont.Font(family="San Francisco", size=14, weight="bold"),
            "small": tkfont.Font(family="San Francisco", size=11),
            "small_bold": tkfont.Font(family="San Francisco", size=12, weight="bold"),
            "number": tkfont.Font(family="San Francisco", size=24, weight="bold"),
            "card_value": tkfont.Font(family="San Francisco", size=28, weight="bold"),
            "console": tkfont.Font(family="Menlo", size=12)
        }
        self.base_font_sizes = {k: v.cget("size") for k, v in self.fonts.items()}
        
        # Apple HIG 浅色主题配置
        self.bg_color = "#F5F5F7"
        self.card_bg = "#FFFFFF"
        self.text_color = "#1D1D1F"
        self.accent_color = "#007AFF"
        self.border_color = "#D1D1D6"
        self.root.configure(bg=self.bg_color)
        # 尝试使用 resource_path 加载图标
        try:
            icon_img = tk.PhotoImage(file=resource_path("assets/icon.png"))
            self.root.iconphoto(True, icon_img)
        except Exception as e:
            pass # 忽略图标缺失

        
        # 隐藏原生边框
        self.root.attributes("-alpha", 1.0)
        
        style = ttk.Style()
        if sys.platform == "darwin":
            style.theme_use('aqua')
        else:
            style.theme_use('clam')
            
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=self.fonts["normal"])
        style.configure("TButton", font=self.fonts["normal"], padding=6)
        
        # 居中、圆角、阴影质感的卡片容器样式（Tkinter 无法实现真圆角阴影，通过颜色和边框模拟悬浮感）
        style.configure("Card.TFrame", background=self.card_bg, relief="flat", borderwidth=0)
        style.configure("Card.TLabel", background=self.card_bg, foreground=self.text_color, font=self.fonts["normal"])
        style.configure("CardValue.TLabel", background=self.card_bg, foreground=self.accent_color, font=self.fonts["card_value"])
        style.configure("CardTitle.TLabel", background=self.card_bg, foreground="#86868B", font=self.fonts["small_bold"])
        
        self.sidebar_bg = "#EAEBEE"
        
        self.main_container = tk.Frame(self.root, bg=self.bg_color)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.sidebar = tk.Frame(self.main_container, bg=self.sidebar_bg, width=180)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        self.content_area = tk.Frame(self.main_container, bg=self.bg_color)
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.dashboard_frame = tk.Frame(self.content_area, bg=self.bg_color)
        self.console_frame = tk.Frame(self.content_area, bg=self.bg_color)
        
        self.is_running = False
        self.start_time = 0
        self.last_test_file = ""
        
        self._build_sidebar()
        self._build_dashboard()
        self._build_console()
        
        self.show_frame(self.dashboard_frame)
        
        self.msg_queue = queue.Queue()
        # 拦截 sys.stdout
        sys.stdout = StdoutRedirector(self.msg_queue)
        
        self.root.after(100, self.check_queue)
        
    def _build_sidebar(self):
        # Sidebar Title
        title_lbl = tk.Label(self.sidebar, text="Excel 智能翻译", bg=self.sidebar_bg, fg="#1D1D1F", font=self.fonts["title"])
        title_lbl.pack(pady=(40, 30), padx=15, anchor="w")
        
        # Navigation Buttons
        self.nav_btns = {}
        
        def make_nav_btn(text, target_frame):
            btn = ModernButton(self.sidebar, text=text, command=lambda: self.show_frame(target_frame), 
                               bg_color=self.sidebar_bg, hover_color="#D1D1D6", click_color="#C7C7CC", 
                               text_color=self.text_color, font=self.fonts["bold"], 
                               corner_radius=8, padding_x=10, padding_y=8)
            btn.pack(fill=tk.X, padx=15, pady=5)
            self.scalable_widgets.append(btn)
            self.nav_btns[target_frame] = btn
            
        make_nav_btn("实时进度", self.dashboard_frame)
        make_nav_btn("运行日志", self.console_frame)
        
    def show_frame(self, frame):
        self.dashboard_frame.pack_forget()
        self.console_frame.pack_forget()
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Update sidebar button states
        for f, btn in self.nav_btns.items():
            if f == frame:
                btn.bg_color = "#D1D1D6"
                btn._draw("#D1D1D6")
            else:
                btn.bg_color = self.sidebar_bg
                btn._draw(self.sidebar_bg)

    def _build_dashboard(self):
        # 居中主容器 (使用 pack(expand=True, fill=BOTH) 实现自适应布局，内部利用网格或相对定位)
        main_container = tk.Frame(self.dashboard_frame, bg=self.bg_color)
        main_container.pack(expand=True, fill=tk.BOTH, padx=40, pady=20)
        
        # 内部使用 grid 布局，让各模块随窗口按比例自适应
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(0, weight=1) # config_card
        main_container.rowconfigure(1, weight=1) # metrics
        main_container.rowconfigure(2, weight=1) # exec_card
        
        # --- File Selection Area (Card Style) ---
        config_card_bg = RoundedFrame(main_container, bg_color=self.card_bg)
        config_card_bg.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        config_card = tk.Frame(config_card_bg, bg=self.card_bg)
        # 使用 place 实现相对于背景的边距
        config_card.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)
        
        # 为了内部对齐，给 config_card 设 grid
        config_card.columnconfigure(1, weight=1)
        
        # File Selection
        tk.Label(config_card, text="选择 Excel 文件", bg=self.card_bg, fg=self.text_color, font=self.fonts["bold"], width=12, anchor="e").grid(row=0, column=0, pady=20, padx=(20, 15), sticky="e")
        self.file_path_var = tk.StringVar()
        
        # 使用 Frame 包裹 Entry，模拟更柔和的边框
        entry_frame = tk.Frame(config_card, bg=self.bg_color, padx=1, pady=1)
        entry_frame.grid(row=0, column=1, sticky="we", pady=20)
        tk.Entry(entry_frame, textvariable=self.file_path_var, font=self.fonts["normal"], bg=self.bg_color, fg=self.text_color, highlightthickness=0, relief="flat").pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        
        browse_btn = ModernButton(config_card, text="浏览", command=self.browse_file, bg_color="#E5E5EA", hover_color="#D1D1D6", click_color="#C7C7CC", text_color="#1D1D1F", font=self.fonts["normal"], corner_radius=8, padding_x=15, padding_y=6)
        browse_btn.grid(row=0, column=2, padx=15, pady=20)
        self.scalable_widgets.append(browse_btn)
        
        # Sheet Selection
        tk.Label(config_card, text="选择工作表", bg=self.card_bg, fg=self.text_color, font=self.fonts["bold"], width=12, anchor="e").grid(row=1, column=0, pady=(0, 20), padx=(20, 15), sticky="e")
        self.sheet_var = tk.StringVar()
        self.sheet_cb = ttk.Combobox(config_card, textvariable=self.sheet_var, state="readonly", font=self.fonts["normal"])
        self.sheet_cb.grid(row=1, column=1, columnspan=2, sticky="we", pady=(0, 20), padx=(0, 15))
        
        # Translation Mode
        tk.Label(config_card, text="翻译模式", bg=self.card_bg, fg=self.text_color, font=self.fonts["bold"], width=12, anchor="e").grid(row=2, column=0, pady=(0, 20), padx=(20, 15), sticky="e")
        self.mode_map = {
            "中翻英": "zh_to_en",
            "英翻中": "en_to_zh",
            "中翻英 (双语)": "zh_to_en_bilingual",
            "英翻中 (双语)": "en_to_zh_bilingual"
        }
        self.mode_var = tk.StringVar(value="中翻英 (双语)")
        self.mode_cb = ttk.Combobox(config_card, textvariable=self.mode_var, values=list(self.mode_map.keys()), state="readonly", font=self.fonts["normal"])
        self.mode_cb.grid(row=2, column=1, columnspan=2, sticky="we", pady=(0, 20), padx=(0, 15))
        
        # --- Metrics Cards Area ---
        metrics_container = tk.Frame(main_container, bg=self.bg_color)
        metrics_container.grid(row=1, column=0, sticky="nsew", pady=10)
        
        metrics_container.columnconfigure(0, weight=1)
        metrics_container.columnconfigure(1, weight=1)
        metrics_container.columnconfigure(2, weight=1)
        
        self.metrics_widgets = {}
        for i, name in enumerate(["待翻译词条", "字典命中", "成功写入"]):
            card_bg = RoundedFrame(metrics_container, bg_color=self.card_bg, corner_radius=15)
            card_bg.grid(row=0, column=i, sticky="nsew", padx=(0 if i==0 else 10, 0 if i==2 else 10))
            
            cp = CircularProgress(card_bg, size=110, thickness=10, bg_color=self.bg_color, fg_color=self.accent_color, text_color=self.text_color, title=name, number_font=self.fonts["number"], title_font=self.fonts["small_bold"])
            cp.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.scalable_widgets.append(cp)
            self.metrics_widgets[name] = cp
            
        # --- Execution & Status Area ---
        exec_card_bg = RoundedFrame(main_container, bg_color=self.card_bg)
        exec_card_bg.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        exec_card = tk.Frame(exec_card_bg, bg=self.card_bg)
        exec_card.place(relx=0.05, rely=0.05, relwidth=0.9, relheight=0.9)
        
        # 纵向均分 exec_card
        exec_card.rowconfigure(0, weight=1)
        exec_card.rowconfigure(1, weight=1)
        exec_card.rowconfigure(2, weight=1)
        exec_card.columnconfigure(0, weight=1)
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(exec_card, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(10, 5))
        
        # Status Indicators and Timer
        status_frame = tk.Frame(exec_card, bg=self.card_bg)
        status_frame.grid(row=1, column=0, sticky="ew", pady=5)
        
        lights_frame = tk.Frame(status_frame, bg=self.card_bg)
        lights_frame.pack(side=tk.LEFT)
        
        self.status_lights = {}
        stages = ["生成副本", "读取Excel", "核心分发", "大模型翻译", "底层写入", "任务完成"]
        for stage in stages:
            lbl = tk.Label(lights_frame, text=f"⚪️ {stage}", font=self.fonts["small"], bg=self.card_bg, fg="#86868B")
            lbl.pack(side=tk.LEFT, padx=2)
            self.status_lights[stage] = lbl
            
        self.time_label = tk.Label(status_frame, text="已耗时: 00:00", font=self.fonts["title"], bg=self.card_bg, fg=self.accent_color)
        self.time_label.pack(side=tk.RIGHT, padx=5)
        
        # Action Buttons
        action_frame = tk.Frame(exec_card, bg=self.card_bg)
        action_frame.grid(row=2, column=0, sticky="ew", pady=(10, 10))
        
        # 左侧工具按钮
        tools_frame = tk.Frame(action_frame, bg=self.card_bg)
        tools_frame.pack(side=tk.LEFT)
        btn1 = ModernButton(tools_frame, text="打开字典", command=self.open_dict, bg_color="#E5E5EA", hover_color="#D1D1D6", click_color="#C7C7CC", text_color="#1D1D1F", font=self.fonts["normal"], padding_x=12, padding_y=8)
        btn1.pack(side=tk.LEFT, padx=(0, 8))
        self.open_file_btn = ModernButton(tools_frame, text="打开文件", command=self.open_translated_file, bg_color="#E5E5EA", hover_color="#D1D1D6", click_color="#C7C7CC", text_color="#1D1D1F", font=self.fonts["normal"], padding_x=12, padding_y=8)
        self.open_file_btn.config_state(tk.DISABLED)
        self.open_file_btn.pack(side=tk.LEFT, padx=8)
        self.open_dir_btn = ModernButton(tools_frame, text="所在目录", command=self.open_file_dir, bg_color="#E5E5EA", hover_color="#D1D1D6", click_color="#C7C7CC", text_color="#1D1D1F", font=self.fonts["normal"], padding_x=12, padding_y=8)
        self.open_dir_btn.config_state(tk.DISABLED)
        self.open_dir_btn.pack(side=tk.LEFT, padx=8)
        self.scalable_widgets.extend([btn1, self.open_file_btn, self.open_dir_btn])
        
        # 右侧主操作按钮
        self.run_btn = ModernButton(action_frame, text="开始翻译", command=self.run_translation, bg_color=self.accent_color, hover_color="#0056b3", click_color="#003d82", text_color="#FFFFFF", font=self.fonts["bold"], padding_x=20, padding_y=10)
        self.run_btn.pack(side=tk.RIGHT)
        self.scalable_widgets.append(self.run_btn)
        
    def _build_console(self):
        console_card = RoundedFrame(self.console_frame, bg_color=self.card_bg)
        console_card.pack(fill=tk.BOTH, expand=True)
        
        self.console_text = tk.Text(console_card, bg=self.card_bg, fg=self.text_color, font=self.fonts["console"], wrap=tk.WORD, highlightthickness=0, relief="flat", padx=20, pady=20)
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(console_card, command=self.console_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=20, padx=(0, 20))
        self.console_text.config(yscrollcommand=scrollbar.set)
        
        # 快捷键绑定
        self.root.bind("<Command-equal>", lambda e: self.zoom(0.1))
        self.root.bind("<Command-minus>", lambda e: self.zoom(-0.1))
        self.root.bind("<Command-0>", lambda e: self.zoom_reset())
        self.root.bind("<Control-equal>", lambda e: self.zoom(0.1)) # 兼容 Windows/Linux
        self.root.bind("<Control-minus>", lambda e: self.zoom(-0.1))
        self.root.bind("<Control-0>", lambda e: self.zoom_reset())

    def zoom(self, delta):
        new_scale = self.scale_factor + delta
        if new_scale < 0.6 or new_scale > 3.0: return
        self.scale_factor = new_scale
        
        # 1. 缩放字体
        for name, font_obj in self.fonts.items():
            new_size = int(self.base_font_sizes[name] * self.scale_factor)
            font_obj.configure(size=new_size)
            
        # 2. 缩放自定义组件 (Canvas)
        for w in self.scalable_widgets:
            if isinstance(w, ModernButton):
                w.padding_x = int(w.base_padding_x * self.scale_factor)
                w.padding_y = int(w.base_padding_y * self.scale_factor)
                w.recalculate_size()
            elif isinstance(w, CircularProgress):
                w.recalculate_size(self.scale_factor)
                
        # 3. 缩放侧边栏
        self.sidebar.config(width=int(self.base_sidebar_width * self.scale_factor))
        
        # 4. 动态调整最小窗口尺寸并强制收缩窗口
        new_min_w = int(self.base_minsize[0] * self.scale_factor)
        new_min_h = int(self.base_minsize[1] * self.scale_factor)
        self.root.minsize(new_min_w, new_min_h)
        
        # 当缩小时，如果当前窗口大小大于需要的最小尺寸，让窗口也跟着缩小回退
        # 放大时，如果当前窗口小于最小尺寸，它会自动被 minsize 推大
        current_w = self.root.winfo_width()
        current_h = self.root.winfo_height()
        
        # 这里的策略是：
        # 如果是缩小 (delta < 0)，强制重置窗口大小以收缩
        # 如果是放大 (delta > 0)，只设置 minsize 即可，窗口会被内容自动撑大，
        # 避免全屏或自由拉伸的窗口在放大时被重置回较小的尺寸
        if delta < 0:
            self.root.geometry(f"{new_min_w}x{new_min_h}")
        else:
            if current_w < new_min_w or current_h < new_min_h:
                self.root.geometry(f"{max(current_w, new_min_w)}x{max(current_h, new_min_h)}")

    def zoom_reset(self):
        self.zoom(1.0 - self.scale_factor)

    def browse_file(self):
        # 使用 macOS 原生调用或 tkinter 的原生封装
        filepath = filedialog.askopenfilename(
            title="选择 Excel 文件",
            filetypes=[("Excel 文件", "*.xlsx *.xls")]
        )
        if filepath:
            self.file_path_var.set(filepath)
            self.load_sheets(filepath)
            
    def load_sheets(self, filepath):
        try:
            wb = openpyxl.load_workbook(filepath, read_only=True, keep_links=False)
            sheet_names = wb.sheetnames
            self.sheet_cb['values'] = sheet_names
            if sheet_names:
                self.sheet_cb.current(0)
            wb.close()
        except Exception as e:
            messagebox.showerror("错误", f"读取工作表失败: {e}")
            
    def open_dict(self):
        dict_dir = os.path.expanduser('~/Library/Application Support/ExcelIntelligentTranslator')
        if not os.path.exists(dict_dir):
            os.makedirs(dict_dir, exist_ok=True)
            # Create a default empty dictionary file to avoid empty folder confusion
            dict_file = os.path.join(dict_dir, 'local_dict_mapping.txt')
            if not os.path.exists(dict_file):
                with open(dict_file, 'w', encoding='utf-8') as f:
                    f.write('# 本地术语对照字典\n')
        
        os.system(f"open '{dict_dir}'")
        
    def open_translated_file(self):
        if self.last_test_file and os.path.exists(self.last_test_file):
            os.system(f"open '{self.last_test_file}'")
            
    def open_file_dir(self):
        if self.last_test_file:
            dir_path = os.path.dirname(self.last_test_file)
            if os.path.exists(dir_path):
                os.system(f"open '{dir_path}'")
        
    def update_timer(self):
        if self.is_running:
            elapsed = time.time() - self.start_time
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            self.time_label.config(text=f"已耗时: {mins:02d}:{secs:02d}")
            self.root.after(1000, self.update_timer)
            
    def run_translation(self):
        original_file = self.file_path_var.get()
        sheet_name = self.sheet_var.get()
        mode_display = self.mode_var.get()
        mode = self.mode_map.get(mode_display, "zh_to_en_bilingual")
        
        if not original_file:
            messagebox.showwarning("警告", "请先选择一个 Excel 文件。")
            return
            
        # 自动切换到 Console 标签
        self.show_frame(self.console_frame)
        self.console_text.delete(1.0, tk.END)
        self.progress_var.set(0)
        for widget in self.metrics_widgets.values():
            widget.set_value(0, 100)
            
        for stage, lbl in self.status_lights.items():
            lbl.config(text=f"⚪️ {stage}", fg="#86868B")
            
        self.current_stage = None
        self.open_file_btn.config_state(tk.DISABLED)
        self.open_dir_btn.config_state(tk.DISABLED)
        
        self.run_btn.config_state(tk.DISABLED)
        
        # 构造测试文件名
        dir_name, file_name = os.path.split(original_file)
        name, ext = os.path.splitext(file_name)
        test_file = os.path.join(dir_name, f"{name}_test_{mode}{ext}")
        self.last_test_file = test_file
        
        self.is_running = True
        self.start_time = time.time()
        self.update_timer()
        
        thread = threading.Thread(
            target=self._run_pipeline_thread,
            args=(original_file, test_file, sheet_name, mode),
            daemon=True
        )
        thread.start()
        
    def _run_pipeline_thread(self, original_file, test_file, sheet_name, mode):
        try:
            run_pipeline(original_file, test_file, sheet_name, mode)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"\n❌ Pipeline 执行失败: {e}")
        finally:
            def restore_ui():
                self.run_btn.config_state(tk.NORMAL)
                self.is_running = False
            self.root.after(0, restore_ui)
            
    def check_queue(self):
        while not self.msg_queue.empty():
            msg = self.msg_queue.get()
            self._process_log_message(msg)
        self.root.after(100, self.check_queue)
        
    def _process_log_message(self, msg):
        # 去除 ANSI 颜色代码
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_msg = ansi_escape.sub('', msg)
        
        # 检查滚动条位置（在插入前）
        at_bottom = self.console_text.yview()[1] >= 0.99 or self.console_text.index("end-1c") == "1.0"
        
        # 处理 \r
        while '\r' in clean_msg:
            idx = clean_msg.find('\r')
            before = clean_msg[:idx]
            after = clean_msg[idx+1:]
            
            if before:
                self.console_text.insert(tk.END, before)
                
            # 删除当前最后一行
            self.console_text.delete("end-1c linestart", "end-1c")
            clean_msg = after
            
        if clean_msg:
            self.console_text.insert(tk.END, clean_msg)
            
        # 提取指标
        if "需要调用 LLM 的去重文本数量:" in clean_msg:
            match = re.search(r"需要调用 LLM 的去重文本数量:\s*(\d+)", clean_msg)
            if match:
                val = int(match.group(1))
                self.metrics_widgets["待翻译词条"].set_value(val, max_value=val)
                
        if "本地字典命中 (LOCAL_DICT_HIT)" in clean_msg:
            match = re.search(r"本地字典命中 \(LOCAL_DICT_HIT\)\s*:\s*(\d+)", clean_msg)
            if match:
                val = int(match.group(1))
                total = self.metrics_widgets["待翻译词条"].value
                self.metrics_widgets["字典命中"].set_value(val, max_value=total if total > 0 else 100)
                
        if "成功更新" in clean_msg and "个单元格" in clean_msg:
            match = re.search(r"成功更新\s*(\d+)\s*个单元格", clean_msg)
            if match:
                val = int(match.group(1))
                total = self.metrics_widgets["待翻译词条"].value
                self.metrics_widgets["成功写入"].set_value(val, max_value=total if total > 0 else 100)
                
        # 更新进度条和状态灯
        if "[防呆机制]" in clean_msg:
            self.progress_var.set(10)
            self.current_stage = "生成副本"
            self.status_lights["生成副本"].config(text="🟡 生成副本", fg="#FFCC00")
        elif "[数据读取]" in clean_msg:
            self.progress_var.set(30)
            if getattr(self, 'current_stage', None) == "生成副本":
                self.status_lights["生成副本"].config(text="🟢 生成副本", fg="#34C759")
            self.current_stage = "读取Excel"
            self.status_lights["读取Excel"].config(text="🟡 读取Excel", fg="#FFCC00")
        elif "[核心分发]" in clean_msg:
            self.progress_var.set(50)
            if getattr(self, 'current_stage', None) == "读取Excel":
                self.status_lights["读取Excel"].config(text="🟢 读取Excel", fg="#34C759")
            self.current_stage = "核心分发"
            self.status_lights["核心分发"].config(text="🟡 核心分发", fg="#FFCC00")
        elif "需要调用 LLM" in clean_msg:
            self.progress_var.set(70)
            if getattr(self, 'current_stage', None) == "核心分发":
                self.status_lights["核心分发"].config(text="🟢 核心分发", fg="#34C759")
            self.current_stage = "大模型翻译"
            self.status_lights["大模型翻译"].config(text="🟡 大模型翻译", fg="#FFCC00")
        elif "[底层写入]" in clean_msg:
            self.progress_var.set(90)
            if getattr(self, 'current_stage', None) == "大模型翻译":
                self.status_lights["大模型翻译"].config(text="🟢 大模型翻译", fg="#34C759")
            self.current_stage = "底层写入"
            self.status_lights["底层写入"].config(text="🟡 底层写入", fg="#FFCC00")
        elif "执行完成！" in clean_msg:
            self.progress_var.set(100)
            if getattr(self, 'current_stage', None) == "底层写入":
                self.status_lights["底层写入"].config(text="🟢 底层写入", fg="#34C759")
            self.current_stage = "任务完成"
            self.status_lights["任务完成"].config(text="🟢 任务完成", fg="#34C759")
            self.is_running = False
            self.open_file_btn.config_state(tk.NORMAL)
            self.open_dir_btn.config_state(tk.NORMAL)
        elif "❌" in clean_msg or "失败" in clean_msg or "错误" in clean_msg:
            if getattr(self, 'current_stage', None):
                self.status_lights[self.current_stage].config(text=f"🟡 {self.current_stage}(报错)", fg="#FFCC00")
            self.is_running = False
            self.open_file_btn.config_state(tk.NORMAL)
            self.open_dir_btn.config_state(tk.NORMAL)
            
        # 智能滚动：只有当垂直滚动条 >= 0.99 时才滚动到底部
        if at_bottom:
            self.console_text.see(tk.END)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()
