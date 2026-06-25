def chunk_texts_zh(texts_to_translate, max_chars=2000):
    """
    按中文字符数进行切分。
    texts_to_translate: list of (text_val, text_type)
    """
    batches = []
    current_batch = []
    current_chars = 0

    for item in texts_to_translate:
        text_val, _ = item
        char_count = len(text_val)

        # 如果单个文本已经超过最大限制，单独作为一个批次
        if char_count >= max_chars:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_chars = 0
            batches.append([item])
            continue

        if current_chars + char_count > max_chars:
            batches.append(current_batch)
            current_batch = [item]
            current_chars = char_count
        else:
            current_batch.append(item)
            current_chars += char_count

    if current_batch:
        batches.append(current_batch)

    return batches
