# 🧠 Legacy Code Parser – AI-Powered Chunking Tool

This project extracts semantically meaningful chunks (functions, classes, blocks) from legacy source code and provides a user inteface for clients to upload github links and chat about that repo 

---


## ✅ Supported Languages & Methods

| Language    | Extension(s)                         | Parser Used           | Chunk Type             |
|-------------|--------------------------------------|------------------------|------------------------|
| C, C++      | `.c`, `.cpp`, `.h`, `.hpp`           | `regex_chunker`        | Function + Context     |
| Java        | `.java`                              | `regex_chunker`        | Function + Context     |
| Shell       | `.sh`, `.bash`                       | `regex_chunker`        | Function-like blocks   |
| Perl        | `.pl`, `.pm`                         | `regex_chunker`        | Subroutines            |
| COBOL       | `.cob`, `.cbl`, `.cpy`               | `sas_cobol_chunkers`   | Paragraphs             |
| SAS         | `.sas`                               | `sas_cobol_chunkers`   | PROC & DATA blocks     |

---

## 🚀 How to Run

> ⚙️ Make sure Python 3.8+ is installed and you're in the project root.

### 1. Activate a Virtual Environment

# On Unix/macOS:
```bash
source venv410/bin/activate
```
# On Windows:
```bash
.\venv410\Scripts\activate
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

4. Run the Parser
   ```bash
       python -m backend.agents.code_parsers.py
   ```
The script will:

List supported files
Parse code based on language
Output chunks to parsed_output.json

5. 🔍 Run NER on Parsed Chunks
   After parsing the code, run the NER module to extract feature-level entities like API usage, user-defined functions, or domain-specific actions:
   before running add a gemini api key in you .env file and then run it
      ```bash
       python backend/agents/ner_extractor.py
   ```
      This will:

Load parsed_output.json
Run NER logic (gemini llm)
Writes enriched output to features_requiremnets.json

🧾 NER Summary
The ner_extractor.py module enhances parsed chunks with structured functional features, including:

Feature name (e.g., "User Login Detection", "Customer Name Retrieval")
Chunk-level description
Inputs/Outputs mentioned in the code
Entity types (e.g., API names, CPF/SSNs, financial terms)
This prepares data for the next stage: knowledge graph construction.

📝 Note - Please recheck input and output file name and path before running the individual py program

⚠️ Known Issue
We're currently facing an error while setting up Tree-sitter for AST-based parsing of C/C++/Java.
Fellow teammates are requested to look into this issue in build_treesitter_lib.py if possible.



