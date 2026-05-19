# Debug Report: Hallucination Issues in Chat RAG

## 🔍 Identified Problems

1.  **Model Power & Reliability:**
    *   The model used is `Qwen2.5-1.5B-Instruct`. While efficient, 1.5B parameters are often insufficient for complex RAG tasks. It is highly prone to:
        *   **Internal Knowledge Leakage:** Answering from its training data even when told to use the provided context.
        *   **False Refusals:** Giving generic refusal messages (e.g., "policy violations") for harmless questions like "Who is the president of France?" when it can't find a good answer in the context.
        *   **Nonsensical Additions:** Adding irrelevant phrases (e.g., "activité physique et mentale de l'espèce" for ecological niche).

2.  **Prompt Engineering Weakness:**
    *   The current prompt is: `Tu es un assistant scientifique expert. Réponds UNIQUEMENT avec le contexte fourni. Max 4 phrases.`
    *   It lacks a **"Fallback Instruction"**: It doesn't tell the model what to do if the context is missing or irrelevant. This often forces the model to "guess" or hallucinate.
    *   The format is basic and might not be leveraging the Instruct capabilities of Qwen2.5 optimally.

3.  **Handling of "Empty" Retrieval:**
    *   When the Graph retriever finds nothing, it returns: `"Aucune entité sémantique trouvée dans le graphe."`
    *   This string is passed to the LLM as the *only* context. The LLM then sees a context that explicitly says "nothing found" but is still asked to answer the question, leading it to hallucinate.

4.  **Agentic Routing False Positives:**
    *   The `RoutingAgent` gives a positive reward (`1.0`) as long as `results` is truthy.
    *   Since "Aucune entité..." is a non-empty string, the agent thinks the Graph search was successful, even if it returned no useful information. This reinforces bad routing decisions.

5.  **Sampling Configuration:**
    *   `do_sample=True` with `temperature=0.1` is used. For a very small model, even a low temperature can lead to instability. `do_sample=False` (greedy decoding) is usually safer for RAG to ensure grounding.

## 💡 Suggestions for Fixes

### 1. Improve the Prompt (Immediate Fix)
Refine the system prompt to include a strict fallback and better structure.
```python
# Suggested Prompt
f"<|im_start|>system\n" \
f"Tu es un assistant scientifique expert. Ton rôle est de répondre aux questions en utilisant EXCLUSIVEMENT le contexte fourni.\n" \
f"RÈGLES STRICTES :\n" \
f"1. Si la réponse n'est pas dans le contexte, réponds exactement : 'Désolé, je ne trouve pas cette information dans les documents fournis.'\n" \
f"2. Ne fais jamais appel à tes connaissances personnelles.\n" \
f"3. Reste concis (max 4 phrases).\n" \
f"<|im_end|>\n"
```

### 2. Robust Retrieval Checks
Modify `main_api.py` and `agent.py` to check if retrieval actually returned *meaningful* content before calling the generator.
*   If context is empty or contains "no results" messages, return a standard "Information not found" response instead of calling the LLM.

### 3. Adjust Generator Parameters
*   Set `do_sample=False` for more deterministic and grounded output.
*   Check for potential `max_length` conflicts in the pipeline.

### 4. Enhance Agent Reward Logic
*   The reward should be based on whether the context actually contains keywords from the query or if the LLM was able to produce a grounded answer (requires a more complex reward signal, e.g., a "Faithfulness" check).

### 5. Consider a Larger Model
*   If resources permit, upgrading to `Qwen2.5-7B-Instruct` would significantly reduce hallucinations and improve synthesis quality.

### 6. Clean up Graph Context
*   The `GraphRetriever` output should be more structured or simply return `None` if no entities are found, allowing the API to handle it gracefully.
