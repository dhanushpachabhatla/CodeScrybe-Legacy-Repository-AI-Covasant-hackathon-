import os
import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from bson import ObjectId
from dotenv import load_dotenv
from Server.backend.agents.repo_loader import is_valid_github_repo
import logging
import shutil
import stat
# Import our database models and services
from Server.backend.database.models import (
    Repository, ChatMessage, RepositoryStatus, MessageType,
    repository_service, chat_service, graph_service
)
from Server.backend.database.neo4j_manager import neo4j_manager
from Server.backend.pipeline import run_pipeline
from Server.backend.agents.graph_rag import enhanced_graph_rag

load_dotenv()

app = FastAPI(title="CodeScrybe - Legacy Repository AI Application API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)

# Request/Response models
class RepoRequest(BaseModel):
    repo_url: str
    description: Optional[str] = ""

class ChatRequest(BaseModel):
    repository_id: str
    message: str

class ChatResponse(BaseModel):
    message_id: str
    response: str
    metadata: Optional[dict] = None

class RepositoryResponse(BaseModel):
    id: str
    name: str
    description: str
    language: str
    status: str
    message_count: int
    stars: int
    last_analyzed: Optional[str] = None
    url: str
    files_analyzed: int = 0
    total_chunks: int = 0
    error_message: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    messages: List[dict]
    total_count: int

# Utility functions
def get_repo_base_name(repo_url: str) -> str:
    """Extract repository name from URL"""
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    if "@" in repo_url and ":" in repo_url:
        repo_url = repo_url.split(":")[1]
    return os.path.basename(repo_url)

def detect_primary_language(repo_path: str) -> str:
    """Detect primary programming language of repository"""
    language_extensions = {
        ".py": "Python", ".js": "JavaScript", ".java": "Java",
        ".cpp": "C++", ".c": "C", ".h": "C++", ".hpp": "C++",
        ".cob": "COBOL", ".cbl": "COBOL", ".cpy": "COBOL",
        ".sas": "SAS", ".pl": "Perl", ".pm": "Perl",
        ".sh": "Shell", ".bash": "Shell", ".scala": "Scala"
    }
    
    language_count = {}
    for root, _, files in os.walk(repo_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in language_extensions:
                lang = language_extensions[ext]
                language_count[lang] = language_count.get(lang, 0) + 1
    
    return max(language_count.items(), key=lambda x: x[1])[0] if language_count else "Unknown"

async def run_pipeline_async(repo_id: str, repo_url: str):
    """Run the analysis pipeline asynchronously"""
    try:
        # Update status to analyzing
        repository_service.update_repository(repo_id, {
            "status": RepositoryStatus.PENDING,
            "last_analyzed": datetime.now()
        })
        
        # Run the pipeline (this will take time)
        result = await asyncio.to_thread(run_pipeline, repo_url, repo_id)
        
        # Update repository with analysis results
        repository_service.update_repository(repo_id, {
            "status": RepositoryStatus.ANALYZED,
            "files_analyzed": result.get("files_analyzed", 0),
            "total_chunks": result.get("total_chunks", 0),
            "last_analyzed": datetime.now()
        })
        
        print(f"✅ Pipeline completed for {repo_url}")
        
    except Exception as e:
        # Update status to error
        repository_service.update_repository(repo_id, {
            "status": RepositoryStatus.ERROR,
            "error_message": str(e),
            "last_analyzed": datetime.now()
        })
        print(f"❌ Pipeline error for {repo_url}: {e}")

# API Endpoints

@app.get("/")
def root():
    return {"message": "CodeScrybe Application API v2.0 is running"}

@app.post("/repositories", response_model=dict)
async def create_repository(req: RepoRequest, background_tasks: BackgroundTasks):
    """Create a new repository and start analysis"""
    try:
        repo_name = get_repo_base_name(req.repo_url)
        
        # Check if repository already exists
        existing_repo = repository_service.get_repository_by_url(req.repo_url)
        if existing_repo:
            return {
                "status": "exists",
                "message": f"Repository already exists",
                "repository_id": existing_repo.id
            }
        
        is_valid = is_valid_github_repo(req.repo_url)
        if not is_valid:
            return {
                "status": "invalid",
                "message": f"Repository Url is Invalid"
            }
        
        # Create repository record
        repo_data = {
            "repo_name": repo_name,
            "description": req.description or f"Repository: {repo_name}",
            "language": "Unknown",  # Will be updated after analysis
            "url": req.repo_url,
            "status": RepositoryStatus.PENDING
        }
        
        repo_id = repository_service.create_repository(repo_data)
        
        # Start analysis in background
        background_tasks.add_task(run_pipeline_async, repo_id, req.repo_url)
        
        return {
            "status": "created",
            "message": f"Repository created and analysis started",
            "repository_id": repo_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/repositories", response_model=List[RepositoryResponse])
def get_repositories():
    """Get all repositories"""
    try:
        repositories = repository_service.get_all_repositories()
        return [
            RepositoryResponse(
                id=repo.id,
                name=repo.repo_name,
                description=repo.description,
                language=repo.language,
                status=repo.status.value,
                message_count=repo.message_count,
                stars=repo.stars,
                last_analyzed=repo.last_analyzed.isoformat() if repo.last_analyzed else None,
                url=repo.url,
                files_analyzed=repo.files_analyzed,
                total_chunks=repo.total_chunks,
                error_message=repo.error_message
            )
            for repo in repositories
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/repositories/{repo_id}", response_model=RepositoryResponse)
def get_repository(repo_id: str):
    """Get a specific repository"""
    try:
        repo = repository_service.get_repository(repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        return RepositoryResponse(
            id=repo.id,
            name=repo.repo_name,
            description=repo.description,
            language=repo.language,
            status=repo.status.value,
            message_count=repo.message_count,
            stars=repo.stars,
            last_analyzed=repo.last_analyzed.isoformat() if repo.last_analyzed else None,
            url=repo.url,
            files_analyzed=repo.files_analyzed,
            total_chunks=repo.total_chunks,
            error_message=repo.error_message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/repositories/{repo_id}")
def delete_repository(repo_id: str):
    """Delete a repository and all associated data"""
    try:
        success = repository_service.delete_repository(repo_id)
        if not success:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Also clear Neo4j graph if this was the current repository
        if neo4j_manager.current_repo_id == repo_id:
            neo4j_manager.clear_graph()
        
        return {"status": "deleted", "message": "Repository and all associated data deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat_with_repository(req: ChatRequest):
    """Chat with a specific repository using Neo4j graph queries"""
    try:
        # Verify repository exists
        repo = repository_service.get_repository(req.repository_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        if repo.status != RepositoryStatus.ANALYZED:
            raise HTTPException(status_code=400, detail="Repository is not analyzed yet")
        
        # Store user message
        user_message_data = {
            "repository_id": req.repository_id,
            "message_type": MessageType.USER,
            "content": req.message
        }
        user_message_id = chat_service.create_message(user_message_data)
        
        # Get response from enhanced graph RAG (now uses Neo4j)
        response_data = await asyncio.to_thread(
            enhanced_graph_rag, 
            req.message, 
            req.repository_id
        )
        
        # Store assistant response
        assistant_message_data = {
            "repository_id": req.repository_id,
            "message_type": MessageType.ASSISTANT,
            "content": response_data["response"],
            "metadata": response_data.get("metadata", {})
        }
        assistant_message_id = chat_service.create_message(assistant_message_data)
        
        return ChatResponse(
            message_id=assistant_message_id,
            response=response_data["response"],
            metadata=response_data.get("metadata", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/repositories/{repo_id}/chat", response_model=ChatHistoryResponse)
def get_chat_history(repo_id: str, limit: int = 50):
    """Get chat history for a repository"""
    try:
        # Verify repository exists
        repo = repository_service.get_repository(repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        messages = chat_service.get_chat_history(repo_id, limit)
        
        return ChatHistoryResponse(
            messages=[
                {
                    "id": msg.id,
                    "type": msg.message_type.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in messages
            ],
            total_count=len(messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/repositories/{repo_id}/chat")
def clear_chat_history(repo_id: str):
    """Clear chat history for a repository"""
    try:
        # Verify repository exists
        repo = repository_service.get_repository(repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        success = chat_service.delete_chat_history(repo_id)
        
        return {"status": "cleared", "message": "Chat history cleared"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/repositories/{repo_id}/status")
def get_repository_status(repo_id: str):
    """Get current analysis status of a repository"""
    try:
        repo = repository_service.get_repository(repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        return repo.status_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/repositories/{repo_id}/graph-status")
def get_graph_status(repo_id: str):
    """Get Neo4j graph loading status for a repository"""
    try:
        repo = repository_service.get_repository(repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Check if graph is loaded in Neo4j
        is_loaded, graph_hash = neo4j_manager.is_graph_loaded(repo_id)
        
        return {
            "repository_id": repo_id,
            "repository_name": repo.repo_name,
            "graph_loaded": is_loaded,
            "graph_hash": graph_hash,
            "current_repo_loaded": neo4j_manager.current_repo_id == repo_id,
            "mongodb_data_available": len(graph_service.get_graph_data(repo_id)) > 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/repositories/{repo_id}/load-graph")
def load_graph(repo_id: str):
    """Manually load graph data from MongoDB to Neo4j"""
    try:
        repo = repository_service.get_repository(repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        if repo.status != RepositoryStatus.ANALYZED:
            raise HTTPException(status_code=400, detail="Repository is not analyzed yet")
        
        # Load graph from MongoDB to Neo4j
        success = neo4j_manager.load_graph_from_mongodb(repo_id)
        
        if success:
            return {
                "status": "loaded",
                "message": f"Graph successfully loaded for {repo.repo_name}",
                "repository_id": repo_id,
                "graph_hash": neo4j_manager.current_graph_hash
            }
        else:
            return {
                "status": "failed",
                "message": "Failed to load graph data",
                "repository_id": repo_id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/repositories/{repo_id}/clear-graph")
def clear_graph(repo_id: str):
    """Clear Neo4j graph for a repository"""
    try:
        repo = repository_service.get_repository(repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Clear graph if it's currently loaded
        if neo4j_manager.current_repo_id == repo_id:
            neo4j_manager.clear_graph()
            return {
                "status": "cleared",
                "message": f"Graph cleared for {repo.repo_name}",
                "repository_id": repo_id
            }
        else:
            return {
                "status": "not_loaded",
                "message": "Graph is not currently loaded for this repository",
                "repository_id": repo_id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/repositories/{repo_id}/graph-insights")
def get_graph_insights(repo_id: str):
    """Get insights about the repository's graph structure"""
    try:
        repo = repository_service.get_repository(repo_id)
        if not repo:
            raise HTTPException(status_code=404, detail="Repository not found")
        
        # Import here to avoid circular import
        from Server.backend.agents.graph_rag import get_graph_insights
        
        insights = get_graph_insights(repo_id)
        
        if "error" in insights:
            raise HTTPException(status_code=500, detail=insights["error"])
        
        return {
            "repository_id": repo_id,
            "repository_name": repo.repo_name,
            "insights": insights
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "neo4j_connected": neo4j_manager.driver is not None,
        "current_repo_loaded": neo4j_manager.current_repo_id
    }

def remove_readonly(func, path, _):
    """Clear read-only bit and retry removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

# Startup event to test connections
@app.on_event("startup")
async def startup_event():
    """Test database connections and clean up on startup"""
    print("🚀 Starting CodeScrybe Application API v2.0...")

    # Delete 'cloned_repository' folder if it exists
    folder_path = os.path.join(os.getcwd(), "cloned_repos")
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        try:
            shutil.rmtree(folder_path, onerror=remove_readonly)
            print("🧹 Deleted 'cloned_repository' folder on startup")
        except Exception as e:
            print(f"⚠️ Failed to delete 'cloned_repository': {e}")
    
    # Test Neo4j connection
    try:
        with neo4j_manager.driver.session() as session:
            result = session.run("RETURN 1 as test")
            test_value = result.single()["test"]
            print(f"✅ Neo4j connection successful (test value: {test_value})")
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")

    print("🎯 API is ready to serve requests!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🔄 Shutting down CodeScrybe Application API...")
    neo4j_manager.close()
    print("✅ Neo4j connection closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)