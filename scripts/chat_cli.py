import os
from pathlib import Path

from backend.agent import RoutingAgent
from backend.generation import LocalGenerator

def main():
    print("\n" + "="*50)
    print("🌟 AGENTIC VECTORIAL GRAPH RAG - CHAT 🌟")
    print("="*50 + "\n")

    # Initialisation
    DATA_DIR = "data"
    agent = RoutingAgent(DATA_DIR)
    generator = LocalGenerator()

    print("\n✅ Système prêt ! Posez vos questions (ou 'exit' pour quitter).")

    while True:
        query = input("\n👤 Vous : ")
        if query.lower() in ['exit', 'quit', 'quitter']:
            break

        print("🤖 L'agent analyse et recherche...")
        
        # 1. Recherche via l'Agent (Vecteur, Graphe ou Hybride)
        results, action_name = agent.run_query(query)
        
        # 2. Préparation du contexte pour le LLM
        context = ""
        if action_name == "Vector":
            context = "\n".join([r['text'] for r in results])
        elif action_name == "Graph":
            context = results # C'est déjà une chaîne formatée
        else: # Hybrid
            v_text = "\n".join([r['text'] for r in results['vector']])
            context = f"INFO VECTEUR:\n{v_text}\n\nINFO GRAPHE:\n{results['graph']}"

        # 3. Génération de la réponse
        print(f"✍️ Génération de la réponse ({action_name})...")
        answer = generator.generate_answer(query, context)

        print("\n" + "-"*30)
        print(f"🤖 RÉPONSE :")
        print(answer)
        print("-"*30)

import traceback

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye !")
    except Exception:
        print("\n❌ UNE ERREUR EST SURVENUE :")
        traceback.print_exc()
