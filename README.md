# PFA_Rag : Agentic Vectorial Graph RAG

Projet de Fin d'Année (4ème année IA) sur le système "Agentic Vectorial Graph RAG".

## 🚀 État du projet
Actuellement, le projet a complété les **4 premières étapes** du pipeline :
1. **Extraction PDF** : Nettoyage et extraction intelligente.
2. **Chunking** : Découpage sémantique et récursif des données.
3. **Indexation Vectorielle** : Création d'un index FAISS et visualisation PCA 2D.
4. **Retrieval Hybride** : Moteur de recherche combinant Vectorial Search et BM25 avec Reranking.

## 🛠️ Installation
1. Cloner le dépôt.
2. Créer un environnement virtuel : `python -m venv venv`.
3. Installer les dépendances : `pip install -r requirements.txt`.
4. Configurer le fichier `.env` (voir `.env.example`).

## 📈 Exécution
Pour lancer le pipeline complet jusqu'à l'étape 4 :
```powershell
python main.py
```

## 📋 Prochaines Étapes
- **Étape 5** : Construction du Graphe de Connaissances (NER + REBEL).
- **Étape 6** : Injection dans Neo4j AuraDB.
- **Étape 8** : Implémentation de l'Agent Q-Learning pour le routage intelligent.
- **Étape 9/10** : Backend FastAPI et Frontend React.
