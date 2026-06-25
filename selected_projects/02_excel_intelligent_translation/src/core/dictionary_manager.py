import os
import re
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

def load_local_dictionary():
    """
    加载本地词典。
    字典格式为：中文 = 英文
    如果目录或文件不存在，则自动创建并初始化。
    返回两个字典：
      1. zh_to_en_norm: { normalize(中文): 英文 }
      2. en_to_zh_norm: { normalize(英文): 中文 }
    """
    dict_dir = os.path.expanduser("~/Library/Application Support/ExcelIntelligentTranslator")
    os.makedirs(dict_dir, exist_ok=True)
    dict_path = os.path.join(dict_dir, "local_dict_mapping.txt")
    
    if not os.path.exists(dict_path):
        print(f"  [初始化] 本地字典不存在，正在创建: {dict_path}")
        with open(dict_path, "w", encoding="utf-8") as f:
            f.write("# 本地术语对照字典\n")
            f.write("# 格式: 中文 = 英文\n")

    local_dict = {}
    normalized_dict = {}
    
    try:
        with open(dict_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    # 避免截断值里的 = 号，只分割第一个 =
                    parts = line.split("=", 1)
                    if len(parts) >= 2:
                        original = parts[0].strip().replace('\\n', '\n')
                        translated = parts[1].strip().replace('\\n', '\n')
                        local_dict[original] = translated
                        normalized_dict[normalize_text(original)] = translated
        print(f"✅ 成功加载本地字典，共包含 {len(local_dict)} 条词条对照。")
    except Exception as e:
        print(f"⚠️ 加载本地字典时发生错误: {e}")
        
    return local_dict, normalized_dict

def append_to_local_dictionary(new_mappings: dict, existing_keys: set, normalized_existing_keys: set, dict_path: str, mode: str):
    """
    将大模型翻译的新词汇批量追加到本地字典
    """
    if not new_mappings:
        return 0
        
    added_count = 0
    try:
        with open(dict_path, "a", encoding="utf-8") as f:
            for original, translated in new_mappings.items():
                clean_key = original.strip().replace('\n', '\\n').replace('\r', '')
                clean_val = translated.strip().replace('\n', '\\n').replace('\r', '')
                
                # 双语模式下的反转或去重
                if mode == "en_to_zh":
                    clean_key, clean_val = clean_val, clean_key
                    
                if not clean_key or not clean_val:
                    continue
                if clean_key == clean_val:
                    continue
                if clean_key in existing_keys or normalize_text(clean_key) in normalized_existing_keys:
                    continue
                    
                # 防呆：字典里不能进动态参数
                if is_dynamic_parameter(clean_key):
                    continue
                    
                f.write(f"{clean_key} = {clean_val}\n")
                added_count += 1
                
        if added_count > 0:
            print(f"  [字典更新] 成功向本地字典追加了 {added_count} 个新词条。")
    except Exception as e:
        print(f"  ⚠️ 写入本地字典失败: {e}")
        
    return added_count
