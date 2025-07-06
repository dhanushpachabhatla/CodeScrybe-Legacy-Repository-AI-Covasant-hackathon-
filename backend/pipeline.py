# run command - python -m backend.pipelin
import os
import json
from collections import defaultdict
from dotenv import load_dotenv
from backend.agents.repo_loader import clone_github_repo
from backend.agents.code_parsers import parse_code_files
from backend.agents.ner import run_ner_pipeline
from backend.agents.graph_builder import KnowledgeGraphBuilder
from backend.agents.graph_rag import graph_rag
from urllib.parse import urlparse

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

#kylobunn credentials
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def get_repo_base_name(repo_url):
    # Handle https:// and git@ URLs
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]
    if "@" in repo_url and ":" in repo_url:
        # SSH URL
        repo_url = repo_url.split(":")[1]
    base_name = os.path.basename(repo_url)
    return base_name

def run_pipeline(repo_url):
    print(" Starting end-to-end pipeline...")

    #  Clone the repository
    repo_path = clone_github_repo(repo_url)
    print(f" Repository cloned at: {repo_path}")

    #  Parse repository
    repo_base_name = get_repo_base_name(repo_url)

    cloned_repo_path = os.path.join("cloned_repos", repo_base_name)
    results = parse_code_files(cloned_repo_path)
    print(f"\n Parsed {len(results)} code chunks from repo")
    
    with open("pipeline_parsed_code.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(" Parsed output written to pipeline_parsed_code.json")
    
    #  Chunk count summary
    summary = defaultdict(int)
    for r in results:
        summary[r['file']] += 1

    print("\n Chunk Summary:")
    for file, count in summary.items():
        print(f"{file} → {count} chunks")

    #  Extract features using Gemini
    run_ner_pipeline()
    print(" Features extracted to: pipeline_ner_output.json")

    #  Build Knowledge Graph in Neo4j
    kg = KnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    kg.create_constraints()
    with open("pipeline_ner_output.json", "r", encoding="utf-8") as f:
        features = json.load(f)
    kg.add_features(features)
    kg.close()
    print(" Knowledge graph built successfully in Neo4j!")

if __name__ == "__main__":
    try:
        repo_url = "https://github.com/jorgekg/Cobol-bank-system.git"
        run_pipeline(repo_url)
    except Exception as e:
        print(f" Pipeline failed: {e}")

