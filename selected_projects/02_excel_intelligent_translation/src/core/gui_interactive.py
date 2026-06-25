import os
import sys
import subprocess

try:
    import tkinter as tk
    from tkinter import filedialog, ttk
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

# Fallback to openpyxl for silent sheet reading
try:
    import openpyxl
except ImportError:
    openpyxl = None

def select_excel_file() -> str:
    """
    弹出原生文件选择对话框，让用户选择 Excel 文件。
    返回绝对路径，如果取消则返回 None。
    """
    if HAS_TKINTER:
        root = tk.Tk()
        root.withdraw() # 隐藏主窗口
        root.attributes('-topmost', True) # 强制前置，特别是在 macOS 上
        
        file_path = filedialog.askopenfilename(
            title="请选择待翻译的 Excel 文件",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        
        root.destroy()
        return file_path if file_path else None
    else:
        # Fallback 1: macOS AppleScript
        if sys.platform == "darwin":
            try:
                cmd = ['osascript', '-e', 'POSIX path of (choose file with prompt "请选择待翻译的 Excel 文件" of type {"public.spreadsheet", "org.openxmlformats.spreadsheetml.sheet", "com.microsoft.excel.xls"})']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            except Exception:
                pass
        
        # Fallback 2: Terminal Input
        print("⚠️ 缺少 tkinter 模块，无法启动 GUI。请执行: brew install python-tk@3.14")
        user_input = input("请输入 Excel 文件的绝对路径 (或输入 q 退出): ").strip()
        if user_input.lower() == 'q' or not user_input:
            return None
        return user_input.replace('\\', '').strip('\'"')

def select_sheet(file_path: str) -> str:
    """
    静默读取 Excel 文件的所有工作表，并弹出带下拉菜单的对话框供用户选择。
    返回选择的工作表名称，如果取消则返回 None。
    """
    if not os.path.exists(file_path):
        return None
        
    sheet_names = []
    
    # 尝试使用 openpyxl 极速静默读取（仅支持 xlsx）
    if openpyxl and file_path.endswith('.xlsx'):
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True)
            sheet_names = wb.sheetnames
            wb.close()
        except Exception as e:
            print(f"openpyxl 读取工作表失败: {e}")
    
    # 如果 openpyxl 失败或不支持，使用 xlwings
    if not sheet_names:
        import xlwings as xw
        try:
            app = xw.App(visible=False, add_book=False)
            wb = app.books.open(file_path)
            sheet_names = [s.name for s in wb.sheets]
            wb.close()
            app.quit()
        except Exception as e:
            print(f"xlwings 读取工作表失败: {e}")
            try:
                app.quit()
            except:
                pass
            return None
            
    if not sheet_names:
        return None
        
    if not HAS_TKINTER:
        # Fallback to Terminal Input
        print("\n=== 请选择工作表 ===")
        for i, name in enumerate(sheet_names):
            print(f"[{i+1}] {name}")
            
        while True:
            try:
                user_input = input(f"请输入工作表序号 (1-{len(sheet_names)}) 或直接输入表名 (q退出): ").strip()
                if user_input.lower() == 'q' or not user_input:
                    return None
                    
                if user_input.isdigit():
                    idx = int(user_input) - 1
                    if 0 <= idx < len(sheet_names):
                        return sheet_names[idx]
                elif user_input in sheet_names:
                    return user_input
                print("输入无效，请重试。")
            except Exception:
                pass
                
    # 构建 UI
    root = tk.Tk()
    root.title("选择工作表")
    
    # 调整大小，适配 macOS 缩放
    root.geometry("400x160")
    
    # 将窗口居中
    root.eval('tk::PlaceWindow . center')
    root.attributes('-topmost', True)
    
    selected_sheet = tk.StringVar()
    
    # 标签
    tk.Label(root, text="请选择需要翻译的工作表：", font=("Arial", 14)).pack(pady=15)
    
    # 下拉菜单
    cb = ttk.Combobox(root, textvariable=selected_sheet, values=sheet_names, state="readonly", width=30)
    
    # 默认选中“TEST”相关表或第一张表
    default_idx = 0
    for i, name in enumerate(sheet_names):
        if "TEST" in name.upper() and not name.startswith("000"):
            default_idx = i
            break
            
    cb.current(default_idx)
    cb.pack(pady=5)
    
    result = {"sheet": None}
    
    def on_confirm():
        result["sheet"] = selected_sheet.get()
        root.quit()
        
    def on_cancel():
        root.quit()
        
    # 按钮框
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=15)
    
    tk.Button(btn_frame, text="确认", command=on_confirm, width=10, bg="#4CAF50", fg="black").pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="取消", command=on_cancel, width=10).pack(side=tk.LEFT, padx=10)
    
    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.mainloop()
    
    sheet_name = result["sheet"]
    root.destroy()
    return sheet_name
