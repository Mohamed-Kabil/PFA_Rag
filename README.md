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

---

## Deploiement Docker

### Prerequis
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installe et en cours d'execution.

### 1. Configurer le fichier `.env`

Copier `.env.example` en `.env` et remplir les valeurs :

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `HF_TOKEN` | Token HuggingFace (telecharger les modeles Qwen, camembert-ner, rebel-large…) |
| `NEO4J_URI` | URI de la base Neo4j AuraDB (format `neo4j+s://…`) |
| `NEO4J_USER` | Nom d'utilisateur Neo4j |
| `NEO4J_PASSWORD` | Mot de passe Neo4j |
| `PDF_PATH` | Chemin vers le document source (defaut : `documents/corpus_clean.docx`) |
| `VITE_API_URL` | URL du backend visible par le navigateur (defaut : `http://localhost:8000`) |

### 2. Lancer les conteneurs

```bash
docker-compose up --build
```

- **Backend FastAPI** → [http://localhost:8000](http://localhost:8000)
- **Frontend React** → [http://localhost:3000](http://localhost:3000)

> **Note :** Le premier demarrage telecharge les modeles HuggingFace (plusieurs Go).
> Les modeles sont mis en cache dans le volume Docker `hf_cache` pour les relances suivantes.

### 3. Arreter les conteneurs

```bash
docker-compose down
```

Pour supprimer egalement le cache des modeles :

```bash
docker-compose down -v
```

### Volumes persistants

| Volume / Montage | Contenu |
|---|---|
| `./data` → `/app/data` | Index FAISS, chunks corpus, modele PCA, graphe de connaissances |
| `./documents` → `/app/documents` | Documents sources PDF / DOCX |
| `hf_cache` (volume nomme) | Modeles HuggingFace telecharges |
