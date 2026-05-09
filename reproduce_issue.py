
import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from backend.agent import RoutingAgent
from backend.generation import LocalGenerator

def debug_query(question):
    print(f"\n--- DEBUGGING QUERY: {question} ---")
    
    data_dir = "data"
    agent = RoutingAgent(data_dir)
    # Force use of a specific action for testing if needed, or let it choose
    # For now, let's see what it chooses
    
    results, action_name = agent.run_query(question)
    print(f"Action chosen by agent: {action_name}")
    
    context = ""
    if action_name == "Vector":
        context = "\n".join([r['text'] for r in results])
    elif action_name == "Graph":
        context = results 
    else: # Hybrid
        v_text = "\n".join([r['text'] for r in results['vector']])
        context = f"VECTEUR:\n{v_text}\n\nGRAPHE:\n{results['graph']}"
    
    print("\n[CONTEXT SENT TO LLM]")
    print(context if context else "[EMPTY CONTEXT]")
    print("-" * 20)
    
    # We might not want to load the whole model if it's too big for this environment
    # But let's try.
    try:
        generator = LocalGenerator()
        answer = generator.generate_answer(question, context)
        print("\n[LLM ANSWER]")
        print(answer)
    except Exception as e:
        print(f"Error loading generator or generating answer: {e}")

if __name__ == "__main__":
    # Example questions that might trigger hallucinations if retrieval is bad
    test_queries = [
        "Quels sont les impacts du changement climatique sur les Alpes ?",
        "Explique le concept de niche écologique selon Hutchinson",
        "Qui est le président de la France ?" # This should NOT be answered if it's not in the context
    ]
    
    for q in test_queries:
        debug_query(q)
