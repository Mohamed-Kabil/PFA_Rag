import os
import json
import docx
from backend.chunking import ChunkingManager
from backend.vector_store import VectorStoreManager
from backend.graph_extraction import GraphExtractor
from backend.neo4j_manager import Neo4jManager


# BLOCK 1: Lecture et extraction DOCX
def read_docx(file_path):
    doc = docx.Document(file_path)
    data = []
    
    current_chapter = "Introduction générale"
    current_section_title = "Introduction"
    section_index = 1
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
            
        # 1. Identifier les chapitres
        is_heading_1 = (para.style.name == "Heading 1" or para.style.style_id == "Heading1")
        if is_heading_1:
            current_chapter = text.replace("#", "").strip()
            
        # 2. Identifier les sections
        is_heading = (
            para.style.name.startswith("Heading") or 
            para.style.style_id.startswith("Heading") or
            text.startswith("## ") or 
            text.startswith("# ")
        )
        
        # 3. Identifier le type de paragraphe
        if is_heading:
            current_section_title = text.replace("#", "").strip()
            section_index += 1
            para_type = "heading"
        elif text.startswith("Tableau") or text.startswith("Table"):
            para_type = "table"
        elif "[Figure]" in text or text.startswith("Figure") or text.startswith("Fig."):
            para_type = "figure"
        else:
            para_type = "paragraph"
            
        # 4. Ajouter l'entrée individuelle
        data.append({
            "section_index": section_index,
            "chapter": current_chapter,
            "section": current_section_title,
            "type": para_type,
            "content": text
        })
        
    return data


def run_pipeline_for_docx():
    DATA_DIR = "agentic_graph_rag/data"
    os.makedirs(DATA_DIR, exist_ok=True)

    docx_path = "coorpus_clean.docx"

    print(f"--- 1. LECTURE DU FICHIER {docx_path} ---")
    data = read_docx(docx_path)

    cleaned_path = os.path.join(DATA_DIR, "corpus_cleaned_fr.json")
    with open(cleaned_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"✅ Fichier lu : {len(data)} blocs générés.\n")

    print("--- 2. CHUNKING ---")
    chunker = ChunkingManager(cleaned_path)
    final_chunks = chunker.run_final()

    chunks_path = os.path.join(DATA_DIR, "corpus_chunks.json")
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(final_chunks, f, ensure_ascii=False, indent=4)
    print(f"✅ Chunking terminé : {len(final_chunks)} chunks.\n")

    print("--- 3. INDEXATION VECTORIELLE ---")
    vector_manager = VectorStoreManager(chunks_path)
    vector_manager.process(DATA_DIR)
    print(f"✅ Indexation FAISS terminée.\n")

    print("--- 4. EXTRACTION GRAPH ---")
    graph_path = os.path.join(DATA_DIR, "knowledge_graph.json")
    graph_extractor = GraphExtractor()
    graph_extractor.run(chunks_path, graph_path, limit_chunks=None)
    print(f"✅ Extraction Graph terminée.\n")

    print("--- 5. IMPORT NEO4J & LOUVAIN ---")
    neo4j_manager = Neo4jManager()
    neo4j_manager.run_pipeline(chunks_path, graph_path)

    print("\n🎉 PIPELINE EXÉCUTÉ AVEC SUCCÈS SUR LE NOUVEAU FICHIER !")


if __name__ == "__main__":
    try:
        run_pipeline_for_docx()
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution : {e}")
        raise