def chunk_with_sliding_window(code, chunk_size=50, overlap=10):
    """
    Sliding window chunker for COBOL and SAS.
    Splits code into overlapping windows.
    """
    lines = code.splitlines()
    chunks = []
    i = 0

    while i < len(lines):
        chunk = lines[i:i + chunk_size]
        chunks.append("\n".join(chunk))
        i += chunk_size - overlap

    return chunks
