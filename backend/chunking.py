import json
import os
import re

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


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
        Nettoyage léger du texte.
        """

        text = re.sub(r"-{3,}", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def is_noise(self, text):
        """
        Détection simple du bruit OCR / tableaux cassés.
        """

        if not text:
            return True

        words = text.split()

        if len(words) < 5:
            return True

        alpha_chars = sum(c.isalpha() for c in text)

        alpha_ratio = alpha_chars / max(len(text), 1)

        # Trop peu de texte alphabétique
        if alpha_ratio < 0.4:
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
        return [
            s.strip()
            for s in re.split(r"(?<=[.!?]) +", text)
            if len(s.strip()) > 20
        ]

    def paragraph_chunking(self, text):
        return [
            p.strip()
            for p in text.split("\n")
            if len(p.strip()) > 30
        ]

    def sliding_window_chunking(
        self,
        text,
        size=500,
        overlap=80
    ):
        chunks = []

        start = 0

        while start < len(text):
            chunks.append(text[start:start + size])

            start += size - overlap

            if start >= len(text):
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
        Chunking sémantique conservé
        (business constraint).
        """

        sentences = self.sentence_chunking(text)

        if len(sentences) < 2:
            return sentences

        embeddings = self.get_model().encode(sentences)

        chunks = []

        current = [sentences[0]]

        for i in range(1, len(sentences)):
            sim = cosine_similarity(
                [embeddings[i - 1]],
                [embeddings[i]]
            )[0][0]

            if sim > 0.6:
                current.append(sentences[i])

            else:
                chunks.append(" ".join(current))
                current = [sentences[i]]

        chunks.append(" ".join(current))

        return chunks

    def section_based_chunking(self, text):
        sections = re.split(
            r"\n#{1,2} .+\n",
            text
        )

        return [
            s.strip()
            for s in sections
            if len(s.strip()) > 30
        ]

    def hierarchical_chunking(self, text):
        """
        Méthode principale recommandée.
        """

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=80,
            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                ""
            ],
        )

        return splitter.split_text(text)

    # =====================================================
    # EVALUATION (KEPT FOR BUSINESS NEEDS)
    # =====================================================
    def evaluate_methods(self, sample_text):
        """
        Évaluation conservée pour contraintes métier.
        MAIS le système utilisera toujours
        hierarchical_chunking.
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
            f"{'Équilibre':<10}"
        )

        print("-" * 70)

        scores = {}

        for name, func in methods.items():
            try:
                chunks = func(sample_text)

                if not chunks or len(chunks) < 2:
                    continue

                # Limite calcul lourd
                chunks = chunks[:30]

                embs = self.get_model().encode(chunks)

                sim_matrix = cosine_similarity(embs)

                np.fill_diagonal(sim_matrix, 0)

                cohesion = np.mean(sim_matrix)

                lens = [len(c) for c in chunks]

                balance = (
                    1 - (
                        np.std(lens)
                        / max(np.mean(lens), 1)
                    )
                )

                print(
                    f"{name:<20} | "
                    f"{len(chunks):<10} | "
                    f"{cohesion:.3f}      | "
                    f"{balance:.3f}"
                )

                scores[name] = (
                    cohesion * 1.5
                    + balance * 0.5
                )

            except Exception as e:
                print(f"{name:<20} | Erreur: {e}")

        if not scores:
            return "Hierarchical"

        best_method = max(scores, key=scores.get)

        print(
            f"\n[INFO] Meilleure méthode détectée : "
            f"{best_method}"
        )

        return best_method

    # =====================================================
    # MAIN PIPELINE
    # =====================================================
    def run_final(self):
        all_chunks = []

        print(
            "\n>>> Analyse du corpus "
            "pour évaluation des méthodes..."
        )

        # =========================
        # SAMPLE EXTRACTION
        # =========================
        sample_content = []

        count = 0

        for entry in self.data:
            if (
                entry.get("content")
                and len(entry["content"].strip()) > 50
            ):
                sample_content.append(
                    entry["content"]
                )

                count += 1

                if count >= 15:
                    break

        # =========================
        # EVALUATION KEPT
        # =========================
        if sample_content:
            sample_text = "\n\n".join(sample_content)

            self.evaluate_methods(sample_text)

        # =========================
        # FORCE HIERARCHICAL
        # =========================
        best_method = "Hierarchical"

        print(
            f"\n>>> Méthode FORCÉE : "
            f"{best_method}"
        )

        chunk_func = self.hierarchical_chunking

        # =========================
        # GROUP BY SECTION
        # =========================
        grouped_sections = {}

        for entry in self.data:
            if not entry.get("content"):
                continue

            cleaned = self.clean_text(
                entry["content"]
            )

            # Ignore bruit
            if self.is_noise(cleaned):
                continue

            section = entry.get(
                "section",
                "Inconnu"
            )

            section_index = entry.get(
                "section_index",
                0
            )

            group_key = (
                section_index,
                section
            )

            if group_key not in grouped_sections:
                grouped_sections[group_key] = {
                    "chapter": entry.get(
                        "chapter",
                        "Inconnu"
                    ),
                    "section": section,
                    "section_index": section_index,
                    "content_list": [],
                }

            grouped_sections[group_key][
                "content_list"
            ].append(cleaned)

        # =========================
        # CHUNK GENERATION
        # =========================
        chunk_counter = 0

        seen_chunks = set()

        for _, section_data in sorted(
            grouped_sections.items(),
            key=lambda item: item[0][0]
        ):
            merged_text = "\n\n".join(
                section_data["content_list"]
            )

            if not merged_text.strip():
                continue

            chunks = chunk_func(merged_text)

            for i, chunk in enumerate(chunks):
                cleaned_chunk = self.clean_text(
                    chunk
                )

                # Ignore petits chunks
                if len(cleaned_chunk.split()) < 15:
                    continue

                # Deduplication
                normalized = cleaned_chunk.lower()

                if normalized in seen_chunks:
                    continue

                seen_chunks.add(normalized)

                all_chunks.append({
                    "id": f"chunk_{chunk_counter}",
                    "text": cleaned_chunk,
                    "metadata": {
                        "section": section_data["section"],
                        "chapter": section_data["chapter"],
                        "section_index": section_data["section_index"],
                        "chunk_index_in_section": i,
                        "method": best_method,
                    },
                })

                chunk_counter += 1

        return all_chunks


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    data_dir = "data"

    input_path = os.path.join(
        data_dir,
        "corpus_cleaned_fr.json"
    )

    output_path = os.path.join(
        data_dir,
        "corpus_chunks.json"
    )

    try:
        manager = ChunkingManager(input_path)

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