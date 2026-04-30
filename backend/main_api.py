from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
import traceback

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

import uvicorn

# Initialisation de l'application FastAPI
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

# --- Initialisation globale ---
DATA_DIR = "agentic_graph_rag/data"
agent = RoutingAgent(DATA_DIR)
generator = LocalGenerator()

# --- ROUTES ---

@app.get("/")
async def root():
    return {"status": "online", "project": "Agentic Graph RAG"}

@app.post("/query", response_model=QueryResponse)
async def run_full_query(request: QueryRequest):
    try:
        results, action_name = agent.run_query(request.question)
        context = ""
        sources = []
        if action_name == "Vector":
            context = "\n".join([r['text'] for r in results])
            sources = results
        elif action_name == "Graph":
            context = results 
            sources = [{"type": "graph", "content": results}]
        else: # Hybrid
            v_text = "\n".join([r['text'] for r in results['vector']])
            context = f"VECTEUR:\n{v_text}\n\nGRAPHE:\n{results['graph']}"
            sources = results['vector']
        answer = generator.generate_answer(request.question, context)
        return QueryResponse(answer=answer, action_taken=action_name, confidence_score=0.85, sources=sources)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vectorial")
async def get_vectorial_results(q: str = Query(..., min_length=3)):
    try:
        results = agent.vector_retriever.hybrid_search(q, top_k=5)
        return {"query": q, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph")
async def get_graph_results(q: str = Query(..., min_length=3)):
    try:
        context = agent.graph_retriever.retrieve_graph_context(q)
        entities = agent.graph_retriever.search_entities(q)
        centrality = {ent.get('entity', 'Inconnu'): len(ent.get('relations', [])) for ent in entities}
        return {"query": q, "raw_context": context, "entities": entities, "metrics": {"centrality": centrality, "density": len(entities) / 10}}
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
        n_q = "MATCH (e:Entity) RETURN e.id as id, e.name as label, e.communityId as community, e.type as type"
        e_q = "MATCH (s:Entity)-[r]->(t:Entity) RETURN s.id as source, t.id as target, type(r) as label"
        with manager.driver.session() as session:
            return {"nodes": session.run(n_q).data(), "edges": session.run(e_q).data()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agentic")
async def get_agent_state():
    return {"q_table": agent.q_table, "actions": ["Vector", "Graph", "Hybrid"], "epsilon": agent.epsilon}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
