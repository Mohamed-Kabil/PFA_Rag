import torch
from transformers import pipeline
import os

class LocalGenerator:
    def __init__(self, model_name="Qwen/Qwen2-0.5B-Instruct"):
        print(f"⏳ Chargement du modèle ultra-rapide ({model_name})...")
        print("🚀 Optimisé pour la vitesse sur CPU (Zéro API nécessaire).")
        
        self.pipe = pipeline(
            "text-generation",
            model=model_name,
            torch_dtype="auto",
            device_map="auto"
        )
        print("✅ Générateur local prêt.")

    def format_prompt(self, query, context):
        """Format de prompt pour Qwen2."""
        return f"<|im_start|>system\nTu es un assistant scientifique expert. " \
               f"Réponds UNIQUEMENT avec le contexte fourni. Max 4 phrases.<|im_end|>\n" \
               f"<|im_start|>user\nCONTEXTE :\n{context}\n\nQUESTION :\n{query}<|im_end|>\n" \
               f"<|im_start|>assistant\n"

    def generate_answer(self, query, context):
        prompt = self.format_prompt(query, context)
        
        response = self.pipe(
            prompt,
            max_new_tokens=300,
            temperature=0.1,
            do_sample=True,
            pad_token_id=151643, # Token de fin spécifique à Qwen2
            return_full_text=False
        )
        
        answer = response[0]['generated_text'].strip()
        return answer

if __name__ == "__main__":
    # Test rapide
    gen = LocalGenerator()
    test_context = "La biodiversité alpine est menacée par le réchauffement climatique."
    test_query = "Qu'est-ce qui menace la biodiversité ?"
    print(f"\nRéponse : {gen.generate_answer(test_query, test_context)}")
