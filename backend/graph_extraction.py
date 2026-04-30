import os
import json
import torch
import re
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
from dotenv import load_dotenv

# Désactiver les avertissements de symlinks sur Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

load_dotenv()

class GraphExtractor:
    def __init__(self):
        # Détection du matériel
        self.device_idx = 0 if torch.cuda.is_available() else -1
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🖥️ Expert Graph Mode : {self.device.upper()}")

        # Patterns de bruit (emails, affiliations, métadonnées brutes)
        self.noise_patterns = [
            r"[\w\.-]+@[\w\.-]+\.\w+", # Emails
            r"University", r"Institute", r"Department", r"Laboratoire", # Affiliations
            r"ID[:\s]*[\d_]+", r"Section[:\s]*", r"Chapter[:\s]*", r"Content[:\s]*",
            r"^P\d+_C\d+$", r"^id$", r"^page \d+$", r"\[\d+\]" # Métadonnées et citations
        ]
        
        print("⏳ Chargement des modèles spécialisés...")
        self.ner_pipe = pipeline(
            "ner", 
            model="Jean-Baptiste/camembert-ner", 
            aggregation_strategy="simple",
            device=self.device_idx
        )
        
        self.rebel_tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
        self.rebel_model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")
        if self.device == "cuda":
            self.rebel_model = self.rebel_model.to("cuda")
            
        print("✅ Modèles prêts pour extraction haute-fidélité.")

    def is_valid_node(self, name):
        """Filtre strict pour n'autoriser que des mots uniques ou termes très courts"""
        name = name.strip()
        
        # 1. Pas de bruit (emails, IDs, etc.)
        for pattern in self.noise_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False
        
        # 2. Pas de mots tronqués ou trop courts (min 2 caractères)
        if len(name) < 2 or name.isdigit() or name.endswith("...") or name.endswith("-"):
            return False
            
        # 3. Règle atomique : 1 à 2 mots maximum
        words = name.split()
        if len(words) > 2:
            return False
            
        # 4. Pas de verbes seuls ou mots de liaison
        stop_concepts = ["C'est", "Il y a", "The", "And", "Est un", "Est le", "A été"]
        if any(name.startswith(s) for s in stop_concepts):
            return False
            
        return True

    def normalize_name(self, name):
        """Nettoyage sémantique et suppression des articles"""
        name = re.sub(r"<.*?>", "", name) # Nettoyage tags REBEL
        
        # Supprimer les articles au début (Le, La, Les, L', Un, Une, Des)
        name = re.sub(r"^(le |la |les |l'|un |une |des )", "", name, flags=re.IGNORECASE)
        
        name = " ".join(name.split()) # Espaces
        # Capitalisation propre des concepts
        return name.capitalize()

    def map_node_type(self, raw_type, name):
        """Mappe les types vers concept | entity | document"""
        raw_type = raw_type.upper()
        if "PER" in raw_type or "ORG" in raw_type or "LOC" in raw_type:
            return "entity"
        if "P" in name and "_" in name and "C" in name: # Cas résiduel de doc ID
            return "document"
        return "concept"

    def parse_rebel_output(self, text):
        triplets = []
        relation, subject, object_ = '', '', ''
        current = 'x'
        for token in text.replace("<s>", "").replace("</s>", "").split():
            if token == "<triplet>":
                current = 't'
                if relation:
                    triplets.append({'head': subject.strip(), 'type': relation.strip(), 'tail': object_.strip()})
                    relation, subject, object_ = '', '', ''
                subject = ''
            elif token == "<subj>":
                current = 's'
                if relation:
                    triplets.append({'head': subject.strip(), 'type': relation.strip(), 'tail': object_.strip()})
                    relation, subject, object_ = '', '', ''
                object_ = ''
            elif token == "<obj>":
                current = 'o'
                relation = ''
            else:
                if current == 't': subject += ' ' + token
                elif current == 's': object_ += ' ' + token
                elif current == 'o': relation += ' ' + token
        if relation:
            triplets.append({'head': subject.strip(), 'type': relation.strip(), 'tail': object_.strip()})
        return triplets

    def extract_relations_local(self, text):
        # Pré-nettoyage du texte pour REBEL
        clean_text = re.sub(r"ID:.*?Content:", "", text, flags=re.DOTALL).strip()
        
        inputs = self.rebel_tokenizer(clean_text, return_tensors="pt", truncation=True, max_length=512)
        if self.device == "cuda":
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
        gen_tokens = self.rebel_model.generate(
            **inputs,
            max_length=256,
            num_beams=3,
            length_penalty=0,
            early_stopping=True
        )
        
        decoded = self.rebel_tokenizer.batch_decode(gen_tokens, skip_special_tokens=False)[0]
        return self.parse_rebel_output(decoded)

    def clean_graph(self, raw_nodes, raw_edges):
        """Post-traitement expert"""
        clean_nodes_map = {}
        
        for node in raw_nodes:
            raw_name = node["name"]
            if not self.is_valid_node(raw_name):
                continue
                
            name = self.normalize_name(raw_name)
            node_key = name.lower()
            
            if node_key not in clean_nodes_map:
                node_type = self.map_node_type(node["type"], name)
                clean_nodes_map[node_key] = {
                    "name": name,
                    "type": node_type,
                    "description": f"Concept scientifique: {name}." if node_type == "concept" else f"Entité identifiée: {name}.",
                    "chunks": {node["chunk_id"]} if "chunk_id" in node else set()
                }
            elif "chunk_id" in node:
                clean_nodes_map[node_key]["chunks"].add(node["chunk_id"])
        
        for node in clean_nodes_map.values():
            node["chunks"] = list(node["chunks"])
        
        clean_edges = []
        seen_edges = set()
        
        # Mappage des relations génériques vers sémantiques
        rel_mapping = {
            "HAS PART": "is_part_of",
            "PART OF": "is_part_of",
            "LOCATION": "located_at",
            "SUBCLASS OF": "is_a",
            "INFLUENCED BY": "depends_on",
            "CAUSES": "affects"
        }
        
        for edge in raw_edges:
            s_raw, t_raw = edge["source"], edge["target"]
            if not (self.is_valid_node(s_raw) and self.is_valid_node(t_raw)):
                continue
                
            s_name = self.normalize_name(s_raw)
            t_name = self.normalize_name(t_raw)
            
            if s_name.lower() == t_name.lower():
                continue
            
            rel = edge["type"].upper()
            rel = rel_mapping.get(rel, rel.lower().replace(" ", "_"))
            
            edge_key = f"{s_name.lower()}|{rel}|{t_name.lower()}"
            if edge_key not in seen_edges:
                clean_edges.append({
                    "source": s_name,
                    "target": t_name,
                    "relation": rel,
                    "chunk_id": edge.get("chunk_id")
                })
                seen_edges.add(edge_key)
                
        return list(clean_nodes_map.values()), clean_edges

    def run(self, chunks_path, output_path, limit_chunks=None):
        if not os.path.exists(chunks_path):
            print(f"❌ Erreur : {chunks_path} introuvable.")
            return

        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        all_nodes = []
        all_edges = []

        n_chunks = limit_chunks if limit_chunks is not None else len(chunks)
        print(f"🚀 Extraction Expert sur {n_chunks} chunks...")
        
        for i, chunk in enumerate(chunks[:n_chunks]):
            text = chunk["text"]
            cid = chunk["id"]
            
            # NER
            try:
                entities = self.ner_pipe(text)
                for ent in entities:
                    all_nodes.append({"name": ent["word"], "type": ent["entity_group"], "chunk_id": cid})
            except Exception as e: pass
            
            # REBEL
            try:
                triplets = self.extract_relations_local(text)
                for t in triplets:
                    all_nodes.append({"name": t['head'], "type": "CONCEPT", "chunk_id": cid})
                    all_nodes.append({"name": t['tail'], "type": "CONCEPT", "chunk_id": cid})
                    all_edges.append({"source": t['head'], "target": t['tail'], "relation": t['type'], "chunk_id": cid})
            except Exception as e: pass
            
            if (i + 1) % 10 == 0:
                print(f"  🧠 Analyse en cours : {i+1}/{n_chunks} chunks...")

        final_nodes, final_edges = self.clean_graph(all_nodes, [
            {"source": e["source"], "target": e["target"], "type": e["relation"], "chunk_id": e["chunk_id"]} for e in all_edges
        ])
        
        output_data = {
            "nodes": final_nodes,
            "edges": final_edges
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        
        print(f"\n✨ Graphe Expert terminé ! {len(final_nodes)} concepts atomiques et {len(final_edges)} relations sémantiques.")

if __name__ == "__main__":
    extractor = GraphExtractor()
    extractor.run(
        "agentic_graph_rag/data/corpus_chunks.json", 
        "agentic_graph_rag/data/knowledge_graph.json",
        limit_chunks=None
    )

