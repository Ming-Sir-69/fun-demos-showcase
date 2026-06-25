import os
import re
import sys

# 把 src 加入 PYTHONPATH 以便能够 import core
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(project_root, "src"))

from core.text_classifier import is_dynamic_parameter

def normalize_text(text: str) -> str:
    """
    归一化文本：全角转半角，移除所有空白字符，转小写。
    用于在字典匹配时忽略中英文符号、括号、空格差异。
    """
    result = ""
    for char in text:
        code = ord(char)
        if 0xFF01 <= code <= 0xFF5E:
            result += chr(code - 0xFEE0)
        elif code == 0x3000:
            result += " "
        else:
            result += char
    result = re.sub(r'\s+', '', result)
    return result.lower()

def cleanup_local_dictionary(dict_path: str):
    """
    对本地字典进行全量归一化整理去重。
    保留格式最标准的记录，剔除所有归一化后重复的冗余词条（如全半角、空格差异）。
    """
    if not os.path.exists(dict_path):
        print(f"❌ 字典文件 {dict_path} 不存在。")
        return

    # 用于保存最终写入的纯净行
    cleaned_lines = []
    
    # 用于记录归一化特征，防止重复 (Normalized Key -> (Original Key, Translated Value))
    seen_normalized = {}
    
    # 统计数据
    total_lines = 0
    duplicate_count = 0
    
    try:
        with open(dict_path, "r", encoding="utf-8") as f:
            for line in f:
                original_line = line
                line = line.strip()
                
                # 保留空行和注释行（保持原有结构）
                if not line or line.startswith("#"):
                    cleaned_lines.append(original_line)
                    continue
                    
                if "=" in line:
                    total_lines += 1
                    parts = line.split("=", 1)
                    if len(parts) >= 2:
                        original_key = parts[0].strip().replace('\\n', '\n')
                        translated_val = parts[1].strip().replace('\\n', '\n')
                        
                        # 特殊防呆1：排除大模型原样返回的废数据（中英文完全一样）
                        if original_key == translated_val:
                            duplicate_count += 1
                            print(f"🗑️ 剔除原样返回废数据: {original_key}")
                            continue
                            
                        # 特殊防呆2：排除包含纯符号/数学参数类、数字、冒号、残缺括号的动态词条
                        # 这与 text_classifier.py 中的 is_dynamic_parameter 保持同步，并额外剔除带冒号的历史组合词条
                        if re.search(r'[≤≥±<>/\\]', original_key) or \
                           re.search(r'\d', original_key) or \
                           re.search(r'[:：]', original_key) or \
                           re.search(r'[\(（]$', original_key.strip()):
                            duplicate_count += 1
                            print(f"🗑️ 剔除无复用价值动态/组合词条: {original_key}")
                            continue
                            
                        # 计算归一化特征
                        norm_key = normalize_text(original_key)
                        
                        if norm_key in seen_normalized:
                            duplicate_count += 1
                            prev_original, prev_translated = seen_normalized[norm_key]
                            print(f"🗑️ 剔除归一化重复项:\n   保留: [{prev_original}] = [{prev_translated}]\n   剔除: [{original_key}] = [{translated_val}]\n")
                        else:
                            seen_normalized[norm_key] = (original_key, translated_val)
                            cleaned_lines.append(original_line)
                else:
                    cleaned_lines.append(original_line)

        # 回写清理后的纯净字典
        with open(dict_path, "w", encoding="utf-8") as f:
            for line in cleaned_lines:
                f.write(line)
                
        print(f"\n✅ 字典清洗完成！")
        print(f"   - 扫描词条总数: {total_lines}")
        print(f"   - 剔除冗余/废词: {duplicate_count}")
        print(f"   - 最终保留词条: {len(seen_normalized)}")
        
    except Exception as e:
        print(f"❌ 清理字典时发生错误: {e}")

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dict_path = os.path.join(project_root, "data", "dictionary", "local_dict_mapping.txt")
    cleanup_local_dictionary(dict_path)