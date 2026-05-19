import os
import traceback
import json
import asyncio
import numpy as np
import faiss as faiss_lib
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from backend.api.analytics import router as analytics_router
from backend.api.graph import router as graph_router
from backend.instances import agent, generator
from backend import config

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

app.include_router(analytics_router)
app.include_router(graph_router)

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

# --- ROUTES ---

@app.get("/")
async def root():
    return {"status": "online", "project": "Agentic Graph RAG"}

@app.post("/query", response_model=QueryResponse)
async def run_full_query(request: QueryRequest):
    try:
        # ============================================
        # RUN AGENT (in thread — CPU-bound, must not block the event loop)
        # ============================================
        results, action_name, metadata = await asyncio.to_thread(
            agent.run_query_with_metadata, request.question
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
            sources = [{"type": "graph", "content": context}]

            # Fallback: if graph returned no useful context, retry with vector search
            if not generator.is_valid_context(context):
                vector_fallback = agent.vector_retriever.hybrid_search(request.question, top_k=5)
                if vector_fallback:
                    context = "\n".join([r.get("text", "") for r in vector_fallback if isinstance(r, dict)])
                    sources = vector_fallback
                    action_name = "Vector (graph fallback)"

        # ============================================
        # HYBRID MODE
        # ============================================
        else:
            vector_text = ""
            if isinstance(results, dict) and results.get("vector"):
                vector_text = "\n\n".join([
                    r.get("text", "")
                    for r in results["vector"]
                    if isinstance(r, dict)
                ])

            graph_text = ""
            if isinstance(results, dict) and results.get("graph"):
                graph_text = str(results.get("graph", ""))

            context = (
                "=== CONTEXTE VECTORIEL ===\n"
                f"{vector_text}\n\n"
                "=== CONTEXTE GRAPHE ===\n"
                f"{graph_text}"
            )
            sources = results.get("vector", [])

        # ============================================
        # FALLBACK EMPTY CONTEXT
        # ============================================
        if not context.strip():
            context = "Aucun contexte pertinent trouvé."

        # ============================================
        # GENERATION (in thread — LLM is CPU-bound)
        # ============================================
        answer = await asyncio.to_thread(
            generator.generate_answer, request.question, context
        )

        # ============================================
        # SAFE RESPONSE
        # ============================================
        return QueryResponse(
            answer=str(answer),
            action_taken=str(action_name),
            confidence_score=float(metadata.get("confidence_score", 0.0)),
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/analyze")
async def analyze_query(request: QueryRequest):
    try:
        return agent.analyze_query(request.question)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vectorial")
async def get_vectorial_results(q: str = Query(..., min_length=3), strategy: str = Query("hybrid")):
    try:
        if strategy == "semantic":
            results = agent.vector_retriever.semantic_search(q, top_k=5)
        elif strategy == "bm25":
            results = agent.vector_retriever.bm25_search(q, top_k=5)
        else:
            results = agent.vector_retriever.hybrid_search(q, top_k=5)
        
        return {"query": q, "strategy": strategy, "results": results, "summary": ""}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pca_query")
async def pca_query(q: str = Query(..., min_length=2), top_k: int = Query(20)):
    try:
        with open(config.DATA_DIR / "indexed_chunks.json", "r", encoding="utf-8") as f:
            indexed_chunks = json.load(f)

        query_vec = agent.vector_retriever.vector_model.encode([q]).astype("float32")
        faiss_lib.normalize_L2(query_vec)

        distances, indices = agent.vector_retriever.index.search(query_vec, top_k)

        results = []
        for rank, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(indexed_chunks):
                continue
            chunk = indexed_chunks[idx]
            results.append({
                "chunk_id": chunk["id"],
                "score": round(float(distances[0][rank]), 4),
                "pca_x": chunk.get("pca_x"),
                "pca_y": chunk.get("pca_y"),
                "text": chunk["text"][:120],
            })

        return {"query": q, "results": results}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agentic")
async def get_agent_state():
    return agent.get_agent_state()

if __name__ == "__main__":
    uvicorn.run(
        "backend.main_api:app",
        host=config.HOST,
        port=config.PORT,
        reload=False
    )
