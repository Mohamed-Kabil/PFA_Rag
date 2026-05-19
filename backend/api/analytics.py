import json
from fastapi import APIRouter, HTTPException
from backend.services.neo4j_service import get_analytics
from backend import config
from langchain_text_splitters import RecursiveCharacterTextSplitter

router = APIRouter()

@router.get("/analytics")
def analytics():
    return get_analytics()

@router.get("/pca_data")
async def get_pca_data():
    try:
        with open(config.DATA_DIR / "indexed_chunks.json", "r", encoding="utf-8") as f:
            chunks = json.load(f)

        with open(config.DATA_DIR / "pca_stats.json", "r", encoding="utf-8") as f:
            stats = json.load(f)

        return {"chunks": chunks, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chunking_stats")
async def get_chunking_stats():
    try:
        with open(config.CHUNKS_JSON, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        current_method = "Inconnue"
        if chunks and "metadata" in chunks[0]:
            current_method = chunks[0]["metadata"].get("method", "Hierarchical")

        method_scores = {}
        eval_path = config.DATA_DIR / "chunking_eval.json"
        if eval_path.exists():
            with open(eval_path, "r", encoding="utf-8") as f:
                eval_data = json.load(f)
            method_scores = eval_data.get("scores", {})

        return {
            "total_chunks": len(chunks),
            "available_methods": list(method_scores.keys()) or [
                "Fixed-Size", "Sentence", "Paragraph", "Sliding Window",
                "Recursive", "Semantic", "Hierarchical", "Section-Based"
            ],
            "current_method": current_method,
            "method_scores": method_scores,
            "hierarchy": {
                "document": "corpus_clean.docx",
                "total_chunks": len(chunks),
                "sample_sub_chunks": [c["text"][:100] + "..." for c in chunks[:3]],
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunking_tree")
async def get_chunking_tree():
    try:
        with open(config.CHUNKS_JSON, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        sub_splitter = RecursiveCharacterTextSplitter(
            chunk_size=200,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        tree_chunks = []
        for chunk in chunks[:3]:
            text = chunk["text"]
            sub_texts = sub_splitter.split_text(text)
            tree_chunks.append({
                "id": chunk["id"],
                "text": text,
                "chapter": chunk["metadata"].get("chapter", ""),
                "section": chunk["metadata"].get("section", ""),
                "sub_chunks": [{"text": t} for t in sub_texts[:4]],
            })

        return {"document": "corpus_clean.docx", "chunks": tree_chunks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
