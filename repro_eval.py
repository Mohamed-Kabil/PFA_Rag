import os
import sys
import json
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.agent import RoutingAgent
from backend.generation import LocalGenerator

def evaluate_system():
    DATA_DIR = "data"
    agent = RoutingAgent(DATA_DIR)
    generator = LocalGenerator()

    test_categories = {
        "A) DIRECT FACT QUESTIONS": [
            "Quels sont les services écosystémiques mentionnés dans le document ?",
            "Quel pourcentage de mammifères et d'oiseaux a disparu au cours des deux derniers siècles selon Ceballos et al. (2015) ?"
        ],
        "B) IMPOSSIBLE QUESTIONS": [
            "Quel est le régime alimentaire précis de l'ours polaire décrit dans le texte ?",
            "Quelles sont les recommandations spécifiques pour la gestion des forêts tropicales en Amazonie ?"
        ],
        "C) PARTIAL CONTEXT QUESTIONS": [
            "Comment l'importation de ruches aux États-Unis a-t-elle évolué au cours des dix dernières années ?",
            "Quelles sont les conclusions de l'étude de Morgera (2018) citée dans le texte ?"
        ],
        "D) MULTI-CHUNK QUESTIONS": [
            "Expliquez le lien entre l'anthropocène, les changements globaux et la disparition des espèces en vous basant sur le texte."
        ]
    }

    results_report = []

    for category, queries in test_categories.items():
        print(f"\n{'='*20} {category} {'='*20}")
        for query in queries:
            print(f"\nProcessing: {query}")
            
            start_time = time.time()
            results, action_name = agent.run_query(query)
            retrieval_time = round(time.time() - start_time, 2)

            context = ""
            chunks_summary = []
            if action_name == "Vector":
                context = "\n".join([r['text'] for r in results])
                chunks_summary = [r['text'][:100] + "..." for r in results]
            elif action_name == "Graph":
                context = results
                chunks_summary = [results[:200] + "..."]
            else: # Hybrid
                v_text = "\n".join([r['text'] for r in results['vector']])
                context = f"INFO VECTEUR:\n{v_text}\n\nINFO GRAPHE:\n{results['graph']}"
                chunks_summary = [r['text'][:100] + "..." for r in results['vector']]
                chunks_summary.append("GRAPH: " + results['graph'][:100] + "...")

            answer = generator.generate_answer(query, context)
            
            results_report.append({
                "category": category,
                "question": query,
                "action": action_name,
                "chunks_summary": chunks_summary,
                "answer": answer,
                "retrieval_time": retrieval_time
            })

    # Save results to a file for analysis
    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump(results_report, f, indent=4, ensure_ascii=False)

    print("\nEvaluation complete. Results saved to eval_results.json")

if __name__ == "__main__":
    evaluate_system()
