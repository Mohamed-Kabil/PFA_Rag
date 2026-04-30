import os
import json
import numpy as np
import random
try:
    from backend.retrieval import HybridRetriever
    from backend.graph_retrieval import GraphRetriever
except ImportError:
    from retrieval import HybridRetriever
    from graph_retrieval import GraphRetriever

class RoutingAgent:
    def __init__(self, data_dir, q_table_path="q_table.json"):
        self.data_dir = data_dir
        self.q_table_path = os.path.join(data_dir, q_table_path)
        self.actions = [0, 1, 2] # 0: Vector, 1: Graph, 2: Hybrid
        self.epsilon = 0.1
        self.alpha = 0.1
        self.gamma = 0.9
        
        # Initialisation des retrievers
        self.vector_retriever = HybridRetriever(data_dir)
        self.graph_retriever = GraphRetriever()
        
        # Chargement/Initialisation de la Q-table
        self.q_table = self.load_q_table()

    def load_q_table(self):
        if os.path.exists(self.q_table_path):
            with open(self.q_table_path, 'r') as f:
                return json.load(f)
        return {}

    def save_q_table(self):
        with open(self.q_table_path, 'w') as f:
            json.dump(self.q_table, f)

    def get_state(self, query):
        """Définit l'état basé sur les caractéristiques de la requête."""
        # Caractéristiques simples : présence d'entités, longueur, mots techniques
        words = query.lower().split()
        has_entities = len([w for w in words if len(w) > 6]) > 1
        is_long = len(words) > 10
        return f"{int(has_entities)}_{int(is_long)}"

    def choose_action(self, state):
        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(self.actions)
            
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(self.actions)
        return np.argmax(self.q_table[state])

    def execute_action(self, action, query):
        if action == 0: # Vector
            return self.vector_retriever.hybrid_search(query), "Vector"
        elif action == 1: # Graph
            return self.graph_retriever.retrieve_graph_context(query), "Graph"
        else: # Hybrid
            v_res = self.vector_retriever.hybrid_search(query)
            g_res = self.graph_retriever.retrieve_graph_context(query)
            return {"vector": v_res, "graph": g_res}, "Hybrid"

    def update_q_table(self, state, action, reward, next_state):
        if next_state not in self.q_table:
            self.q_table[next_state] = [0.0] * len(self.actions)
            
        old_value = self.q_table[state][action]
        next_max = max(self.q_table[next_state])
        
        # Formule Q-Learning
        new_value = (1 - self.alpha) * old_value + self.alpha * (reward + self.gamma * next_max)
        self.q_table[state][action] = new_value
        self.save_q_table()

    def run_query(self, query):
        state = self.get_state(query)
        action = self.choose_action(state)
        results, action_name = self.execute_action(action, query)
        
        # Dans un système réel, le reward viendrait de l'utilisateur ou d'un juge LLM
        # Ici on simule un reward basé sur la présence de résultats
        reward = 1.0 if results else -0.5
        
        # Mise à jour simplifiée (état suivant identique pour cet exemple)
        self.update_q_table(state, action, reward, state)
        
        return results, action_name

if __name__ == "__main__":
    agent = RoutingAgent("agentic_graph_rag/data")
    
    queries = [
        "Quelle est l'influence du pâturage sur la biodiversité alpine ?",
        "Comment les espèces survivent au changement climatique ?",
        "Hutchinson et la niche écologique"
    ]
    
    for q in queries:
        print(f"\n--- Question: {q} ---")
        res, act = agent.run_query(q)
        print(f"Agent a choisi: {act}")
