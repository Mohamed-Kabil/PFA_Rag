import json
import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import pickle
from dotenv import load_dotenv

load_dotenv()

class VectorStoreManager:
    def __init__(self, chunks_file):
        self.chunks_file = chunks_file
        if not os.path.exists(chunks_file):
            raise FileNotFoundError(f"Fichier chunks introuvable : {chunks_file}")
            
        with open(chunks_file, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
        
        print("Chargement du modèle d'embeddings...")
        self.model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
        self.index = None
        self.pca_model = None

    def plot_pca(self, pca_points, output_path):
        """Génère et sauvegarde la visualisation PCA en PNG."""
        print(f"Génération du graphique PCA dans {output_path}...")
        plt.figure(figsize=(12, 8))
        plt.scatter(pca_points[:, 0], pca_points[:, 1], alpha=0.5, c='blue', edgecolors='w', s=30)
        plt.title('Visualisation 2D des Chunks du Corpus (PCA)')
        plt.xlabel('Composante Principale 1')
        plt.ylabel('Composante Principale 2')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.savefig(output_path)
        plt.close() # Fermer pour libérer la mémoire

    def process(self, output_dir):
        """Génère les embeddings, crée l'index FAISS, calcule la PCA et génère l'image."""
        texts = [c['text'] for c in self.chunks]
        
        print(f"Génération des embeddings pour {len(texts)} chunks...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')

        # Normalisation pour la similarité cosinus
        faiss.normalize_L2(embeddings)

        # 1. Création de l'index FAISS
        print("Création de l'index FAISS...")
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)

        # 2. Calcul de la PCA 2D
        print("Calcul de la projection PCA 2D...")
        self.pca_model = PCA(n_components=2)
        pca_points = self.pca_model.fit_transform(embeddings)

        # Sauvegarde des fichiers
        os.makedirs(output_dir, exist_ok=True)
        
        # Sauvegarder l'index
        faiss.write_index(self.index, os.path.join(output_dir, "faiss_index.bin"))
        
        # Sauvegarder le modèle PCA
        with open(os.path.join(output_dir, "pca_model.pkl"), "wb") as f:
            pickle.dump(self.pca_model, f)
            
        # Générer l'image PNG
        self.plot_pca(pca_points, os.path.join(output_dir, "pca_visualization.png"))

        # Mettre à jour les chunks avec les coordonnées PCA
        for i, chunk in enumerate(self.chunks):
            chunk['pca_x'] = float(pca_points[i][0])
            chunk['pca_y'] = float(pca_points[i][1])

        with open(os.path.join(output_dir, "indexed_chunks.json"), "w", encoding='utf-8') as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=4)
        
        print(f"Indexation et visualisation terminées dans {output_dir}")

if __name__ == "__main__":
    DATA_DIR = "agentic_graph_rag/data"
    chunks_path = os.path.join(DATA_DIR, "corpus_chunks.json")
    
    try:
        manager = VectorStoreManager(chunks_path)
        manager.process(DATA_DIR)
    except Exception as e:
        print(f"Erreur lors de l'indexation : {e}")
