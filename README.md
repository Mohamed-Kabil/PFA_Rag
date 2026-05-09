# PFA_Rag: Agentic Vectorial Graph RAG

Projet de Fin d'Annee sur un systeme Agentic Vectorial Graph RAG.

## Structure
- `apps/` : interface Streamlit.
- `backend/` : API, retrieval, graph, generation, chunking et ingestion.
- `scripts/` : commandes CLI pour le pipeline et le chat.
- `data/` : artefacts generes ou traites par le pipeline RAG.
- `documents/` : documents sources et references du projet.
- `vendor/` : bibliotheques web vendorees.
- `outputs/` : fichiers generes a l'execution, ignores par Git.

## Installation
1. Creer un environnement virtuel : `python -m venv venv`.
2. Installer les dependances : `pip install -r requirements.txt`.
3. Configurer le fichier `.env` a partir de `.env.example`.

## Execution
Lancer le pipeline complet :
```powershell
python scripts/run_pipeline.py
```

Lancer l'API FastAPI :
```powershell
python backend/main_api.py
```

Lancer l'interface Streamlit :
```powershell
streamlit run apps/streamlit_app.py
```

Lancer le chat CLI :
```powershell
python scripts/chat_cli.py
```

## Nettoyage
Les dossiers `venv/`, `__pycache__/` et les fichiers `*.pyc` ne doivent pas etre versionnes.
Les visualisations temporaires sont ecrites dans `outputs/`.
