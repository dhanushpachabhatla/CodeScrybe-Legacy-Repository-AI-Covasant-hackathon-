# backend/database/models.py
import os
import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('repository_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MongoDB Connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "CodeScrybe")

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

# Collections
repositories_collection = db.repositories
chat_messages_collection = db.chat_messages
graph_data_collection = db.graph_data

# Enums
class RepositoryStatus(Enum):
    PENDING = "pending"
    CLONING = "cloning"
    PARSING = "parsing"
    EXTRACTING_FEATURES = "extracting_features"
    STORING_DATA = "storing_data"
    CLEANING_UP = "cleaning_up"
    ANALYZED = "analyzed"
    ERROR = "error"

class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"

# Data Models
@dataclass
class StatusData:
    current_step: str
    total_steps: int
    completed_steps: int
    current_operation: str
    files_discovered: int = 0
    files_processed: int = 0
    total_batches: int = 0
    processed_batches: int = 0
    current_batch: int = 0
    eta_seconds: Optional[int] = None
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    error_count: int = 0
    warnings: List[str] = field(default_factory=list)
    progress_percentage: float = 0.0
    detailed_progress: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Repository:
    id: str
    repo_name: str
    description: str
    language: str
    url: str
    status: RepositoryStatus
    status_data: Optional[StatusData] = None
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
        self.logger = logging.getLogger(f"{__name__}.RepositoryService")
    
    def create_repository(self, repo_data: dict) -> str:
        """Create a new repository"""
        try:
            repo_data["created_at"] = datetime.now()
            repo_data["updated_at"] = datetime.now()
            repo_data["status"] = repo_data.get("status", RepositoryStatus.PENDING).value
            
            # Initialize status data
            initial_status = StatusData(
                current_step="Initializing",
                total_steps=6,  # cloning, parsing, extracting, storing, cleaning, complete
                completed_steps=0,
                current_operation="Repository created, waiting to start analysis",
                start_time=datetime.now(),
                last_update=datetime.now(),
                progress_percentage=0.0
            )
            repo_data["status_data"] = self._status_data_to_dict(initial_status)
            
            result = self.collection.insert_one(repo_data)
            repo_id = str(result.inserted_id)
            
            self.logger.info(f"Repository created successfully: {repo_id}")
            return repo_id
            
        except Exception as e:
            self.logger.error(f"Error creating repository: {e}")
            raise
    
    def update_status(self, repo_id: str, status: RepositoryStatus, status_data: StatusData) -> bool:
        """Update repository status and status data"""
        try:
            status_data.last_update = datetime.now()
            
            update_data = {
                "status": status.value,
                "status_data": self._status_data_to_dict(status_data),
                "updated_at": datetime.now()
            }
            
            result = self.collection.update_one(
                {"_id": ObjectId(repo_id)},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Repository {repo_id} status updated to {status.value}")
                return True
            else:
                self.logger.warning(f"No changes made to repository {repo_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating repository status: {e}")
            return False
    
    def get_repository(self, repo_id: str) -> Optional[Repository]:
        """Get repository by ID"""
        try:
            doc = self.collection.find_one({"_id": ObjectId(repo_id)})
            if doc:
                return self._doc_to_repository(doc)
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving repository {repo_id}: {e}")
            return None
    
    def get_repository_by_url(self, url: str) -> Optional[Repository]:
        """Get repository by URL"""
        try:
            doc = self.collection.find_one({"url": url})
            if doc:
                return self._doc_to_repository(doc)
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving repository by URL {url}: {e}")
            return None
    
    def get_all_repositories(self) -> List[Repository]:
        """Get all repositories"""
        try:
            docs = self.collection.find().sort("created_at", -1)
            return [self._doc_to_repository(doc) for doc in docs]
        except Exception as e:
            self.logger.error(f"Error retrieving all repositories: {e}")
            return []
    
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
            
            if result.modified_count > 0:
                self.logger.info(f"Repository {repo_id} updated successfully")
                return True
            else:
                self.logger.warning(f"No changes made to repository {repo_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating repository {repo_id}: {e}")
            return False
    
    def delete_repository(self, repo_id: str) -> bool:
        """Delete repository and all associated data"""
        try:
            self.logger.info(f"Deleting repository {repo_id} and all associated data")
            
            # Delete chat messages
            chat_result = chat_messages_collection.delete_many({"repository_id": repo_id})
            self.logger.info(f"Deleted {chat_result.deleted_count} chat messages")
            
            # Delete graph data
            graph_result = graph_data_collection.delete_many({"repository_id": repo_id})
            self.logger.info(f"Deleted {graph_result.deleted_count} graph data entries")
            
            # Delete repository
            result = self.collection.delete_one({"_id": ObjectId(repo_id)})
            
            if result.deleted_count > 0:
                self.logger.info(f"Repository {repo_id} deleted successfully")
                return True
            else:
                self.logger.warning(f"Repository {repo_id} not found for deletion")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting repository {repo_id}: {e}")
            return False
    
    def _status_data_to_dict(self, status_data: StatusData) -> dict:
        """Convert StatusData to dictionary for storage"""
        return {
            "current_step": status_data.current_step,
            "total_steps": status_data.total_steps,
            "completed_steps": status_data.completed_steps,
            "current_operation": status_data.current_operation,
            "files_discovered": status_data.files_discovered,
            "files_processed": status_data.files_processed,
            "total_batches": status_data.total_batches,
            "processed_batches": status_data.processed_batches,
            "current_batch": status_data.current_batch,
            "eta_seconds": status_data.eta_seconds,
            "start_time": status_data.start_time,
            "last_update": status_data.last_update,
            "error_count": status_data.error_count,
            "warnings": status_data.warnings,
            "progress_percentage": status_data.progress_percentage,
            "detailed_progress": status_data.detailed_progress
        }
    
    def _dict_to_status_data(self, data: dict) -> StatusData:
        """Convert dictionary to StatusData"""
        return StatusData(
            current_step=data.get("current_step", "Unknown"),
            total_steps=data.get("total_steps", 0),
            completed_steps=data.get("completed_steps", 0),
            current_operation=data.get("current_operation", ""),
            files_discovered=data.get("files_discovered", 0),
            files_processed=data.get("files_processed", 0),
            total_batches=data.get("total_batches", 0),
            processed_batches=data.get("processed_batches", 0),
            current_batch=data.get("current_batch", 0),
            eta_seconds=data.get("eta_seconds"),
            start_time=data.get("start_time"),
            last_update=data.get("last_update"),
            error_count=data.get("error_count", 0),
            warnings=data.get("warnings", []),
            progress_percentage=data.get("progress_percentage", 0.0),
            detailed_progress=data.get("detailed_progress", {})
        )
    
    def _doc_to_repository(self, doc: dict) -> Repository:
        """Convert MongoDB document to Repository object"""
        status_data = None
        if "status_data" in doc:
            status_data = self._dict_to_status_data(doc["status_data"])
        
        return Repository(
            id=str(doc["_id"]),
            repo_name=doc["repo_name"],
            description=doc["description"],
            language=doc.get("language", "Unknown"),
            url=doc["url"],
            status=RepositoryStatus(doc.get("status", "pending")),
            status_data=status_data,
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
        self.logger = logging.getLogger(f"{__name__}.ChatService")
    
    def create_message(self, message_data: dict) -> str:
        """Create a new chat message"""
        try:
            message_data["timestamp"] = datetime.now()
            message_data["message_type"] = message_data.get("message_type", MessageType.USER).value
            
            result = self.collection.insert_one(message_data)
            
            # Update repository message count
            repositories_collection.update_one(
                {"_id": ObjectId(message_data["repository_id"])},
                {"$inc": {"message_count": 1}}
            )
            
            self.logger.info(f"Chat message created for repository {message_data['repository_id']}")
            return str(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"Error creating chat message: {e}")
            raise
    
    def get_chat_history(self, repo_id: str, limit: int = 50) -> List[ChatMessage]:
        """Get chat history for a repository"""
        try:
            docs = self.collection.find(
                {"repository_id": repo_id}
            ).sort("timestamp", -1).limit(limit)
            
            messages = []
            for doc in docs:
                messages.append(self._doc_to_message(doc))
            
            return list(reversed(messages))  # Return in chronological order
            
        except Exception as e:
            self.logger.error(f"Error retrieving chat history for {repo_id}: {e}")
            return []
    
    def delete_chat_history(self, repo_id: str) -> bool:
        """Delete all chat messages for a repository"""
        try:
            result = self.collection.delete_many({"repository_id": repo_id})
            
            # Reset message count in repository
            repositories_collection.update_one(
                {"_id": ObjectId(repo_id)},
                {"$set": {"message_count": 0}}
            )
            
            self.logger.info(f"Deleted {result.deleted_count} chat messages for repository {repo_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting chat history for {repo_id}: {e}")
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
        self.logger = logging.getLogger(f"{__name__}.GraphService")
    
    def store_graph_data(self, repo_id: str, features: List[dict]) -> bool:
        """Store graph data for a repository"""
        try:
            self.logger.info(f"Storing graph data for repository {repo_id}")
            
            # Clear existing data
            delete_result = self.collection.delete_many({"repository_id": repo_id})
            self.logger.info(f"Cleared {delete_result.deleted_count} existing graph entries")
            
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
                result = self.collection.insert_many(documents)
                self.logger.info(f"Inserted {len(result.inserted_ids)} graph data entries")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing graph data for {repo_id}: {e}")
            return False
    
    def get_graph_data(self, repo_id: str) -> List[dict]:
        """Get graph data for a repository"""
        try:
            docs = self.collection.find({"repository_id": repo_id})
            return list(docs)
        except Exception as e:
            self.logger.error(f"Error retrieving graph data for {repo_id}: {e}")
            return []
    
    def delete_graph_data(self, repo_id: str) -> bool:
        """Delete graph data for a repository"""
        try:
            result = self.collection.delete_many({"repository_id": repo_id})
            self.logger.info(f"Deleted {result.deleted_count} graph data entries for repository {repo_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting graph data for {repo_id}: {e}")
            return False

# Create service instances
repository_service = RepositoryService()
chat_service = ChatService()
graph_service = GraphService()