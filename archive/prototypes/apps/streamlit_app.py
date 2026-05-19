import streamlit as st
import requests
import pandas as pd
import time
import os
from pathlib import Path
from pyvis.network import Network
import streamlit.components.v1 as components
import plotly.express as px

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Configuration de la page
st.set_page_config(
    page_title="Agentic Graph RAG",
    page_icon="🤖",
    layout="wide"
)

# Style CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #FF4B4B; color: white; }
    .metric-card { background-color: #1e1e26; padding: 15px; border-radius: 8px; text-align: center; border-left: 5px solid #FF4B4B; margin-bottom: 10px; }
    .chat-bubble { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

API_URL = "http://localhost:8000"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

st.title("🤖 Agentic Vectorial Graph RAG")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ Configuration")
    st.info("Modèle : Qwen2-0.5B\n\nBackend : FastAPI")
    
    if st.button("🔄 Rafraîchir les Stats Agentic"):
        try:
            resp = requests.get(f"{API_URL}/agentic").json()
            st.session_state.agent_state = resp
        except: st.error("API non connectée")

    if st.button("🗑️ Réinitialiser (Reset)"):
        st.session_state.chat_history = []
        st.rerun()

    if 'agent_state' in st.session_state:
        st.subheader("📊 État de la Q-Table")
        df_q = pd.DataFrame(st.session_state.agent_state['q_table']).T
        df_q.columns = ["Vector", "Graph", "Hybrid"]
        st.dataframe(df_q.style.highlight_max(axis=1, color="#FF4B4B"))

tab_chat, tab_vector, tab_graph, tab_agent = st.tabs([
    "💬 Chat (Full RAG)", "📁 Module 1: Vectorial", "🕸️ Module 2: Graph", "🧠 Module 3: Agentic"
])

# --- TAB 1: CHAT ---
with tab_chat:
    st.subheader("Posez une question scientifique")
    query = st.text_input("Saisie de la requête :", placeholder="Ex: Quel est l'impact de la fragmentation ?")
    
    if st.button("🚀 Exécuter l'Analyse"):
        if query:
            with st.spinner("Analyse en cours..."):
                try:
                    response = requests.post(f"{API_URL}/query", json={"question": query}).json()
                    st.session_state.chat_history.append({"query": query, "answer": response['answer'], "action": response['action_taken'], "confidence": response['confidence_score']})
                    
                    col1, col2, col3 = st.columns(3)
                    with col1: st.markdown(f"<div class='metric-card'><b>Action</b><br>{response['action_taken']}</div>", unsafe_allow_html=True)
                    with col2: st.markdown(f"<div class='metric-card'><b>Confiance</b><br>{response['confidence_score']*100}%</div>", unsafe_allow_html=True)
                    with col3: st.markdown(f"<div class='metric-card'><b>Status</b><br>Success</div>", unsafe_allow_html=True)
                    
                    st.markdown("### 🤖 Réponse Finale")
                    st.success(response['answer'])
                except Exception as e: st.error(f"Erreur : {e}")

    if st.session_state.chat_history:
        st.markdown("---")
        st.subheader("📜 Historique")
        for item in reversed(st.session_state.chat_history):
            with st.expander(f"Q: {item['query']} ({item['action']})"):
                st.write(item['answer'])

# --- TAB 2: VECTORIAL ---
with tab_vector:
    st.header("⚙️ Module 1: Vectorial RAG")
    
    # --- Sous-module: Chunking ---
    st.subheader("1. Text Chunking & Hierarchical Splitting")
    col_c1, col_c2 = st.columns([1, 2])
    
    with col_c1:
        st.markdown("**Méthodes de découpage :**")
        chunk_method = st.selectbox("Sélectionnez une méthode", 
            ["Hierarchical Splitting", "Recursive Splitting", "Semantic Chunking", "Sliding Window", "Fixed-Size", "Sentence", "Paragraph"], index=0)
        st.info("L'interface choisit automatiquement la meilleure méthode selon ton corpus.")
        
    with col_c2:
        try:
            c_stats = requests.get(f"{API_URL}/chunking_stats").json()
            st.metric("Total des Chunks générés", c_stats['total_chunks'])
            with st.expander("Voir la hiérarchie Document -> Chunks -> Sub-Chunks"):
                st.write(f"📄 **Document Complet:** {c_stats['hierarchy']['document']}")
                st.write(f" └─ 🧩 **Chunks:** {c_stats['hierarchy']['total_chunks']} blocs principaux")
                st.write("     └─ ✂️ **Sub-Chunks (Extraits):**")
                for sub in c_stats['hierarchy']['sample_sub_chunks']:
                    st.caption(f"      - {sub}")
        except Exception as e:
            st.error(f"Erreur chargement chunking stats: {e}")

    st.markdown("---")
    
    # --- Sous-module: Embeddings & PCA ---
    st.subheader("2. Embeddings Visualization (PCA 2D)")
    col_e1, col_e2 = st.columns([1, 3])
    
    pca_query = col_e1.text_input("Filtrer (Proximité requête):", placeholder="Mot clé...", key="pca_filter")
    
    with col_e2:
        try:
            pca_data = requests.get(f"{API_URL}/pca_data").json()
            chunks = pca_data['chunks']
            df_pca = pd.DataFrame([{
                'x': c['pca_x'], 'y': c['pca_y'], 
                'label': c['plot_label'], 'text': c['text'][:100] + "..."
            } for c in chunks if 'pca_x' in c])
            
            if pca_query:
                # Basic simulated filter for proximity in UI
                df_pca['is_match'] = df_pca['text'].str.contains(pca_query, case=False, na=False)
                df_pca = df_pca.sort_values(by='is_match')
                fig = px.scatter(df_pca, x='x', y='y', color='label', hover_data=['text'], 
                                 symbol='is_match', symbol_sequence=['circle', 'star'],
                                 title=f"PCA des Embeddings FAISS (Filtre: {pca_query})")
                fig.update_traces(marker=dict(size=8, line=dict(width=1, color='DarkSlateGrey')))
            else:
                fig = px.scatter(df_pca, x='x', y='y', color='label', hover_data=['text'], 
                                 title="PCA des Embeddings FAISS")
                fig.update_traces(marker=dict(size=6, opacity=0.7))
                
            fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=400)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Erreur chargement PCA Interactive: {e}")

    st.markdown("---")
    
    # --- Sous-module: Retrieval Vectoriel ---
    st.subheader("3. Vector Retrieval")
    col_v1, col_v2 = st.columns([1, 2])
    
    with col_v1:
        search_view = st.selectbox("Sélectionnez la vue de recherche :", 
            ["Hybrid BM25 + Embeddings", "Top-k Semantic Search", "Cosine Similarity", "Keyword Match (BM25)"], index=0)
        
        strategy_map = {
            "Hybrid BM25 + Embeddings": "hybrid",
            "Top-k Semantic Search": "semantic",
            "Cosine Similarity": "semantic",
            "Keyword Match (BM25)": "bm25"
        }
        
    v_query = st.text_input("Recherche sémantique :", key="v_search", placeholder="Que cherche-t-on ?")
    
    if st.button("🔍 Lancer la Recherche"):
        if v_query:
            strat = strategy_map.get(search_view, "hybrid")
            with st.spinner("Recherche et synthèse en cours..."):
                resp = requests.get(f"{API_URL}/vectorial", params={"q": v_query, "strategy": strat}).json()
            
            st.markdown(f"**Documents pertinents ({search_view}) :**")
            for res in resp['results']: 
                st.markdown(f"<div class='chat-bubble'><b>Score: {res['score']:.4f}</b><br>{res['text']}</div>", unsafe_allow_html=True)
            
            # --- Résumé Récupéré (Requirement satisfied) ---
            st.markdown("### 📝 Résumé Récupéré")
            if 'summary' in resp:
                st.success(resp['summary'])
            else:
                st.warning("Résumé non disponible.")


# --- TAB 3: GRAPH ---
with tab_graph:
    st.subheader("Analyse du Graphe de Connaissances")
    g_query = st.text_input("Explorer un concept :", key="g_search")
    if st.button("🕸️ Analyser le Graphe"):
        resp = requests.get(f"{API_URL}/graph", params={"q": g_query}).json()
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: st.metric("Densité globale", f"{resp['metrics']['density']:.4f}")
        with col_m2: st.metric("Total Nœuds", resp['metrics']['total_nodes'])
        with col_m3: st.metric("Total Relations", resp['metrics']['total_edges'])
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.write("#### 📊 Centralité (Top 5 Global)")
            st.bar_chart(pd.DataFrame(list(resp['metrics']['global_centrality'].items()), columns=['Concept', 'Degré']).set_index('Concept'))
        with col_c2:
            st.write("#### 🔍 Centralité (Résultats Query)")
            st.bar_chart(pd.DataFrame(list(resp['metrics']['centrality'].items()), columns=['Concept', 'Centralité']).set_index('Concept'))
        
        st.write("### 🧬 Liste des Entités et Communautés")
        for ent in resp['entities']:
            st.markdown(f"**{ent['entity']}** (Communauté: {ent.get('community', 'N/A')})")
            for r in ent['relations']:
                if r['rel']: st.write(f" └─ [{r['rel']}] -> {r['target']}")

    st.markdown("---")
    st.subheader("🛣️ Chemins Sémantiques (Shortest Path)")
    col_p1, col_p2 = st.columns(2)
    p_start = col_p1.text_input("Concept A", value="Espèces")
    p_end = col_p2.text_input("Concept B", value="Climat")
    
    if st.button("🗺️ Trouver le chemin"):
        path_resp = requests.get(f"{API_URL}/shortest_path", params={"start": p_start, "end": p_end}).json()
        if path_resp['status'] == "success":
            path = path_resp['path']
            st.info(" -> ".join(path['nodes']))
            st.caption(f"Relations: {', '.join(path['rels'])}")
        else:
            st.warning(path_resp['message'])

    st.markdown("---")
    st.subheader("🌐 Visualisation Interactive")
    if st.button("📊 Générer la Carte Interactive"):
        with st.spinner("Génération du graphe en cours..."):
            try:
                response = requests.get(f"{API_URL}/graph_data")
                if response.status_code == 200:
                    graph_resp = response.json()
                    nodes = graph_resp['nodes']
                    edges = graph_resp['edges']
                    
                    # Création du graphe Pyvis avec options de stabilisation
                    net = Network(height="600px", width="100%", bgcolor="#0e1117", font_color="white", notebook=False)
                    
                    # Configuration avancée pour le centrage et la fluidité
                    net.set_options("""
                    {
                      "physics": {
                        "forceAtlas2Based": {
                          "gravitationalConstant": -50,
                          "centralGravity": 0.01,
                          "springLength": 100,
                          "springConstant": 0.08
                        },
                        "maxVelocity": 50,
                        "solver": "forceAtlas2Based",
                        "timestep": 0.35,
                        "stabilization": {
                          "enabled": true,
                          "iterations": 1000,
                          "updateInterval": 25,
                          "onlyDynamicEdges": false,
                          "fit": true
                        }
                      },
                      "interaction": {
                        "hover": true,
                        "navigationButtons": true,
                        "multiselect": true
                      }
                    }
                    """)

                    colors = ["#FF4B4B", "#4BFF4B", "#4B4BFF", "#FFFF4B", "#FF4BFF", "#4BFFFF", "#FFA500"]
                    
                    for n in nodes:
                        c_id = n.get('community', 0) or 0
                        net.add_node(n['id'], label=n['label'], color=colors[c_id % len(colors)], title=f"Type: {n['type']}")
                    
                    for e in edges:
                        net.add_edge(e['source'], e['target'], label=e['label'], title=e['label'])
                    
                    # Affichage
                    graph_path = OUTPUT_DIR / "graph.html"
                    net.save_graph(str(graph_path))
                    
                    # Injection de script pour forcer le "Fit" après le chargement
                    with open(graph_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # On injecte l'appel network.fit() juste avant la fin du script
                    fit_script = """
                        network.on("stabilizationIterationsDone", function () {
                            network.fit();
                        });
                        setTimeout(function() { network.fit(); }, 500);
                    </script>"""
                    html_content = html_content.replace("</script>", fit_script)
                    
                    components.html(html_content, height=600, scrolling=False)
                else:
                    st.error("Erreur de récupération des données du graphe.")
            except Exception as e:
                st.error(f"Erreur lors de la visualisation : {e}")

    st.markdown("---")
    st.subheader("📊 Visualisation Louvain")
    if st.button("🚀 Lancer Louvain & Visualiser"):
        with st.spinner("Calcul en cours..."):
            resp = requests.get(f"{API_URL}/louvain").json()
            if resp['status'] == "success":
                st.success(f"✅ Terminé ! {resp['communities_count']} communautés identifiées.")
                st.balloons()
                
                # Récupérer et afficher les détails des communautés
                response = requests.get(f"{API_URL}/communities")
                if response.status_code == 200:
                    comm_resp = response.json()
                    if 'communities' in comm_resp:
                        st.write("### 🔝 Top 10 des Communautés (Clusters)")
                        for comm in comm_resp['communities']:
                            with st.expander(f"Communauté #{comm['id']} ({comm['size']} membres)"):
                                st.write("**Membres principaux :**")
                                st.write(", ".join(comm['members']))
                    else:
                        st.warning("⚠️ La route /communities est bien là, mais elle n'a pas renvoyé de données. Vérifiez votre base Neo4j.")
                else:
                    st.error(f"❌ Erreur API ({response.status_code}) : Assurez-vous d'avoir redémarré main_api.py !")
            
    st.info("💡 Les communautés permettent de regrouper les concepts scientifiques par thématiques connexes.")

# --- TAB 4: AGENTIC ---
with tab_agent:
    st.subheader("Logique de Décision Q-Learning")
    if 'agent_state' in st.session_state:
        st.write(f"**Epsilon** : {st.session_state.agent_state['epsilon']}")
        st.info("Récompenses : 🏆 +1 si information trouvée | ❌ -1 si vide.")
    else: st.warning("Rafraîchissez les stats dans la sidebar.")
