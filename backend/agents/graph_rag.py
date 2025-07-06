import os
import json
from dotenv import load_dotenv
from neo4j import GraphDatabase
from google import genai

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

#kylobun credentials
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def generate_cypher_from_question(question):
    """
    Use Gemini to generate a Cypher query from natural language.
    """
    cypher_prompt = f"""
You are an AI assistant that converts natural language questions into Cypher queries for Neo4j.

The graph contains these node types:
- Feature, Input, Output, Dependency, SideEffect, Requirement, API, Function, File

The relationships include:
- (Feature)-[:PART_OF_FILE]->(File) 
- (Feature)-[:TAKES_INPUT]->(Input)
- (Feature)-[:PRODUCES]->(Output)
- (Feature)-[:DEPENDS_ON]->(Dependency)
- (Feature)-[:CAUSES]->(SideEffect)
- (Feature)-[:REQUIRES]->(Requirement)
- (Feature)-[:USES_API]->(API)
- (Function)-[:PART_OF_FEATURE]->(Feature)

**Important rules:**
1. For file name filtering, always use `file.name CONTAINS "<partial name>"`.
2. Include OPTIONAL MATCH for related nodes for richer subgraph context when needed.
3. If the question asks for specific attributes (e.g., "code of feature"), generate a Cypher query that only returns those attributes like only return code if asked for code dont indclude any other useless optional matches.
4. The `Feature` node has attributes: name, description, code, language, file, chunk_id, annotations.
5. When the user asks for "code of feature", generate a query that returns `f.code`.
6. The `File` node does NOT have a `code` property.

User Question: "{question}"

Return only the Cypher query. No explanations or markdown.
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=cypher_prompt
    )
    cypher_query = response.text.strip().strip("```").strip("cypher").strip()
    print(f" Generated Cypher Query:\n{cypher_query}\n")
    return cypher_query

def execute_cypher_query(tx, cypher_query):
    """
    Execute the Cypher query and return raw Neo4j results.
    """
    result = tx.run(cypher_query)
    data = [record.data() for record in result]
    return data

def graph_rag(question):
    try:
        cypher_query = generate_cypher_from_question(question)

        with driver.session() as session:
            result_data = session.execute_read(execute_cypher_query, cypher_query)

        if not result_data:
            return " No relevant information found in the graph."

        prompt = f"""
You are an expert software analyst. Using the following Neo4j query results, answer the user’s question in clear, concise English.

User Question: "{question}"
Neo4j Query Results: {json.dumps(result_data, indent=2)}

Answer:
"""
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text.strip()

    except Exception as e:
        return f" Error: {e}"

if __name__ == "__main__":
    print("🚀 GraphRAG with Gemini (natural language answers) is ready!")
    while True:
        user_question = input("\nAsk a question (or type 'exit' to quit): ")
        if user_question.lower() in ["exit", "quit"]:
            break
        answer = graph_rag(user_question)
        print(f"\n Answer: {answer}")

driver.close()