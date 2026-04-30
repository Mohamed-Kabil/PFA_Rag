import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv

load_dotenv()

class HybridRetriever:
    def __init__(self, data_dir):
        # 1. Charger les chunks
        chunks_path = os.path.join(data_dir, "corpus_chunks.json")
        with open(chunks_path, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
            
        # 2. Charger l'index FAISS
        self.index = faiss.read_index(os.path.join(data_dir, "faiss_index.bin"))
        self.vector_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        
        # 3. Initialiser BM25 (Mots-clés : Orbis, Bomb, etc.)
        # Cette partie remplace le BM25Retriever de LangChain
        print("🔧 Initialisation du moteur BM25 (Mots-clés)...")
        tokenized_corpus = [c['text'].lower().split() for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def hybrid_search(self, query, top_k=5):
        """[MODIF 1 & 2] Fusion 0.5/0.5 entre BM25 et Vecteur avec k=5."""
        # A. Score BM25
        tokenized_query = query.lower().split()
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # B. Score Vectoriel (FAISS)
        query_vec = self.vector_model.encode([query])
        v_distances, v_indices = self.index.search(query_vec, len(self.chunks))
        
        # C. Normalisation et Fusion (RRF simple)
        combined_scores = np.zeros(len(self.chunks))
        max_bm25 = np.max(bm25_scores) if np.max(bm25_scores) > 0 else 1
        
        for i in range(len(self.chunks)):
            # Score normalisé BM25 (0 à 1)
            s_bm25 = bm25_scores[i] / max_bm25
            
            # Score normalisé Vecteur (1 / (1 + distance))
            idx_in_faiss = np.where(v_indices[0] == i)[0][0]
            dist = v_distances[0][idx_in_faiss]
            s_vector = 1 / (1 + dist)
            
            # Fusion 50/50
            combined_scores[i] = (0.5 * s_bm25) + (0.5 * s_vector)
            
        # D. Sélection des k=5 meilleurs chunks
        best_indices = np.argsort(combined_scores)[::-1][:top_k]
        
        formatted_results = []
        for idx in best_indices:
            chunk = self.chunks[idx]
            formatted_results.append({
                "text": chunk['text'],
                "page": chunk.get('metadata', {}).get('page', 'N/A'),
                "score": float(combined_scores[idx])
            })
        return formatted_results

    def evaluate_methods(self, query):
        print(f"\n--- TEST HYBRIDE (ENSEMBLE MANUEL) ---")
        print(f"Question : '{query}'")
        res = self.hybrid_search(query, top_k=3)
        for i, r in enumerate(res):
            print(f"[{i+1}] (Score: {r['score']:.4f}) {r['text'][:150]}...")

if __name__ == "__main__":
    DATA_DIR = "agentic_graph_rag/data"
    retriever = HybridRetriever(DATA_DIR)
    # Test sur les marqueurs spécifiques
    retriever.evaluate_methods("Explique les marqueurs Orbis et Bomb")
