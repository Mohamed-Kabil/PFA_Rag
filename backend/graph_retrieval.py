import os
import json

import certifi
from dotenv import load_dotenv
from neo4j import GraphDatabase

# SSL fix for Windows
os.environ["SSL_CERT_FILE"] = certifi.where()

from backend import config


class GraphRetriever:
    def __init__(self):
        self.uri = config.NEO4J_URI
        self.user = config.NEO4J_USER
        self.password = config.NEO4J_PASSWORD

        if not all([self.uri, self.user, self.password]):
            raise ValueError("Credentials Neo4j manquants pour le Retriever.")

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
        )

    def close(self):
        self.driver.close()

    def search_entities(self, query_text):
        """Recherche des entites mentionnees dans la requete et leurs voisins."""
        words = [w.strip() for w in query_text.lower().split() if len(w) > 3]
        if not words:
            return []

        cypher = """
        MATCH (e:Entity)
        WHERE any(word IN $words WHERE toLower(e.name) CONTAINS word)
        CALL (e) {
            OPTIONAL MATCH (e)-[r:RELATED_TO]->(neighbor:Entity)
            WITH r, neighbor
            WHERE neighbor IS NOT NULL
            WITH r, neighbor
            ORDER BY coalesce(r.weight, 1.0) DESC,
                     coalesce(r.evidence_count, 1) DESC,
                     neighbor.name
            RETURN collect({
                rel: coalesce(r.type, "related_to"),
                target: neighbor.name,
                weight: coalesce(r.weight, 1.0),
                evidence_count: coalesce(r.evidence_count, 1),
                chunk_ids: coalesce(r.chunk_ids, [])
            })[0..5] as relations
        }
        RETURN e.name as entity,
               e.type as type,
               e.description as description,
               relations,
               e.communityId as community
        LIMIT 10
        """

        with self.driver.session() as session:
            result = session.run(cypher, {"words": words})
            return [record.data() for record in result]

    def get_community_context(self, community_id):
        """Recupere les concepts d'une communaute pour donner une vue d'ensemble."""
        if community_id is None:
            return []

        cypher = """
        MATCH (e:Entity {communityId: $cid})
        RETURN e.name as name, e.description as description
        LIMIT 20
        """
        with self.driver.session() as session:
            result = session.run(cypher, {"cid": community_id})
            return [record.data() for record in result]

    def get_shortest_path(self, start_entity, end_entity):
        """Trouve le chemin le plus court entre deux concepts."""
        cypher = """
        MATCH (start:Entity {id: toLower($start)}),
              (end:Entity {id: toLower($end)})
        MATCH p = shortestPath((start)-[:RELATED_TO*]-(end))
        RETURN [n in nodes(p) | n.name] as nodes,
               [r in relationships(p) | coalesce(r.type, "related_to")] as rels,
               [r in relationships(p) | {
                   rel: coalesce(r.type, "related_to"),
                   weight: coalesce(r.weight, 1.0),
                   evidence_count: coalesce(r.evidence_count, 1),
                   chunk_ids: coalesce(r.chunk_ids, [])
               }] as rel_details
        """
        with self.driver.session() as session:
            result = session.run(
                cypher,
                {"start": start_entity, "end": end_entity},
            ).single()
            if result:
                return result.data()
            return None

    def get_graph_metrics(self):
        """Calcule les metriques globales sur le backbone semantique RELATED_TO."""
        cypher = """
        MATCH (e:Entity)
        WITH count(DISTINCT e) as nodeCount
        MATCH (:Entity)-[r:RELATED_TO]->(:Entity)
        WITH nodeCount, count(r) as edgeCount
        RETURN nodeCount,
               edgeCount,
               CASE
                   WHEN nodeCount > 1
                   THEN toFloat(edgeCount) / (nodeCount * (nodeCount - 1))
                   ELSE 0
               END as density
        """
        with self.driver.session() as session:
            res = session.run(cypher).single()

            centrality_cypher = """
            MATCH (e:Entity)
            OPTIONAL MATCH (e)-[r:RELATED_TO]-(:Entity)
            RETURN e.name as name, count(r) as degree
            ORDER BY degree DESC
            LIMIT 5
            """
            centrality = {
                rec["name"]: rec["degree"]
                for rec in session.run(centrality_cypher)
            }

            return {
                "nodes": res["nodeCount"],
                "edges": res["edgeCount"],
                "density": res["density"],
                "top_centrality": centrality,
            }

    def retrieve_graph_context(self, query_text):
        """Methode principale pour obtenir le contexte du graphe."""
        entities = self.search_entities(query_text)
        if not entities:
            return "Aucune entite semantique trouvee dans le graphe."

        context = "CONTEXTE GRAPHE (Entites et Relations):\n"
        for ent in entities:
            name = ent.get("entity", "Inconnu")
            etype = ent.get("type", "Concept")
            desc = ent.get("description", "Pas de description disponible.")

            context += f"- {name} ({etype}): {desc}\n"

            relations = ent.get("relations", [])
            for rel in relations:
                target = rel.get("target")
                rel_type = rel.get("rel", "related_to")
                if target:
                    weight = rel.get("weight", 1.0)
                    evidence_count = rel.get("evidence_count", 1)
                    context += (
                        f"  - [{rel_type} | "
                        f"w={weight} | evidence={evidence_count}] -> {target}\n"
                    )

        communities = [
            e.get("community")
            for e in entities
            if e.get("community") is not None
        ]
        if communities:
            dom_community = max(set(communities), key=communities.count)
            comm_nodes = self.get_community_context(dom_community)
            context += f"\nTHEME ASSOCIE (Communaute {dom_community}):\n"
            context += ", ".join([n.get("name", "Inconnu") for n in comm_nodes])
            context += "\n"

        return context


if __name__ == "__main__":
    retriever = GraphRetriever()
    try:
        query = "Comment le changement climatique affecte la survie des especes ?"
        print(retriever.retrieve_graph_context(query))
    finally:
        retriever.close()
