import re

def chunk_with_regex(code: str, ext: str) -> list:
    lines = code.splitlines()
    global_lines = []
    chunks = []

    # Regex patterns
    func_pattern = re.compile(r'^\s*(?:[\w\[\]\*&<>]+[\s]+)+(\w+)\s*\(.*?\)\s*\{', re.MULTILINE)
    class_pattern = re.compile(r'^\s*(class|struct)\s+\w+\s*(?:[:\w\s,<>]*)?\{', re.MULTILINE)

    # Collect global lines (context)
    for line in lines:
        if line.strip().startswith(("#include", "#define")) or (
            ";" in line and "(" not in line and ")" not in line and not line.strip().startswith("//")
        ):
            global_lines.append(line.strip())

    global_context = "\n".join(global_lines)
    chunks.append(global_context)  # chunk_id = 0 → global context

    # Match both class and function blocks
    patterns = list(func_pattern.finditer(code)) + list(class_pattern.finditer(code))
    patterns.sort(key=lambda x: x.start())

    if not patterns:
        return [code]  # fallback: return full code if no matches

    for i in range(len(patterns)):
        start = patterns[i].start()
        end = patterns[i + 1].start() if i + 1 < len(patterns) else len(code)
        body = code[start:end].strip()
        chunks.append(body)  # Do NOT prepend global context here

    return chunks
