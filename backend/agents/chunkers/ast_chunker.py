from tree_sitter import Language, Parser
import os

# Paths
LIB_PATH = 'backend/agents/tree_sitter_langs/build/my-languages.so'
LANGUAGE_MAP = {
    'c': 'tree-sitter-c',
    'cpp': 'tree-sitter-cpp',
    'java': 'tree-sitter-java'
}

EXT_LANGUAGE = {
    '.c': 'c', '.h': 'c',
    '.cpp': 'cpp', '.hpp': 'cpp',
    '.java': 'java'
}

# Build shared lib if not already
if not os.path.exists(LIB_PATH):
    print("🔧 Building Tree-sitter parsers...")
    Language.build_library(
        LIB_PATH,
        [f'backend/agents/tree_sitter_langs/{v}' for v in LANGUAGE_MAP.values()]
    )

LANG_OBJECTS = {
    lang_key: Language(LIB_PATH, lang_key)
    for lang_key in LANGUAGE_MAP
}

PARSERS = {
    lang_key: Parser()
    for lang_key in LANG_OBJECTS
}

for lang in PARSERS:
    PARSERS[lang].set_language(LANG_OBJECTS[lang])

def chunk_with_ast(code: str, ext: str) -> list:
    lang_key = EXT_LANGUAGE.get(ext.lower())
    if lang_key not in PARSERS:
        print(f"⚠️ AST chunking not supported for: {ext}")
        return [code]

    parser = PARSERS[lang_key]
    try:
        tree = parser.parse(bytes(code, "utf8"))
        root_node = tree.root_node

        function_chunks = []
        included_lines = []

        # Extract context nodes (includes, typedefs, etc.)
        for child in root_node.children:
            if child.type in ["preproc_include", "preproc_def", "declaration", "type_definition", "package_declaration", "import_declaration"]:
                included_lines.append(code[child.start_byte:child.end_byte].strip())
            elif child.type in ["function_definition", "method_declaration", "constructor_declaration"]:
                break  # stop context at first function/method

        global_context = "\n".join(included_lines)

        # Now extract all top-level functions/methods
        for node in root_node.children:
            if node.type in ["function_definition", "method_declaration", "constructor_declaration"]:
                func_code = code[node.start_byte:node.end_byte]
                full_chunk = global_context + "\n\n" + func_code
                function_chunks.append(full_chunk)

        if not function_chunks:
            print("⚠️ No functions/methods detected, returning entire file.")
        return function_chunks if function_chunks else [code]

    except Exception as e:
        print(f"❌ AST parsing error: {e}")
        return [code]
