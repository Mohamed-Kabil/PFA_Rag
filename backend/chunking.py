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
        text = re.sub(r'-{3,}', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    # 1. Taille Fixe
    def fixed_size_chunking(self, text, size=500):
        return [text[i:i+size] for i in range(0, len(text), size)]

    # 2. Par Phrases
    def sentence_chunking(self, text):
        return [s.strip() for s in re.split(r'(?<=[.!?]) +', text) if len(s.strip()) > 20]

    # 3. Par Paragraphes
    def paragraph_chunking(self, text):
        return [p.strip() for p in text.split('\n') if len(p.strip()) > 30]

    # 4. Fenêtre Glissante
    def sliding_window_chunking(self, text, size=600, overlap=150):
        chunks = []
        start = 0
        while start < len(text):
            chunks.append(text[start:start+size])
            start += (size - overlap)
            if start >= len(text):
                break
        return chunks

    # 5. Récursif (LangChain)
    def recursive_chunking(self, text):
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        return splitter.split_text(text)

    # 6. Sémantique
    def semantic_chunking(self, text):
        sentences = self.sentence_chunking(text)
        if len(sentences) < 2:
            return sentences
        embeddings = self.model.encode(sentences)
        chunks, current = [], [sentences[0]]
        for i in range(1, len(sentences)):
            sim = cosine_similarity([embeddings[i-1]], [embeddings[i]])[0][0]
            if sim > 0.6:
                current.append(sentences[i])
            else:
                chunks.append(" ".join(current))
                current = [sentences[i]]
        chunks.append(" ".join(current))
        return chunks

    # 7. Basé sur les Sections (corrigé pour matcher les headers ## du corpus)
    def section_based_chunking(self, text):
        sections = re.split(r'\n#{1,2} .+\n', text)
        return [s.strip() for s in sections if len(s.strip()) > 30]

    # BLOCK 2: Hierarchical Chunking
    # 8. Hierarchical (Structure-Based)
    def hierarchical_chunking(self, text):
        # Groupement toujours appliqué sans condition de taille
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=150,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        return splitter.split_text(text)

    def evaluate_methods(self, sample_text):
        """Évalue chaque méthode sur un échantillon et retourne la meilleure."""
        methods = {
            "Fixed-Size":     self.fixed_size_chunking,
            "Sentence":       self.sentence_chunking,
            "Paragraph":      self.paragraph_chunking,
            "Sliding Window": self.sliding_window_chunking,
            "Recursive":      self.recursive_chunking,
            "Semantic":       self.semantic_chunking,
            "Section-Based":  self.section_based_chunking,
        }

        print(f"\n{'Méthode':<20} | {'Nb Chunks':<10} | {'Cohésion':<10} | {'Équilibre':<10}")
        print("-" * 65)

        scores = {}
        for name, func in methods.items():
            chunks = func(sample_text)
            if not chunks or len(chunks) < 2:
                continue

            embs = self.model.encode(chunks)

            # Cohésion : exclure la diagonale pour ne pas gonfler le score
            sim_matrix = cosine_similarity(embs)
            np.fill_diagonal(sim_matrix, 0)
            cohesion = np.mean(sim_matrix)

            # Équilibre des tailles
            lens = [len(c) for c in chunks]
            balance = 1 - (np.std(lens) / np.mean(lens)) if np.mean(lens) > 0 else 0

            print(f"{name:<20} | {len(chunks):<10} | {cohesion:.3f}    | {balance:.3f}")

            # Cohésion pèse plus que l'équilibre en RAG
            scores[name] = (cohesion * 1.5) + (balance * 0.5)

        best = max(scores, key=scores.get)
        return best

    # BLOCK 3: Pipeline de Chunking (run_final)
    def run_final(self):
        """Lance le chunking final avec la méthode hiérarchique sur les sections groupées."""
        all_chunks = []

        best_method = "Hierarchical"
        print(f"\n>>> Méthode utilisée : {best_method} (Structure-Based)")

        method_map = {
            "Hierarchical":   self.hierarchical_chunking,
            "Recursive":      self.recursive_chunking,
            "Semantic":       self.semantic_chunking,
            "Section-Based":  self.section_based_chunking,
            "Sliding Window": self.sliding_window_chunking,
            "Paragraph":      self.paragraph_chunking,
            "Sentence":       self.sentence_chunking,
            "Fixed-Size":     self.fixed_size_chunking,
        }
        chunk_func = method_map.get(best_method, self.hierarchical_chunking)

        # Grouper par section
        grouped_sections = {}
        for entry in self.data:
            entry_type = entry.get("type", "")
            # Ignorer figures et tables
            if entry_type in ["figure", "table"]:
                continue
                
            sec = entry.get("section", "Inconnu")
            if sec not in grouped_sections:
                grouped_sections[sec] = {
                    "chapter": entry.get("chapter", "Inconnu"),
                    "section_index": entry.get("section_index", 0),
                    "content_list": []
                }
            
            text_content = entry.get("content", "")
            if text_content:
                cleaned = self.clean_text(text_content)
                if cleaned:
                    grouped_sections[sec]["content_list"].append(cleaned)

        chunk_counter = 0
        for sec_title, sec_data in grouped_sections.items():
            merged_text = "\n\n".join(sec_data["content_list"])
            if not merged_text.strip():
                continue
                
            chunks = chunk_func(merged_text)
            
            for i, c in enumerate(chunks):
                if len(c.strip()) < 50:
                    continue
                    
                all_chunks.append({
                    "id": f"chunk_{chunk_counter}",
                    "text": c,
                    "metadata": {
                        "section": sec_title,
                        "chapter": sec_data["chapter"],
                        "section_index": sec_data["section_index"],
                        "chunk_index_in_section": i,
                        "method": best_method
                    }
                })
                chunk_counter += 1

        return all_chunks


if __name__ == "__main__":
    DATA_DIR = "agentic_graph_rag/data"
    input_path  = os.path.join(DATA_DIR, "corpus_cleaned_fr.json")
    output_path = os.path.join(DATA_DIR, "corpus_chunks.json")

    try:
        manager = ChunkingManager(input_path)
        final_data = manager.run_final()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)

        print(f"\nTraitement terminé. {len(final_data)} chunks sauvegardés dans {output_path}")
    except Exception as e:
        print(f"Erreur : {e}")
        raise