import fitz  # PyMuPDF
import os
import re
import requests
import time
from dotenv import load_dotenv

load_dotenv()

class PDFExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.hf_token = os.getenv("HF_TOKEN")
        self.translation_api_url = "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-fr-en"
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Fichier non trouvé : {pdf_path}")

    def clean_text(self, text):
        """Nettoyage approfondi selon les exigences utilisateur."""
        if not text: return ""
        
        for word in ["type", "page", "text_fr"]:
            text = re.sub(rf'\b{word}\b', '', text, flags=re.IGNORECASE)
        # 2. Supprimer les sauts de ligne multiples et espaces inutiles
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # 3. Supprimer les caractères non-standard (garde le texte et la ponctuation de base)
        text = re.sub(r'[^\x00-\x7F\u00C0-\u00FF]+', ' ', text)
        
        return text.strip()

    def should_skip_content(self, text):
        """Vérifie si la page contient des sections à supprimer."""
        text_lower = text.lower()
        keywords_to_skip = [
            "remerciement", 
            "liste complète des observateurs", 
            "bibliographie", 
            "structurer les questions autour d’un protocole de sciences participative",
            "table des matières",
            "table de matiere"
        ]
        for key in keywords_to_skip:
            if key in text_lower:
                return True
        return False

    def translate_to_english(self, text):
        """Traduit le texte via l'API Hugging Face."""
        if not self.hf_token:
            print("Warning: HF_TOKEN manquant, traduction impossible.")
            return text
            
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        
        # On découpe par morceaux de 400 mots pour l'API
        words = text.split()
        chunks = [" ".join(words[i:i + 400]) for i in range(0, len(words), 400)]
        translated_chunks = []
        
        for chunk in chunks:
            payload = {"inputs": chunk}
            try:
                # Retry loop pour charger le modèle si nécessaire
                for _ in range(3):
                    response = requests.post(self.translation_api_url, headers=headers, json=payload)
                    result = response.json()
                    
                    if isinstance(result, list) and "translation_text" in result[0]:
                        translated_chunks.append(result[0]["translation_text"])
                        break
                    elif "error" in result and "loading" in result["error"]:
                        print("Modèle en cours de chargement... attente 10s")
                        time.sleep(10)
                    else:
                        print(f"Erreur API Traduction : {result}")
                        translated_chunks.append(chunk) # Fallback sur l'original
                        break
            except Exception as e:
                print(f"Exception traduction : {e}")
                translated_chunks.append(chunk)
                
        return " ".join(translated_chunks)

    def extract_and_clean(self):
        """Pipeline complet : Extraction -> Filtrage -> Nettoyage -> Traduction."""
        doc = fitz.open(self.pdf_path)
        final_data = []

        print(f"Début du traitement de {self.pdf_path}...")

        # Commencer à la page 3 (index 2) car on supprime page 1 et 2
        for page_num in range(2, len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text") # "text" garde le texte et les tabs/espaces
            
            # Vérifier si c'est une page vide ou une section à ignorer
            if not text.strip() or self.should_skip_content(text):
                print(f"Page {page_num+1} ignorée (vide ou section filtrée).")
                continue
                
            # Nettoyage
            clean_content = self.clean_text(text)
            
            # Traduction
            print(f"Traduction de la page {page_num+1}...")
            english_content = self.translate_to_english(clean_content)
            
            final_data.append({
                "page_originale": page_num + 1,
                "content": english_content
            })
        
        doc.close()
        return final_data

if __name__ == "__main__":
    pdf_file = os.getenv("PDF_PATH", "rag_translated_fr.pdf")
    extractor = PDFExtractor(pdf_file)
    
    try:
        results = extractor.extract_and_clean()
        
        # Sauvegarde du résultat nettoyé
        import json
        output_file = os.path.join(os.getenv("DATA_DIR", "agentic_graph_rag/data"), "corpus_cleaned_en.json")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
            
        print(f"\nTraitement terminé !")
        print(f"Fichier sauvegardé : {output_file}")
        print(f"Total pages utiles : {len(results)}")
        
    except Exception as e:
        print(f"Erreur : {e}")
