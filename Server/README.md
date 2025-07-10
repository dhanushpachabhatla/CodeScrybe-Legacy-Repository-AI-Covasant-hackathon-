# 🧠 Legacy Code Parser – AI-Powered Chunking Tool

ThThis project is an AI-powered platform that helps developers and organizations analyze and understand legacy codebases with ease.

Users can:
- Connect a GitHub repository containing legacy source code.
- Parse and semantically chunk the code into meaningful units (functions, classes, blocks).
- Automatically extract features and metadata from the code using Google Gemini AI.
- Build an interactive knowledge graph in Neo4j to visualize relationships between code components.
 -Ask natural language questions about the repository (e.g., “What are the key functions?”, “Which files  depend on X?”) and get intelligent answers powered by GraphRAG (Graph Retrieval-Augmented Generation).

- The backend is designed to integrate seamlessly with a Next.js frontend, enabling users to upload repositories and chat with their code directly from a web interface.



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

if the present venv410 virtual environment is not working (due to frontend integration in future, if you change the path of project from one place to another there might be chance that present venv410 might not work ) then kindly create one using command uisng the below method else directly activate venv410 if it is working fine and follow the remaining steps : 

## 🚀 Setup Instructions 

1. Clone this repository:
   ```bash
   git clone <my-repo-url>
   cd ai-legacy-code-discovery-app-backend
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate      # On Linux/Mac
   venv\Scripts\activate         # On Windows
   ```

3. Install dependencies: (only install if you are creating new venv - virtual environment , else no need to install if you are using venv410)
   ```bash
   pip install fastapi uvicorn python-dotenv neo4j google-generativeai gitpython
    ```

4. Create a `.env` file and keep there your Api keys:
   for gemini api -> go to google studio api key and click on get key also make sure that you have gpc acc where you have created a project
   for Neo4j -> go to Neo4j aura website and logic and create first instance and it will giv eyou credentials to use it
   ```
   NEO4J_URI=bolt://<your-neo4j-uri>
   NEO4J_USERNAME=<your-username>
   NEO4J_PASSWORD=<your-password>
   GEMINI_API_KEY=<your-gemini-key>
   ```

6. Start the API server:
   ```bash
   uvicorn Server.backend.app:app --reload
   ```
   or
   ```bash
   python -m Server.backend.app
   ```
7. Explore API Endpoints
   API Root (Health Check):
   http://127.0.0.1:8000/health
✅ Should return:
```bash
{"message": "🚀 AI Discovery Tool API is running."}
```
Interactive API Docs (Swagger UI):
http://127.0.0.1:8000/docs
-Test your repo api and question api here

# 🧪 To test Individual File (for furthur backend development)  : 


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
this will place your cloned repo inside the cloned_repos/ folder. Example:

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

7. Build the Knowledge Graph
   
   -After extracting features, you can create a Neo4j Knowledge Graph using the graph_builder.py module.
   -Make sure you’ve added your Neo4j credentials to the .env file:
   ```bash
   NEO4J_URI=bolt://<your-neo4j-uri>
   NEO4J_USERNAME=<your-username>
   NEO4J_PASSWORD=<your-password>
   ```
   Run the script:
      ```bash
      python backend/agents/graph_builder.py
   ```
   
This will:
-Connect to your Neo4j database.
-Create nodes for features, inputs, and outputs.
-Set up relationships between them.

7. Test GraphRAG Queries
   
-To test natural language questions on the Knowledge Graph, use the graph_rag.py module:
-Make sure your .env contains the Gemini API key and Neo4j credentials.

Run:
      ```bash
      python backend/agents/graph_rag.py
    ```

8. Run the Full Pipeline

   -Once individual modules are tested, you can execute the end-to-end pipeline:
   Run:
      ```bash
      python backend/pipeline.py
    ```

    




