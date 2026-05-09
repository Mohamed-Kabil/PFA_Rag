import sys
import os
import traceback
import json
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Ajout du chemin racine pour permettre les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.agent import RoutingAgent
    from backend.generation import LocalGenerator
    from backend.neo4j_manager import Neo4jManager
except ImportError:
    from agent import RoutingAgent
    from generation import LocalGenerator
    from neo4j_manager import Neo4jManager

app = FastAPI(
    title="Agentic Vectorial Graph RAG API",
    description="Backend conforme aux exigences du PFA - 4 Modules",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Modèles de données ---
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    action_taken: str
    confidence_score: float
    sources: list
    query_type: str | None = None
    state: str | None = None
    decision_path: list | None = None
    q_values: dict | None = None
    policy_scores: dict | None = None
    reward: float | None = None
    routing_reason: str | None = None
    retrieval_summary: dict | None = None
    features: dict | None = None
    q_update: dict | None = None

# --- Initialisation globale ---
DATA_DIR = os.getenv("DATA_DIR", "data")
agent = RoutingAgent(DATA_DIR)
generator = LocalGenerator()

# --- ROUTES ---

@app.get("/")
async def root():
    return {"status": "online", "project": "Agentic Graph RAG"}

@app.post("/query", response_model=QueryResponse)
async def run_full_query(request: QueryRequest):

    try:

        # ============================================
        # RUN AGENT
        # ============================================
        results, action_name, metadata = agent.run_query_with_metadata(
            request.question
        )

        context = ""
        sources = []

        # ============================================
        # VECTOR MODE
        # ============================================
        if action_name == "Vector":

            if isinstance(results, list):

                context = "\n".join([
                    r.get("text", "")
                    for r in results
                    if isinstance(r, dict)
                ])

                sources = results

            else:

                context = str(results)

        # ============================================
        # GRAPH MODE
        # ============================================
        elif action_name == "Graph":

            context = str(results)

            sources = [
                {
                    "type": "graph",
                    "content": context
                }
            ]

        # ============================================
        # HYBRID MODE
        # ============================================
        else:

            vector_text = ""

            # ----------------------------------------
            # VECTOR CONTEXT
            # ----------------------------------------
            if (
                isinstance(results, dict)
                and results.get("vector")
            ):

                vector_text = "\n\n".join([
                    r.get("text", "")
                    for r in results["vector"]
                    if isinstance(r, dict)
                ])

            # ----------------------------------------
            # GRAPH CONTEXT
            # ----------------------------------------
            graph_text = ""

            if (
                isinstance(results, dict)
                and results.get("graph")
            ):

                graph_text = str(
                    results.get("graph", "")
                )

            # ----------------------------------------
            # FINAL HYBRID CONTEXT
            # ----------------------------------------
            context = (
                "=== CONTEXTE VECTORIEL ===\n"
                f"{vector_text}\n\n"
                "=== CONTEXTE GRAPHE ===\n"
                f"{graph_text}"
            )

            sources = results.get(
                "vector",
                []
            )

        # ============================================
        # FALLBACK EMPTY CONTEXT
        # ============================================
        if not context.strip():

            context = (
                "Aucun contexte pertinent trouvé."
            )

        # ============================================
        # GENERATION
        # ============================================
        answer = generator.generate_answer(
            request.question,
            context
        )

        # ============================================
        # SAFE RESPONSE
        # ============================================
        return QueryResponse(
            answer=str(answer),
            action_taken=str(action_name),
            confidence_score=float(
                metadata.get("confidence_score", 0.0)
            ),
            sources=sources,
            query_type=metadata.get("query_type"),
            state=metadata.get("state"),
            decision_path=metadata.get("decision_path"),
            q_values=metadata.get("q_values"),
            policy_scores=metadata.get("policy_scores"),
            reward=metadata.get("reward"),
            routing_reason=metadata.get("routing_reason"),
            retrieval_summary=metadata.get("retrieval_summary"),
            features=metadata.get("features"),
            q_update=metadata.get("q_update")
        )

    except Exception as e:

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/query/analyze")
async def analyze_query(request: QueryRequest):
    try:
        return agent.analyze_query(request.question)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/vectorial")
async def get_vectorial_results(q: str = Query(..., min_length=3), strategy: str = Query("hybrid")):
    try:
        if strategy == "semantic":
            results = agent.vector_retriever.semantic_search(q, top_k=5)
        elif strategy == "bm25":
            results = agent.vector_retriever.bm25_search(q, top_k=5)
        else:
            results = agent.vector_retriever.hybrid_search(q, top_k=5)
        
        # --- Génération du résumé (Requirement: résumé récupéré final) ---
        context = "\n".join([r['text'] for r in results])
        summary = generator.generate_answer(f"Fais une synthèse courte des points clés concernant : {q}", context)
        
        return {"query": q, "strategy": strategy, "results": results, "summary": summary}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pca_data")
async def get_pca_data():
    try:
        with open(os.path.join(DATA_DIR, "indexed_chunks.json"), "r", encoding="utf-8") as f:
            chunks = json.load(f)
        
        with open(os.path.join(DATA_DIR, "pca_stats.json"), "r", encoding="utf-8") as f:
            stats = json.load(f)
            
        return {"chunks": chunks, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chunking_stats")
async def get_chunking_stats():
    try:
        with open(os.path.join(DATA_DIR, "corpus_chunks.json"), "r", encoding="utf-8") as f:
            chunks = json.load(f)
            
        methods = [
            "Fixed-Size", "Sentence", "Paragraph", "Sliding Window", 
            "Recursive", "Semantic", "Hierarchical", "Section-Based"
        ]
        
        # Détecter la méthode utilisée depuis les métadonnées
        current_method = "Inconnue"
        if chunks and "metadata" in chunks[0]:
            current_method = chunks[0]["metadata"].get("method", "Hierarchical")
        
        return {
            "total_chunks": len(chunks),
            "available_methods": methods,
            "current_method": current_method,
            "hierarchy": {
                "document": "corpus_clean.docx",
                "total_chunks": len(chunks),
                "sample_sub_chunks": [c['text'][:100] + "..." for c in chunks[:3]]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph")
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

@app.get("/shortest_path")
async def get_shortest_path(start: str, end: str):
    try:
        path = agent.graph_retriever.get_shortest_path(start, end)
        if not path:
            return {"status": "not_found", "message": f"Aucun chemin entre '{start}' et '{end}'"}
        return {"status": "success", "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/louvain")
async def run_louvain_algorithm():
    try:
        manager = Neo4jManager()
        manager.run_louvain()
        with manager.driver.session() as session:
            count = session.run("MATCH (e:Entity) RETURN count(distinct e.communityId) as count").single()["count"]
        manager.close()
        return {"status": "success", "communities_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/communities")
async def get_communities_list():
    try:
        manager = Neo4jManager()
        cypher = "MATCH (e:Entity) WHERE e.communityId IS NOT NULL RETURN e.communityId as id, collect(e.name)[0..10] as members, count(e) as size ORDER BY size DESC LIMIT 10"
        with manager.driver.session() as session:
            results = session.run(cypher).data()
        manager.close()
        return {"communities": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph_data")
async def get_full_graph():
    try:
        manager = Neo4jManager()
        # Nœuds avec leur communauté
        n_q = "MATCH (e:Entity) RETURN e.id as id, e.name as label, coalesce(e.communityId, 0) as community, e.type as type"
        
        # Relations avec priorité au type sémantique stocké dans la propriété 'type'
        e_q = """
        MATCH (s:Entity)-[r]->(t:Entity) 
        RETURN s.id as source, t.id as target, 
               CASE WHEN type(r) = 'RELATED_TO' AND r.type IS NOT NULL THEN r.type ELSE type(r) END as label
        """
        
        with manager.driver.session() as session:
            nodes = session.run(n_q).data()
            edges = session.run(e_q).data()
        manager.close()
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agentic")
async def get_agent_state():
    return agent.get_agent_state()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
