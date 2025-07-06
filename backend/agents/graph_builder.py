import os
import json
from dotenv import load_dotenv
from neo4j import GraphDatabase

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
load_dotenv(dotenv_path=env_path)

#kylobunn
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
FEATURE_FILE = "pipeline_ner_output.json"


class KnowledgeGraphBuilder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_constraints(self):
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (f:Feature) REQUIRE f.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (i:Input) REQUIRE i.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (o:Output) REQUIRE o.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Dependency) REQUIRE d.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:SideEffect) REQUIRE s.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (r:Requirement) REQUIRE r.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (api:API) REQUIRE api.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (fn:Function) REQUIRE fn.name IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (fl:File) REQUIRE fl.name IS UNIQUE")

    def add_features(self, features):
        with self.driver.session() as session:
            session.execute_write(self._create_features_tx, features)

    @staticmethod
    def _create_features_tx(tx, features):
        for data in features:
            # Creating File node
            tx.run("""
                MERGE (fl:File {name: $file_name})
                SET fl.language = $language
            """, file_name=data["file"], language=data["language"])

            # Created Feature node and linked to File
            tx.run("""
                WITH CASE WHEN $annotations IS NOT NULL THEN $annotations ELSE NULL END AS safe_annotations
                MERGE (f:Feature {name: $feature_name})
                SET f.description = $description,
                    f.language = $language,
                    f.chunk_id = $chunk_id,
                    f.code = $code,
                    f.annotations = safe_annotations
                MERGE (fl:File {name: $file_name})
                MERGE (f)-[:PART_OF_FILE]->(fl)
            """, feature_name=data["feature"],
                 description=data["description"],
                 language=data["language"],
                 file_name=data["file"],
                 chunk_id=data["chunk_id"],
                 code=data["code"],
                 annotations=data.get("annotations", {}).get("comments", None))

            # Inputs
            for inp in data.get("inputs", []):
                tx.run("""
                    MERGE (i:Input {name: $name})
                    MERGE (f:Feature {name: $feature})
                    MERGE (f)-[:TAKES_INPUT]->(i)
                """, name=inp, feature=data["feature"])

            # Outputs
            for out in data.get("outputs", []):
                tx.run("""
                    MERGE (o:Output {name: $name})
                    MERGE (f:Feature {name: $feature})
                    MERGE (f)-[:PRODUCES]->(o)
                """, name=out, feature=data["feature"])

            # Dependencies
            for dep in data.get("dependencies", []):
                tx.run("""
                    MERGE (d:Dependency {name: $name})
                    MERGE (f:Feature {name: $feature})
                    MERGE (f)-[:DEPENDS_ON]->(d)
                """, name=dep, feature=data["feature"])

            # Side Effects
            for effect in data.get("side_effects", []):
                tx.run("""
                    MERGE (s:SideEffect {name: $name})
                    MERGE (f:Feature {name: $feature})
                    MERGE (f)-[:CAUSES]->(s)
                """, name=effect, feature=data["feature"])

            # Requirements
            for req in data.get("requirements", []):
                tx.run("""
                    MERGE (r:Requirement {name: $name})
                    MERGE (f:Feature {name: $feature})
                    MERGE (f)-[:REQUIRES]->(r)
                """, name=req, feature=data["feature"])

            # APIs
            for api in data.get("apis", []):
                tx.run("""
                    MERGE (a:API {name: $name})
                    MERGE (f:Feature {name: $feature})
                    MERGE (f)-[:USES_API]->(a)
                """, name=api, feature=data["feature"])


            # Functions
            for func in data.get("functions", []):
                if func.get("name"):  
                    tx.run("""
                        MERGE (fn:Function {name: $name, signature: $signature})
                        SET fn.start_line = $start_line, fn.end_line = $end_line
                        MERGE (f:Feature {name: $feature})
                        MERGE (fn)-[:PART_OF_FEATURE]->(f)
                    """, name=func["name"], signature=func["signature"],
                         start_line=func["start_line"], end_line=func["end_line"],
                         feature=data["feature"])

def main():
    kg = KnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    kg.create_constraints()

    with open(FEATURE_FILE, "r", encoding="utf-8") as f:
        features = json.load(f)

    kg.add_features(features)

    kg.close()
    print(" Knowledge graph built successfully in Neo4j.")

if __name__ == "__main__":
    main()
