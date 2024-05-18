import re

def split_string(s, max_words):
    parts = re.split(r'[,.]', s)
    parts = [part.strip() for part in parts if part.strip()]
    
    result = []
    current_part = []
    current_word_count = 0

    for part in parts:
        words = part.split()
        for word in words:
            if current_word_count < max_words:
                current_part.append(word)
                current_word_count += 1
            else:
                result.append(" ".join(current_part))
                current_part = [word]
                current_word_count = 1

        if current_part:
            result.append(" ".join(current_part))
            current_part = []
            current_word_count = 0
    
    return result