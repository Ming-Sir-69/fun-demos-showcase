import os
import sys
import time
import shutil
import re

# 兼容 Python 3.14 下 xlwings/appscript 的 pth 路径问题
if sys.platform.startswith("darwin"):
    aeosa_path = os.path.join(sys.prefix, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages", "aeosa")
    if os.path.exists(aeosa_path) and aeosa_path not in sys.path:
        sys.path.append(aeosa_path)

import xlwings as xw

from core.text_classifier import classify_text
from core.llm_translator import batch_translate
from core.dictionary_manager import normalize_text, load_local_dictionary, append_to_local_dictionary
from utils.timer import StageTimer

def run_pipeline(original_file: str, test_file: str, sheet_name: str = None, mode: str = "zh_to_en_bilingual"):
    """
    核心执行流水线，接收明确的文件路径和工作表参数，不再硬编码。
    """
    start_time = time.time()
    
    valid_modes = ["zh_to_en", "en_to_zh", "zh_to_en_bilingual", "en_to_zh_bilingual"]
    if mode not in valid_modes:
        print(f"❌ 错误：不支持的模式 '{mode}'。请从 {valid_modes} 中选择。")
        return

    print(f"1. [防呆机制] 生成测试副本 (模式: {mode})...")
    with StageTimer("副本生成中...") as st_copy:
        shutil.copy2(original_file, test_file)
        abs_path = os.path.abspath(test_file)
    t_copy_time = st_copy.end_time - st_copy.start_time

    # 加载本地字典
    local_dict, normalized_dict = load_local_dictionary()

    print("2. [数据读取] 使用 xlwings 进行扫描...")
    app = xw.App(visible=False, add_book=False)
    
    # 声明耗时变量防止异常跳过未定义
    t_read_time = 0.0
    t_route_time = 0.0
    t_llm_time = 0.0
    t_write_time = 0.0
    total_cells_in_range = 0
    stats = {
        "TRANSLATE_CHINESE": 0,
        "TRANSLATE_ENGLISH": 0,
        "KEEP_ORIGINAL": 0,
        "EMPTY/INVALID": 0,
        "LOCAL_DICT_HIT": 0,
        "NEW_DICT_ENTRIES": 0
    }
    
    try:
        with StageTimer("Excel 读取中...") as st_read:
            wb = app.books.open(abs_path)
            
            # 优先根据传入的 sheet_name 匹配，若未传或没找到则尝试找 TEST 表，否则取第一张
            if sheet_name:
                try:
                    sheet = wb.sheets[sheet_name]
                except Exception:
                    sheet = wb.sheets[0]
            else:
                test_sheets = [s for s in wb.sheets if "TEST" in s.name.upper() and not s.name.startswith("000")]
                sheet = test_sheets[0] if test_sheets else wb.sheets[0]
                
            print(f"正在处理工作表: {sheet.name}")
            
            used_range = sheet.used_range
            print(f"全篇测试模式，扫描整个工作表数据范围: {used_range.address}")
            total_cells_in_range = used_range.shape[0] * used_range.shape[1] if used_range.shape else 0
            
            all_values = used_range.value
        t_read_time = st_read.end_time - st_read.start_time
        
        texts_to_translate = []
        cell_mapping = []
        pre_translation_results = {}
        
        print("3. [核心分发] 开始经过文本分类器路由 (Text Classifier)...")
        with StageTimer("路由与去重中...") as st_route:
            if not isinstance(all_values, list):
                all_values = [[all_values]]
            elif len(all_values) > 0 and not isinstance(all_values[0], list):
                if used_range.shape[0] == 1:
                    all_values = [all_values]
                else:
                    all_values = [[v] for v in all_values]
                
            seen_texts = set()
                
            # 扫描 1: 常规单元格数据
            for row_idx, row in enumerate(all_values):
                for col_idx, val in enumerate(row):
                    if val is not None and str(val).strip() != "":
                        cell = used_range[row_idx, col_idx]
                        original_val = str(val)
                        
                        parts = re.split(r'( {2,}|\t+)', original_val)
                        cell_text_chunks = []
                        for i, part in enumerate(parts):
                            if i % 2 == 1:
                                cell_text_chunks.append({"type": "space", "text": part})
                            else:
                                text_val = part.strip()
                                if not text_val:
                                    cell_text_chunks.append({"type": "text", "original": part, "translated": part})
                                    continue
                                    
                                text_type = classify_text(text_val)
                                stats[text_type] += 1
                                
                                if text_type in ["TRANSLATE_CHINESE", "TRANSLATE_ENGLISH"]:
                                    if (mode in ["zh_to_en", "zh_to_en_bilingual"] and text_type == "TRANSLATE_CHINESE") or \
                                       (mode in ["en_to_zh", "en_to_zh_bilingual"] and text_type == "TRANSLATE_ENGLISH"):
                                        
                                        norm_val = normalize_text(text_val)
                                        if norm_val in normalized_dict:
                                            stats["LOCAL_DICT_HIT"] += 1
                                            translated = normalized_dict[norm_val]
                                            cell_text_chunks.append({"type": "text", "original": part, "translated": translated})
                                        else:
                                            cell_text_chunks.append({"type": "text", "original": part, "needs_llm": True, "text_val": text_val, "text_type": text_type})
                                            if text_val not in seen_texts:
                                                seen_texts.add(text_val)
                                                texts_to_translate.append((text_val, text_type))
                                    else:
                                        cell_text_chunks.append({"type": "text", "original": part, "translated": part})
                                else:
                                    cell_text_chunks.append({"type": "text", "original": part, "translated": part})
                                    
                        cell_mapping.append({
                            "cell": cell,
                            "original_val": original_val,
                            "chunks": cell_text_chunks
                        })

            # 扫描 2: 浮动文本框/形状 (Shapes)
            print(f"正在扫描工作表中的文字框图(Shapes)... 共发现 {len(sheet.shapes)} 个图形。")
            for shape in sheet.shapes:
                try:
                    shape_text = shape.text
                    if shape_text and str(shape_text).strip() != "":
                        original_val = str(shape_text)
                        parts = re.split(r'( {2,}|\t+)', original_val)
                        cell_text_chunks = []
                        for i, part in enumerate(parts):
                            if i % 2 == 1:
                                cell_text_chunks.append({"type": "space", "text": part})
                            else:
                                text_val = part.strip()
                                if not text_val:
                                    cell_text_chunks.append({"type": "text", "original": part, "translated": part})
                                    continue
                                    
                                text_type = classify_text(text_val)
                                stats[text_type] += 1
                                
                                if text_type in ["TRANSLATE_CHINESE", "TRANSLATE_ENGLISH"]:
                                    if (mode in ["zh_to_en", "zh_to_en_bilingual"] and text_type == "TRANSLATE_CHINESE") or \
                                       (mode in ["en_to_zh", "en_to_zh_bilingual"] and text_type == "TRANSLATE_ENGLISH"):
                                        
                                        norm_val = normalize_text(text_val)
                                        if norm_val in normalized_dict:
                                            stats["LOCAL_DICT_HIT"] += 1
                                            translated = normalized_dict[norm_val]
                                            cell_text_chunks.append({"type": "text", "original": part, "translated": translated})
                                        else:
                                            cell_text_chunks.append({"type": "text", "original": part, "needs_llm": True, "text_val": text_val, "text_type": text_type})
                                            if text_val not in seen_texts:
                                                seen_texts.add(text_val)
                                                texts_to_translate.append((text_val, text_type))
                                    else:
                                        cell_text_chunks.append({"type": "text", "original": part, "translated": part})
                                else:
                                    cell_text_chunks.append({"type": "text", "original": part, "translated": part})
                                    
                        cell_mapping.append({
                            "cell": shape,
                            "original_val": original_val,
                            "chunks": cell_text_chunks
                        })
                except Exception:
                    pass
        t_route_time = st_route.end_time - st_route.start_time
        print(f"\n需要调用 LLM 的去重文本数量: {len(texts_to_translate)}")
        
        t_llm_start = time.time()
        if texts_to_translate:
            glossary = {k: v for k, v in local_dict.items() if len(k) <= 15 and "\\n" not in k and "■" not in k}
            translation_results = batch_translate(texts_to_translate, mode=mode, glossary=glossary)
        else:
            translation_results = {}
        translation_results.update(pre_translation_results)
        
        if texts_to_translate:
            existing_keys = set(local_dict.keys())
            normalized_existing_keys = set(normalized_dict.keys())
            dict_path = os.path.join(os.path.expanduser("~/Library/Application Support/ExcelIntelligentTranslator"), "local_dict_mapping.txt")
            stats["NEW_DICT_ENTRIES"] = append_to_local_dictionary(
                new_mappings={k: v for k, v in translation_results.items() if k not in existing_keys},
                existing_keys=existing_keys,
                normalized_existing_keys=normalized_existing_keys,
                dict_path=dict_path,
                mode=mode
            )
            
        t_llm_time = time.time() - t_llm_start
        
        print("\n4. [底层写入] 组装并写入 Excel...")
        with StageTimer("Excel 单元格写入中...") as st_write:
            updates_count = 0
            for item in cell_mapping:
                cell = item["cell"]
                original_val = item["original_val"]
                chunks = item["chunks"]
                
                translated_parts = []
                has_translation = False
                
                for chunk in chunks:
                    if chunk["type"] == "space":
                        translated_parts.append(chunk["text"])
                    else:
                        if "translated" in chunk:
                            trans = chunk["translated"]
                        else:
                            text_val = chunk.get("text_val", "")
                            trans = translation_results.get(text_val, chunk["original"])
                        
                        if trans != chunk["original"] and not str(trans).startswith("[Translation Failed"):
                            has_translation = True
                            
                        original_chunk_text = chunk["original"]
                        if trans == original_chunk_text:
                            translated_parts.append(original_chunk_text)
                        else:
                            leading_spaces = len(original_chunk_text) - len(original_chunk_text.lstrip())
                            trailing_spaces = len(original_chunk_text) - len(original_chunk_text.rstrip())
                            prefix = original_chunk_text[:leading_spaces]
                            suffix = original_chunk_text[len(original_chunk_text) - trailing_spaces:] if trailing_spaces > 0 else ""
                            translated_parts.append(f"{prefix}{trans}{suffix}")

                en_val = "".join(translated_parts)

                if has_translation and en_val != original_val:
                    if mode == "zh_to_en":
                        final_val = en_val
                    elif mode == "en_to_zh":
                        final_val = en_val
                    elif mode == "zh_to_en_bilingual":
                        final_val = f"{original_val}\n{en_val}"
                    elif mode == "en_to_zh_bilingual":
                        final_val = f"{en_val}\n{original_val}"
                    else:
                        final_val = en_val
                    
                    if isinstance(cell, xw.Shape):
                        cell.text = final_val
                    else:
                        cell.value = final_val
                        try:
                            if sys.platform == "darwin":
                                cell.api.wrap_text.set(True)
                            else:
                                cell.api.WrapText = True
                        except Exception:
                            pass
                    updates_count += 1
    
            if updates_count == 0:
                print("\n未发现有效翻译内容，无需更新 Excel。")
            else:
                print(f"\n✅ 成功更新 {updates_count} 个单元格。")
                
            try:
                # 强制将焦点重置到 A1 单元格
                sheet.range('A1').select()
            except Exception as e:
                print(f"⚠️ 焦点重置到 A1 失败: {e}")
                
            wb.save()
        t_write_time = st_write.end_time - st_write.start_time
    except Exception as e:
        print(f"\n❌ 处理过程中出现异常: {e}")
    finally:
        try:
            wb.close()
        except:
            pass
        app.quit()
        
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print("\n--- 整合执行报告 ---")
    print(f"\n✅ 执行完成！文件已保存: {os.path.basename(test_file)}")
    print(f"⏱️ 任务总耗时: {minutes}分 {seconds}秒 ({elapsed_time:.2f}s)")
    
    print("核心阶段耗时分布:")
    print(f"   - 1. 副本生成: {t_copy_time:.2f}s")
    print(f"   - 2. Excel读: {t_read_time:.2f}s")
    print(f"   - 3. 路由与去重: {t_route_time:.2f}s")
    print(f"   - 4. LLM翻译: {t_llm_time:.2f}s")
    print(f"   - 5. Excel写: {t_write_time:.2f}s")

    print("\n数据处理规模与拦截统计:")
    print(f"   - 扫描总单元格数                  : {total_cells_in_range} 个")
    print(f"   - 本地字典命中 (LOCAL_DICT_HIT)   : {stats.get('LOCAL_DICT_HIT', 0)} 个")
    print(f"   - 需翻译中文 (TRANSLATE_CHINESE)  : {stats['TRANSLATE_CHINESE']} 个")
    print(f"   - 需翻译英文 (TRANSLATE_ENGLISH)  : {stats['TRANSLATE_ENGLISH']} 个")
    print(f"   - 保留原文 (KEEP_ORIGINAL)        : {stats['KEEP_ORIGINAL']} 个")
    print(f"   - 空白无效 (EMPTY/INVALID)        : {stats['EMPTY/INVALID']} 个")
    print(f"   - 字典新收录 (NEW_DICT_ENTRIES)   : {stats.get('NEW_DICT_ENTRIES', 0)} 个")
