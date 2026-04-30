import streamlit as st
import requests
import pandas as pd
import time
import os
from pyvis.network import Network
import streamlit.components.v1 as components

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
DATA_DIR = "agentic_graph_rag/data"

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
    st.subheader("Visualisation PCA 2D et Retrieval")
    pca_path = os.path.join(DATA_DIR, "pca_visualization.png")
    if os.path.exists(pca_path): st.image(pca_path, use_container_width=True)
    
    v_query = st.text_input("Recherche sémantique :", key="v_search")
    if st.button("🔍 Rechercher Chunks"):
        resp = requests.get(f"{API_URL}/vectorial", params={"q": v_query}).json()
        for res in resp['results']: st.markdown(f"<div class='chat-bubble'><b>Score: {res['score']:.4f}</b><br>{res['text']}</div>", unsafe_allow_html=True)

# --- TAB 3: GRAPH ---
with tab_graph:
    st.subheader("Analyse du Graphe de Connaissances")
    g_query = st.text_input("Explorer un concept :", key="g_search")
    if st.button("🕸️ Analyser le Graphe"):
        resp = requests.get(f"{API_URL}/graph", params={"q": g_query}).json()
        col_m1, col_m2 = st.columns(2)
        with col_m1: st.metric("Densité locale", f"{resp['metrics']['density']:.2f}")
        with col_m2: st.metric("Nœuds trouvés", len(resp['entities']))
        st.bar_chart(pd.DataFrame(list(resp['metrics']['centrality'].items()), columns=['Concept', 'Centralité']).set_index('Concept'))
        
        st.write("### 🧬 Liste des Entités et Communautés")
        for ent in resp['entities']:
            st.markdown(f"**{ent['entity']}** (Communauté: {ent.get('community', 'N/A')})")
            for r in ent['relations']:
                if r['rel']: st.write(f" └─ [{r['rel']}] -> {r['target']}")

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
                    
                    # Création du graphe Pyvis
                    net = Network(height="600px", width="100%", bgcolor="#0e1117", font_color="white")
                    colors = ["#FF4B4B", "#4BFF4B", "#4B4BFF", "#FFFF4B", "#FF4BFF", "#4BFFFF", "#FFA500"]
                    
                    for n in nodes:
                        c_id = n.get('community', 0) or 0
                        net.add_node(n['id'], label=n['label'], color=colors[c_id % len(colors)], title=f"Type: {n['type']}")
                    
                    for e in edges:
                        net.add_edge(e['source'], e['target'], title=e['label'])
                    
                    # Affichage
                    net.save_graph("graph.html")
                    with open("graph.html", 'r', encoding='utf-8') as f:
                        components.html(f.read(), height=600)
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
