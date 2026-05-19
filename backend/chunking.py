import json
import os
import re
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Charger les variables d'environnement
load_dotenv()


class ChunkingManager:
    def __init__(self, input_file):
        if not os.path.exists(input_file):
            raise FileNotFoundError(
                f"Fichier d'entrée introuvable : {input_file}"
            )

        with open(input_file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.model = None

    # =====================================================
    # MODEL
    # =====================================================
    def get_model(self):
        """
        Chargement lazy du modèle embeddings.
        """

        if self.model is None:
            print(
                "Chargement du modèle SentenceTransformer..."
            )

            self.model = SentenceTransformer(
                "paraphrase-multilingual-mpnet-base-v2"
            )

        return self.model

    # =====================================================
    # CLEANING
    # =====================================================
    def clean_text(self, text):
        """
        Nettoyage léger du texte tout en préservant les sauts de ligne significatifs.
        """
        if not text:
            return ""
        
        # Supprimer les lignes de tirets (souvent du bruit OCR)
        text = re.sub(r"-{3,}", " ", text)
        # Normaliser les espaces horizontaux
        text = re.sub(r"[ \t]+", " ", text)
        # Supprimer les espaces en début/fin de ligne
        text = "\n".join(line.strip() for line in text.split("\n"))
        # Limiter à max 2 sauts de ligne consécutifs
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        return text.strip()

    def is_noise(self, text, entry_type=None):
        """
        Détection du bruit OCR / tableaux cassés.
        Les titres sont préservés même s'ils sont courts.
        """
        if not text:
            return True

        # Si c'est un titre, on le garde
        if entry_type == "heading":
            return False

        words = text.split()
        if len(words) < 5:
            # Sauf si c'est très court mais alphabétique (peut être un mini-paragraphe utile)
            alpha_chars = sum(c.isalpha() for c in text)
            if alpha_chars > 10:
                return False
            return True

        alpha_chars = sum(c.isalpha() for c in text)
        alpha_ratio = alpha_chars / max(len(text), 1)

        # Trop peu de texte alphabétique (probablement des tableaux cassés ou des chiffres seuls)
        if alpha_ratio < 0.3:
            return True

        return False

    # =====================================================
    # CHUNKING METHODS
    # =====================================================
    def fixed_size_chunking(self, text, size=500):
        return [
            text[i:i + size]
            for i in range(0, len(text), size)
        ]

    def sentence_chunking(self, text):
        """
        Découpage en phrases plus robuste.
        """
        # Utilise une regex qui gère mieux les ponctuations suivies ou non d'espaces
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [
            s.strip()
            for s in sentences
            if len(s.strip()) > 15
        ]

    def paragraph_chunking(self, text):
        return [
            p.strip()
            for p in text.split("\n\n")
            if len(p.strip()) > 30
        ]

    def sliding_window_chunking(
        self,
        text,
        size=500,
        overlap=100
    ):
        chunks = []
        if len(text) <= size:
            return [text]

        start = 0
        while start < len(text):
            end = start + size
            chunks.append(text[start:end])
            start += size - overlap
            
            # Éviter de créer un dernier chunk minuscule
            if start + overlap >= len(text):
                break

        return chunks

    def recursive_chunking(self, text):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=80,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return splitter.split_text(text)

    def semantic_chunking(self, text):
        """
        Chunking sémantique amélioré avec seuil adaptatif.
        """
        sentences = self.sentence_chunking(text)
        if len(sentences) < 2:
            return sentences

        embeddings = self.get_model().encode(sentences)
        chunks = []
        current_chunk_sentences = [sentences[0]]
        
        for i in range(1, len(sentences)):
            sim = cosine_similarity(
                [embeddings[i - 1]],
                [embeddings[i]]
            )[0][0]

            # Seuil plus réaliste pour MPNet (souvent > 0.7-0.8 pour du contenu lié)
            if sim > 0.7:
                current_chunk_sentences.append(sentences[i])
            else:
                chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = [sentences[i]]

        chunks.append(" ".join(current_chunk_sentences))
        return chunks

    def section_based_chunking(self, text):
        # On suppose ici que le texte contient des marqueurs de section
        # Sinon cette méthode est moins utile sur du texte brut
        sections = re.split(r"\n#{1,3} ", "\n" + text)
        return [
            s.strip()
            for s in sections
            if len(s.strip()) > 30
        ]

    def hierarchical_chunking(self, text):
        """
        Approche hybride : split par paragraphes puis récursif.
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return splitter.split_text(text)

    # =====================================================
    # EVALUATION
    # =====================================================
    def evaluate_methods(self, sample_text):
        """
        Évaluation des méthodes avec des métriques moins biaisées.
        Retourne (best_method, detailed_scores) où detailed_scores est un dict
        method → {chunks_count, cohesion, balance, score}.
        """
        methods = {
            "Fixed-Size": self.fixed_size_chunking,
            "Sentence": self.sentence_chunking,
            "Paragraph": self.paragraph_chunking,
            "Sliding Window": self.sliding_window_chunking,
            "Recursive": self.recursive_chunking,
            "Semantic": self.semantic_chunking,
            "Section-Based": self.section_based_chunking,
            "Hierarchical": self.hierarchical_chunking,
        }

        print(
            f"\n{'Méthode':<20} | "
            f"{'Nb Chunks':<10} | "
            f"{'Cohésion':<10} | "
            f"{'Équilibre':<10} | "
            f"{'Score':<8}"
        )
        print("-" * 80)

        scores = {}
        detailed_scores = {}
        for name, func in methods.items():
            try:
                chunks = func(sample_text)
                if not chunks:
                    continue

                eval_chunks = chunks[:20]
                if len(eval_chunks) < 2:
                    continue

                embs = self.get_model().encode(eval_chunks)
                sim_matrix = cosine_similarity(embs)

                adj_sims = [sim_matrix[i][i + 1] for i in range(len(eval_chunks) - 1)]
                cohesion = float(np.mean(adj_sims)) if adj_sims else 0.0

                lens = [len(c) for c in chunks]
                avg_len = np.mean(lens)
                std_len = np.std(lens)
                balance = float(1 / (1 + (std_len / max(avg_len, 1))))

                total = cohesion * 2.0 + balance * 0.5

                print(
                    f"{name:<20} | "
                    f"{len(chunks):<10} | "
                    f"{cohesion:.3f}      | "
                    f"{balance:.3f}      | "
                    f"{total:.3f}"
                )

                scores[name] = total
                detailed_scores[name] = {
                    "chunks_count": len(chunks),
                    "cohesion": round(cohesion, 4),
                    "balance": round(balance, 4),
                    "score": round(total, 4),
                }

            except Exception as e:
                print(f"{name:<20} | Erreur: {e}")

        if not scores:
            return "Hierarchical", {}

        best_method = max(scores, key=scores.get)
        print(f"\n[INFO] Meilleure méthode suggérée : {best_method}")
        return best_method, detailed_scores

    # =====================================================
    # MAIN PIPELINE
    # =====================================================
    def run_final(self):
        all_chunks = []

        print("\n>>> Analyse et traitement du corpus...")

        # Extraction d'un échantillon pour évaluation
        sample_content = []
        for entry in self.data[:50]:
            if entry.get("content") and len(entry["content"]) > 100:
                sample_content.append(entry["content"])
                if len(sample_content) >= 10:
                    break

        method_scores = {}
        if sample_content:
            sample_text = "\n\n".join(sample_content)
            _, method_scores = self.evaluate_methods(sample_text)

        # On utilise Hierarchical par défaut car c'est le plus robuste pour le RAG
        best_method = "Hierarchical"
        chunk_func = self.hierarchical_chunking

        # Groupement par section et chapitre pour garder le contexte
        grouped_sections = {}
        for entry in self.data:
            content = entry.get("content", "")
            if not content:
                continue

            cleaned = self.clean_text(content)
            if self.is_noise(cleaned, entry.get("type")):
                continue

            chapter = entry.get("chapter", "Inconnu")
            section = entry.get("section", "Inconnu")
            section_idx = entry.get("section_index", 0)

            # Clé de groupement incluant le chapitre pour éviter les collisions
            group_key = (chapter, section_idx, section)

            if group_key not in grouped_sections:
                grouped_sections[group_key] = []
            
            grouped_sections[group_key].append(cleaned)

        # Génération des chunks
        chunk_counter = 0
        seen_chunks = set()

        # Trier par chapitre et index de section
        sorted_keys = sorted(grouped_sections.keys(), key=lambda x: (x[0], x[1]))

        for key in sorted_keys:
            chapter, s_idx, section = key
            content_list = grouped_sections[key]
            merged_text = "\n\n".join(content_list)

            if not merged_text.strip():
                continue

            chunks = chunk_func(merged_text)

            for i, chunk in enumerate(chunks):
                cleaned_chunk = chunk.strip()
                if len(cleaned_chunk.split()) < 10:
                    continue

                # Déduplication simple
                normalized = cleaned_chunk.lower()
                if normalized in seen_chunks:
                    continue
                seen_chunks.add(normalized)

                all_chunks.append({
                    "id": f"chunk_{chunk_counter}",
                    "text": cleaned_chunk,
                    "metadata": {
                        "section": section,
                        "chapter": chapter,
                        "section_index": s_idx,
                        "chunk_index_in_section": i,
                        "method": best_method,
                    },
                })
                chunk_counter += 1

        # Persist evaluation scores so the API can serve them without re-running
        if method_scores:
            eval_path = Path(__file__).resolve().parent.parent / "data" / "chunking_eval.json"
            eval_path.parent.mkdir(parents=True, exist_ok=True)
            with open(eval_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"best_method": best_method, "scores": method_scores},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            print(f"\n[INFO] Scores sauvegardés dans {eval_path}")

        return all_chunks


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"

    input_path = DATA_DIR / "corpus_cleaned_fr.json"
    output_path = DATA_DIR / "corpus_chunks.json"

    try:
        manager = ChunkingManager(str(input_path))

        final_data = manager.run_final()

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                final_data,
                f,
                ensure_ascii=False,
                indent=4
            )

        print(
            f"\nTraitement terminé. "
            f"{len(final_data)} chunks "
            f"sauvegardés dans {output_path}"
        )

    except Exception as e:
        print(f"Erreur : {e}")
        raise