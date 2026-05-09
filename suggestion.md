# Project Gap Analysis & Suggestions

Date: 2026-05-05

This document compares the project requirements outlined in `documents/project_form.pdf` with the current state of the codebase (`apps/streamlit_app.py`, `backend/main_api.py`, `backend/agent.py`) and suggests necessary fixes and implementations to meet the required specifications.

## 1. Vectorial RAG Module (Module 1)
**Current State:** 
- Displays a static PCA 2D visualization (`pca_visualization.png`).
- Basic semantic search input returning text chunks and scores.

**Missing Elements from PDF:**
- **Chunking Sub-module:** No interface to display the "7 chunking methods" (fixed size, sentences, paragraphs, semantic, sliding window, recursive). Missing the hierarchical visualization of document splitting (Document -> Chunks -> Sub-Chunks).
- **Advanced Retrieval:** The UI only shows one generic search. It needs to expose the "5 search views" (e.g., Top-k Semantic Search, Cosine Similarity, Hybrid BM25 + Embeddings).
- **PCA Filtering:** The PCA plot is a static image. The PDF requires the ability to "add a filter to display the points closest to the query". This requires migrating from a static PNG to an interactive Plotly/Altair chart.
- **Résumé Récupéré:** Missing a dedicated UI zone that synthesizes the retrieved documents before the final answer generation.

**Suggestions for Fixes:**
- **Frontend:** Update `tab_vector` in Streamlit to include dropdowns for chunking methods and search strategies. Replace `st.image` with `st.plotly_chart` for an interactive PCA.
- **Backend:** Add endpoints `/chunking_stats` to return hierarchical chunk data and update `/vectorial` to accept a `strategy` parameter (e.g., `?strategy=hybrid`).

## 2. Graph RAG Module (Module 2)
**Current State:**
- Pyvis interactive graph generation.
- Basic Louvain community execution and display of top 10 communities.
- Basic centrality and density metrics.

**Missing Elements from PDF:**
- **Modularity Score:** The Louvain algorithm runs, but the modularity score (e.g., `0.82` in the PDF) is not calculated or returned by the backend.
- **Advanced Graph Analysis:** Missing "Chemins sémantiques" (Semantic Paths) and "Fusion Graphe + Vectoriel". 
- **Graph Aura Filters/Legends:** The PDF explicitly requests zoom, filter options, and relationship legends. While Pyvis supports zoom, it lacks a dedicated UI for filtering specific nodes/relationships.

**Suggestions for Fixes:**
- **Frontend:** Add a section for Semantic Paths (Shortest path between two concepts). Add a metric card for the Modularity Score in the Louvain section.
- **Backend:** Update the `/louvain` endpoint to calculate and return the modularity score. Add an endpoint `/semantic_path?source=X&target=Y` using Neo4j's shortest path algorithms.

## 3. Agentic Graph RAG Module (Module 3)
**Current State:**
- Sidebar displays a raw DataFrame of the Q-Table.
- Basic Q-Learning logic exists in `agent.py`.

**Missing Elements from PDF:**
- **Policy Visualization:** Missing a visual state diagram (State -> Action).
- **Reward Monitor:** Missing a line chart showing rewards over time / iterations.
- **Decision Path:** Missing a visual flowchart of the chosen path (Query -> Semantic/Systematic Analysis -> Vectorial/Graph Branch).
- **Graph Query Execution:** Does not show the actual Neo4j Cypher queries executed under the hood when Graph RAG is chosen.
- **Hybrid Feedback Loop:** Missing explanation/UI showing how the result updates the Q-Learning memory.

**Suggestions for Fixes:**
- **Frontend:** Completely revamp `tab_agent`. Use `st.line_chart` for the Reward Monitor. Use `st.graphviz_chart` or custom HTML/CSS to visualize the Decision Path and Policy state machine. 
- **Backend:** Modify `agent.py` to maintain a history of rewards (e.g., `self.reward_history = []`) and return it via the `/agentic` endpoint. Modify `run_query` to return the specific features detected (Semantic vs Systematic) and the Cypher queries used, so the frontend can render the Decision Path.

## 4. Query Module (Module 4)
**Current State:**
- Functional chat interface taking a query and returning an answer, action taken, and confidence score.

**Missing Elements from PDF:**
- **Automatic Query Analysis Display:** The PDF requires displaying the detected type in real-time (Semantic, Systematic, or Hybrid). Currently, it only shows the final "Action" taken by the agent.
- **Routing Preview:** Missing a visual indicator (like an arrow pointing to a specific module block) showing where the request is routed *before* or *during* execution.
- **Reset Button Location:** The "Réinitialiser" button is currently in the sidebar, but the PDF mockup places it directly under the history in the Query tab.

**Suggestions for Fixes:**
- **Frontend:** Move the Reset button into the `tab_chat` layout. Add dynamic UI elements (like progress bars or colored badges) that light up to show the "Routing Preview" and "Query Analysis" based on the metadata returned by the API.

## Conclusion & Next Steps
The backend architecture (`FastAPI` + `agent.py`) is solidly in place and functional, but the **Streamlit Frontend** is currently a simplified prototype. To align with the PDF, significant UI work is required to expose the underlying complexity (chunking methods, reward charts, dynamic PCA, and decision flowcharts). 

**Recommended First Step:** Upgrade the PCA visualization to Plotly to support the requested query filtering, and add the missing Reward History chart to the Agentic tab, as these provide immediate visual alignment with the project mockup.