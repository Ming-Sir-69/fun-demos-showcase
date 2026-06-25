def chunk_texts_en(texts_to_translate, max_words=1000):
    """
    按英文单词数进行切分。
    texts_to_translate: list of (text_val, text_type)
    """
    batches = []
    current_batch = []
    current_words = 0

    for item in texts_to_translate:
        text_val, _ = item
        # 简单使用 split() 计算单词数
        word_count = len(text_val.split())

        # 如果单个文本已经超过最大限制，单独作为一个批次
        if word_count >= max_words:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_words = 0
            batches.append([item])
            continue

        if current_words + word_count > max_words:
            batches.append(current_batch)
            current_batch = [item]
            current_words = word_count
        else:
            current_batch.append(item)
            current_words += word_count

    if current_batch:
        batches.append(current_batch)

    return batches
