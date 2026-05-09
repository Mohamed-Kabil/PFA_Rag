import os
import certifi
from dotenv import load_dotenv

import networkx as nx
from neo4j import GraphDatabase
from community import community_louvain

# SSL Fix Windows
os.environ['SSL_CERT_FILE'] = certifi.where()

# =====================================================
# LOAD ENV VARIABLES
# =====================================================
load_dotenv()

# =====================================================
# NEO4J CONFIG
# =====================================================
URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(
    URI,
    auth=(USER, PASSWORD)
)

# =====================================================
# LOAD GRAPH FROM NEO4J
# =====================================================
def load_graph():

    G = nx.Graph()

    query = """
    MATCH (a)-[r]->(b)
    WHERE a.name IS NOT NULL
      AND b.name IS NOT NULL
    RETURN a.name AS source,
           b.name AS target,
           type(r) AS relation
    """

    with driver.session() as session:

        results = session.run(query)

        for row in results:

            source = row["source"]
            target = row["target"]
            relation = row["relation"]

            if not source or not target:
                continue

            if source == target:
                continue

            G.add_edge(
                source,
                target,
                relation=relation
            )

    return G

# =====================================================
# GRAPH TOPOLOGY CLEANING
# =====================================================
def clean_graph_topology(
    G,
    min_degree=2
):

    print("\nNettoyage topologique...")

    initial_nodes = len(G.nodes())

    low_degree_nodes = [
        n for n in G.nodes()
        if G.degree(n) < min_degree
    ]

    G.remove_nodes_from(low_degree_nodes)

    removed = len(low_degree_nodes)

    print(f"Noeuds supprimés : {removed}")
    print(f"Noeuds restants : {len(G.nodes())}")

    return G

# =====================================================
# CENTRALITY ANALYSIS
# =====================================================
def compute_centrality(G):

    print("\nCalcul des centralités...")

    pagerank = nx.pagerank(G)

    degree = nx.degree_centrality(G)

    betweenness = nx.betweenness_centrality(
        G,
        k=min(100, len(G.nodes()))
    )

    return {
        "pagerank": pagerank,
        "degree": degree,
        "betweenness": betweenness
    }

# =====================================================
# DETECT COMMUNITIES WITH LOUVAIN
# =====================================================
def detect_communities(G):

    print("\nDétection Louvain...")

    partition = community_louvain.best_partition(
        G,
        random_state=42
    )

    modularity = community_louvain.modularity(
        partition,
        G
    )

    return partition, modularity

# =====================================================
# GENERATE COMMUNITY SUMMARY
# =====================================================
def generate_community_summary(
    top_nodes
):

    if len(top_nodes) == 0:
        return "Communauté vide."

    summary = (
        "Cette communauté regroupe les concepts liés à "
        + ", ".join(top_nodes[:3])
        + "."
    )

    return summary

# =====================================================
# LABEL COMMUNITIES
# =====================================================
def label_communities(
    G,
    partition,
    centrality
):

    communities = {}

    # -------------------------------------------------
    # Group nodes by community
    # -------------------------------------------------
    for node, cid in partition.items():

        communities.setdefault(
            cid,
            []
        ).append(node)

    labels = {}

    # -------------------------------------------------
    # Build semantic labels
    # -------------------------------------------------
    for cid, nodes in communities.items():

        # Top PageRank nodes
        top_nodes = sorted(
            nodes,
            key=lambda n:
                centrality["pagerank"].get(n, 0),
            reverse=True
        )[:5]

        label = " / ".join(top_nodes[:3])

        summary = generate_community_summary(
            top_nodes
        )

        labels[cid] = {
            "label": label,
            "summary": summary,
            "size": len(nodes),
            "top_nodes": top_nodes
        }

    return labels

# =====================================================
# SAVE COMMUNITIES TO NEO4J
# =====================================================
def save_communities_to_neo4j(
    partition,
    labels
):

    print("\nSauvegarde des communautés dans Neo4j...")

    query = """
    MATCH (n {name: $name})
    SET n.community = $community,
        n.community_label = $label,
        n.community_summary = $summary
    """

    with driver.session() as session:

        for node, cid in partition.items():

            label = labels[cid]["label"]

            summary = labels[cid]["summary"]

            session.run(
                query,
                name=node,
                community=int(cid),
                label=label,
                summary=summary
            )

    print("Communautés sauvegardées.")

# =====================================================
# DISPLAY COMMUNITIES
# =====================================================
def display_communities(
    labels,
    centrality
):

    print("\n====================================")
    print("COMMUNAUTÉS DÉTECTÉES")
    print("====================================\n")

    for cid, data in labels.items():

        print(f"Community ID : {cid}")

        print(f"Label : {data['label']}")

        print(f"Résumé : {data['summary']}")

        print(f"Taille : {data['size']}")

        print("\nTop concepts :")

        for node in data["top_nodes"]:

            pr = centrality["pagerank"].get(
                node,
                0
            )

            deg = centrality["degree"].get(
                node,
                0
            )

            btw = centrality["betweenness"].get(
                node,
                0
            )

            print(
                f" - {node}"
                f" | PR={pr:.4f}"
                f" | DEG={deg:.4f}"
                f" | BTW={btw:.4f}"
            )

        print("-" * 60)

# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":

    print("\n====================================")
    print("GRAPH COMMUNITY ANALYSIS")
    print("====================================")

    # =================================================
    # LOAD GRAPH
    # =================================================
    print("\nChargement du graphe Neo4j...")

    G = load_graph()

    print(f"Noeuds initiaux : {len(G.nodes())}")
    print(f"Relations initiales : {len(G.edges())}")

    # =================================================
    # CLEAN GRAPH
    # =================================================
    G = clean_graph_topology(
        G,
        min_degree=2
    )

    print(
        f"\nNoeuds après nettoyage : "
        f"{len(G.nodes())}"
    )

    print(
        f"Relations après nettoyage : "
        f"{len(G.edges())}"
    )

    # =================================================
    # CENTRALITY
    # =================================================
    centrality = compute_centrality(G)

    # =================================================
    # LOUVAIN
    # =================================================
    partition, modularity = detect_communities(G)

    print(
        f"\nModularity Score : "
        f"{modularity:.4f}"
    )

    print(
        f"Nombre de communautés : "
        f"{len(set(partition.values()))}"
    )

    # =================================================
    # LABEL COMMUNITIES
    # =================================================
    labels = label_communities(
        G,
        partition,
        centrality
    )

    # =================================================
    # SAVE TO NEO4J
    # =================================================
    save_communities_to_neo4j(
        partition,
        labels
    )

    # =================================================
    # DISPLAY RESULTS
    # =================================================
    display_communities(
        labels,
        centrality
    )

    print("\nAnalyse terminée.")

    driver.close()