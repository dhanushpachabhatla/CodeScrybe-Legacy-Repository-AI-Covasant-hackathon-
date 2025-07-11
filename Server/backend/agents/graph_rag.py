# backend/agents/graph_rag.py
import os
import json
import time
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
from google import genai
from Server.backend.database.models import repository_service
from Server.backend.database.neo4j_manager import neo4j_manager
import anthropic

load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("ANTHROPIC_CLAUDE_API_KEY")
PREFERRED_API = os.getenv("PREFERRED_API", "gemini").lower()  # Default to gemini

# Initialize clients
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY) if CLAUDE_API_KEY else None
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def get_api_response(prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """Get response from preferred API with fallback"""
    try:
        if PREFERRED_API == "claude" and claude_client:
            response = claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        elif PREFERRED_API == "gemini" and gemini_client:
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text
        
        else:
            # Fallback to available API
            if gemini_client:
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                return response.text
            elif claude_client:
                response = claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            else:
                raise Exception("No API keys available")
                
    except Exception as e:
        print(f"Error with {PREFERRED_API} API: {e}")
        # Try fallback API
        try:
            if PREFERRED_API == "claude" and gemini_client:
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                return response.text
            elif PREFERRED_API == "gemini" and claude_client:
                response = claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
        except Exception as fallback_error:
            print(f"Fallback API also failed: {fallback_error}")
            raise Exception(f"Both APIs failed: {e}, {fallback_error}")

def is_greeting_or_casual(question: str) -> bool:
    """Check if the question is a greeting or casual conversation"""
    casual_patterns = [
        r'\b(hi|hello|hey|greetings)\b',
        r'\b(how are you|what\'s up|sup)\b',
        r'\b(good morning|good afternoon|good evening)\b',
        r'\b(thanks|thank you|thx)\b',
        r'\b(bye|goodbye|see you)\b'
    ]
    
    question_lower = question.lower().strip()
    
    # Check for exact matches or very short greetings
    if len(question_lower) <= 15 and any(re.search(pattern, question_lower) for pattern in casual_patterns):
        return True
    
    return False

def generate_casual_response(question: str, repo_name: str = None) -> str:
    """Generate casual response for greetings and simple interactions"""
    question_lower = question.lower().strip()
    
    greeting_responses = [
        f"Hello! 👋 I'm here to help you explore and understand the {repo_name} repository.",
        f"Hi there! 😊 Ready to dive into the {repo_name} codebase?",
        f"Hey! 🚀 Let's explore what's in the {repo_name} repository together!"
    ]
    
    thanks_responses = [
        "You're welcome! Feel free to ask me anything about the repository.",
        "Happy to help! What would you like to know about the code?",
        "No problem! I'm here whenever you need to understand the codebase."
    ]
    
    goodbye_responses = [
        "Goodbye! Come back anytime you need help with the repository.",
        "See you later! Happy coding! 👋",
        "Take care! I'll be here when you need code insights."
    ]
    
    if any(word in question_lower for word in ['hi', 'hello', 'hey', 'morning', 'afternoon', 'evening']):
        return greeting_responses[hash(question) % len(greeting_responses)]
    elif any(word in question_lower for word in ['thanks', 'thank', 'thx']):
        return thanks_responses[hash(question) % len(thanks_responses)]
    elif any(word in question_lower for word in ['bye', 'goodbye', 'see you']):
        return goodbye_responses[hash(question) % len(goodbye_responses)]
    else:
        return f"I'm doing great! 😊 I'm here to help you understand the {repo_name} repository. What would you like to explore?"

def generate_cypher_from_question(question: str, repository_context: str = "") -> str:
    """Generate Cypher query from natural language question using preferred API"""
    
    cypher_prompt = f"""
You are an expert Neo4j Cypher query generator. Convert natural language questions into efficient Cypher queries.

GRAPH SCHEMA:
Nodes:
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

CONTEXT: {repository_context}

QUESTION: "{question}"

INSTRUCTIONS:
1. Generate a Cypher query that finds the most relevant information
2. Use CASE-INSENSITIVE matching with CONTAINS for text searches
3. Return comprehensive node properties and relationships
4. Limit results to 25 for performance
5. Prioritize Features, Functions, and Classes
6. Include file information when available

Return ONLY the Cypher query without explanations, markdown, or formatting:
"""

    try:
        response = get_api_response(cypher_prompt, temperature=0.3)
        cypher_query = response.strip()
        
        # Clean up any markdown formatting
        cypher_query = cypher_query.replace('```cypher', '').replace('```', '').strip()
        
        return cypher_query
        
    except Exception as e:
        print(f"Error generating Cypher query: {e}")
        # Enhanced fallback query
        search_terms = extract_search_terms(question)
        if search_terms:
            term = search_terms[0]
            return f"""
            MATCH (f:Feature)-[:PART_OF_FILE]->(file:File)
            WHERE toLower(f.name) CONTAINS toLower('{term}') 
               OR toLower(f.description) CONTAINS toLower('{term}')
               OR toLower(f.code) CONTAINS toLower('{term}')
            OPTIONAL MATCH (f)<-[:PART_OF_FEATURE]-(func:Function)
            OPTIONAL MATCH (f)<-[:PART_OF_FEATURE]-(cls:Class)
            RETURN f.name, f.description, f.language, f.code, file.name as file_name,
                   collect(func.name) as functions, collect(cls.name) as classes
            LIMIT 20
            """
        else:
            return """
            MATCH (f:Feature)-[:PART_OF_FILE]->(file:File)
            OPTIONAL MATCH (f)<-[:PART_OF_FEATURE]-(func:Function)
            OPTIONAL MATCH (f)<-[:PART_OF_FEATURE]-(cls:Class)
            RETURN f.name, f.description, f.language, f.code, file.name as file_name,
                   collect(func.name) as functions, collect(cls.name) as classes
            LIMIT 15
            """

def execute_cypher_query(cypher_query: str) -> List[Dict[str, Any]]:
    """Execute Cypher query on Neo4j with enhanced error handling"""
    try:
        results = neo4j_manager.query_graph(cypher_query)
        return results
    except Exception as e:
        print(f"Error executing Cypher query: {e}")
        return []

def extract_search_terms(question: str) -> List[str]:
    """Extract meaningful search terms from the question"""
    # Remove common words and punctuation
    common_words = {
        'what', 'how', 'where', 'when', 'why', 'who', 'is', 'are', 'was', 'were',
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
        'with', 'by', 'this', 'that', 'these', 'those', 'can', 'could', 'should',
        'would', 'will', 'do', 'does', 'did', 'have', 'has', 'had', 'me', 'about',
        'tell', 'show', 'find', 'get', 'give', 'make', 'code', 'function', 'class'
    }
    
    # Extract words and clean them
    words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', question.lower())
    search_terms = [word for word in words if word not in common_words and len(word) > 2]
    
    return search_terms[:5]

def format_response_beautifully(response_text: str, question: str, metadata: Dict) -> str:
    """Format the response in an attractive and readable way"""
    
    # Add emojis and formatting based on question type
    if any(word in question.lower() for word in ['function', 'method', 'def']):
        icon = "🔧"
    elif any(word in question.lower() for word in ['class', 'object', 'inheritance']):
        icon = "📦"
    elif any(word in question.lower() for word in ['file', 'structure', 'architecture']):
        icon = "📁"
    elif any(word in question.lower() for word in ['api', 'endpoint', 'service']):
        icon = "🌐"
    elif any(word in question.lower() for word in ['error', 'bug', 'issue', 'problem']):
        icon = "🐛"
    elif any(word in question.lower() for word in ['dependency', 'import', 'require']):
        icon = "🔗"
    else:
        icon = "💡"
    
    # Clean and format the response
    formatted_response = f"{icon} **Analysis Results**\n\n{response_text}"
    
    # Add metadata footer if available
    if metadata.get('results_found', 0) > 0:
        confidence = metadata.get('confidence', 0)
        confidence_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.6 else "🔴"
        
        footer = f"\n\n---\n📊 **Query Info**: Found {metadata['results_found']} relevant code elements {confidence_emoji} (Confidence: {confidence:.0%})"
        formatted_response += footer
    
    return formatted_response

def enhanced_graph_rag(question: str, repository_id: str) -> Dict[str, Any]:
    """Enhanced Graph RAG with dynamic API selection and improved user interaction"""
    start_time = time.time()
    
    try:
        # Get repository information
        repo = repository_service.get_repository(repository_id)
        if not repo:
            return {
                "response": "❌ Repository not found. Please check the repository ID.",
                "metadata": {"error": "Repository not found"}
            }
        
        # Handle casual/greeting interactions
        if is_greeting_or_casual(question):
            casual_response = generate_casual_response(question, repo.repo_name)
            return {
                "response": casual_response,
                "metadata": {
                    "repository": repo.repo_name,
                    "interaction_type": "casual",
                    "execution_time": f"{time.time() - start_time:.2f}s"
                }
            }
        
        # Ensure Neo4j graph is loaded
        graph_loaded = neo4j_manager.ensure_graph_loaded(repository_id)
        if not graph_loaded:
            return {
                "response": f"⚠️ Graph data for **{repo.repo_name}** is not available. Please ensure the repository has been analyzed and indexed.",
                "metadata": {
                    "error": "Graph not loaded",
                    "repository": repo.repo_name
                }
            }
        
        # Generate and execute Cypher query
        repo_context = f"Repository: {repo.repo_name}, Language: {repo.language}, Description: {repo.description}"
        cypher_query = generate_cypher_from_question(question, repo_context)
        search_results = execute_cypher_query(cypher_query)
        
        # Enhanced fallback with multiple strategies
        if not search_results:
            fallback_strategies = [
                # Strategy 1: Broader search
                f"""
                MATCH (f:Feature)-[:PART_OF_FILE]->(file:File)
                OPTIONAL MATCH (f)<-[:PART_OF_FEATURE]-(func:Function)
                OPTIONAL MATCH (f)<-[:PART_OF_FEATURE]-(cls:Class)
                RETURN f.name, f.description, f.language, f.code, file.name as file_name,
                       collect(func.name) as functions, collect(cls.name) as classes
                LIMIT 10
                """,
                # Strategy 2: Focus on functions
                f"""
                MATCH (func:Function)-[:PART_OF_FEATURE]->(f:Feature)-[:PART_OF_FILE]->(file:File)
                RETURN func.name, func.signature, f.description, f.code, file.name as file_name
                LIMIT 10
                """,
                # Strategy 3: Focus on classes
                f"""
                MATCH (cls:Class)-[:PART_OF_FEATURE]->(f:Feature)-[:PART_OF_FILE]->(file:File)
                RETURN cls.name, cls.parent_class, f.description, f.code, file.name as file_name
                LIMIT 10
                """
            ]
            
            for strategy in fallback_strategies:
                search_results = execute_cypher_query(strategy)
                if search_results:
                    break
        
        # If still no results, provide a helpful response
        if not search_results:
            return {
                "response": f"🔍 **No Direct Matches Found**\n\nI searched through the **{repo.repo_name}** repository but couldn't find specific code elements matching your query. This could mean:\n\n• The feature you're looking for might use different terminology\n• The code might not be indexed yet\n• Try rephrasing your question with different keywords\n\n💡 **Tip**: Try asking about general concepts like 'show me the main functions' or 'what classes are available'",
                "metadata": {
                    "repository": repo.repo_name,
                    "files_analyzed": repo.files_analyzed,
                    "execution_time": f"{time.time() - start_time:.2f}s",
                    "results_found": 0,
                    "cypher_query": cypher_query,
                    "suggestion": "Try broader search terms"
                }
            }
        
        # Prepare enhanced context for LLM
        context_data = []
        for result in search_results:
            context_item = {
                "feature_name": result.get('f.name', result.get('func.name', result.get('cls.name', 'Unknown'))),
                "description": result.get('f.description', result.get('description', 'No description available')),
                "language": result.get('f.language', result.get('language', repo.language)),
                "file": result.get('file_name', result.get('file.name', 'Unknown file')),
                "type": "function" if result.get('func.name') else "class" if result.get('cls.name') else "feature"
            }
            
            # Add code snippet with smart truncation
            code = result.get('f.code', result.get('code', ''))
            if code:
                if len(code) > 800:
                    # Smart truncation - try to keep complete functions/classes
                    lines = code.split('\n')
                    if len(lines) > 20:
                        context_item["code_snippet"] = '\n'.join(lines[:15]) + f"\n... ({len(lines)-15} more lines)"
                    else:
                        context_item["code_snippet"] = code[:800] + "..."
                else:
                    context_item["code_snippet"] = code
            
            # Add additional metadata
            for key, value in result.items():
                if key not in ['f.name', 'f.description', 'f.language', 'f.code', 'file.name', 'file_name', 'description', 'code']:
                    if value and value != []:  # Only add non-empty values
                        context_item[key] = value
            
            context_data.append(context_item)
        
        # Generate enhanced response using preferred API
        response_prompt = f"""
You are an expert software analyst and code documentation assistant. Your role is to help developers understand codebases by providing clear, accurate, and actionable insights.

REPOSITORY CONTEXT:
- Name: {repo.repo_name}
- Language: {repo.language}
- Description: {repo.description}
- Files Analyzed: {repo.files_analyzed}

USER QUESTION: "{question}"

RELEVANT CODE ANALYSIS DATA:
{json.dumps(context_data, indent=2)}

INSTRUCTIONS:
1. **BE DIRECT & HELPFUL**: Answer the user's question directly and comprehensively
2. **USE SPECIFIC DETAILS**: Reference actual function names, class names, file locations
3. **PROVIDE CONTEXT**: Explain what the code does and how it fits into the larger system
4. **BE PRACTICAL**: Include actionable insights and usage examples when relevant
5. **STRUCTURE YOUR RESPONSE**: Use clear headings and bullet points for readability
6. **HIGHLIGHT KEY FINDINGS**: Emphasize the most important information
7. **AVOID GENERIC RESPONSES**: Never say "no data available" - always provide value from what's found

RESPONSE FORMAT:
- Start with a clear, direct answer
- Use markdown formatting for better readability
- Include code snippets when helpful
- Mention specific files and locations
- End with practical next steps or related suggestions

Your response should be informative, professional, and genuinely helpful to someone trying to understand this codebase.
"""

        try:
            response_text = get_api_response(response_prompt, temperature=0.4, max_tokens=2500)
        except Exception as e:
            return {
                "response": f"⚠️ **Analysis Error**\n\nI found {len(search_results)} relevant code elements in **{repo.repo_name}**, but encountered an issue generating the detailed analysis. The raw data is available in the metadata.",
                "metadata": {
                    "error": str(e),
                    "repository": repo.repo_name,
                    "results_found": len(search_results),
                    "raw_data": context_data[:3]  # Include first 3 results
                }
            }
        
        # Calculate confidence and execution time
        confidence = min(0.95, 0.5 + (len(search_results) * 0.03) + (len(context_data) * 0.02))
        execution_time = time.time() - start_time
        
        # Format the response beautifully
        formatted_response = format_response_beautifully(response_text, question, {
            "results_found": len(search_results),
            "confidence": confidence
        })
        
        return {
            "response": formatted_response,
            "metadata": {
                "repository": repo.repo_name,
                "files_analyzed": repo.files_analyzed,
                "execution_time": f"{execution_time:.2f}s",
                "confidence": confidence,
                "results_found": len(search_results),
                "api_used": PREFERRED_API,
                "cypher_query": cypher_query,
                "graph_loaded": True,
                "search_method": "enhanced_neo4j_graph_query"
            }
        }
        
    except Exception as e:
        return {
            "response": f"🚨 **System Error**\n\nI encountered an unexpected error while analyzing the repository: {str(e)}\n\nPlease try rephrasing your question or contact support if the issue persists.",
            "metadata": {
                "error": str(e),
                "execution_time": f"{time.time() - start_time:.2f}s",
                "api_used": PREFERRED_API
            }
        }

def get_graph_insights(repository_id: str) -> Dict[str, Any]:
    """Get comprehensive insights about the repository graph"""
    try:
        graph_loaded = neo4j_manager.ensure_graph_loaded(repository_id)
        if not graph_loaded:
            return {"error": "Could not load graph"}
        
        # Enhanced stats query
        stats_query = """
        OPTIONAL MATCH (f:Feature) WITH count(f) as features
        OPTIONAL MATCH (fn:Function) WITH features, count(fn) as functions
        OPTIONAL MATCH (c:Class) WITH features, functions, count(c) as classes
        OPTIONAL MATCH (file:File) WITH features, functions, classes, count(file) as files
        OPTIONAL MATCH (api:API) WITH features, functions, classes, files, count(api) as apis
        OPTIONAL MATCH (dep:Dependency) WITH features, functions, classes, files, apis, count(dep) as dependencies
        OPTIONAL MATCH (lang:File) WITH features, functions, classes, files, apis, dependencies, 
                       collect(DISTINCT lang.language) as languages
        RETURN features, functions, classes, files, apis, dependencies, languages
        """
        
        stats = neo4j_manager.query_graph(stats_query)
        
        # Get most connected and important features
        insights_query = """
        MATCH (f:Feature)
        OPTIONAL MATCH (f)-[r]-()
        WITH f, count(r) as connections
        ORDER BY connections DESC
        LIMIT 10
        RETURN f.name as feature, f.description as description, connections
        """
        
        important_features = neo4j_manager.query_graph(insights_query)
        
        # Get file distribution
        file_stats_query = """
        MATCH (file:File)
        OPTIONAL MATCH (file)<-[:PART_OF_FILE]-(f:Feature)
        WITH file, count(f) as feature_count
        RETURN file.name as filename, file.language as language, feature_count
        ORDER BY feature_count DESC
        LIMIT 10
        """
        
        file_stats = neo4j_manager.query_graph(file_stats_query)
        
        return {
            "stats": stats[0] if stats else {},
            "most_important_features": important_features,
            "file_distribution": file_stats
        }
        
    except Exception as e:
        return {"error": str(e)}

def test_enhanced_graph_rag():
    """Enhanced test function with better UI"""
    print("🚀 **Enhanced GraphRAG with Dynamic API Selection**")
    print(f"📡 **Current API**: {PREFERRED_API.upper()}")
    print(f"🔑 **Available APIs**: {'✅ Gemini' if gemini_client else '❌ Gemini'} | {'✅ Claude' if claude_client else '❌ Claude'}")
    print("\n" + "="*60)
    
    repos = repository_service.get_all_repositories()
    if not repos:
        print("❌ No repositories found. Please add some repositories first.")
        return
    
    print("📚 **Available Repositories**:")
    for i, repo in enumerate(repos, 1):
        status_emoji = "✅" if repo.status.value == "completed" else "⏳" if repo.status.value == "processing" else "❌"
        print(f"   {i}. {repo.repo_name} ({repo.language}) {status_emoji}")
    
    while True:
        try:
            print("\n" + "-"*60)
            repo_choice = input("🎯 **Select repository number** (or 'exit' to quit): ")
            if repo_choice.lower() in ['exit', 'quit', 'q']:
                print("👋 **Goodbye!** Happy coding!")
                break
            
            repo_index = int(repo_choice) - 1
            if 0 <= repo_index < len(repos):
                selected_repo = repos[repo_index]
                print(f"\n🎉 **Selected**: {selected_repo.repo_name}")
                
                # Show enhanced graph insights
                print("📊 **Loading repository insights...**")
                insights = get_graph_insights(selected_repo.id)
                
                if "error" not in insights:
                    stats = insights.get("stats", {})
                    print(f"\n📈 **Repository Statistics**:")
                    print(f"   🔹 Features: {stats.get('features', 0)}")
                    print(f"   🔹 Functions: {stats.get('functions', 0)}")
                    print(f"   🔹 Classes: {stats.get('classes', 0)}")
                    print(f"   🔹 Files: {stats.get('files', 0)}")
                    print(f"   🔹 APIs: {stats.get('apis', 0)}")
                    print(f"   🔹 Dependencies: {stats.get('dependencies', 0)}")
                    
                    languages = stats.get('languages', [])
                    if languages:
                        print(f"   🔹 Languages: {', '.join(languages)}")
                
                print(f"\n💬 **Chat with {selected_repo.repo_name}** (type 'back' to select another repo)")
                print("💡 **Examples**: 'What functions are available?', 'Show me the main classes', 'Hi'")
                
                while True:
                    question = input(f"\n🤔 **Your question**: ")
                    if question.lower() in ['back', 'b']:
                        break
                    
                    if not question.strip():
                        continue
                    
                    print("⏳ **Analyzing...**")
                    result = enhanced_graph_rag(question, selected_repo.id)
                    
                    print("\n" + "="*80)
                    print(result['response'])
                    
                    if result.get('metadata'):
                        metadata = result['metadata']
                        print(f"\n📊 **Metadata**:")
                        print(f"   ⏱️  Execution time: {metadata.get('execution_time', 'N/A')}")
                        if metadata.get('confidence'):
                            print(f"   🎯 Confidence: {metadata.get('confidence', 0):.0%}")
                        if metadata.get('results_found'):
                            print(f"   📋 Results found: {metadata.get('results_found', 'N/A')}")
                        if metadata.get('api_used'):
                            print(f"   🤖 API used: {metadata.get('api_used', 'N/A').upper()}")
                    
                    print("="*80)
                    
            else:
                print("❌ **Invalid selection**. Please try again.")
                
        except ValueError:
            print("❌ **Please enter a valid number**.")
        except KeyboardInterrupt:
            print("\n\n👋 **Exiting...** Goodbye!")
            break
        except Exception as e:
            print(f"❌ **Error**: {e}")

if __name__ == "__main__":
    test_enhanced_graph_rag()