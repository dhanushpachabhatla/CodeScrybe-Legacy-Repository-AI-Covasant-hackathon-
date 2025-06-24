# python -m backend.agents.code_parsers
import os
import json
from collections import defaultdict
# from backend.agents.chunkers.ast_chunker import chunk_with_ast
from backend.agents.chunkers.regex_chunker import chunk_with_regex
from backend.agents.chunkers.sas_cobol_chunkers import chunk_sas_by_block, chunk_cobol_by_paragraph

# Supported legacy and target languages
SUPPORTED_EXTENSIONS = [
    ".cpp", ".c", ".h", ".hpp",             # C, C++
    ".cob", ".cbl", ".cpy",                 # COBOL
    ".sas",                                 # SAS
    ".java", ".scala",                      # Flink (Java/Scala based)
    ".pl", ".pm",                           # Perl
    ".sh", ".bash"                          # Shell
]

LANG_MAP = {
    ".cpp": "C++", ".c": "C", ".h": "C++", ".hpp": "C++",
    ".cob": "COBOL", ".cbl": "COBOL", ".cpy": "COBOL",
    ".sas": "SAS",
    ".java": "Flink (Java)", ".scala": "Flink (Scala)",
    ".pl": "Perl", ".pm": "Perl",
    ".sh": "Shell", ".bash": "Shell"
}

def list_source_files(repo_path):
    source_files = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in SUPPORTED_EXTENSIONS:
                full_path = os.path.join(root, file)
                lang = LANG_MAP.get(ext, "Unknown")
                print(f"🗂 Found {lang} file: {file}")
                source_files.append((full_path, ext))
    print(f"📦 Total supported files found: {len(source_files)}")
    return source_files

def parse_code_files(repo_path):
    files = list_source_files(repo_path)
    parsed_output = []

    for file_path, ext in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
                lang = LANG_MAP.get(ext, "Unknown")

                # Strategy based on language
                if ext in [".cpp", ".c", ".h", ".hpp", ".java", ".scala"]:
                    chunks = chunk_with_regex(code, ext)
                    for idx, chunk in enumerate(chunks):
                        parsed_output.append({
                            "file": file_path,
                            "chunk_id": idx,
                            "language": lang,
                            "code": chunk
                        })

                elif ext in [".pl", ".pm", ".sh", ".bash"]:
                    chunks = chunk_with_regex(code, ext)
                    for idx, chunk in enumerate(chunks):
                        parsed_output.append({
                            "file": file_path,
                            "chunk_id": idx,
                            "language": lang,
                            "code": chunk
                        })

                elif ext == ".sas":
                    chunks = chunk_sas_by_block(code)
                    for idx, chunk in enumerate(chunks):
                        parsed_output.append({
                            "file": file_path,
                            "chunk_id": idx,
                            "language": lang,
                            "chunk_type": chunk.get("chunk_type"),
                            "chunk_name": chunk.get("chunk_name"),
                            "code": chunk.get("code")
                        })

                elif ext in [".cob", ".cbl", ".cpy"]:
                    chunks = chunk_cobol_by_paragraph(code)
                    for idx, chunk in enumerate(chunks):
                        parsed_output.append({
                            "file": file_path,
                            "chunk_id": idx,
                            "language": lang,
                            "chunk_type": chunk.get("chunk_type"),
                            "chunk_name": chunk.get("chunk_name"),
                            "code": chunk.get("code")
                        })

        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")

    return parsed_output

if __name__ == "__main__":
    repo = "cloned_repos/SAS"
    # repo = "cloned_repos/Cobol-bank-system"
    print(f"🔍 Parsing repo path: {repo}")
    results = parse_code_files(repo)
    print(f"\n✅ Parsed {len(results)} code chunks from repo")

    for r in results[:3]:
        print(f"\n--- {r['file']} [chunk {r['chunk_id']}] ({r['language']}) ---\n{r['code']}\n")

    # 🔄 Save to JSON file
    with open("parsed_output_SAS_repo.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("📝 Parsed output written to parsed_output.json")

    # 📊 Chunk count summary
    summary = defaultdict(int)
    for r in results:
        summary[r['file']] += 1

    print("\n📊 Chunk Summary:")
    for file, count in summary.items():
        print(f"{file} → {count} chunks")
