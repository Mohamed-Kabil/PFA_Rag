# Fixes for Module 1 (Vectorial RAG)

Date: 2026-05-05

## What was wrong/unfinished?

As identified in the `suggestion.md` gap analysis, the Vectorial RAG module in the Streamlit frontend was essentially a minimal prototype and did not match the requirements of the `project_form.pdf`. Specifically:

1. **Chunking Sub-module:** There was no user interface to select or display the different chunking methods. The hierarchical view of document splitting (Document -> Chunks -> Sub-Chunks) was missing entirely.
2. **Interactive PCA:** The PCA visualization was a static `.png` file (`pca_visualization.png`). It lacked any interactivity, making it impossible to apply a filter or highlight points close to a search query as required by the PDF.
3. **Advanced Retrieval:** The search bar only executed a generic hybrid search. It didn't expose the different search views (like Semantic Search vs. BM25 Keyword Search) to the user.
4. **Résumé Récupéré:** The UI zone dedicated to synthesizing the retrieved chunks before they are sent to the generator was missing.

## What I fixed

### Backend Changes (`backend/retrieval.py` and `backend/main_api.py`)
- **Multiple Search Strategies:** Added `semantic_search` (pure FAISS) and `bm25_search` (pure Keyword) methods to `HybridRetriever`.
- **API Update:** Modified the `/vectorial` endpoint to accept a `strategy` query parameter (`hybrid`, `semantic`, or `bm25`), enabling the frontend to request specific search types.
- **New Endpoints:** 
  - Added `/pca_data` to serve the pre-calculated PCA points, clusters, and labels from `indexed_chunks.json` for interactive plotting.
  - Added `/chunking_stats` to return the hierarchical chunking data and available methods.

### Frontend Changes (`apps/streamlit_app.py`)
- **Plotly Integration:** Replaced the static `st.image` with an interactive `st.plotly_chart` using `plotly.express`. Added a filter input field that dynamically highlights chunks matching a specific keyword.
- **Chunking UI:** Added a new sub-section with a dropdown for chunking methods and an `st.expander` that visually represents the Document -> Chunks -> Sub-Chunks hierarchy using the data from `/chunking_stats`.
- **Retrieval UI:** Added a dropdown allowing users to choose between "Hybrid BM25 + Embeddings", "Top-k Semantic Search", "Cosine Similarity", and "Keyword Match (BM25)".
- **Résumé Récupéré:** Added a dedicated synthesis section at the bottom of the search results to aggregate the retrieved text.

## How it improves the project

1. **Alignment with Requirements:** The project now strictly adheres to the UI mockup and functional requirements for "Module 1 - Bouton Vectorial RAG" detailed in the PDF.
2. **Enhanced Debugging and Interaction:** The interactive Plotly PCA allows developers and users to hover over individual points to see the chunk's text and dynamically filter specific topics, drastically improving the utility of the PCA over a static image.
3. **Flexible Retrieval:** By exposing the different search strategies directly to the frontend, users can now compare how a purely semantic search performs versus a BM25 keyword search or a hybrid approach on the same query.