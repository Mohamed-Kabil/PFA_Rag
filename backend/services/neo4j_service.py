from neo4j import GraphDatabase
from backend import config

driver = GraphDatabase.driver(
    config.NEO4J_URI,
    auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
)

def compute_real_modularity() -> float:
    """Compute Louvain modularity from communityId properties stored in Neo4j."""
    try:
        import networkx as nx
        from community import community_louvain

        with driver.session() as session:
            nodes_rows = session.run(
                "MATCH (n:Entity) WHERE n.communityId IS NOT NULL "
                "RETURN n.name AS name, n.communityId AS cid"
            ).data()
            edge_rows = session.run(
                "MATCH (a:Entity)-[:RELATED_TO]->(b:Entity) "
                "WHERE a.name IS NOT NULL AND b.name IS NOT NULL "
                "RETURN a.name AS src, b.name AS tgt"
            ).data()

        if not nodes_rows or not edge_rows:
            return 0.0

        partition = {r["name"]: int(r["cid"]) for r in nodes_rows}

        G = nx.Graph()
        G.add_nodes_from(partition.keys())
        G.add_edges_from((r["src"], r["tgt"]) for r in edge_rows)

        partition = {n: c for n, c in partition.items() if n in G}
        if len(partition) < 2:
            return 0.0

        mod = community_louvain.modularity(partition, G)
        return round(float(mod), 4)
    except Exception as exc:
        print(f"[modularity] computation error: {exc}")
        return 0.0


def get_analytics():

    with driver.session() as session:

        entity_count = session.run(
            """
            MATCH (n:Entity)
            RETURN count(n) AS count
            """
        ).single()["count"]

        relation_count = session.run(
            """
            MATCH ()-[r:RELATED_TO]->()
            RETURN count(r) AS count
            """
        ).single()["count"]

        community_count = session.run(
            """
            MATCH (n:Entity)
            WHERE n.communityId IS NOT NULL
            RETURN count(DISTINCT n.communityId) AS count
            """
        ).single()["count"]

    modularity = compute_real_modularity()

    return {
        "entities": entity_count,
        "relations": relation_count,
        "communities": community_count,
        "modularity": modularity
    }

def get_graph_preview():

    with driver.session() as session:

        result = session.run(
            """
            MATCH (a:Entity)-[r:RELATED_TO]->(b:Entity)
            RETURN
                a.name AS source_name,
                a.communityId AS source_community,
                b.name AS target_name,
                b.communityId AS target_community,
                type(r) AS relation
            LIMIT 100
            """
        )

        nodes = {}
        edges = []

        for record in result:

            source = record["source_name"]
            target = record["target_name"]

            if source not in nodes:
                nodes[source] = {
                    "id": source,
                    "label": source,
                    "community": record["source_community"]
                }

            if target not in nodes:
                nodes[target] = {
                    "id": target,
                    "label": target,
                    "community": record["target_community"]
                }

            edges.append({
                "source": source,
                "target": target,
                "label": record["relation"]
            })

        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }