import traceback
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from backend.services.neo4j_service import get_graph_preview
from backend.instances import agent, neo4j_manager

router = APIRouter()

@router.get("/graph/preview")
def graph_preview():
    return get_graph_preview()

@router.get("/graph")
async def get_graph_results(q: str = Query(..., min_length=3)):
    try:
        context = agent.graph_retriever.retrieve_graph_context(q)
        entities = agent.graph_retriever.search_entities(q)
        
        # Métriques expertes
        metrics = agent.graph_retriever.get_graph_metrics()
        
        # Centralité locale (pour le graphique de barres spécifique à la requête)
        local_centrality = {ent.get('entity', 'Inconnu'): len(ent.get('relations', [])) for ent in entities}
        
        return {
            "query": q, 
            "raw_context": context, 
            "entities": entities, 
            "metrics": {
                "centrality": local_centrality, 
                "global_centrality": metrics["top_centrality"],
                "density": metrics["density"],
                "total_nodes": metrics["nodes"],
                "total_edges": metrics["edges"]
            }
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shortest_path")
async def get_shortest_path(start: str, end: str):
    try:
        path = agent.graph_retriever.get_shortest_path(start, end)
        if not path:
            return {"status": "not_found", "message": f"Aucun chemin entre '{start}' et '{end}'"}
        return {"status": "success", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/louvain")
async def run_louvain_algorithm():
    try:
        if hasattr(neo4j_manager, 'run_louvain'):
            neo4j_manager.run_louvain()

        with neo4j_manager.driver.session() as session:
            count = session.run("MATCH (e:Entity) RETURN count(distinct e.communityId) as count").single()["count"]
        return {"status": "success", "communities_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/communities")
async def get_communities_list():
    try:
        cypher = "MATCH (e:Entity) WHERE e.communityId IS NOT NULL RETURN e.communityId as id, collect(e.name)[0..10] as members, count(e) as size ORDER BY size DESC LIMIT 10"
        with neo4j_manager.driver.session() as session:
            results = session.run(cypher).data()
        return {"communities": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/graph_data")
async def get_full_graph():
    try:
        n_q = "MATCH (e:Entity) RETURN e.id as id, e.name as label, coalesce(e.communityId, 0) as community, e.type as type"
        e_q = """
        MATCH (s:Entity)-[r]->(t:Entity)
        RETURN s.id as source, t.id as target,
               CASE WHEN type(r) = 'RELATED_TO' AND r.type IS NOT NULL THEN r.type ELSE type(r) END as label,
               coalesce(r.weight, 1.0) as weight
        ORDER BY weight DESC
        LIMIT 2000
        """
        with neo4j_manager.driver.session() as session:
            nodes = session.run(n_q).data()
            edges = session.run(e_q).data()
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


class CypherRequest(BaseModel):
    query: str


def _serialize(v):
    """Recursively serialize Neo4j values to JSON-safe dicts."""
    try:
        from neo4j.graph import Node, Relationship
    except ImportError:
        return v
    if isinstance(v, Node):
        return {
            "_neo4j_type": "node",
            "_id": v.element_id,
            "_labels": list(v.labels),
            **{k: _serialize(val) for k, val in dict(v).items()},
        }
    if isinstance(v, Relationship):
        return {
            "_neo4j_type": "relationship",
            "_id": v.element_id,
            "_rel_type": v.type,
            "_start_id": v.start_node.element_id,
            "_end_id": v.end_node.element_id,
            **{k: _serialize(val) for k, val in dict(v).items()},
        }
    if isinstance(v, list):
        return [_serialize(i) for i in v]
    if isinstance(v, dict):
        return {k: _serialize(val) for k, val in v.items()}
    return v


@router.post("/cypher")
async def run_cypher(body: CypherRequest):
    try:
        with neo4j_manager.driver.session() as session:
            records = list(session.run(body.query))

        if not records:
            return {"keys": [], "rows": [], "count": 0, "is_graph": False}

        keys = list(records[0].keys())
        rows = [{k: _serialize(record[k]) for k in keys} for record in records]

        is_graph = any(
            isinstance(v, dict) and v.get("_neo4j_type") in ("node", "relationship")
            for row in rows
            for v in row.values()
        )

        return {"keys": keys, "rows": rows, "count": len(rows), "is_graph": is_graph}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
