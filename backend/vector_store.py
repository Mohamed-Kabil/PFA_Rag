import json
import os
import pickle
from collections import Counter

import faiss
import matplotlib.pyplot as plt
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from pathlib import Path
from backend import config

class VectorStoreManager:
    def __init__(self, chunks_file):
        self.chunks_file = Path(chunks_file)
        if not self.chunks_file.exists():
            raise FileNotFoundError(f"Fichier chunks introuvable : {chunks_file}")

        with open(self.chunks_file, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        print("Chargement du modele d'embeddings...")
        self.model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
        self.index = None
        self.pca_model = None

    def _labels_for_plot(self, cluster_labels):
        chapters = [c.get("metadata", {}).get("chapter", "Inconnu") for c in self.chunks]
        chapter_counts = Counter(chapters)
        useful_chapters = [chapter for chapter, count in chapter_counts.items() if count >= 3]

        if 1 < len(useful_chapters) <= 12:
            return "chapter", chapters
        return "cluster", [f"Cluster {label}" for label in cluster_labels]

    def plot_pca(self, pca_points, labels, explained_variance, output_path):
        print(f"Generation du graphique PCA dans {output_path}...")
        unique_labels = list(dict.fromkeys(labels))
        cmap = plt.get_cmap("tab20", max(len(unique_labels), 1))

        plt.figure(figsize=(14, 9))
        for idx, label in enumerate(unique_labels):
            mask = np.array(labels) == label
            plt.scatter(
                pca_points[mask, 0],
                pca_points[mask, 1],
                alpha=0.72,
                s=38,
                color=cmap(idx),
                label=label[:45],
                edgecolors="white",
                linewidths=0.35,
            )

        total_variance = explained_variance[0] + explained_variance[1]
        plt.title(f"PCA des chunks - variance conservee: {total_variance:.1%}")
        plt.xlabel(f"PC1 ({explained_variance[0]:.1%})")
        plt.ylabel(f"PC2 ({explained_variance[1]:.1%})")
        plt.grid(True, linestyle="--", alpha=0.35)
        if len(unique_labels) <= 12:
            plt.legend(loc="best", fontsize=8, frameon=True)
        plt.tight_layout()
        plt.savefig(output_path, dpi=180)
        plt.close()

    def process(self, output_dir):
        texts = [c["text"] for c in self.chunks]
        if not texts:
            raise ValueError("Aucun chunk disponible pour l'indexation.")

        print(f"Generation des embeddings pour {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        embeddings = np.array(embeddings).astype("float32")

        faiss.normalize_L2(embeddings)

        print("Creation de l'index FAISS...")
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)

        print("Calcul de la projection PCA 2D...")
        self.pca_model = PCA(n_components=2)
        pca_points = self.pca_model.fit_transform(embeddings)

        cluster_count = min(8, max(2, int(np.sqrt(len(texts)))))
        kmeans = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
        label_type, plot_labels = self._labels_for_plot(cluster_labels)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(output_dir / "faiss_index.bin"))

        with open(output_dir / "pca_model.pkl", "wb") as f:
            pickle.dump(self.pca_model, f)

        explained = self.pca_model.explained_variance_ratio_
        self.plot_pca(
            pca_points,
            plot_labels,
            explained,
            str(output_dir / "pca_visualization.png"),
        )

        for i, chunk in enumerate(self.chunks):
            chunk["pca_x"] = float(pca_points[i][0])
            chunk["pca_y"] = float(pca_points[i][1])
            chunk["cluster_id"] = int(cluster_labels[i])
            chunk["plot_label"] = plot_labels[i]

        with open(output_dir / "indexed_chunks.json", "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=4)

        stats = {
            "chunk_count": len(self.chunks),
            "embedding_dimension": int(dimension),
            "pca_explained_variance_ratio": [float(v) for v in explained],
            "pca_total_2d_variance": float(explained[0] + explained[1]),
            "cluster_count": int(cluster_count),
            "plot_label_type": label_type,
            "plot_label_counts": dict(Counter(plot_labels)),
        }
        with open(output_dir / "pca_stats.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=4)

        print(f"Indexation et visualisation terminees dans {output_dir}")


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    chunks_path = DATA_DIR / "corpus_chunks.json"

    try:
        manager = VectorStoreManager(chunks_path)
        manager.process(DATA_DIR)
    except Exception as e:
        print(f"Erreur lors de l'indexation : {e}")
