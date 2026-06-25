import os
import sys

# 将当前目录加入路径，以保证能正确引入 core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.pipeline import run_pipeline

if __name__ == "__main__":
    # 项目根目录 (src/ 的上一级)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    mode = "zh_to_en_bilingual"
    
    # 模拟从 GUI 或外部传入的参数
    if mode in ["zh_to_en", "zh_to_en_bilingual"]:
        original_file = os.path.join(project_root, "data", "original_excel_doc", "L4NHS013-QT-R 检验规范(SIP).xlsx")
        test_file = os.path.join(project_root, "data", "original_excel_doc", f"L4NHS013-QT-R 检验规范(SIP)_test_{mode}.xlsx")
    else:
        original_file = os.path.join(project_root, "data", "original_excel_doc", "英文模板.xlsx")
        test_file = os.path.join(project_root, "data", "original_excel_doc", f"英文模板_test_{mode}.xlsx")
        
    print(f"正在以终端模式启动 (目标文件: {os.path.basename(original_file)})...")
    
    # 调用拆分后的核心流水线，支持接收 explicit file paths 和 sheet_name
    run_pipeline(
        original_file=original_file,
        test_file=test_file,
        sheet_name=None,  # 传入 None 将触发内部寻找 TEST 名字的工作表或第一张表
        mode=mode
    )
