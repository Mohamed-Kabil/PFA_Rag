import os
import json
from dotenv import load_dotenv

# Import des modules du backend
from backend.data_extraction import PDFExtractor
from backend.chunking import ChunkingManager
from backend.vector_store import VectorStoreManager
from backend.retrieval import HybridRetriever

load_dotenv()

def run_pipeline():
    DATA_DIR = "agentic_graph_rag/data"
    os.makedirs(DATA_DIR, exist_ok=True)

    print("🚀 DÉMARRAGE DU PIPELINE RAG (ÉTAPES 1 À 4)\n")

    # --- ÉTAPE 1 : EXTRACTION PDF ---
    cleaned_path = os.path.join(DATA_DIR, "corpus_cleaned_en.json")
    if os.path.exists(cleaned_path):
        print("--- ÉTAPE 1 : EXTRACTION  ---")
        print(f"✅ Fichier déjà présent : {cleaned_path}\n")
    else:
        print("--- ÉTAPE 1 : EXTRACTION ---")
        pdf_path = os.getenv("PDF_PATH", "rag_translated_fr.pdf")
        extractor = PDFExtractor(pdf_path)
        extracted_data = extractor.extract_and_clean()
        with open(cleaned_path, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        print(f"✅ Extraction terminée : {len(extracted_data)} pages traitées.\n")

    # --- ÉTAPE 2 : CHUNKING ---
    chunks_path = os.path.join(DATA_DIR, "corpus_chunks.json")
    if os.path.exists(chunks_path):
        print("--- ÉTAPE 2 : CHUNKING ---")
        print(f"✅ Fichier déjà présent : {chunks_path}\n")
    else:
        print("--- ÉTAPE 2 : CHUNKING ---")
        chunker = ChunkingManager(cleaned_path)
        final_chunks = chunker.run_final()
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump(final_chunks, f, ensure_ascii=False, indent=4)
        print(f"✅ Chunking terminé : {len(final_chunks)} chunks générés.\n")

    # --- ÉTAPE 3 : INDEXATION VECTORIELLE ---
    index_path = os.path.join(DATA_DIR, "faiss_index.bin")
    if os.path.exists(index_path):
        print("--- ÉTAPE 3 : INDEXATION  ---")
        print(f"✅ Index FAISS déjà présent : {index_path}\n")
    else:
        print("--- ÉTAPE 3 : INDEXATION ---")
        vector_manager = VectorStoreManager(chunks_path)
        vector_manager.process(DATA_DIR)
        print(f"✅ Indexation FAISS et visualisation PCA terminées.\n")

    # --- ÉTAPE 4 : RETRIEVAL (TEST) ---
    print("--- ÉTAPE 4 : RETRIEVAL (TEST) ---")
    retriever = HybridRetriever(DATA_DIR)
    test_query = "Quels sont les effets du changement climatique sur la biodiversité ?"
    retriever.evaluate_methods(test_query)
    
    print("\n🎉 PIPELINE EXÉCUTÉ AVEC SUCCÈS JUSQU'À L'ÉTAPE 4 !")

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution : {e}")
