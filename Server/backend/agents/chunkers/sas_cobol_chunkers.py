import re

def chunk_sas_by_block(code: str) -> list:
    """
    Splits SAS code into chunks based on 'data' and 'proc' blocks.
    Returns chunks with metadata for each block.
    """
    pattern = re.compile(r'^\s*(data|proc)\s+(\w+)', re.IGNORECASE | re.MULTILINE)
    matches = list(pattern.finditer(code))

    chunks = []
    for i, match in enumerate(matches):
        block_type, name = match.group(1).lower(), match.group(2)
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(code)
        body = code[start:end].strip()

        chunks.append({
            "chunk_type": block_type,
            "chunk_name": name,
            "code": body
        })

    return chunks if chunks else [{
        "chunk_type": "full",
        "chunk_name": "entire_script",
        "code": code
    }]

def chunk_cobol_by_paragraph(code: str) -> list:
    """
    Splits COBOL code by paragraph labels (lines ending in a dot).
    Returns chunks with paragraph names and metadata.
    """
    pattern = re.compile(r'^\s*([\w-]+)\.\s*$', re.MULTILINE)
    matches = list(pattern.finditer(code))

    chunks = []
    for i, match in enumerate(matches):
        name = match.group(1)
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(code)
        body = code[start:end].strip()

        chunks.append({
            "chunk_type": "paragraph",
            "chunk_name": name,
            "code": body
        })

    return chunks if chunks else [{
        "chunk_type": "full",
        "chunk_name": "entire_program",
        "code": code
    }]
