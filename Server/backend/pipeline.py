import os
import json
import shutil
import logging
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from Server.backend.agents.repo_loader import clone_github_repo
from Server.backend.agents.code_parsers import parse_code_files
from Server.backend.agents.ner import run_ner_pipeline
from Server.backend.database.models import (
    repository_service, 
    graph_service, 
    RepositoryStatus, 
    StatusData
)
from urllib.parse import urlparse

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ProgressTracker:
    """Helper class to track and calculate progress metrics"""
    
    def __init__(self, repository_id: str):
        self.repository_id = repository_id
        self.start_time = datetime.now()
        self.step_start_times = {}
        
    def start_step(self, step_name: str):
        """Mark the start of a step"""
        self.step_start_times[step_name] = datetime.now()
        logger.info(f"Starting step: {step_name}")
    
    def calculate_eta(self, completed_steps: int, total_steps: int) -> Optional[int]:
        """Calculate estimated time of arrival"""
        if completed_steps == 0:
            return None
            
        elapsed = (datetime.now() - self.start_time).total_seconds()
        avg_time_per_step = elapsed / completed_steps
        remaining_steps = total_steps - completed_steps
        
        return int(avg_time_per_step * remaining_steps)
    
    def calculate_progress_percentage(self, completed_steps: int, total_steps: int, 
                                    current_step_progress: float = 0.0) -> float:
        """Calculate overall progress percentage"""
        if total_steps == 0:
            return 0.0
            
        base_progress = (completed_steps / total_steps) * 100
        step_progress = (current_step_progress / total_steps) * 100
        
        return min(base_progress + step_progress, 100.0)

def get_repo_base_name(repo_url: str) -> str:
    """Extract repository name from URL"""
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    if "@" in repo_url and ":" in repo_url:
        repo_url = repo_url.split(":")[1]
    base_name = os.path.basename(repo_url)
    return base_name

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
    file_count = 0
    
    try:
        for root, _, files in os.walk(repo_path):
            for file in files:
                file_count += 1
                ext = os.path.splitext(file)[1].lower()
                if ext in language_extensions:
                    lang = language_extensions[ext]
                    language_count[lang] = language_count.get(lang, 0) + 1
        
        logger.info(f"Scanned {file_count} files, detected languages: {language_count}")
        return max(language_count.items(), key=lambda x: x[1])[0] if language_count else "Unknown"
        
    except Exception as e:
        logger.error(f"Error detecting primary language: {e}")
        return "Unknown"

def cleanup_repository(repo_path: str, temp_files: List[str] = None) -> bool:
    """Clean up cloned repository and temporary files"""
    cleanup_success = True
    
    try:
        # Remove cloned repository
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
            logger.info(f"Cleaned up cloned repository: {repo_path}")
        
        # Remove temporary files
        if temp_files:
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        logger.info(f"Cleaned up temporary file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {temp_file}: {e}")
                    cleanup_success = False
        
        return cleanup_success
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return False

def update_repository_status(repository_id: str, status: RepositoryStatus, 
                           status_data: StatusData) -> bool:
    """Update repository status in database"""
    try:
        return repository_service.update_status(repository_id, status, status_data)
    except Exception as e:
        logger.error(f"Failed to update repository status: {e}")
        return False

def run_pipeline(repo_url: str, repository_id: str = None) -> dict:
    """
    Enhanced pipeline with comprehensive status tracking and cleanup
    """
    logger.info(f"Starting enhanced pipeline for {repo_url}")
    
    if not repository_id:
        logger.error("Repository ID is required for status tracking")
        raise ValueError("Repository ID is required")
    
    # Initialize progress tracker
    progress_tracker = ProgressTracker(repository_id)
    repo_base_name = get_repo_base_name(repo_url)
    repo_path = None
    temp_files = []
    
    try:
        # Initialize status data
        status_data = StatusData(
            current_step="Initializing",
            total_steps=6,
            completed_steps=0,
            current_operation="Preparing to clone repository",
            start_time=datetime.now(),
            last_update=datetime.now(),
            progress_percentage=0.0,
            detailed_progress={"repo_url": repo_url, "repo_name": repo_base_name}
        )
        
        update_repository_status(repository_id, RepositoryStatus.PENDING, status_data)
        
        # Step 1: Clone the repository
        progress_tracker.start_step("cloning")
        status_data.current_step = "Cloning Repository"
        status_data.current_operation = f"Cloning {repo_url}"
        status_data.progress_percentage = progress_tracker.calculate_progress_percentage(0, 6, 0.1)
        update_repository_status(repository_id, RepositoryStatus.CLONING, status_data)
        
        repo_path = clone_github_repo(repo_url)
        if not repo_path:
            raise Exception("Failed to clone repository")
        
        logger.info(f"Repository cloned successfully at: {repo_path}")
        
        status_data.completed_steps = 1
        status_data.current_operation = "Repository cloned successfully"
        status_data.progress_percentage = progress_tracker.calculate_progress_percentage(1, 6)
        status_data.eta_seconds = progress_tracker.calculate_eta(1, 6)
        update_repository_status(repository_id, RepositoryStatus.CLONING, status_data)
        
        # Step 2: Detect primary language
        progress_tracker.start_step("language_detection")
        status_data.current_step = "Analyzing Repository"
        status_data.current_operation = "Detecting primary programming language"
        status_data.progress_percentage = progress_tracker.calculate_progress_percentage(1, 6, 0.2)
        update_repository_status(repository_id, RepositoryStatus.PARSING, status_data)
        
        primary_language = detect_primary_language(repo_path)
        logger.info(f"Detected primary language: {primary_language}")
        
        status_data.detailed_progress["primary_language"] = primary_language
        
        # Step 3: Parse repository
        progress_tracker.start_step("parsing")
        status_data.current_operation = "Parsing code files and creating chunks"
        status_data.progress_percentage = progress_tracker.calculate_progress_percentage(1, 6, 0.5)
        update_repository_status(repository_id, RepositoryStatus.PARSING, status_data)
        
        cloned_repo_path = os.path.join("cloned_repos", repo_base_name)
        results = parse_code_files(cloned_repo_path)
        
        if not results:
            raise Exception("No code files found to parse")
        
        logger.info(f"Parsed {len(results)} code chunks from repository")
        
        # Save parsed results temporarily
        parsed_file = f"pipeline_parsed_code_{repo_base_name}.json"
        temp_files.append(parsed_file)
        
        with open(parsed_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        # Update file and chunk statistics
        summary = defaultdict(int)
        total_files = set()
        for r in results:
            summary[r['file']] += 1
            total_files.add(r['file'])
        
        status_data.completed_steps = 2
        status_data.files_discovered = len(total_files)
        status_data.current_operation = f"Parsed {len(results)} chunks from {len(total_files)} files"
        status_data.progress_percentage = progress_tracker.calculate_progress_percentage(2, 6)
        status_data.eta_seconds = progress_tracker.calculate_eta(2, 6)
        status_data.detailed_progress.update({
            "total_files": len(total_files),
            "total_chunks": len(results),
            "files_by_chunks": dict(summary)
        })
        update_repository_status(repository_id, RepositoryStatus.PARSING, status_data)
        
        logger.info(f"Files analyzed: {len(total_files)}, Total chunks: {len(results)}")
        
        # Step 4: Extract features using Gemini
        progress_tracker.start_step("feature_extraction")
        status_data.current_step = "Extracting Features"
        status_data.current_operation = "Initializing AI feature extraction"
        status_data.progress_percentage = progress_tracker.calculate_progress_percentage(2, 6, 0.1)
        update_repository_status(repository_id, RepositoryStatus.EXTRACTING_FEATURES, status_data)
        
        logger.info("Starting feature extraction with Gemini...")
        
        # Enhanced NER pipeline with progress tracking
        features = run_enhanced_ner_pipeline(parsed_file, repository_id, status_data, progress_tracker)
        
        if not features:
            logger.warning("No features extracted, using basic parsing results")
            status_data.warnings.append("AI feature extraction failed, using basic parsing")
            
            # Convert parsing results to basic features
            features = []
            for i, result in enumerate(results):
                basic_feature = {
                    "file": result["file"],
                    "chunk_id": result["chunk_id"],
                    "language": result["language"],
                    "feature": f"Code Block {result['chunk_id']}",
                    "description": f"Code chunk from {os.path.basename(result['file'])}",
                    "code": result["code"],
                    "functions": [],
                    "classes": [],
                    "apis": [],
                    "dependencies": [],
                    "inputs": [],
                    "outputs": [],
                    "side_effects": [],
                    "requirements": [],
                    "comments": [],
                    "annotations": {}
                }
                features.append(basic_feature)
                
                # Update progress for basic feature generation
                if i % 10 == 0:  # Update every 10 items
                    progress = (i / len(results)) * 100
                    status_data.current_operation = f"Generating basic features: {i}/{len(results)}"
                    status_data.progress_percentage = progress_tracker.calculate_progress_percentage(2, 6, 0.8)
                    update_repository_status(repository_id, RepositoryStatus.EXTRACTING_FEATURES, status_data)
        
        status_data.completed_steps = 3
        status_data.current_operation = f"Extracted {len(features)} features"
        status_data.progress_percentage = progress_tracker.calculate_progress_percentage(3, 6)
        status_data.eta_seconds = progress_tracker.calculate_eta(3, 6)
        update_repository_status(repository_id, RepositoryStatus.EXTRACTING_FEATURES, status_data)
        
        # Step 5: Store in MongoDB
        progress_tracker.start_step("storing_data")
        status_data.current_step = "Storing Data"
        status_data.current_operation = "Saving features to database"
        status_data.progress_percentage = progress_tracker.calculate_progress_percentage(3, 6, 0.1)
        update_repository_status(repository_id, RepositoryStatus.STORING_DATA, status_data)
        
        logger.info("Storing graph data in MongoDB...")
        
        # Store graph data
        storage_success = graph_service.store_graph_data(repository_id, features)
        if not storage_success:
            raise Exception("Failed to store graph data in MongoDB")
        
        # Update repository information
        repo_update_success = repository_service.update_repository(repository_id, {
            "language": primary_language,
            "files_analyzed": len(total_files),
            "total_chunks": len(results),
            "last_analyzed": datetime.now()
        })
        
        if not repo_update_success:
            logger.warning("Failed to update repository metadata")
            status_data.warnings.append("Failed to update repository metadata")
        
        status_data.completed_steps = 4
        status_data.current_operation = "Data stored successfully in MongoDB"
        status_data.progress_percentage = progress_tracker.calculate_progress_percentage(4, 6)
        status_data.eta_seconds = progress_tracker.calculate_eta(4, 6)
        update_repository_status(repository_id, RepositoryStatus.STORING_DATA, status_data)
        
        logger.info("Data stored successfully in MongoDB!")
        
        # Step 6: Cleanup
        progress_tracker.start_step("cleanup")
        status_data.current_step = "Cleaning Up"
        status_data.current_operation = "Removing temporary files and cloned repository"
        status_data.progress_percentage = progress_tracker.calculate_progress_percentage(4, 6, 0.1)
        update_repository_status(repository_id, RepositoryStatus.CLEANING_UP, status_data)
        
        logger.info("Starting cleanup process...")
        
        # Add additional temporary files that might have been created
        additional_temp_files = [
            f"pipeline_ner_output_{repo_base_name}.json",
            f"pipeline_ner_output_cache_{repo_base_name}.json"
        ]
        temp_files.extend(additional_temp_files)
        
        cleanup_success = cleanup_repository(cloned_repo_path, temp_files)
        
        if not cleanup_success:
            logger.warning("Some cleanup operations failed")
            status_data.warnings.append("Some temporary files may not have been cleaned up")
        
        status_data.completed_steps = 5
        status_data.current_operation = "Cleanup completed"
        status_data.progress_percentage = progress_tracker.calculate_progress_percentage(5, 6)
        
        # Step 7: Final completion
        status_data.current_step = "Completed"
        status_data.completed_steps = 6
        status_data.current_operation = "Repository analysis completed successfully"
        status_data.progress_percentage = 100.0
        status_data.eta_seconds = 0
        
        # Calculate total processing time
        total_time = (datetime.now() - status_data.start_time).total_seconds()
        status_data.detailed_progress["total_processing_time_seconds"] = total_time
        status_data.detailed_progress["processing_completed_at"] = datetime.now().isoformat()
        
        update_repository_status(repository_id, RepositoryStatus.ANALYZED, status_data)
        
        logger.info(f"Pipeline completed successfully in {total_time:.2f} seconds!")
        
        return {
            "status": "success",
            "repository_id": repository_id,
            "files_analyzed": len(total_files),
            "total_chunks": len(results),
            "features_extracted": len(features),
            "primary_language": primary_language,
            "processing_time_seconds": total_time,
            "warnings": status_data.warnings,
            "cleanup_success": cleanup_success
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        
        # Update status to error
        error_status = StatusData(
            current_step="Error",
            total_steps=6,
            completed_steps=status_data.completed_steps if 'status_data' in locals() else 0,
            current_operation=f"Pipeline failed: {str(e)}",
            start_time=status_data.start_time if 'status_data' in locals() else datetime.now(),
            last_update=datetime.now(),
            progress_percentage=0.0,
            error_count=1,
            warnings=status_data.warnings if 'status_data' in locals() else [],
            detailed_progress={"error": str(e), "error_time": datetime.now().isoformat()}
        )
        
        update_repository_status(repository_id, RepositoryStatus.ERROR, error_status)
        
        # Attempt cleanup even on error
        if repo_path and temp_files:
            try:
                cleanup_repository(repo_path, temp_files)
                logger.info("Cleanup completed after error")
            except Exception as cleanup_error:
                logger.error(f"Cleanup failed after error: {cleanup_error}")
        
        # Update repository with error message
        repository_service.update_repository(repository_id, {
            "error_message": str(e),
            "updated_at": datetime.now()
        })
        
        raise e

def run_enhanced_ner_pipeline(input_file: str, repository_id: str, 
                            status_data: StatusData, progress_tracker: ProgressTracker) -> List[dict]:
    """
    Enhanced NER pipeline with detailed progress tracking
    """
    import re
    import tiktoken
    from google import genai
    
    logger.info(f"Starting enhanced NER pipeline for {input_file}")
    
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        logger.warning("No Gemini API key found, skipping feature extraction")
        return []
    
    client = genai.Client(api_key=API_KEY)
    
    # Generate unique output files based on input file
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"pipeline_ner_output_{base_name}.json"
    cache_file = f"pipeline_ner_output_cache_{base_name}.json"
    
    TOK_LIMIT = 6000
    encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    def count_tokens(text):
        return len(encoder.encode(text))
    
    def create_prompt(batch):
        formatted_chunks = "\n\n".join([
            f"---\nFile: {c['file']}\nChunk ID: {c['chunk_id']}\nLanguage: {c['language']}\n\n{c['code']}\n---"
            for c in batch
        ])
        return f"""
You are an expert software analyst. For each code segment, extract the following in structured JSON format:

[
  {{
    "file": "...",
    "chunk_id": 0,
    "language": "...",
    "feature": "...",
    "description": "...",
    "functions": [
        {{
            "name": "...",
            "signature": "...",
            "start_line": 0,
            "end_line": 0,
            "class": "Optional enclosing class name"
        }}
    ],
    "classes": [
        {{
            "name": "...",
            "parent_class": "...",
            "methods": ["...", "..."]
        }}
    ],
    "apis": ["API_1", "API_2"],
    "database_tables": ["table1", "table2"],
    "inputs": ["..."],
    "outputs": ["..."],
    "dependencies": ["..."],
    "side_effects": ["..."],
    "requirements": ["..."],
    "comments": [
        {{
            "content": "...",
            "type": "inline|block|docstring",
            "line_number": 0
        }}
    ],
    "annotations": {{
      "developer_notes": "..."
    }}
  }}
]

Code:
{formatted_chunks}
""".strip()
    
    def clean_json_string(text):
        if text.strip().startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text.strip())
        return text
    
    try:
        # Load parsed code chunks
        with open(input_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        
        logger.info(f"Loaded {len(chunks)} code chunks for NER processing")
        
        # Load or initialize cache
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                cache = json.load(f)
            logger.info(f"Loaded existing cache with {len(cache)} entries")
        else:
            cache = {}
        
        results = []
        
        # Build file -> chunk 0 map
        global_chunks = {c["file"]: c for c in chunks if c["chunk_id"] == 0}
        
        # Token-aware batching
        batches = []
        current_batch = []
        
        for chunk in chunks:
            if chunk["chunk_id"] == 0:
                continue
            
            file_global_chunk = global_chunks.get(chunk["file"])
            test_batch = current_batch + [chunk]
            code_blob = "\n\n".join([c['code'] for c in test_batch])
            
            if file_global_chunk and file_global_chunk not in test_batch:
                code_blob = file_global_chunk['code'] + "\n\n" + code_blob
            
            token_count = count_tokens(code_blob)
            if token_count > TOK_LIMIT:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [chunk]
            else:
                current_batch.append(chunk)
        
        if current_batch:
            batches.append(current_batch)
        
        logger.info(f"Created {len(batches)} batches for processing")
        
        # Update status with batch information
        status_data.total_batches = len(batches)
        status_data.processed_batches = 0
        status_data.current_operation = f"Processing {len(batches)} batches with AI"
        update_repository_status(repository_id, RepositoryStatus.EXTRACTING_FEATURES, status_data)
        
        # Process batches with detailed progress tracking
        for i, batch in enumerate(batches):
            batch_key = f"batch_{i}"
            
            # Update current batch progress
            status_data.current_batch = i + 1
            status_data.processed_batches = i
            batch_progress = (i / len(batches)) * 0.8  # 80% of the feature extraction step
            status_data.progress_percentage = progress_tracker.calculate_progress_percentage(2, 6, batch_progress)
            status_data.current_operation = f"Processing batch {i+1}/{len(batches)}"
            update_repository_status(repository_id, RepositoryStatus.EXTRACTING_FEATURES, status_data)
            
            if batch_key in cache:
                logger.info(f"Using cached result for batch {i+1}")
                results.extend(cache[batch_key])
                continue
            
            logger.info(f"Processing batch {i+1}/{len(batches)} with {len(batch)} chunks")
            
            file_global_chunk = global_chunks.get(batch[0]["file"])
            if file_global_chunk and file_global_chunk not in batch:
                batch = [file_global_chunk] + batch
            
            prompt = create_prompt(batch)
            
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                raw = response.text
                cleaned = clean_json_string(raw)
                output_json = json.loads(cleaned)
                results.extend(output_json)
                
                # Merge code back into result
                for item in output_json:
                    file = item["file"]
                    chunk_id = item["chunk_id"]
                    match = next((c for c in batch if c["file"] == file and c["chunk_id"] == chunk_id), None)
                    if match:
                        item["code"] = match["code"]
                
                cache[batch_key] = output_json
                with open(cache_file, "w") as f:
                    json.dump(cache, f, indent=2)
                
                logger.info(f"Batch {i+1} completed successfully, extracted {len(output_json)} features")
                
                # Rate limiting
                time.sleep(1.2)
                
            except Exception as e:
                logger.error(f"Error processing batch {i+1}: {e}")
                status_data.error_count += 1
                status_data.warnings.append(f"Failed to process batch {i+1}: {str(e)}")
                continue
        
        # Update final batch processing status
        status_data.processed_batches = len(batches)
        status_data.current_operation = f"Completed processing {len(batches)} batches"
        
        # Save final result
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"NER pipeline completed. Extracted {len(results)} features total")
        return results
        
    except Exception as e:
        logger.error(f"NER pipeline failed: {e}")
        status_data.error_count += 1
        status_data.warnings.append(f"Feature extraction failed: {str(e)}")
        return []

if __name__ == "__main__":
    # Test the pipeline
    try:
        repo_url = "https://github.com/jorgekg/Cobol-bank-system.git"
        
        # Create a test repository entry
        repo_data = {
            "repo_name": "Cobol-bank-system",
            "description": "Test repository for pipeline",
            "language": "Unknown",
            "url": repo_url,
            "status": RepositoryStatus.PENDING
        }
        
        repository_id = repository_service.create_repository(repo_data)
        logger.info(f"Created test repository with ID: {repository_id}")
        
        result = run_pipeline(repo_url, repository_id)
        logger.info(f"Pipeline completed successfully!")
        logger.info(f"Results: {result}")
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        raise