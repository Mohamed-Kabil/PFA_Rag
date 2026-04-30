import certifi
import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Correction robuste pour les erreurs SSL sur Windows
os.environ['SSL_CERT_FILE'] = certifi.where()

load_dotenv()

class Neo4jManager:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        # Support pour NEO4J_USER ou NEO4J_USERNAME
        self.user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        
        if not all([self.uri, self.user, self.password]):
            raise ValueError(f"❌ Erreur : Credentials Neo4j manquants (URI: {self.uri}, User: {self.user})")
            
        print(f"🔌 Connexion à Neo4j ({self.uri}) en tant que '{self.user}'...")
        try:
            # On utilise TRUST_ALL_CERTIFICATES en plus de certifi pour une sécurité maximale/souplesse
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password),
                max_connection_lifetime=30 * 60,
                connection_timeout=30
            )
            self.driver.verify_connectivity()
            print("✅ Connexion Neo4j établie.")
        except Exception as e:
            print(f"⚠️ Échec de la connexion : {e}")
            raise ConnectionError(f"❌ Impossible de se connecter à Neo4j. Vérifiez vos identifiants et votre instance.\nErreur: {e}")

    def close(self):
        self.driver.close()

    def query(self, cypher, parameters=None):
        with self.driver.session() as session:
            return session.run(cypher, parameters)

    def clear_database(self):
        """Supprime tous les nœuds et relations pour repartir sur une base propre"""
        print("🗑️ Nettoyage de la base de données Neo4j...")
        # Suppression par blocs pour éviter de saturer la mémoire sur de gros graphes
        self.query("MATCH (n) DETACH DELETE n")
        print("✅ Base de données vidée.")

    def setup_constraints(self):
        """Crée les index et contraintes d'unicité pour un graphe propre"""
        print("⚙️ Configuration des contraintes Neo4j...")
        # Contrainte d'unicité sur l'ID pour éviter les doublons lors des MERGE
        constraints = [
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE"
        ]
        for c in constraints:
            try:
                self.query(c)
            except Exception as e:
                print(f"⚠️ Note sur contrainte : {e}")

    def upload_chunks(self, chunks_path):
        """Importe les chunks de texte pour lier les entités à leur source"""
        print(f"📥 Importation des chunks depuis {chunks_path}...")
        if not os.path.exists(chunks_path):
            print(f"❌ Fichier {chunks_path} introuvable.")
            return

        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        
        # MERGE permet d'éviter les doublons si on relance le script
        cypher = """
        UNWIND $data as row
        MERGE (c:Chunk {id: row.id})
        SET c.text = row.text,
            c.page = row.metadata.page_label
        """
        self.query(cypher, {"data": chunks})
        print(f"✅ {len(chunks)} chunks importés.")

    def upload_graph_data(self, graph_path):
        """Importe les entités et les relations sémantiques"""
        print(f"📥 Importation du graphe sémantique depuis {graph_path}...")
        if not os.path.exists(graph_path):
            print(f"❌ Fichier {graph_path} introuvable.")
            return

        with open(graph_path, "r", encoding="utf-8") as f:
            graph = json.load(f)

        # 1. Import des Nœuds (Entity) et lien avec les Chunks
        print("   - Création des nœuds Entity et relations MENTIONED_IN...")
        node_cypher = """
        UNWIND $nodes as row
        // On utilise le nom comme identifiant unique (slugifié ou direct)
        MERGE (e:Entity {id: toLower(row.name)})
        SET e.name = row.name, 
            e.type = row.type, 
            e.description = row.description
        WITH e, row
        UNWIND row.chunks as chunk_id
        MATCH (c:Chunk {id: chunk_id})
        MERGE (e)-[:MENTIONED_IN]->(c)
        """
        self.query(node_cypher, {"nodes": graph["nodes"]})

        # 2. Import des Relations (Edges)
        print("   - Création des relations sémantiques entre entités...")
        edge_cypher = """
        UNWIND $edges as row
        MATCH (source:Entity {id: toLower(row.source)})
        MATCH (target:Entity {id: toLower(row.target)})
        // Utilisation de la relation spécifiée dans le JSON
        CALL apoc.merge.relationship(source, row.relation, {}, {}, target) YIELD rel
        SET rel.chunk_id = row.chunk_id
        """
        try:
            self.query(edge_cypher, {"edges": graph["edges"]})
        except Exception as e:
            print(f"⚠️ Erreur lors de l'import des relations (APOC requis) : {e}")
            # Fallback
            fallback_cypher = """
            UNWIND $edges as row
            MATCH (source:Entity {id: toLower(row.source)})
            MATCH (target:Entity {id: toLower(row.target)})
            MERGE (source)-[r:RELATED_TO]->(target)
            SET r.original_relation = row.relation, r.chunk_id = row.chunk_id
            """
            self.query(fallback_cypher, {"edges": graph["edges"]})
        
        print(f"✅ {len(graph['nodes'])} entités et {len(graph['edges'])} relations traitées.")

    def run_louvain(self):
        """Détection de communautés Louvain (GDS ou Fallback Local)"""
        print("🧪 Lancement de l'algorithme Louvain...")
        
        with self.driver.session() as session:
            try:
                # Tentative native GDS (pour les versions pro/locales)
                session.run("CALL gds.graph.drop('myGraph', false)").consume()
                session.run("CALL gds.graph.project('myGraph', 'Entity', '*')").consume()
                louvain_cypher = "CALL gds.louvain.write('myGraph', {writeProperty: 'communityId'}) YIELD communityCount, modularity"
                result = session.run(louvain_cypher).single()
                print(f"✅ Louvain (GDS) terminé : {result['communityCount']} communautés.")
            except Exception:
                print("⚠️ GDS non disponible. Passage au calcul local (NetworkX)...")
                try:
                    import networkx as nx
                    import community as community_louvain # python-louvain
                    
                    # 1. Récupérer TOUTES les relations depuis Neo4j
                    graph_data = session.run("MATCH (s:Entity)-[r]->(t:Entity) RETURN s.id as s, t.id as t").data()
                    
                    if not graph_data:
                        print("❌ Graphe vide, impossible de calculer les communautés.")
                        return
                        
                    G = nx.Graph()
                    for rel in graph_data:
                        G.add_edge(rel['s'], rel['t'])
                    
                    # 2. Calculer Louvain localement
                    partition = community_louvain.best_partition(G)
                    
                    # 3. Réinjecter dans Neo4j
                    update_cypher = """
                    UNWIND $data as row
                    MATCH (e:Entity {id: row.id})
                    SET e.communityId = row.cid
                    """
                    data_to_push = [{"id": node, "cid": cid} for node, cid in partition.items()]
                    session.run(update_cypher, {"data": data_to_push})
                    print(f"✅ Louvain (Local) terminé : {len(set(partition.values()))} communautés injectées.")
                    
                except ImportError:
                    print("❌ Bibliothèques networkx ou python-louvain manquantes.")
                except Exception as e:
                    print(f"❌ Échec du calcul local : {e}")

    def run_pipeline(self, chunks_path, graph_path):
        """Pipeline complet d'ingestion et d'analyse"""
        print("\n🚀 DÉMARRAGE DE L'IMPORTATION NEO4J\n")
        try:
            self.clear_database() # Nettoyage pour repartir sur une base propre
            self.setup_constraints()
            self.upload_chunks(chunks_path)
            self.upload_graph_data(graph_path)
            self.run_louvain()
            print("\n🎉 PIPELINE NEO4J TERMINÉ AVEC SUCCÈS !")
        finally:
            self.close()

if __name__ == "__main__":
    manager = Neo4jManager()
    # Chemins par défaut
    manager.run_pipeline(
        "agentic_graph_rag/data/corpus_chunks.json",
        "agentic_graph_rag/data/knowledge_graph.json"
    )
