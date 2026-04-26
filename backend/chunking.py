import json
import os
import re
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

class ChunkingManager:
    def __init__(self, input_file):
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Fichier d'entrée introuvable : {input_file}")
            
        with open(input_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        print("Chargement du modèle SentenceTransformer pour l'évaluation...")
        self.model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

    def clean_text(self, text):
        """Supprime les tirets et les résidus de formatage."""
        # Supprime les lignes de tirets (----)
        text = re.sub(r'-{3,}', '', text)
        # Supprime les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    # 1. Taille Fixe (Character)
    def fixed_size_chunking(self, text, size=500):
        return [text[i:i+size] for i in range(0, len(text), size)]

    # 2. Par Phrases
    def sentence_chunking(self, text):
        return [s.strip() for s in re.split(r'(?<=[.!?]) +', text) if len(s.strip()) > 20]

    # 3. Par Paragraphes
    def paragraph_chunking(self, text):
        return [p.strip() for p in text.split('\n') if len(p.strip()) > 30]

    # 4. Fenêtre Glissante (Sliding Window)
    def sliding_window_chunking(self, text, size=600, overlap=150):
        chunks = []
        start = 0
        while start < len(text):
            chunks.append(text[start:start+size])
            start += (size - overlap)
            if start >= len(text): break
        return chunks

    # 5. Récursif (LangChain)
    def recursive_chunking(self, text):
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        return splitter.split_text(text)

    # 6. Sémantique (Similarity)
    def semantic_chunking(self, text):
        sentences = self.sentence_chunking(text)
        if len(sentences) < 2: return sentences
        embeddings = self.model.encode(sentences)
        chunks, current = [], [sentences[0]]
        for i in range(1, len(sentences)):
            sim = cosine_similarity([embeddings[i-1]], [embeddings[i]])[0][0]
            if sim > 0.6: current.append(sentences[i])
            else:
                chunks.append(" ".join(current))
                current = [sentences[i]]
        chunks.append(" ".join(current))
        return chunks

    # 7. Basé sur les Sections
    def section_based_chunking(self, text):
        sections = re.split(r'ID:\s*\d+_\d+', text)
        return [s.strip() for s in sections if len(s.strip()) > 30]

    def evaluate_methods(self, sample_text):
        """Calcule les scores pour chaque méthode et affiche le tableau."""
        methods = {
            "Fixed-Size": self.fixed_size_chunking,
            "Sentence": self.sentence_chunking,
            "Paragraph": self.paragraph_chunking,
            "Sliding Window": self.sliding_window_chunking,
            "Recursive": self.recursive_chunking,
            "Semantic": self.semantic_chunking,
            "Section-Based": self.section_based_chunking
        }
        
        print(f"\n{'Méthode':<20} | {'Nb Chunks':<10} | {'Cohésion':<10} | {'Équilibre':<10}")
        print("-" * 65)
        
        scores = {}
        for name, func in methods.items():
            chunks = func(sample_text)
            if not chunks: continue
            
            # 1. Cohésion Sémantique (Similiarité moyenne)
            if len(chunks) > 1:
                embs = self.model.encode(chunks)
                cohesion = np.mean(cosine_similarity(embs))
            else:
                cohesion = 1.0
            
            # 2. Équilibre (Régularité des tailles)
            lens = [len(c) for c in chunks]
            balance = 1 - (np.std(lens) / np.mean(lens)) if np.mean(lens) > 0 else 0
            
            print(f"{name:<20} | {len(chunks):<10} | {cohesion:.3f}    | {balance:.3f}")
            scores[name] = cohesion + balance
            
        return max(scores, key=scores.get)

    def run_final(self):
        """Lance le chunking final avec la meilleure méthode détectée."""
        all_chunks = []
        # On teste sur une page représentative (ex: page 10)
        sample_page = self.data[min(10, len(self.data)-1)]['content']
        best_method = self.evaluate_methods(self.clean_text(sample_page))
        
        print(f"\n>>> Méthode recommandée : {best_method}")
        
        for entry in self.data:
            text = self.clean_text(entry['content'])
            
            # Application de la meilleure méthode
            if best_method == "Recursive": chunks = self.recursive_chunking(text)
            elif best_method == "Semantic": chunks = self.semantic_chunking(text)
            elif best_method == "Section-Based": chunks = self.section_based_chunking(text)
            elif best_method == "Sliding Window": chunks = self.sliding_window_chunking(text)
            else: chunks = self.fixed_size_chunking(text)
            
            for i, c in enumerate(chunks):
                if len(c.strip()) < 15: continue
                all_chunks.append({
                    "id": f"P{entry['page_originale']}_C{i}",
                    "text": c,
                    "metadata": {
                        "method": best_method,
                        "page": entry['page_originale']
                    }
                })
        return all_chunks

if __name__ == "__main__":
    DATA_DIR = "agentic_graph_rag/data"
    input_path = os.path.join(DATA_DIR, "corpus_cleaned_en.json")
    output_path = os.path.join(DATA_DIR, "corpus_chunks.json")
    
    try:
        manager = ChunkingManager(input_path)
        final_data = manager.run_final()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)
            
        print(f"\nTraitement terminé. {len(final_data)} chunks sauvegardés dans {output_path}")
    except Exception as e:
        print(f"Erreur : {e}")
