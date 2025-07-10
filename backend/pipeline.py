import os
import json
from collections import defaultdict
from dotenv import load_dotenv
from backend.agents.repo_loader import clone_github_repo
from backend.agents.code_parsers import parse_code_files
from backend.agents.ner import run_ner_pipeline
from backend.database.models import repository_service, graph_service
from urllib.parse import urlparse

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

def get_repo_base_name(repo_url):
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
    for root, _, files in os.walk(repo_path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in language_extensions:
                lang = language_extensions[ext]
                language_count[lang] = language_count.get(lang, 0) + 1
    
    return max(language_count.items(), key=lambda x: x[1])[0] if language_count else "Unknown"

def run_pipeline(repo_url: str, repository_id: str = None) -> dict:
    """
    Enhanced pipeline that stores data in MongoDB instead of Neo4j
    """
    print(f"🚀 Starting enhanced pipeline for {repo_url}...")
    
    try:
        # Step 1: Clone the repository
        repo_path = clone_github_repo(repo_url)
        if not repo_path:
            raise Exception("Failed to clone repository")
        
        print(f"✅ Repository cloned at: {repo_path}")
        
        # Step 2: Detect primary language
        primary_language = detect_primary_language(repo_path)
        print(f"🔍 Detected primary language: {primary_language}")
        
        # Step 3: Parse repository
        repo_base_name = get_repo_base_name(repo_url)
        cloned_repo_path = os.path.join("cloned_repos", repo_base_name)
        results = parse_code_files(cloned_repo_path)
        
        print(f"📊 Parsed {len(results)} code chunks from repo")
        
        # Save parsed results temporarily
        parsed_file = f"pipeline_parsed_code_{repo_base_name}.json"
        with open(parsed_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        # Step 4: Chunk count summary
        summary = defaultdict(int)
        total_files = set()
        for r in results:
            summary[r['file']] += 1
            total_files.add(r['file'])
        
        print(f"📁 Files analyzed: {len(total_files)}")
        print(f"📋 Total chunks: {len(results)}")
        
        # Step 5: Extract features using Gemini
        print("🧠 Extracting features with Gemini...")
        
        # Update the NER pipeline to use the specific file
        features = run_ner_pipeline(parsed_file)
        
        if not features:
            print("⚠️  No features extracted, using basic parsing results")
            # Convert parsing results to basic features
            features = []
            for result in results:
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
        
        # Step 6: Store in MongoDB instead of Neo4j
        if repository_id:
            print("💾 Storing graph data in MongoDB...")
            graph_service.store_graph_data(repository_id, features)
            
            # Update repository information
            repository_service.update_repository(repository_id, {
                "language": primary_language,
                "files_analyzed": len(total_files),
                "total_chunks": len(results)
            })
            
            print("✅ Data stored successfully in MongoDB!")
        
        # Step 7: Cleanup temporary files
        try:
            os.remove(parsed_file)
            if os.path.exists(f"pipeline_ner_output_{repo_base_name}.json"):
                os.remove(f"pipeline_ner_output_{repo_base_name}.json")
            if os.path.exists(f"pipeline_ner_output_cache_{repo_base_name}.json"):
                os.remove(f"pipeline_ner_output_cache_{repo_base_name}.json")
        except:
            pass  # Ignore cleanup errors
        
        return {
            "status": "success",
            "files_analyzed": len(total_files),
            "total_chunks": len(results),
            "primary_language": primary_language,
            "features": features
        }
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        raise e

def run_ner_pipeline(input_file: str) -> list:
    """
    Run NER pipeline on a specific input file
    """
    import time
    import re
    import tiktoken
    from google import genai
    
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        print("⚠️  No Gemini API key found, skipping feature extraction")
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
        
        # Load or initialize cache
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                cache = json.load(f)
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
        
        print(f"📦 Total batches prepared: {len(batches)}")
        
        # Process batches
        for i, batch in enumerate(batches):
            batch_key = f"batch_{i}"
            
            if batch_key in cache:
                print(f"✅ Skipping cached {batch_key}")
                results.extend(cache[batch_key])
                continue
            
            print(f"🚀 Processing {batch_key}...")
            
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
                
                time.sleep(1.2)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error in {batch_key}: {e}")
                continue
        
        # Save final result
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Feature extraction complete. Results saved to {output_file}")
        return results
        
    except Exception as e:
        print(f"❌ NER pipeline failed: {e}")
        return []

if __name__ == "__main__":
    # Test the pipeline
    try:
        repo_url = "https://github.com/jorgekg/Cobol-bank-system.git"
        result = run_pipeline(repo_url)
        print(f"✅ Pipeline completed successfully!")
        print(f"📊 Results: {result}")
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")