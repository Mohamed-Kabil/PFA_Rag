import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory (PFA_Rag/)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from PFA_Rag/.env
load_dotenv(ROOT_DIR / ".env")

# Data Directories
DATA_DIR = ROOT_DIR / "data"
CHUNKS_DIR = DATA_DIR  # Currently chunks are directly in data/
CORPUS_DIR = ROOT_DIR / "documents"
EMBEDDINGS_DIR = DATA_DIR
GRAPH_DIR = DATA_DIR

# File Paths
CHUNKS_JSON = DATA_DIR / "corpus_chunks.json"
FAISS_INDEX = DATA_DIR / "faiss_index.bin"
KNOWLEDGE_GRAPH_JSON = DATA_DIR / "knowledge_graph.json"
Q_TABLE_JSON = DATA_DIR / "q_table.json"
CORPUS_CLEAN_DOCX = CORPUS_DIR / "corpus_clean.docx"

# Neo4j Config
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Hugging Face
HF_TOKEN = os.getenv("HF_TOKEN")

# Model Config
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
RERANK_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
LLM_MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
NER_MODEL_NAME = "Jean-Baptiste/camembert-ner"
REBEL_MODEL_NAME = "Babelscape/rebel-large"

# Server Config
HOST = "0.0.0.0"
PORT = 8000
