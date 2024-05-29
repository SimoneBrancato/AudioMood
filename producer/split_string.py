def split_into_chunks(text, chunk_size):

    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i + chunk_size]
        chunks.append(' '.join(chunk))
    
    return chunks