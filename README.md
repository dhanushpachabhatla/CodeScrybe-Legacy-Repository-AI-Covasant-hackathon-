# 🧠 Legacy Code Parser – AI-Powered Chunking Tool

This project extracts semantically meaningful chunks (functions, classes, blocks) from legacy source code for downstream analysis with LLMs.

---

## 📁 Project Structure 

Updates so far : 

backend/
├── agents/
│ └── chunkers/
│ ├── regex_chunker.py # Regex-based parser for C/C++/Java/Shell/Perl
│ ├── sas_cobol_chunkers.py # Specialized block/paragraph chunker for SAS & COBOL
│
├── code_parsers.py # Main controller script for parsing source repos
├── build_treesitter_lib.py # (Optional) AST setup using Tree-sitter (WIP)
cloned_repos/ # Folder where target repos are cloned
parsed_output.json # Final output written here


---

## ✅ Supported Languages & Methods

| Language    | Extension(s)                         | Parser Used       | Chunk Type              |
|-------------|--------------------------------------|-------------------|--------------------------|
| C, C++      | `.c`, `.cpp`, `.h`, `.hpp`           | `regex_chunker`   | Function + Context       |
| Java        | `.java`                              | `regex_chunker`   | Function + Context       |
| Shell       | `.sh`, `.bash`                       | `regex_chunker`   | Function-like blocks     |
| Perl        | `.pl`, `.pm`                         | `regex_chunker`   | Subroutines              |
| COBOL       | `.cob`, `.cbl`, `.cpy`               | `sas_cobol_chunkers` | Paragraphs           |
| SAS         | `.sas`                               | `sas_cobol_chunkers` | PROC & DATA blocks   |

---

## 🚀 How to Run

> Make sure Python 3.8+ is installed and you're in the project root.

### 1. Create & Activate Virtual Environment

```bash
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
```
 Install Required Packages
```bash
pip install -r pip install gitpython fastapi uvicorn openai py2neo tree_sitter
```

3. Clone a GitHub Repo to Analyze
    ```bash
       python backend/agents/repo_loader.py 
   ```
tthis will place your cloned repo inside the cloned_repos/ folder. Example:
cloned_repos/
└── my-legacy-codebase/
    └── src/
        └── main.c

5. Run the Parser
   ```bash
       python -m backend.agents.code_parsers.py
   ```
The script will:

List supported files

Parse code based on language

Output chunks to parsed_output.json

Problem : i am getting error setting up tree_sitter for ATS parsing for c/c++/java, kinly look into this error if possible my felow team mates
   




