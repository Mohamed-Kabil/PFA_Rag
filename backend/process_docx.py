import json
import os
import re
from pathlib import Path

import docx

from backend.chunking import ChunkingManager


KNOWN_SECTION_TITLES = {
    "abstract",
    "introduction",
    "materiel & methodes",
    "materiel et methodes",
    "matériel & méthodes",
    "matériel et méthodes",
    "methods",
    "results",
    "resultats",
    "résultats",
    "discussion",
    "conclusion",
    "remerciements",
    "bibliographie",
    "references",
    "perspectives",
}


def _normalized_title(text):
    return re.sub(r"\s+", " ", text.replace("#", "")).strip()


def _looks_like_chapter(text):
    lowered = _normalized_title(text).lower()
    return (
        lowered.startswith(("chapitre", "chapter"))
        or lowered
        in {
            "introduction générale",
            "introduction generale",
            "conclusion générale",
            "conclusion generale",
        }
    )


def _looks_like_heading(text):
    cleaned = _normalized_title(text)
    lowered = cleaned.lower()
    word_count = len(cleaned.split())

    # Empty / invalid
    if not cleaned:
        return False

    # Ignore figures/tables
    if text.startswith(("Tableau", "Table", "Figure", "Fig.")):
        return False

    # Prevent OCR garbage / giant uppercase blocks
    if cleaned.isupper() and len(cleaned) > 80:
        return False

    # Too short to be a real heading
    if word_count < 2:
        return False

    # Known scientific sections
    if lowered in KNOWN_SECTION_TITLES:
        return True

    # Chapter detection
    if _looks_like_chapter(cleaned):
        return True

    # Markdown headings
    if text.startswith(("# ", "## ")):
        return True

    has_sentence_punctuation = cleaned.endswith((".", ";", ":"))

    has_citation = bool(
        re.search(
            r"\([A-Z][A-Za-z-]+ et al\.|\b\d{4}\b",
            cleaned
        )
    )

    return (
        len(cleaned) <= 140
        and word_count <= 16
        and not has_sentence_punctuation
        and not has_citation
    )

def read_docx(file_path):
    """
    Lecture structurée du document DOCX.
    """

    doc = docx.Document(file_path)

    data = []

    current_chapter = "Document"
    current_section_title = "Front matter"

    section_index = 0

    for para in doc.paragraphs:
        text = para.text.strip()

        if not text:
            continue

        # =========================
        # SAFE STYLE ACCESS
        # =========================
        style_name = getattr(
            para.style,
            "name",
            ""
        )

        style_id = getattr(
            para.style,
            "style_id",
            ""
        )

        # =========================
        # HEADING DETECTION
        # =========================
        is_heading_1 = (
            style_name == "Heading 1"
            or style_id == "Heading1"
        )

        is_heading = (
            style_name.startswith("Heading")
            or style_id.startswith("Heading")
            or _looks_like_heading(text)
        )

        # =========================
        # HEADING
        # =========================
        if is_heading:
            heading_text = _normalized_title(text)

            # Nouveau chapitre
            if (
                is_heading_1
                or _looks_like_chapter(heading_text)
            ):
                current_chapter = heading_text

            current_section_title = heading_text

            section_index += 1

            para_type = "heading"

        # =========================
        # TABLE
        # =========================
        elif text.startswith(("Tableau", "Table")):
            para_type = "table"

        # =========================
        # FIGURE
        # =========================
        elif (
            "[Figure]" in text
            or text.startswith(("Figure", "Fig."))
        ):
            para_type = "figure"

        # =========================
        # NORMAL PARAGRAPH
        # =========================
        else:
            para_type = "paragraph"

        data.append({
            "section_index": section_index,
            "chapter": current_chapter,
            "section": current_section_title,
            "type": para_type,
            "content": text,
        })

    return data

from backend import config

def run_pipeline_for_docx(include_graph=False, include_neo4j=False):
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    docx_path = config.CORPUS_CLEAN_DOCX

    print(f"--- 1. LECTURE DU FICHIER {docx_path} ---")
    data = read_docx(str(docx_path))

    cleaned_path = config.DATA_DIR / "corpus_cleaned_fr.json"
    with open(cleaned_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Fichier lu : {len(data)} blocs generes.\n")

    print("--- 2. CHUNKING ---")
    chunker = ChunkingManager(str(cleaned_path))
    final_chunks = chunker.run_final()

    chunks_path = config.CHUNKS_JSON
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(final_chunks, f, ensure_ascii=False, indent=4)
    print(f"Chunking termine : {len(final_chunks)} chunks.\n")

    print("--- 3. INDEXATION VECTORIELLE ---")
    from backend.vector_store import VectorStoreManager

    vector_manager = VectorStoreManager(str(chunks_path))
    vector_manager.process(str(config.DATA_DIR))
    print("Indexation FAISS terminee.\n")

    if include_graph:
        from backend.graph_extraction import GraphExtractor

        print("--- 4. EXTRACTION GRAPH ---")
        graph_path = config.KNOWLEDGE_GRAPH_JSON
        graph_extractor = GraphExtractor()
        graph_extractor.run(str(chunks_path), str(graph_path), limit_chunks=None)
        print("Extraction Graph terminee.\n")

    if include_neo4j:
        from backend.neo4j_manager import Neo4jManager

        print("--- 5. IMPORT NEO4J & LOUVAIN ---")
        neo4j_manager = Neo4jManager()
        graph_path = config.KNOWLEDGE_GRAPH_JSON
        neo4j_manager.run_pipeline(str(chunks_path), str(graph_path))

    print("\nPipeline DOCX execute avec succes.")


if __name__ == "__main__":
    try:
        run_pipeline_for_docx()
    except Exception as e:
        print(f"\nErreur lors de l'execution : {e}")
        raise
