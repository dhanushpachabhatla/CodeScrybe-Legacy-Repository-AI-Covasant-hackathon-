# backend/database/models.py
import os
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

# MongoDB Connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ai_discovery_tool")

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

# Collections
repositories_collection = db.repositories
chat_messages_collection = db.chat_messages
graph_data_collection = db.graph_data

# Enums
class RepositoryStatus(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    ERROR = "error"

class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"

# Data Models
@dataclass
class Repository:
    id: str
    repo_name: str
    description: str
    language: str
    url: str
    status: RepositoryStatus
    message_count: int = 0
    stars: int = 0
    last_analyzed: Optional[datetime] = None
    files_analyzed: int = 0
    total_chunks: int = 0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ChatMessage:
    id: str
    repository_id: str
    message_type: MessageType
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)

# Repository Service
class RepositoryService:
    def __init__(self):
        self.collection = repositories_collection
    
    def create_repository(self, repo_data: dict) -> str:
        """Create a new repository"""
        repo_data["created_at"] = datetime.now()
        repo_data["updated_at"] = datetime.now()
        repo_data["status"] = repo_data.get("status", RepositoryStatus.PENDING).value
        
        result = self.collection.insert_one(repo_data)
        return str(result.inserted_id)
    
    def get_repository(self, repo_id: str) -> Optional[Repository]:
        """Get repository by ID"""
        try:
            doc = self.collection.find_one({"_id": ObjectId(repo_id)})
            if doc:
                return self._doc_to_repository(doc)
            return None
        except Exception:
            return None
    
    def get_repository_by_url(self, url: str) -> Optional[Repository]:
        """Get repository by URL"""
        doc = self.collection.find_one({"url": url})
        if doc:
            return self._doc_to_repository(doc)
        return None
    
    def get_all_repositories(self) -> List[Repository]:
        """Get all repositories"""
        docs = self.collection.find().sort("created_at", -1)
        return [self._doc_to_repository(doc) for doc in docs]
    
    def update_repository(self, repo_id: str, update_data: dict) -> bool:
        """Update repository"""
        try:
            update_data["updated_at"] = datetime.now()
            
            # Handle status enum
            if "status" in update_data and isinstance(update_data["status"], RepositoryStatus):
                update_data["status"] = update_data["status"].value
            
            result = self.collection.update_one(
                {"_id": ObjectId(repo_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def delete_repository(self, repo_id: str) -> bool:
        """Delete repository and all associated data"""
        try:
            # Delete chat messages
            chat_messages_collection.delete_many({"repository_id": repo_id})
            
            # Delete graph data
            graph_data_collection.delete_many({"repository_id": repo_id})
            
            # Delete repository
            result = self.collection.delete_one({"_id": ObjectId(repo_id)})
            return result.deleted_count > 0
        except Exception:
            return False
    
    def _doc_to_repository(self, doc: dict) -> Repository:
        """Convert MongoDB document to Repository object"""
        return Repository(
            id=str(doc["_id"]),
            repo_name=doc["repo_name"],
            description=doc["description"],
            language=doc.get("language", "Unknown"),
            url=doc["url"],
            status=RepositoryStatus(doc.get("status", "pending")),
            message_count=doc.get("message_count", 0),
            stars=doc.get("stars", 0),
            last_analyzed=doc.get("last_analyzed"),
            files_analyzed=doc.get("files_analyzed", 0),
            total_chunks=doc.get("total_chunks", 0),
            error_message=doc.get("error_message"),
            created_at=doc.get("created_at", datetime.now()),
            updated_at=doc.get("updated_at", datetime.now())
        )

# Chat Service
class ChatService:
    def __init__(self):
        self.collection = chat_messages_collection
    
    def create_message(self, message_data: dict) -> str:
        """Create a new chat message"""
        message_data["timestamp"] = datetime.now()
        message_data["message_type"] = message_data.get("message_type", MessageType.USER).value
        
        result = self.collection.insert_one(message_data)
        
        # Update repository message count
        repositories_collection.update_one(
            {"_id": ObjectId(message_data["repository_id"])},
            {"$inc": {"message_count": 1}}
        )
        
        return str(result.inserted_id)
    
    def get_chat_history(self, repo_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get chat history for a repository"""
        docs = self.collection.find(
            {"repository_id": repo_id}
        ).sort("timestamp", -1).limit(limit)
        
        messages = []
        for doc in docs:
            messages.append(self._doc_to_message(doc))
        
        return list(reversed(messages))  # Return in chronological order
    
    def delete_chat_history(self, repo_id: str) -> bool:
        """Delete all chat messages for a repository"""
        try:
            result = self.collection.delete_many({"repository_id": repo_id})
            
            # Reset message count in repository
            repositories_collection.update_one(
                {"_id": ObjectId(repo_id)},
                {"$set": {"message_count": 0}}
            )
            
            return True
        except Exception:
            return False
    
    def _doc_to_message(self, doc: dict) -> ChatMessage:
        """Convert MongoDB document to ChatMessage object"""
        return ChatMessage(
            id=str(doc["_id"]),
            repository_id=doc["repository_id"],
            message_type=MessageType(doc["message_type"]),
            content=doc["content"],
            timestamp=doc["timestamp"],
            metadata=doc.get("metadata", {})
        )

# Graph Service
class GraphService:
    def __init__(self):
        self.collection = graph_data_collection
    
    def store_graph_data(self, repo_id: str, features: List[dict]) -> bool:
        """Store graph data for a repository"""
        try:
            # Clear existing data
            self.collection.delete_many({"repository_id": repo_id})
            
            # Prepare documents
            documents = []
            for feature in features:
                doc = {
                    "repository_id": repo_id,
                    "properties": feature,
                    "created_at": datetime.now()
                }
                documents.append(doc)
            
            # Insert new data
            if documents:
                self.collection.insert_many(documents)
            
            return True
        except Exception as e:
            print(f"Error storing graph data: {e}")
            return False
    
    def get_graph_data(self, repo_id: str) -> List[dict]:
        """Get graph data for a repository"""
        try:
            docs = self.collection.find({"repository_id": repo_id})
            return list(docs)
        except Exception as e:
            print(f"Error retrieving graph data: {e}")
            return []
    
    def delete_graph_data(self, repo_id: str) -> bool:
        """Delete graph data for a repository"""
        try:
            result = self.collection.delete_many({"repository_id": repo_id})
            return True
        except Exception:
            return False

# Create service instances
repository_service = RepositoryService()
chat_service = ChatService()
graph_service = GraphService()