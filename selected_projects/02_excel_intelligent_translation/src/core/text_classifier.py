import re

def contains_chinese(text: str) -> bool:
    """判断是否包含中文字符"""
    if not text or not isinstance(text, str):
        return False
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def is_part_number_or_value(text: str) -> bool:
    """
    判断是否为工程料号、纯数字、尺寸公差、日期/页码值等不需要翻译的文本
    例如：'L6TCP010-DT-R', 'CW-9061037-WW', '10.5±0.1', '1/4', '2024/08/13'
    """
    # 如果是纯数字或只包含数字和标点符号（包含冒号、斜杠等）
    if re.fullmatch(r'^[0-9\.\-\+±,<>%\s/\\*:]+$', text):
        return True
        
    # 如果没有小写字母且没有空格（很可能是料号或大写缩写）
    if not re.search(r'[a-z]', text) and ' ' not in text:
        return True
        
    # 长度很短且没有空格（可能是简单的代号）
    if len(text) <= 15 and ' ' not in text:
        if not re.search(r'[a-z]', text):
            return True
            
    return False

def is_dynamic_parameter(text: str) -> bool:
    """
    判断是否为动态参数组合或纯符号组合，这类数据即使包含中文需要翻译，
    也因为缺乏跨项目复用价值，不应参与字典匹配和字典录入。
    例如：'L≤2.3mm,允许2处', '目视/塞尺', '装零件包2', '页码 1/4'
    注：冒号 (:) 的拆分已在外部通过 re.split 解决，因此这里不用考虑带冒号的组合词条。
    """
    # 包含数字（如 "装零件包2", "允许2处"）
    if re.search(r'\d', text):
        return True
    # 包含数学符号或特殊分隔符（如 "≤", "/"）
    if re.search(r'[≤≥±<>/\\]', text):
        return True
    # 包含孤立的残缺括号（如末尾的 "(" 或 "（"）
    if re.search(r'[\(（]$', text.strip()):
        return True
    return False

def classify_text(text: str) -> str:
    """
    文本分类器：
    包含中文 -> TRANSLATE_CHINESE
    不包含中文，但包含英文字母且不是料号 -> TRANSLATE_ENGLISH
    否则 -> KEEP_ORIGINAL
    """
    if not text or not isinstance(text, str):
        return "EMPTY/INVALID"
    
    text = str(text).strip()
    if not text:
        return "EMPTY/INVALID"

    if contains_chinese(text):
        return "TRANSLATE_CHINESE"
        
    if re.search(r'[A-Za-z]', text):
        if is_part_number_or_value(text):
            return "KEEP_ORIGINAL"
        else:
            return "TRANSLATE_ENGLISH"
    
    return "KEEP_ORIGINAL"
