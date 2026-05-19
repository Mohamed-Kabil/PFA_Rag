import time
import torch
from transformers import pipeline


from backend import config


class LocalGenerator:
    def __init__(self, model_name=None):
        model_name = model_name or config.LLM_MODEL_NAME
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"Chargement du modèle {model_name} sur {self.device}...")

        model_kwargs = {
            "low_cpu_mem_usage": True
        }

        # Configuration GPU
        if self.device == "cuda":
            model_kwargs.update({
                "device_map": "auto",
                "load_in_4bit": True,
                "bnb_4bit_compute_dtype": torch.bfloat16,
                "bnb_4bit_quant_type": "nf4",
            })

        # Configuration CPU
        else:
            model_kwargs["torch_dtype"] = torch.float32

        self.pipe = pipeline(
            "text-generation",
            model=model_name,
            device_map="auto" if self.device == "cuda" else None,
            device=-1 if self.device == "cpu" else None,
            model_kwargs=model_kwargs
        )

        print(f"Générateur {model_name} prêt sur {self.device}.")

    def is_valid_context(self, context):
        """
        Validation du contexte avant génération.
        Empêche les hallucinations dues aux mauvais résultats.
        """

        if context is None:
            return False

        if not isinstance(context, str):
            return False

        text = context.strip()

        if len(text) == 0:
            return False

        bad_patterns = [
            "Aucune entité",
            "No results",
            "not found",
            "aucun résultat"
        ]

        for pattern in bad_patterns:
            if pattern.lower() in text.lower():
                return False

        # Évite les contextes trop faibles
        if len(text.split()) < 5:
            return False

        return True

    def clean_context(self, context):
        """
        Nettoyage léger du contexte.
        """

        lines = context.splitlines()

        cleaned_lines = []

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Ignore lignes inutiles
            if len(line.split()) < 2:
                continue

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def format_prompt(self, query, context):
       return f"""
<|im_start|>system
Tu es un assistant scientifique spécialisé en RAG et en analyse écologique.

Tu dois répondre UNIQUEMENT à partir du CONTEXTE fourni.

RÈGLES OBLIGATOIRES :
- N'utilise aucune connaissance externe.
- N'invente jamais d'information.
- N'invente jamais de nombres, statistiques ou pourcentages.
- Si une information n'est pas présente dans le contexte, ne la crée pas.
- Si le contexte est insuffisant, réponds :
"Désolé, je ne trouve pas cette information dans les documents fournis."

INSTRUCTIONS DE QUALITÉ :
- Réponds directement à la question dès la première phrase.
- Synthétise les informations importantes du contexte.
- Tu peux relier plusieurs informations SI le lien est clairement suggéré dans le contexte.
- Évite les répétitions.
- Réponse concise et scientifique.
- Maximum 5 phrases.
- Utilise un ton académique clair.
- Termine toujours par une phrase de conclusion claire.
- Évite les phrases incomplètes.
- Structure la réponse de manière logique.
- Évite les répétitions ou formulations redondantes.
- Ne répète pas la question dans ta réponse.
- Va directement à l'essentiel.
- Ne mentionne pas que tu réponds à partir du contexte.
- Préserve précisément le sens scientifique du contexte.
- N'utilise pas de reformulations ambiguës ou approximatives.
- Si une relation est seulement suggérée dans le contexte, utilise des formulations prudentes comme "semble", "suggère" ou "pourrait".
- Sélectionne uniquement les informations pertinentes pour répondre à la question.
- Utilise les termes scientifiques du contexte lorsque cela est possible.
- Ne modifie pas le sens des relations causales ou statistiques présentes dans le contexte.

EXEMPLE :

QUESTION :
Quelles sont les stratégies de gestion des forêts tropicales en Amazonie ?

CONTEXTE :
Le document parle uniquement des écosystèmes alpins.

RÉPONSE :
"Désolé, je ne trouve pas cette information dans les documents fournis."
<|im_end|>

<|im_start|>user
CONTEXTE :
{context}

QUESTION :
{query}
<|im_end|>

<|im_start|>assistant
"""

    def generate_answer(self, query, context):
        """
        Génération sécurisée pour RAG.
        """

        start_time = time.time()

        # Validation du contexte AVANT appel LLM
        if not self.is_valid_context(context):
            return "Désolé, je ne trouve pas cette information dans les documents fournis."

        # Nettoyage du contexte
        context = self.clean_context(context)

        # Debug contexte
        print("\n=== CONTEXTE REÇU PAR LE LLM ===")
        print(context[:400])
        print("=================================\n")

        prompt = self.format_prompt(query, context)

        response = self.pipe(
            prompt,
            max_new_tokens=300,
            do_sample=False,
            temperature=0.0,
            top_p=1.0,
            repetition_penalty=1.1,
            truncation=True,
            eos_token_id=self.pipe.tokenizer.eos_token_id,
            pad_token_id=self.pipe.tokenizer.eos_token_id,
            return_full_text=False
        )

        answer = response[0]["generated_text"].strip()

        # Cut at the last sentence-ending punctuation so the answer never stops mid-sentence
        last_stop = max(answer.rfind('.'), answer.rfind('!'), answer.rfind('?'))
        if last_stop > len(answer) // 3:
            answer = answer[:last_stop + 1].strip()

        elapsed = round(time.time() - start_time, 2)

        print(f"\nTemps de génération : {elapsed}s")

        return answer


if __name__ == "__main__":
    # Test rapide
    gen = LocalGenerator()

    test_context = """
La biodiversité alpine est menacée par le réchauffement climatique.
Les températures élevées modifient les habitats naturels.
Certaines espèces animales disparaissent progressivement.
"""

    test_query = "Qu'est-ce qui menace la biodiversité alpine ?"

    answer = gen.generate_answer(test_query, test_context)

    print("\n=== RÉPONSE ===")
    print(answer)