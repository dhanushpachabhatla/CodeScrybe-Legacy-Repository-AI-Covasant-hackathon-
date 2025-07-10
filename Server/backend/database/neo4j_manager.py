# backend/database/neo4j_manager.py
import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from dotenv import load_dotenv
from .models import repository_service, graph_service

load_dotenv()

class Neo4jManager:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USERNAME") 
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.current_repo_id = None
        self.current_graph_hash = None
        
    def close(self):
        if self.driver:
            self.driver.close()
    
    def get_graph_fingerprint(self, features: List[dict]) -> str:
        """Generate a hash fingerprint of the graph data"""
        # Create a deterministic hash based on the feature data
        fingerprint_data = []
        for feature in features:
            # Sort keys to ensure consistent hashing
            sorted_feature = {k: v for k, v in sorted(feature.items())}
            fingerprint_data.append(sorted_feature)
        
        # Create hash from sorted data
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    def clear_graph(self):
        """Clear all data from Neo4j"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        self.current_repo_id = None
        self.current_graph_hash = None
    
    def is_graph_loaded(self, repo_id: str) -> tuple[bool, Optional[str]]:
        """Check if graph is already loaded for this repository"""
        if self.current_repo_id != repo_id:
            return False, None
            
        # Get current graph fingerprint from MongoDB
        features = graph_service.get_graph_data(repo_id)
        if not features:
            return False, None
            
        current_hash = self.get_graph_fingerprint([f['properties'] for f in features])
        return self.current_graph_hash == current_hash, current_hash
    
    def create_constraints(self):
        """Create Neo4j constraints"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (f:Feature) REQUIRE f.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Input) REQUIRE i.name IS UNIQUE", 
            "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Output) REQUIRE o.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Dependency) REQUIRE d.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:SideEffect) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (r:Requirement) REQUIRE r.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (api:API) REQUIRE api.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (fn:Function) REQUIRE fn.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (fl:File) REQUIRE fl.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Class) REQUIRE c.name IS UNIQUE"
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"Warning: Could not create constraint: {e}")
    
    def load_graph_from_mongodb(self, repo_id: str) -> bool:
        """Load graph data from MongoDB into Neo4j"""
        try:
            # Get graph data from MongoDB
            graph_data = graph_service.get_graph_data(repo_id)
            if not graph_data:
                print(f"No graph data found in MongoDB for repo {repo_id}")
                return False
            
            # Clear existing graph
            self.clear_graph()
            
            # Create constraints
            self.create_constraints()
            
            # Build graph from MongoDB data
            features = [item['properties'] for item in graph_data]
            self._build_graph_from_features(features)
            
            # Update tracking
            self.current_repo_id = repo_id
            self.current_graph_hash = self.get_graph_fingerprint(features)
            
            print(f"✅ Graph loaded from MongoDB for repo {repo_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading graph from MongoDB: {e}")
            return False
    
    def _build_graph_from_features(self, features: List[dict]):
        """Build Neo4j graph from feature data (same logic as original builder)"""
        with self.driver.session() as session:
            session.execute_write(self._create_features_tx, features)
    
    @staticmethod
    def _create_features_tx(tx, features):
        """Transaction to create features and relationships in Neo4j"""
        for data in features:
            # Create File node
            tx.run("""
                MERGE (fl:File {name: $file_name})
                SET fl.language = $language
            """, file_name=data["file"], language=data["language"])

            # Create Feature node and link to File
            annotations = data.get("annotations", {})
            annotations_json = json.dumps(annotations) if annotations else "{}"
            
            tx.run("""
                MERGE (f:Feature {name: $feature_name})
                SET f.description = $description,
                    f.language = $language,
                    f.chunk_id = $chunk_id,
                    f.code = $code,
                    f.annotations = $annotations_json
                MERGE (fl:File {name: $file_name})
                MERGE (f)-[:PART_OF_FILE]->(fl)
            """, feature_name=data["feature"],
                 description=data["description"],
                 language=data["language"],
                 file_name=data["file"],
                 chunk_id=data["chunk_id"],
                 code=data["code"],
                 annotations_json=annotations_json)

            # Create Functions
            for func in data.get("functions", []):
                if func.get("name"):
                    tx.run("""
                        MERGE (fn:Function {name: $name})
                        SET fn.signature = $signature,
                            fn.start_line = $start_line,
                            fn.end_line = $end_line,
                            fn.class = $class_name
                        MERGE (f:Feature {name: $feature})
                        MERGE (fn)-[:PART_OF_FEATURE]->(f)
                    """, name=func["name"], 
                         signature=func.get("signature", ""),
                         start_line=func.get("start_line", 0),
                         end_line=func.get("end_line", 0),
                         class_name=func.get("class", ""),
                         feature=data["feature"])

            # Create Classes
            for cls in data.get("classes", []):
                if cls.get("name"):
                    methods = cls.get("methods", [])
                    methods_json = json.dumps(methods) if methods else "[]"
                    
                    tx.run("""
                        MERGE (c:Class {name: $name})
                        SET c.parent_class = $parent_class,
                            c.methods = $methods_json
                        MERGE (f:Feature {name: $feature})
                        MERGE (c)-[:PART_OF_FEATURE]->(f)
                    """, name=cls["name"],
                         parent_class=cls.get("parent_class", ""),
                         methods_json=methods_json,
                         feature=data["feature"])
                    
                    # Create inheritance relationships
                    if cls.get("parent_class"):
                        tx.run("""
                            MATCH (c:Class {name: $child})
                            MERGE (p:Class {name: $parent})
                            MERGE (c)-[:INHERITS_FROM]->(p)
                        """, child=cls["name"], parent=cls["parent_class"])

            # Create APIs
            for api in data.get("apis", []):
                tx.run("""
                    MERGE (a:API {name: $name})
                    MERGE (f:Feature {name: $feature})
                    MERGE (f)-[:USES_API]->(a)
                """, name=api, feature=data["feature"])

            # Create Dependencies
            for dep in data.get("dependencies", []):
                tx.run("""
                    MERGE (d:Dependency {name: $name})
                    MERGE (f:Feature {name: $feature})
                    MERGE (f)-[:DEPENDS_ON]->(d)
                """, name=dep, feature=data["feature"])

            # Create Inputs
            for inp in data.get("inputs", []):
                tx.run("""
                    MERGE (i:Input {name: $name})
                    MERGE (f:Feature {name: $feature})
                    MERGE (f)-[:TAKES_INPUT]->(i)
                """, name=inp, feature=data["feature"])

            # Create Outputs
            for out in data.get("outputs", []):
                tx.run("""
                    MERGE (o:Output {name: $name})
                    MERGE (f:Feature {name: $feature})
                    MERGE (f)-[:PRODUCES]->(o)
                """, name=out, feature=data["feature"])

            # Create Side Effects
            for effect in data.get("side_effects", []):
                tx.run("""
                    MERGE (s:SideEffect {name: $name})
                    MERGE (f:Feature {name: $feature})
                    MERGE (f)-[:CAUSES]->(s)
                """, name=effect, feature=data["feature"])

            # Create Requirements
            for req in data.get("requirements", []):
                tx.run("""
                    MERGE (r:Requirement {name: $name})
                    MERGE (f:Feature {name: $feature})
                    MERGE (f)-[:REQUIRES]->(r)
                """, name=req, feature=data["feature"])

    def ensure_graph_loaded(self, repo_id: str) -> bool:
        """Ensure graph is loaded for the specified repository"""
        is_loaded, current_hash = self.is_graph_loaded(repo_id)
        
        if is_loaded:
            print(f"✅ Graph already loaded for repo {repo_id}")
            return True
        
        print(f"🔄 Loading graph for repo {repo_id}...")
        return self.load_graph_from_mongodb(repo_id)
    
    def query_graph(self, cypher_query: str, parameters: dict = None) -> List[dict]:
        """Execute a Cypher query on the current graph"""
        if parameters is None:
            parameters = {}
            
        with self.driver.session() as session:
            result = session.run(cypher_query, parameters)
            return [record.data() for record in result]

# Global Neo4j manager instance
neo4j_manager = Neo4jManager()

# Cleanup on exit
import atexit
atexit.register(neo4j_manager.close)