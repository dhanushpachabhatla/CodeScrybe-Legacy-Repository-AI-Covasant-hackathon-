from tree_sitter import Language
import os

LIB_PATH = 'backend/agents/tree_sitter_langs/build/my-languages.so'

os.makedirs(os.path.dirname(LIB_PATH), exist_ok=True)

Language.build_library(
    LIB_PATH,
    [
        'backend/agents/tree_sitter_langs/tree-sitter-c',
        'backend/agents/tree_sitter_langs/tree-sitter-cpp',
        'backend/agents/tree_sitter_langs/tree-sitter-java'
    ]
)

print(f"✅ Built tree-sitter languages to: {LIB_PATH}")
