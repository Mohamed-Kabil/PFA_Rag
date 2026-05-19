# Cleanup Report

Date: 2026-05-04

## Deleted Files And Folders

### Runtime/generated artifacts
- `venv/` - local Python virtual environment. It can be recreated with `python -m venv venv`.
- `__pycache__/` - generated Python bytecode cache at the project root.
- `backend/__pycache__/` - generated Python bytecode cache.
- `apps/__pycache__/` - generated Python bytecode cache created during verification.
- `scripts/__pycache__/` - generated Python bytecode cache created during verification.
- `graph.html` - generated graph visualization. New graph output is written to `outputs/graph.html`.

### Empty or unused legacy placeholders
- `agentic_graph_rag/backend/agentic.py` - empty placeholder.
- `agentic_graph_rag/backend/graph.py` - empty placeholder.
- `agentic_graph_rag/backend/vectorial.py` - empty placeholder.
- `agentic_graph_rag/backend/main.py` - placeholder script.
- `agentic_graph_rag/notebooks/01_pdf_cleaning.py` - empty placeholder.
- `agentic_graph_rag/requirements.txt` - empty placeholder.
- `agent_graph_rag/data/knowledge_graph.json` - duplicate empty graph data file.

### Security cleanup
- `backend/neo_test.py` - removed because it was only a Neo4j connection test and contained hardcoded credentials.

## Moved, Not Deleted

- `app.py` -> `apps/streamlit_app.py`
- `main.py` -> `scripts/run_pipeline.py`
- `chat.py` -> `scripts/chat_cli.py`
- `process_docx.py` -> `backend/process_docx.py`
- `coorpus_clean.docx` -> `documents/corpus_clean.docx`
- `Forme du Projet Agentic Graph RAG (1).pdf` -> `documents/project_form.pdf`
- `agentic_graph_rag/data/*` -> `data/*`
- `lib/*` -> `vendor/web/*`

## Notes

- `.gitignore` now ignores `outputs/`, `data/raw/`, and `data/cleaned/`.
- The README was updated with the new run commands.
