import certifi
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase
from backend import config

os.environ["SSL_CERT_FILE"] = certifi.where()


class Neo4jManager:
    def __init__(self):
        self.uri = config.NEO4J_URI
        self.user = config.NEO4J_USER
        self.password = config.NEO4J_PASSWORD

        if not all([self.uri, self.user, self.password]):
            raise ValueError("Credentials Neo4j manquants.")

        print(f"Connexion Neo4j : {self.uri}")

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
            max_connection_lifetime=30 * 60,
            connection_timeout=30,
        )
        self.driver.verify_connectivity()

        print("Connexion Neo4j etablie.")

    def close(self):
        self.driver.close()

    def query(self, cypher, parameters=None):
        with self.driver.session() as session:
            result = session.run(cypher, parameters)
            return list(result)

    def clear_database(self):
        print("Nettoyage Neo4j...")
        self.query("MATCH (n) DETACH DELETE n")
        print("Base videe.")

    def setup_constraints(self):
        print("Creation contraintes...")

        constraints = [
            """
            CREATE CONSTRAINT entity_id_unique
            IF NOT EXISTS
            FOR (e:Entity)
            REQUIRE e.id IS UNIQUE
            """,
            """
            CREATE CONSTRAINT chunk_id_unique
            IF NOT EXISTS
            FOR (c:Chunk)
            REQUIRE c.id IS UNIQUE
            """,
        ]

        for constraint in constraints:
            try:
                self.query(constraint)
            except Exception as exc:
                print(f"Contrainte : {exc}")

    def normalize_relation_value(self, relation):
        relation = str(relation or "related_to").strip().lower()
        relation = relation.replace("-", "_").replace(" ", "_")
        relation = re.sub(r"[^a-z0-9_]", "", relation)
        return relation or "related_to"

    def upload_chunks(self, chunks_path):
        print(f"Import chunks : {chunks_path}")

        chunks_path = Path(chunks_path)
        if not chunks_path.exists():
            print(f"Fichier introuvable : {chunks_path}")
            return

        with open(chunks_path, "r", encoding="utf-8") as handle:
            chunks = json.load(handle)

        cypher = """
        UNWIND $data AS row
        MERGE (c:Chunk {id: row.id})
        SET
            c.text = row.text,
            c.page = coalesce(row.metadata.page_label, ""),
            c.section = coalesce(row.metadata.section, ""),
            c.chapter = coalesce(row.metadata.chapter, "")
        """

        self.query(cypher, {"data": chunks})
        print(f"{len(chunks)} chunks importes.")

    def upload_graph_data(self, graph_path):
        print(f"Import graphe : {graph_path}")

        graph_path = Path(graph_path)
        if not graph_path.exists():
            print(f"Fichier introuvable : {graph_path}")
            return

        with open(graph_path, "r", encoding="utf-8") as handle:
            graph = json.load(handle)

        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])

        print("Creation entites...")

        node_cypher = """
        UNWIND $nodes AS row
        MERGE (e:Entity {id: toLower(row.name)})
        SET
            e.name = row.name,
            e.type = coalesce(row.type, "concept"),
            e.description = coalesce(row.description, "")
        WITH e, row
        FOREACH (
            chunk_id IN coalesce(row.chunks, []) |
            MERGE (c:Chunk {id: chunk_id})
            MERGE (e)-[:MENTIONED_IN]->(c)
        )
        """

        self.query(node_cypher, {"nodes": nodes})
        print(f"{len(nodes)} entites creees.")

        print("Creation relations...")
        imported_edges = 0

        edge_cypher = """
        MERGE (s:Entity {id: toLower($source_id)})
        ON CREATE SET
            s.name = $source_name,
            s.type = "concept"
        MERGE (t:Entity {id: toLower($target_id)})
        ON CREATE SET
            t.name = $target_name,
            t.type = "concept"
        MERGE (s)-[r:RELATED_TO {type: $relation}]->(t)
        SET
            r.chunk_id = $chunk_id,
            r.chunk_ids = coalesce($chunk_ids, []),
            r.type = $relation,
            r.evidence_count = coalesce($evidence_count, 1),
            r.weight = coalesce($weight, 1.0)
        """

        with self.driver.session() as session:
            for edge in edges:
                try:
                    relation = self.normalize_relation_value(edge.get("relation"))
                    session.run(
                        edge_cypher,
                        {
                            "source_id": edge["source"],
                            "source_name": edge["source"],
                            "target_id": edge["target"],
                            "target_name": edge["target"],
                            "relation": relation,
                            "chunk_id": edge.get("chunk_id"),
                            "chunk_ids": edge.get("chunk_ids", []),
                            "evidence_count": edge.get("evidence_count", 1),
                            "weight": edge.get("weight", 1.0),
                        },
                    ).consume()
                    imported_edges += 1
                except Exception as exc:
                    print(
                        f"Erreur relation : {edge.get('relation')} -> {exc}"
                    )

        print(f"{imported_edges} relations creees.")

    def run_louvain(self):
        print("Calcul Louvain local...")

        with self.driver.session() as session:
            try:
                import community as community_louvain
                import networkx as nx

                graph_data = session.run(
                    """
                    MATCH (s:Entity)-[r:RELATED_TO]->(t:Entity)
                    RETURN
                        s.id AS s,
                        t.id AS t,
                        coalesce(r.weight, 1.0) AS weight
                    """
                ).data()

                if not graph_data:
                    print("Graphe vide.")
                    return

                graph = nx.Graph()
                for relation in graph_data:
                    graph.add_edge(
                        relation["s"],
                        relation["t"],
                        weight=float(relation["weight"]),
                    )

                print(
                    f"Graphe NetworkX : {len(graph.nodes())} noeuds / "
                    f"{len(graph.edges())} relations"
                )

                partition = community_louvain.best_partition(
                    graph,
                    weight="weight",
                    random_state=42,
                )
                modularity = community_louvain.modularity(
                    partition,
                    graph,
                    weight="weight",
                )

                print(f"Communautes : {len(set(partition.values()))}")
                print(f"Modularity : {modularity:.4f}")

                update_cypher = """
                UNWIND $data AS row
                MATCH (e:Entity {id: row.id})
                SET e.communityId = row.cid
                """

                data_to_push = [
                    {"id": node, "cid": int(cid)}
                    for node, cid in partition.items()
                ]

                session.run(update_cypher, {"data": data_to_push}).consume()
                print("Communautes sauvegardees.")
            except Exception as exc:
                print(f"Erreur Louvain local : {exc}")

    def run_pipeline(self, chunks_path, graph_path, clear_first=None):
        print("\n=== PIPELINE NEO4J ===\n")

        try:
            if clear_first is None:
                clear_first = (
                    os.getenv("NEO4J_CLEAR_ON_IMPORT", "false").lower()
                    == "true"
                )

            if clear_first:
                self.clear_database()

            self.setup_constraints()
            self.upload_chunks(chunks_path)
            self.upload_graph_data(graph_path)
            self.run_louvain()
            print("\nPIPELINE TERMINE")
        finally:
            self.close()


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"

    manager = Neo4jManager()
    manager.run_pipeline(
        str(DATA_DIR / "corpus_chunks.json"),
        str(DATA_DIR / "knowledge_graph.json"),
    )
