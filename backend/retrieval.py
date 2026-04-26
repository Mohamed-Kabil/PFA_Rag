import json
import os
import numpy as np
import faiss
import time
import re
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv

load_dotenv()

class HybridRetriever:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        
        # 1. Charger les chunks indexés
        chunks_path = os.path.join(data_dir, "indexed_chunks.json")
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Fichier indexed_chunks.json introuvable.")
            
        with open(chunks_path, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
            
        # 2. Charger l'index FAISS
        self.index = faiss.read_index(os.path.join(data_dir, "faiss_index.bin"))
        
        # 3. Charger les modèles
        print("Chargement des modèles (Embeddings + Reranker)...")
        self.vector_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # 4. Initialiser BM25
        print("Initialisation du moteur BM25...")
        tokenized_corpus = [self._tokenize(c['text']) for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def _tokenize(self, text):
        """Tokenisation simple pour BM25."""
        return re.sub(r'[^\w\s]', '', text.lower()).split()

    def search_vectorial(self, query, top_k=5):
        """Recherche sémantique pure via FAISS."""
        query_vector = self.vector_model.encode([query]).astype('float32')
        faiss.normalize_L2(query_vector)
        scores, indices = self.index.search(query_vector, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                chunk = self.chunks[idx]
                # Accès sécurisé à la page dans metadata
                page = chunk.get('metadata', {}).get('page', 'N/A')
                results.append({
                    "text": chunk['text'],
                    "score": float(scores[0][i]),
                    "page": page
                })
        return results

    def search_bm25(self, query, top_k=5):
        """Recherche textuelle pure via BM25."""
        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in indices:
            chunk = self.chunks[idx]
            # Accès sécurisé à la page dans metadata
            page = chunk.get('metadata', {}).get('page', 'N/A')
            results.append({
                "text": chunk['text'],
                "score": float(scores[idx]),
                "page": page
            })
        return results

    def hybrid_search(self, query, top_k=5, use_rerank=True):
        """Combinaison Vectorial + BM25 + Reranking."""
        v_res = self.search_vectorial(query, 20)
        b_res = self.search_bm25(query, 20)
        
        # Fusion des candidats sans doublons
        seen_texts = set()
        candidates = []
        for res in v_res + b_res:
            if res['text'] not in seen_texts:
                candidates.append(res)
                seen_texts.add(res['text'])
        
        if not use_rerank:
            return candidates[:top_k]
            
        # Reranking avec Cross-Encoder
        pairs = [[query, c['text']] for c in candidates]
        rerank_scores = self.reranker.predict(pairs)
        for i, c in enumerate(candidates):
            c['rerank_score'] = float(rerank_scores[i])
            
        return sorted(candidates, key=lambda x: x.get('rerank_score', 0), reverse=True)[:top_k]

    def evaluate_methods(self, query):
        """Compare les approches de recherche."""
        print(f"\n--- BENCHMARK DES MÉTHODES DE RETRIEVAL ---")
        print(f"Question test : '{query}'\n")
        print(f"{'Méthode':<20} | {'Score Max':<12} | {'Temps (ms)':<10}")
        print("-" * 50)
        
        methods = [
            ("Vectorial Only", lambda: self.search_vectorial(query)),
            ("Keyword Only", lambda: self.search_bm25(query)),
            ("Hybrid", lambda: self.hybrid_search(query, use_rerank=False)),
            ("Hybrid + Rerank", lambda: self.hybrid_search(query, use_rerank=True))
        ]
        
        for name, func in methods:
            try:
                start = time.time()
                res = func()
                duration = (time.time() - start) * 1000
                
                if res:
                    score_val = res[0].get('rerank_score', res[0].get('score', 0))
                    print(f"{name:<20} | {score_val:<12.3f} | {duration:<10.1f}")
                else:
                    print(f"{name:<20} | {'N/A':<12} | {duration:<10.1f}")
            except Exception as e:
                print(f"{name:<20} | Erreur: {str(e)}")

if __name__ == "__main__":
    DATA_DIR = "agentic_graph_rag/data"
    
    try:
        retriever = HybridRetriever(DATA_DIR)
        test_query = "Quelle est l'influence du pâturage sur la biodiversité alpine ?"
        retriever.evaluate_methods(test_query)
        
        # Aperçu final
        final = retriever.hybrid_search(test_query, top_k=1)
        if final:
            print(f"\n--- MEILLEUR RÉSULTAT (Hybrid + Rerank) ---")
            print(f"Page: {final[0]['page']}")
            print(f"Texte: {final[0]['text'][:300]}...")
            
    except Exception as e:
        print(f"Erreur globale : {e}")
