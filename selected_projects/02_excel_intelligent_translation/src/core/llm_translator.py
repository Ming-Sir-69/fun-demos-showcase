import sys
import time
import json
import re
import threading
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from abc import ABC, abstractmethod
from core.prompts import ZH_TO_EN_PROMPT, EN_TO_ZH_PROMPT

def live_timer(stop_event: threading.Event, prefix_msg: str, start_time: float):
    """后台计时器线程，用于在终端实时刷新耗时，精度 0.01s，刷新率 20Hz"""
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        sys.stdout.write(f"\r\033[K{prefix_msg} [{elapsed:.2f}s]")
        sys.stdout.flush()
        time.sleep(0.05)
    sys.stdout.write("\n")
    sys.stdout.flush()

class StageTimer:
    """阶段计时器上下文管理器"""
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.stop_event = threading.Event()
        self.thread = None
        self.start_time = 0
        self.end_time = 0

    def __enter__(self):
        self.start_time = time.time()
        self.thread = threading.Thread(target=live_timer, args=(self.stop_event, self.stage_name, self.start_time), daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time
        if exc_type is None:
            # 成功时打印带耗时的绿色标记
            sys.stdout.write(f"\033[F\033[K  ✅ {self.stage_name} 成功 (耗时 {elapsed:.2f}s)\n")
        else:
            # 失败时打印红色标记
            sys.stdout.write(f"\033[F\033[K  ❌ {self.stage_name} 失败 (耗时 {elapsed:.2f}s)\n")
        sys.stdout.flush()

# 动态 LLM API 配置
LLM_CONFIG = {
    "VENDOR": "moonshot",  # moonshot, deepseek, ollama
    "BASE_URL": "https://api.moonshot.cn/v1",
    "MODEL_ID": "moonshot-v1-128k",
    "API_KEY": "<REPLACE_WITH_LOCAL_API_KEY>"  # 对外副本仅保留占位符
}

def set_llm_config(vendor: str, base_url: str, model_id: str, api_key: str):
    """供外部动态修改大模型配置"""
    LLM_CONFIG["VENDOR"] = vendor
    LLM_CONFIG["BASE_URL"] = base_url
    LLM_CONFIG["MODEL_ID"] = model_id
    LLM_CONFIG["API_KEY"] = api_key

class BaseLLMAdapter(ABC):
    def __init__(self, base_url: str, model_id: str, api_key: str):
        self.base_url = base_url
        self.model_id = model_id
        self.api_key = api_key
        # Ollama 可能没有 api_key，但 OpenAI SDK 需要传递一个非空字符串
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key or "sk-dummy")
        
    @abstractmethod
    def generate(self, messages: list, prompt: str) -> str:
        pass
        
    def _stream_with_loop_detection(self, response_stream, read_timeout: float = 15.0) -> str:
        """
        处理流式返回数据，包含：
        1. 动态读超时（Read Timeout）检测：只要在规定时间内有新 Token，就保持连接。
        2. 复读机（死循环）检测：利用滑动窗口检测连续生成的重复片段。
        """
        full_text = ""
        last_chunk_time = time.time()
        
        # 用于复读机检测的参数
        # 记录最近生成的字符
        recent_buffer = ""
        # 触发检测的最小重复片段长度
        min_pattern_len = 10
        # 最大允许重复次数
        max_repeats = 5
        
        try:
            for chunk in response_stream:
                current_time = time.time()
                # 1. 读超时检测
                if current_time - last_chunk_time > read_timeout:
                    raise TimeoutError(f"API Read Timeout: 超过 {read_timeout} 秒未收到新的 Token。")
                
                last_chunk_time = current_time
                
                # 获取新片段（不同 API 客户端的结构可能略有不同，这里适配 OpenAI 格式）
                delta = getattr(chunk.choices[0].delta, "content", "")
                if delta:
                    full_text += delta
                    recent_buffer += delta
                    
                    # 2. 复读机检测：仅当 buffer 积攒到一定长度才检测
                    if len(recent_buffer) > min_pattern_len * max_repeats * 2:
                        # 取最近的 200 个字符进行分析（避免全量正则导致性能问题）
                        window = recent_buffer[-200:]
                        
                        # 寻找循环模式：假设结尾存在一个长度为 L 的 pattern，并且它重复了 N 次
                        # 这里用简单的字符串比对来寻找最基础的连续重复
                        is_looping = False
                        
                        # 特殊过滤：如果重复的仅仅是空格或换行符，不要轻易熔断
                        # 只有当重复片段中包含实际内容时才认为是真的死循环
                        for p_len in range(min_pattern_len, 50):
                            pattern = window[-p_len:]
                            
                            # 如果 pattern 全是空格或换行，直接跳过检测
                            if not pattern.strip():
                                continue
                                
                            # 检查这个 pattern 是否在末尾连续出现了 max_repeats 次
                            expected_tail = pattern * max_repeats
                            if window.endswith(expected_tail):
                                is_looping = True
                                break
                                
                        if is_looping:
                            print(f"\n[Debug] 触发复读机自动熔断！")
                            print(f"--- 当前已生成完整内容 (最后 500 字) ---\n{full_text[-500:]}")
                            print(f"--- 循环片段检测窗口 (最后 200 字) ---\n{window}\n")
                            raise RuntimeError(f"Looping Error: 侦测到大模型陷入复读机状态，自动熔断。")
                            
        except Exception as e:
            # 将异常抛给上层的重试逻辑
            raise e
            
        return full_text

class MoonshotAdapter(BaseLLMAdapter):
    def generate(self, messages: list, prompt: str, batch_id: str = "") -> str:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 处理 Moonshot 的 temperature 限制（通常需 > 0，例如 0.3）
                # 移除 timeout=30.0 的硬限制，改用 stream=True 流式输出，并交由 _stream_with_loop_detection 处理读超时
                response_stream = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=8192,
                    stream=True
                )
                
                # 通过智能检测流接收所有文本
                full_text = self._stream_with_loop_detection(response_stream, read_timeout=15.0)
                res_text = full_text.strip()
                
                if res_text == prompt:
                    print(f"\n    {batch_id} ⚠️ [LLM Warning] 模型原样返回了输入 (拒答): {prompt[:30]}...")
                return res_text
            except Exception as e:
                err_str = str(e)
                if "rate_limit_reached_error" in err_str or "429" in err_str:
                    wait_time = 3
                    if attempt < max_retries - 1:
                        # 使用带进度条的倒计时，提升用户感知
                        sys.stdout.flush()
                        for i in range(wait_time * 10, 0, -1):
                            sys.stdout.write(f"\r\033[K    {batch_id} ⚠️ 触发限流，正在退避: {i/10.0:.1f}s...")
                            sys.stdout.flush()
                            time.sleep(0.1)
                        sys.stdout.write(f"\r\033[K    {batch_id} 🔄 重新发送!\n")
                        sys.stdout.flush()
                    else:
                        time.sleep(wait_time)
                else:
                    print(f"\n    {batch_id} ❌ [API 错误] 尝试 {attempt+1}/{max_retries} 失败: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        return f"[Translation Failed: {e}]"
        return f"[Translation Failed: Max retries reached]"

class DeepSeekAdapter(BaseLLMAdapter):
    def generate(self, messages: list, prompt: str, batch_id: str = "") -> str:
        max_retries = 5  # DeepSeek 并发防流控，重试次数较多
        for attempt in range(max_retries):
            try:
                response_stream = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=8192,
                    stream=True
                )
                full_text = self._stream_with_loop_detection(response_stream, read_timeout=15.0)
                res_text = full_text.strip()
                
                if res_text == prompt:
                    print(f"\n    {batch_id} ⚠️ [LLM Warning] 模型原样返回了输入 (拒答): {prompt[:30]}...")
                return res_text
            except Exception as e:
                err_str = str(e)
                if "rate limit" in err_str.lower() or "429" in err_str:
                    wait_time = 2 ** attempt  # 指数退避
                    if attempt < max_retries - 1:
                        # 同样增加倒计时机制
                        sys.stdout.flush()
                        for i in range(wait_time * 10, 0, -1):
                            sys.stdout.write(f"\r\033[K    {batch_id} ⚠️ 触发流控，正在退避: {i/10.0:.1f}s...")
                            sys.stdout.flush()
                            time.sleep(0.1)
                        sys.stdout.write(f"\r\033[K    {batch_id} 🔄 重新发送!\n")
                        sys.stdout.flush()
                    else:
                        time.sleep(wait_time)
                else:
                    print(f"\n    {batch_id} ❌ [API 错误] 尝试 {attempt+1}/{max_retries} 失败: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        return f"[Translation Failed: {e}]"
        return f"[Translation Failed: Max retries reached]"

class OllamaAdapter(BaseLLMAdapter):
    def generate(self, messages: list, prompt: str, batch_id: str = "") -> str:
        # Ollama 本地调用，增加超时时间，无需复杂限流退避
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=messages,
                temperature=0.0,
                max_tokens=2048,
                timeout=120.0
            )
            res_text = response.choices[0].message.content.strip()
            if res_text == prompt:
                print(f"\n    {batch_id} ⚠️ [LLM Warning] 模型原样返回了输入 (拒答): {prompt[:30]}...")
            return res_text
        except Exception as e:
            print(f"\n    {batch_id} ❌ [Ollama API 错误] 本地调用失败: {e}")
            return f"[Translation Failed: {e}]"

def get_llm_adapter() -> BaseLLMAdapter:
    vendor = LLM_CONFIG.get("VENDOR", "moonshot").lower()
    base_url = LLM_CONFIG.get("BASE_URL", "")
    model_id = LLM_CONFIG.get("MODEL_ID", "")
    api_key = LLM_CONFIG.get("API_KEY", "")
    
    if vendor == "deepseek":
        return DeepSeekAdapter(base_url, model_id, api_key)
    elif vendor == "ollama":
        return OllamaAdapter(base_url, model_id, api_key)
    else:
        return MoonshotAdapter(base_url, model_id, api_key)

def call_llm(prompt: str, system_prompt: str = "", batch_id: str = "") -> str:
    """
    底层调用 API，通过多厂商 Adapter 带有重试和降级机制
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    adapter = get_llm_adapter()
    return adapter.generate(messages, prompt, batch_id)

def translate_batch_chunks(texts: list, mode: str, batch_idx: int, total_batches: int, glossary: dict = None) -> dict:
    """
    批量翻译多个文本块，并在内部使用 StageTimer 实时显示进度
    """
    batch_id = f"[批次 {batch_idx}/{total_batches}]"
    
    # 构造 Glossary 注入字符串
    glossary_str = ""
    if glossary:
        # 只取前 50 个词汇避免过度占用 Token
        sampled_glossary = {k: glossary[k] for k in list(glossary.keys())[:50]}
        glossary_str = "\n[专业术语表 / Glossary]\n"
        for k, v in sampled_glossary.items():
            glossary_str += f"- {k} = {v}\n"
        glossary_str += "在翻译时，请务必优先参考并使用上述术语表中的词汇。\n"

    if mode in ["zh_to_en", "zh_to_en_bilingual"]:
        system_prompt = ZH_TO_EN_PROMPT + glossary_str
    elif mode in ["en_to_zh", "en_to_zh_bilingual"]:
        system_prompt = EN_TO_ZH_PROMPT + glossary_str
    else:
        system_prompt = ZH_TO_EN_PROMPT + glossary_str

    prompt = json.dumps(texts, ensure_ascii=False)
    
    stage_name = f"{batch_id} 翻译中"
    with StageTimer(stage_name):
        en_trans = call_llm(prompt, system_prompt, batch_id)
    
    if en_trans.startswith("[Translation Failed"):
        return {t: en_trans for t in texts}
        
    try:
        clean_json = re.sub(r'^```json\s*', '', en_trans)
        clean_json = re.sub(r'\s*```$', '', clean_json).strip()
        translated_dict = json.loads(clean_json)
        
        if isinstance(translated_dict, dict):
            print(f"  ✅ 解析 {len(translated_dict)} 条记录成功")
            # 补齐可能漏掉的项
            for t in texts:
                if t not in translated_dict:
                    translated_dict[t] = t
            return translated_dict
        else:
            print(f"  ⚠️ [JSON Warning] 返回结果不是预期的 JSON 字典格式")
            return {t: t for t in texts}
    except Exception as e:
        print(f"  ❌ [JSON Parse Error] 无法解析大模型返回结果: {e}")
        return {t: t for t in texts}

def batch_translate(texts_with_types: list, mode: str = "zh_to_en", glossary: dict = None) -> dict:
    """
    并发处理所有单元格
    """
    from core.chunking_zh import chunk_texts_zh
    from core.chunking_en import chunk_texts_en

    results = {}
    total_cells = len(texts_with_types)
    if total_cells == 0:
        return results
        
    # 计算字数/词数统计
    total_length = 0
    is_zh = mode in ["zh_to_en", "zh_to_en_bilingual"]
    for t in texts_with_types:
        total_length += len(t[0]) if is_zh else len(t[0].split())
    unit = "字符" if is_zh else "单词"
    avg_length = total_length / total_cells if total_cells else 0
        
    print(f"\n[LLM Engine] 开始处理 {total_cells} 个单元格 (模型: {LLM_CONFIG['MODEL_ID']}, 模式: {mode})...")
    print(f"  -> 文本体量: 共计 {total_length} 个{unit}，平均每格 {avg_length:.1f} 个{unit}")
    
    # 区分中英切分
    if mode in ["zh_to_en", "zh_to_en_bilingual"]:
        chunks_with_types = chunk_texts_zh(texts_with_types, max_chars=2000)
    elif mode in ["en_to_zh", "en_to_zh_bilingual"]:
        chunks_with_types = chunk_texts_en(texts_with_types, max_words=1000)
    else:
        chunks_with_types = chunk_texts_zh(texts_with_types, max_chars=2000)

    # 提取纯文本列表用于请求
    chunks = [[t[0] for t in chunk] for chunk in chunks_with_types]
        
    print(f"  -> 共拆分为 {len(chunks)} 个请求批次")

    with ThreadPoolExecutor(max_workers=1) as executor:
        future_to_chunk = {}
        for idx, chunk in enumerate(chunks, start=1):
            future = executor.submit(translate_batch_chunks, chunk, mode, idx, len(chunks), glossary)
            future_to_chunk[future] = chunk

        completed_count = 0
        for future in as_completed(future_to_chunk):
            chunk = future_to_chunk[future]
            try:
                translated_dict = future.result()
                for original_text in chunk:
                    res = translated_dict.get(original_text, original_text)
                    results[original_text] = res
                        
                completed_count += 1
            except Exception as exc:
                print(f"\n  ❌ [Error] 处理批次抛出未捕获的严重异常: {exc}")
                for original_text in chunk:
                    results[original_text] = "[Translation Failed]"
    
    print("\n[LLM Engine] 所有单元格处理完成！")
    return results

if __name__ == "__main__":
    # 极简切块测试
    test_texts = ["缺点判定:\n1. 抽样计划:采用MIL-STD-1916, II级. 允收标准C=0；\n2. 检验环境条件:湿度:常温常湿；", "变更理由"]
    print("--- 原始文本 ---")
    print(test_texts)
    print("\n--- 批量翻译后 ---")
    res = translate_batch_chunks(test_texts, mode="zh_to_en", batch_idx=1, total_batches=1)
    print(res)
