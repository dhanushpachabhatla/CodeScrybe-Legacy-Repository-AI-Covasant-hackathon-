# backend/agents/graph_rag.py
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from google import genai
from backend.database.models import repository_service
from backend.database.neo4j_manager import neo4j_manager

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_cypher_from_question(question: str, repository_context: str = "") -> str:
    """Generate Cypher query from natural language question"""
    cypher_prompt = f"""
You are an expert at converting natural language questions into Cypher queries for Neo4j.

The graph schema contains these nodes and relationships:
- Feature (name, description, language, chunk_id, code, annotations)
- Function (name, signature, start_line, end_line, class)
- Class (name, parent_class, methods)
- File (name, language)
- API (name)
- Dependency (name)
- Input (name)
- Output (name)
- SideEffect (name)
- Requirement (name)

Relationships:
- (Feature)-[:PART_OF_FILE]->(File)
- (Function)-[:PART_OF_FEATURE]->(Feature)
- (Class)-[:PART_OF_FEATURE]->(Feature)
- (Class)-[:INHERITS_FROM]->(Class)
- (Feature)-[:USES_API]->(API)
- (Feature)-[:DEPENDS_ON]->(Dependency)
- (Feature)-[:TAKES_INPUT]->(Input)
- (Feature)-[:PRODUCES]->(Output)
- (Feature)-[:CAUSES]->(SideEffect)
- (Feature)-[:REQUIRES]->(Requirement)

Repository Context: {repository_context}

Question: "{question}"

Generate a Cypher query that will find relevant information to answer this question.
Focus on retrieving nodes and their properties, along with relevant relationships.
Limit results to 20 items for performance.

Return ONLY the Cypher query, no explanations or markdown:
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=cypher_prompt
        )
        
        cypher_query = response.text.strip()
        # Clean up any markdown formatting
        cypher_query = cypher_query.replace('```cypher', '').replace('```', '').strip()
        
        return cypher_query
        
    except Exception as e:
        print(f"Error generating Cypher query: {e}")
        # Fallback to a basic query
        return """
        MATCH (f:Feature)-[:PART_OF_FILE]->(file:File)
        RETURN f.name, f.description, f.language, file.name as file_name, f.code
        LIMIT 20
        """

def execute_cypher_query(cypher_query: str) -> List[Dict[str, Any]]:
    """Execute Cypher query on Neo4j"""
    try:
        results = neo4j_manager.query_graph(cypher_query)
        return results
    except Exception as e:
        print(f"Error executing Cypher query: {e}")
        return []

def fallback_search(question: str) -> str:
    """Fallback Cypher query for basic search"""
    search_terms = extract_search_terms(question)
    if not search_terms:
        return """
        MATCH (f:Feature)-[:PART_OF_FILE]->(file:File)
        RETURN f.name, f.description, f.language, file.name as file_name, f.code
        LIMIT 10
        """
    
    search_term = search_terms[0]
    return f"""
    MATCH (f:Feature)-[:PART_OF_FILE]->(file:File)
    WHERE f.name CONTAINS '{search_term}' 
       OR f.description CONTAINS '{search_term}'
       OR f.code CONTAINS '{search_term}'
    RETURN f.name, f.description, f.language, file.name as file_name, f.code
    LIMIT 10
    """

def extract_search_terms(question: str) -> List[str]:
    """Extract key search terms from the question"""
    common_words = {'what', 'how', 'where', 'when', 'why', 'who', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    words = question.lower().split()
    search_terms = [word.strip('.,!?;:') for word in words if word.strip('.,!?;:') not in common_words and len(word) > 2]
    
    return search_terms[:5]

def enhanced_graph_rag(question: str, repository_id: str) -> Dict[str, Any]:
    """Enhanced Graph RAG using Neo4j for graph queries"""
    start_time = time.time()
    
    try:
        # Get repository information
        repo = repository_service.get_repository(repository_id)
        if not repo:
            return {
                "response": "Repository not found.",
                "metadata": {"error": "Repository not found"}
            }
        
        # Ensure Neo4j graph is loaded for this repository
        graph_loaded = neo4j_manager.ensure_graph_loaded(repository_id)
        if not graph_loaded:
            return {
                "response": f"Could not load graph data for repository {repo.repo_name}. Please ensure the repository has been analyzed.",
                "metadata": {
                    "error": "Graph not loaded",
                    "repository": repo.repo_name
                }
            }
        
        # Generate Cypher query from question
        repo_context = f"Repository: {repo.repo_name}, Language: {repo.language}, Description: {repo.description}"
        cypher_query = generate_cypher_from_question(question, repo_context)
        
        # Execute Cypher query
        search_results = execute_cypher_query(cypher_query)
        
        # If no results, try fallback search
        if not search_results:
            fallback_query = fallback_search(question)
            search_results = execute_cypher_query(fallback_query)
        
        if not search_results:
            return {
                "response": f"No relevant information found in the {repo.repo_name} repository for your question.",
                "metadata": {
                    "repository": repo.repo_name,
                    "files_analyzed": repo.files_analyzed,
                    "execution_time": f"{time.time() - start_time:.2f}s",
                    "results_found": 0,
                    "cypher_query": cypher_query
                }
            }
        
        # Prepare context for LLM
        context_data = []
        for result in search_results:
            context_item = {
                "feature_name": result.get('f.name', 'Unknown'),
                "description": result.get('f.description', 'No description'),
                "language": result.get('f.language', 'Unknown'),
                "file": result.get('file_name', result.get('file.name', 'Unknown')),
                "code_snippet": result.get('f.code', result.get('code', ''))[:500] + "..." if len(result.get('f.code', result.get('code', ''))) > 500 else result.get('f.code', result.get('code', ''))
            }
            
            # Add any additional fields from the query result
            for key, value in result.items():
                if key not in ['f.name', 'f.description', 'f.language', 'f.code', 'file.name', 'file_name']:
                    context_item[key] = value
            
            context_data.append(context_item)
        
        # Generate response using LLM
        response_prompt = f"""
You are an expert software analyst helping developers understand code repositories.

Repository: {repo.repo_name}
Repository Language: {repo.language}
Repository Description: {repo.description}

User Question: "{question}"

Relevant Code Analysis Data from Neo4j Graph:
{json.dumps(context_data, indent=2)}

Based on the graph analysis data above, provide a comprehensive and helpful answer to the user's question.

Guidelines:
1. Be specific and reference actual code features, functions, or files when relevant
2. Explain technical concepts clearly
3. If you mention specific functions or classes, include their names
4. If relevant, mention the programming language and file locations
5. Keep the response conversational but informative
6. If the data doesn't fully answer the question, acknowledge what information is available
7. Use the graph relationships to provide deeper insights about code structure and dependencies

Answer:
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=response_prompt
        )
        
        # Calculate confidence based on result quality
        confidence = min(0.95, 0.6 + (len(search_results) * 0.05))
        
        execution_time = time.time() - start_time
        
        return {
            "response": response.text.strip(),
            "metadata": {
                "repository": repo.repo_name,
                "files_analyzed": repo.files_analyzed,
                "execution_time": f"{execution_time:.2f}s",
                "confidence": confidence,
                "results_found": len(search_results),
                "cypher_query": cypher_query,
                "graph_loaded": True,
                "search_method": "neo4j_graph_query"
            }
        }
        
    except Exception as e:
        return {
            "response": f"I encountered an error while analyzing the repository: {str(e)}",
            "metadata": {
                "error": str(e),
                "execution_time": f"{time.time() - start_time:.2f}s"
            }
        }

def get_graph_insights(repository_id: str) -> Dict[str, Any]:
    """Get high-level insights about the repository graph"""
    try:
        # Ensure graph is loaded
        graph_loaded = neo4j_manager.ensure_graph_loaded(repository_id)
        if not graph_loaded:
            return {"error": "Could not load graph"}
        
        # Fixed stats query using OPTIONAL MATCH
        stats_query = """
        OPTIONAL MATCH (f:Feature)
        WITH count(f) as features
        OPTIONAL MATCH (fn:Function)
        WITH features, count(fn) as functions
        OPTIONAL MATCH (c:Class)
        WITH features, functions, count(c) as classes
        OPTIONAL MATCH (file:File)
        WITH features, functions, classes, count(file) as files
        OPTIONAL MATCH (api:API)
        WITH features, functions, classes, files, count(api) as apis
        OPTIONAL MATCH (dep:Dependency)
        RETURN features, functions, classes, files, apis, count(dep) as dependencies
        """
        
        stats = neo4j_manager.query_graph(stats_query)
        
        # Get most connected features
        connected_features_query = """
        MATCH (f:Feature)
        OPTIONAL MATCH (f)-[r]-()
        RETURN f.name as feature, count(r) as connections
        ORDER BY connections DESC
        LIMIT 5
        """
        
        connected_features = neo4j_manager.query_graph(connected_features_query)
        
        return {
            "stats": stats[0] if stats else {},
            "most_connected_features": connected_features
        }
        
    except Exception as e:
        return {"error": str(e)}


# Test function
def test_enhanced_graph_rag():
    """Test function for the enhanced graph RAG"""
    print("🚀 Enhanced GraphRAG with Neo4j is ready!")
    print("Available repositories:")
    
    repos = repository_service.get_all_repositories()
    for i, repo in enumerate(repos, 1):
        print(f"{i}. {repo.repo_name} ({repo.language}) - {repo.status.value}")
    
    while True:
        try:
            repo_choice = input("\nSelect repository number (or 'exit' to quit): ")
            if repo_choice.lower() in ['exit', 'quit']:
                break
            
            repo_index = int(repo_choice) - 1
            if 0 <= repo_index < len(repos):
                selected_repo = repos[repo_index]
                print(f"\nSelected: {selected_repo.repo_name}")
                
                # Show graph insights
                insights = get_graph_insights(selected_repo.id)
                if "error" not in insights:
                    print(f"\n📊 Graph Insights:")
                    if insights.get("stats"):
                        stats = insights["stats"]
                        print(f"   • Features: {stats.get('features', 0)}")
                        print(f"   • Functions: {stats.get('functions', 0)}")
                        print(f"   • Classes: {stats.get('classes', 0)}")
                        print(f"   • Files: {stats.get('files', 0)}")
                        print(f"   • APIs: {stats.get('apis', 0)}")
                        print(f"   • Dependencies: {stats.get('dependencies', 0)}")
                
                while True:
                    question = input("\nAsk a question about this repository (or 'back' to select another repo): ")
                    if question.lower() == 'back':
                        break
                    
                    result = enhanced_graph_rag(question, selected_repo.id)
                    print(f"\n📋 Answer: {result['response']}")
                    
                    if result.get('metadata'):
                        metadata = result['metadata']
                        print(f"\n📊 Metadata:")
                        print(f"   • Execution time: {metadata.get('execution_time', 'N/A')}")
                        print(f"   • Confidence: {metadata.get('confidence', 'N/A')}")
                        print(f"   • Results found: {metadata.get('results_found', 'N/A')}")
                        print(f"   • Graph loaded: {metadata.get('graph_loaded', 'N/A')}")
                        if metadata.get('cypher_query'):
                            print(f"   • Cypher query: {metadata['cypher_query']}")
            else:
                print("Invalid selection. Please try again.")
                
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_enhanced_graph_rag()