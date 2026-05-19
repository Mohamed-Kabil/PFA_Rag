import os
import json
import faiss
import numpy as np

from sentence_transformers import (
    SentenceTransformer,
    CrossEncoder
)

from rank_bm25 import BM25Okapi
from dotenv import load_dotenv

from pathlib import Path
from backend import config

class HybridRetriever:
    def __init__(self, data_dir=None):
        print("Chargement du système de retrieval...")
        
        # Conversion en Path si c'est une chaîne
        self.data_dir = Path(data_dir) if data_dir else config.DATA_DIR

        # =====================================================
        # LOAD CHUNKS
        # =====================================================
        chunks_path = config.CHUNKS_JSON if not data_dir else self.data_dir / "corpus_chunks.json"

        with open(
            chunks_path,
            "r",
            encoding="utf-8"
        ) as f:
            self.chunks = json.load(f)

        print(f"{len(self.chunks)} chunks chargés")

        # =====================================================
        # LOAD FAISS
        # =====================================================
        index_path = config.FAISS_INDEX if not data_dir else self.data_dir / "faiss_index.bin"

        self.index = faiss.read_index(str(index_path))

        print("Index FAISS chargé")

        # =====================================================
        # EMBEDDINGS
        # =====================================================
        print("Chargement du modèle embeddings...")

        self.vector_model = SentenceTransformer(
            config.EMBEDDING_MODEL_NAME
        )

        # =====================================================
        # RERANKER
        # =====================================================
        print("Chargement du reranker...")

        self.reranker = CrossEncoder(
            config.RERANK_MODEL_NAME
        )

        # =====================================================
        # BM25
        # =====================================================
        print("Initialisation BM25...")

        self.tokenized_corpus = [
            self._tokenize(chunk["text"])
            for chunk in self.chunks
        ]

        self.bm25 = BM25Okapi(
            self.tokenized_corpus
        )

        print("Retriever hybride prêt")

    # =====================================================
    # TOKENIZATION
    # =====================================================
    def _tokenize(self, text):
        import re

        return re.findall(
            r"\w+",
            text.lower()
        )

    # =====================================================
    # VECTOR SEARCH
    # =====================================================
    def semantic_search(self, query, top_k=10):
        """
        Recherche FAISS.
        """

        query_vec = self.vector_model.encode(
            [query]
        ).astype("float32")

        faiss.normalize_L2(query_vec)

        distances, indices = self.index.search(
            query_vec,
            top_k
        )

        results = []

        for rank, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue

            chunk = self.chunks[idx]

            score = float(
                distances[0][rank]
            )

            results.append({
                "id": int(idx),
                "text": str(chunk["text"]),
                "score": float(score)
            })

        return results

    # =====================================================
    # BM25 SEARCH
    # =====================================================
    def bm25_search(self, query, top_k=10):
        """
        Recherche BM25.
        """

        tokenized_query = self._tokenize(query)

        scores = self.bm25.get_scores(
            tokenized_query
        )

        best_indices = np.argsort(scores)[::-1][:top_k]

        max_score = np.max(scores)

        if max_score <= 0:
            max_score = 1.0

        results = []

        for idx in best_indices:
            results.append({
                "id": int(idx),
                "text": self.chunks[idx]["text"],
                "score": float(
                    scores[idx] / max_score
                )
            })

        return results

    # =====================================================
    # RERANKING
    # =====================================================
    def rerank_results(
        self,
        query,
        results,
        top_k=3
    ):
        """
        Cross-encoder reranking + filtering.
        """

        if not results:
            return []

        pairs = [
            (query, r["text"])
            for r in results
        ]

        rerank_scores = self.reranker.predict(
            pairs
        )

        reranked = []

        for r, score in zip(results, rerank_scores):
            r["rerank_score"] = float(score)

            reranked.append(r)

        reranked = sorted(
            reranked,
            key=lambda x: x["rerank_score"],
            reverse=True
        )

        # =====================================================
        # RERANK FILTERING
        # =====================================================
        filtered = []

        MIN_RERANK_SCORE = -0.5

        for r in reranked:
            if r["rerank_score"] < MIN_RERANK_SCORE:
                continue

            filtered.append(r)

        return filtered[:top_k]

    # =====================================================
    # HYBRID SEARCH
    # =====================================================
    def hybrid_search(self, query, top_k=3):
        """
        Hybrid retrieval pipeline.
        """

        VECTOR_WEIGHT = 0.7
        BM25_WEIGHT = 0.3

        vec_results = self.semantic_search(
            query,
            top_k=10
        )

        bm25_results = self.bm25_search(
            query,
            top_k=10
        )

        scores = {}

        # =====================================================
        # VECTOR SCORES
        # =====================================================
        for r in vec_results:
            scores[r["id"]] = (
                scores.get(r["id"], 0)
                + r["score"] * VECTOR_WEIGHT
            )

        # =====================================================
        # BM25 SCORES
        # =====================================================
        for r in bm25_results:
            scores[r["id"]] = (
                scores.get(r["id"], 0)
                + r["score"] * BM25_WEIGHT
            )

        # =====================================================
        # SORT
        # =====================================================
        ranked = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        if not ranked:
            return []

        best_score = ranked[0][1]

        final_results = []

        seen_texts = set()

        MAX_CHARS = 1800

        # =====================================================
        # FILTERING
        # =====================================================
        for idx, score in ranked:
            # Dynamic threshold
            if score < best_score * 0.5:
                continue

            chunk = self.chunks[idx]

            text = chunk["text"].strip()

            # Deduplication
            normalized = text.lower()

            if normalized in seen_texts:
                continue

            seen_texts.add(normalized)

            # Truncate huge chunks
            text = text[:MAX_CHARS]

            final_results.append({
                "id": int(idx),
                "text": str(text),
                "score": float(score)
            })

        # =====================================================
        # RERANKING STEP
        # =====================================================
        reranked_results = self.rerank_results(
            query,
            final_results,
            top_k=top_k
        )

        return reranked_results

    # =====================================================
    # BUILD CONTEXT
    # =====================================================
    def build_context(self, results):
        """
        Build final LLM context.
        """

        if not results:
            return None

        context_parts = []

        for r in results:
            context_parts.append(
                r["text"]
            )

        return "\n\n".join(context_parts)

    # =====================================================
    # MAIN RETRIEVAL
    # =====================================================
    def retrieve(self, query, top_k=3):
        """
        Full retrieval pipeline.
        """

        results = self.hybrid_search(
            query,
            top_k=top_k
        )

        if not results:
            return None

        return self.build_context(results)

    # =====================================================
    # DEBUG
    # =====================================================
    def debug_query(self, query):
        print("\n=== DEBUG RETRIEVAL ===")

        print("QUESTION :", query)

        results = self.hybrid_search(
            query,
            top_k=5
        )

        if not results:
            print("❌ Aucun chunk pertinent trouvé")
            return

        for i, r in enumerate(results):
            print(
                f"\n[{i+1}] "
                f"Score={r['score']:.4f} | "
                f"Rerank={r['rerank_score']:.4f}"
            )

            print(r["text"][:400])

    # =====================================================
    # TEST
    # =====================================================


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"

    retriever = HybridRetriever(DATA_DIR)

    retriever.debug_query(
        "Explique les marqueurs Orbis et Bomb"
    )