# 🧠 CodeScrybe - Legacy Repository AI

A comprehensive AI-powered platform that helps developers and organizations analyze, understand, and interact with legacy codebases through intelligent parsing, semantic chunking, and natural language queries.

## 🌟 Key Features

- **🔗 GitHub Integration**: Connect and analyze any GitHub repository (Future Scope)
- **🧩 Smart Code Parsing**: Semantically chunk code into meaningful units (functions, classes, blocks)
- **🤖 AI-Powered Analysis**: Extract features and metadata using Google Gemini AI
- **📊 Knowledge Graph**: Build interactive visualizations in Neo4j to map code relationships
- **💬 Natural Language Queries**: Ask questions about your codebase using GraphRAG
- **🌐 Web Interface**: User-friendly React.js frontend for seamless interaction

## 🏗️ Project Structure

```
CodeScrybe-Legacy-Repository-AI/
├── Server/                     # Backend API (FastAPI)
│   ├── backend/
│   │   ├── agents/           # Core parsing, graph builder and analysis modules
│   │   ├── database/         # models & services related to db
│   │   ├── app.py            # FastAPI application
│   │   └── pipeline.py       # End-to-end processing pipeline
│   ├── venv410/              # Python virtual environment
│   ├── .env                  # Environent Variables
│   └── README.md             # Server-specific documentation
├── Client/                   # Frontend (React.js)
│   ├── src/                  # All UI & Business Logic Files
│   ├── public/
│   ├── package.json
│   └── README.md             # Client-specific documentation
├── .gitignore
└── README.md                # This file
```

## ✅ Supported Languages

| Language    | Extensions                           | Parser Type           | Chunk Type             |
|-------------|--------------------------------------|------------------------|------------------------|
| C, C++      | `.c`, `.cpp`, `.h`, `.hpp`           | `regex_chunker`        | Function + Context     |
| Java        | `.java`                              | `regex_chunker`        | Function + Context     |
| Shell       | `.sh`, `.bash`                       | `regex_chunker`        | Function-like blocks   |
| Perl        | `.pl`, `.pm`                         | `regex_chunker`        | Subroutines            |
| COBOL       | `.cob`, `.cbl`, `.cpy`               | `sas_cobol_chunkers`   | Paragraphs             |
| SAS         | `.sas`                               | `sas_cobol_chunkers`   | PROC & DATA blocks     |

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** for backend
- **Node.js 18+** for frontend
- **Neo4j Aura** account (free tier available)
- **Google AI Studio** API key

### 1. Clone the Repository

```bash
git clone <repository-url>
cd CodeScrybe-Legacy-Repository-AI
```

### 2. Environment Setup

Create a `.env` file in the Server directory:

```env
# Neo4j Configuration
NEO4J_URI=bolt://<your-neo4j-uri>
NEO4J_USERNAME=<your-username>
NEO4J_PASSWORD=<your-password>

# Google Gemini AI
GEMINI_API_KEY=<your-gemini-api-key>
```

#### Getting Your API Keys:

**Neo4j Aura:**
1. Visit [Neo4j Aura](https://aura.neo4j.io/)
2. Create a free account and new instance
3. Copy the connection details to your `.env`

**Google Gemini:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

### 3. Backend Setup

```bash
# Create virtual environment (if venv410 doesn't work)
python -m venv venv
source Server/venv/bin/activate      # Linux/Mac
# or
Server\venv410\Scripts\activate.bat         # Windows

# Install dependencies
pip install -r Server/requirements.txt

# Start the backend server
uvicorn Server.backend.app:app --reload
```

The backend will be available at: `http://127.0.0.1:8000`

### 4. Frontend Setup

```bash
# Navigate to client directory (from root)
cd Client

# Install dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at: `http://localhost:3000`

## 📚 API Endpoints

### Health Check
```
GET /health
```
### Other Endpoints access from below

### Interactive Documentation
Visit `http://127.0.0.1:8000/docs` for complete API documentation.

## 🔧 Development Workflow

### Full Pipeline Testing

1. **Test Individual Components:**
   ```bash
   cd Server
   source venv410/bin/activate  # or your venv
   
   # Test repo cloning
   python backend/agents/repo_loader.py
   
   # Test code parsing
   python -m backend.agents.code_parsers.py
   
   # Test NER extraction
   python backend/agents/ner_extractor.py
   
   # Test knowledge graph building
   python backend/agents/graph_builder.py
   
   # Test GraphRAG queries
   python backend/agents/graph_rag.py
   ```

2. **Run Complete Pipeline:**
   ```bash
   python backend/pipeline.py
   ```

### Frontend Development

```bash
cd client
npm start        # Start development server
```

## 🐛 Troubleshooting

### Common Issues

**Virtual Environment Issues:**
- If `venv410` doesn't work, create a new virtual environment
- Ensure Python 3.8+ is installed
- Check path issues when moving project directories

**API Connection Issues:**
- Verify `.env` file is in the Server directory
- Check Neo4j instance is running
- Validate Gemini API key is active

**Port Conflicts:**
- Backend default: `8000`
- Frontend default: `3000`
- Modify ports in respective configuration files if needed

## 📝 Usage Examples

### Analyzing a Repository

1. Start both backend and frontend servers
2. Navigate to `http://localhost:3000/dashboard`
2. Click on Add Repo
3. Enter a GitHub repository URL
4. Wait for analysis to complete
5. Explore the knowledge graph and ask questions in their chat section

### Sample Questions

- "What are the main functions in this codebase?"
- "Which files depend on the database module?"
- "Show me all the API endpoints defined"
- "What security-related functions are implemented?"

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini AI for intelligent code analysis
- Neo4j for graph database capabilities
- FastAPI for robust backend development
- React.js for modern frontend development

---

**CodeScrybe - Legacy Repository AI** | *Transforming Legacy Code Understanding Through AI*

**Need Help?** Check the individual README files in the `Server/` and `client/` directories for more detailed setup instructions.