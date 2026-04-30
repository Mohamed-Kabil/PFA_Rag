import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
import certifi

# SSL fix for Windows
os.environ['SSL_CERT_FILE'] = certifi.where()

load_dotenv()

class GraphRetriever:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        if not all([self.uri, self.user, self.password]):
            raise ValueError("❌ Credentials Neo4j manquants pour le Retriever.")
            
        self.driver = GraphDatabase.driver(
            self.uri, 
            auth=(self.user, self.password)
        )

    def close(self):
        self.driver.close()

    def search_entities(self, query_text):
        """Recherche des entités mentionnées dans la requête et leurs voisins"""
        # Note: Dans une version avancée, on utiliserait un modèle NER ici.
        # Pour l'instant, on va chercher des correspondances de mots-clés dans Neo4j.
        
        words = [w.strip() for w in query_text.lower().split() if len(w) > 3]
        if not words:
            return []

        # Cypher pour trouver les nœuds dont le nom contient l'un des mots-clés
        cypher = """
        MATCH (e:Entity)
        WHERE any(word IN $words WHERE toLower(e.name) CONTAINS word)
        OPTIONAL MATCH (e)-[r]->(neighbor:Entity)
        RETURN e.name as entity, e.type as type, e.description as description, 
               collect({rel: type(r), target: neighbor.name})[0..5] as relations,
               e.communityId as community
        LIMIT 10
        """
        
        with self.driver.session() as session:
            result = session.run(cypher, {"words": words})
            return [record.data() for record in result]

    def get_community_context(self, community_id):
        """Récupère tous les concepts d'une communauté pour donner une vue d'ensemble"""
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

    def retrieve_graph_context(self, query_text):
        """Méthode principale pour obtenir le contexte du graphe"""
        entities = self.search_entities(query_text)
        if not entities:
            return "Aucune entité sémantique trouvée dans le graphe."
            
        context = "CONTEXTE GRAPHE (Entités et Relations):\n"
        for ent in entities:
            name = ent.get('entity', 'Inconnu')
            etype = ent.get('type', 'Concept')
            desc = ent.get('description', 'Pas de description disponible.')
            
            context += f"- {name} ({etype}): {desc}\n"
            
            # Gestion sécurisée des relations
            relations = ent.get('relations', [])
            for rel in relations:
                target = rel.get('target')
                rel_type = rel.get('rel', 'RELIE_A')
                if target:
                    context += f"  └─ [{rel_type}] -> {target}\n"
                    
        # Optionnel: Ajouter le contexte de la communauté dominante
        communities = [e.get('community') for e in entities if e.get('community') is not None]
        if communities:
            dom_community = max(set(communities), key=communities.count)
            comm_nodes = self.get_community_context(dom_community)
            context += f"\nTHÈME ASSOCIÉ (Communauté {dom_community}):\n"
            context += ", ".join([n.get('name', 'Inconnu') for n in comm_nodes]) + "\n"
            
        return context

if __name__ == "__main__":
    retriever = GraphRetriever()
    try:
        query = "Comment le changement climatique affecte la survie des espèces ?"
        print(retriever.retrieve_graph_context(query))
    finally:
        retriever.close()
