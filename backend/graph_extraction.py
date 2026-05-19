import json
import os
import re
import unicodedata
from itertools import combinations
from pathlib import Path

import torch
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

# Disable symlink warnings on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from backend import config


class GraphExtractor:
    def __init__(self):
        self.device_idx = 0 if torch.cuda.is_available() else -1
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"Expert Graph Mode : {self.device.upper()}")

        self.noise_patterns = [
            r"[\w\.-]+@[\w\.-]+\.\w+",
            r"University",
            r"Institute",
            r"Department",
            r"Laboratoire",
            r"ID[:\s]*[\d_]+",
            r"Section[:\s]*",
            r"Chapter[:\s]*",
            r"Content[:\s]*",
            r"^P\d+_C\d+$",
            r"^id$",
            r"^page \d+$",
            r"\[\d+\]",
        ]

        self.bad_terms = {
            "avons",
            "juin",
            "juillet",
            "aout",
            "septembre",
            "octobre",
            "novembre",
            "decembre",
            "analyse",
            "resultat",
            "resultats",
            "donnee",
            "donnees",
            "etude",
            "tableau",
            "figure",
            "section",
            "chapitre",
            "contenu",
            "espece",
            "especes",
            "important",
            "possible",
            "present",
            "methode",
            "cas",
            "effet",
            "climatique",
            "temporel",
            "general",
            "et al",
            "fig",
            "annee",
            "annees",
            "exemple",
            "cependant",
            "egalement",
            "notamment",
            "voir",
            "rapport",
            "nombre",
            "moyenne",
            "fonction",
            "partir",
            "chaque",
            "deux",
            "certaines",
            "tres",
            "differents",
            "differentes",
            "fortement",
            "attendions",
            "augmente",
            "augmentent",
            "concernant",
            "deplacer",
            "dernieres",
            "ensembles",
            "etait",
            "etant",
            "forte",
            "groupe",
            "lay",
            "lineaire",
            "maniere",
            "multi",
            "negative",
            "pers",
            "place",
            "premieres",
            "prediction",
            "predictions",
            "pseudo",
            "realisee",
            "realisees",
            "semble",
            "similaire",
            "souvent",
            "toute",
            "uniquement",
            "utilisant",
        }

        self.stop_words = {
            "afin",
            "ainsi",
            "alors",
            "apres",
            "assez",
            "aucun",
            "aussi",
            "autre",
            "autres",
            "avant",
            "avec",
            "avoir",
            "cela",
            "celle",
            "celles",
            "celui",
            "cependant",
            "ces",
            "cet",
            "cette",
            "chaque",
            "chez",
            "comme",
            "contre",
            "dans",
            "depuis",
            "dont",
            "donc",
            "elle",
            "elles",
            "entre",
            "etre",
            "fait",
            "font",
            "leur",
            "leurs",
            "lors",
            "lorsque",
            "mais",
            "meme",
            "memes",
            "moins",
            "notamment",
            "nous",
            "notre",
            "parce",
            "pendant",
            "peut",
            "peuvent",
            "plus",
            "pour",
            "quand",
            "sans",
            "selon",
            "sous",
            "sont",
            "tous",
            "tout",
            "tres",
            "vers",
            "voir",
            "vous",
            "avons",
        }

        self.domain_terms = {
            "abondance",
            "accenteur",
            "adaptation",
            "adaptatif",
            "altitude",
            "alpin",
            "alpine",
            "alpines",
            "alpins",
            "animal",
            "animaux",
            "biodiversite",
            "biosphere",
            "bouquetin",
            "chamois",
            "changement",
            "changements",
            "chardonneret",
            "climat",
            "communautes",
            "communaute",
            "competition",
            "contrainte",
            "contraintes",
            "correlation",
            "couverture",
            "crave",
            "croissance",
            "distribution",
            "dunnock",
            "eau",
            "eaux",
            "echantillonnage",
            "ecologie",
            "ecologique",
            "ecosysteme",
            "ecosystemes",
            "enneigement",
            "environnement",
            "environnementale",
            "environnementales",
            "espece",
            "exposition",
            "femelle",
            "femelles",
            "fertilite",
            "foret",
            "froid",
            "gradient",
            "habitat",
            "habitats",
            "herbivore",
            "herbivores",
            "hiver",
            "insecte",
            "insectes",
            "interaction",
            "interactions",
            "latitude",
            "linotte",
            "longitude",
            "mammifere",
            "mammiferes",
            "migration",
            "milieu",
            "milieux",
            "modele",
            "modeles",
            "montagne",
            "mortalite",
            "niche",
            "ndvi",
            "neige",
            "neiges",
            "oiseau",
            "oiseaux",
            "ongule",
            "ongules",
            "pelouse",
            "pelouses",
            "phenologie",
            "pipit",
            "plaine",
            "plantes",
            "pollinisation",
            "population",
            "populations",
            "prairie",
            "prairies",
            "precipitation",
            "precipitations",
            "predation",
            "probabilite",
            "printemps",
            "rayonnement",
            "regime",
            "repartition",
            "reproduction",
            "ressource",
            "ressources",
            "richesse",
            "rocheuse",
            "saison",
            "site",
            "sites",
            "sol",
            "solaire",
            "sols",
            "sommets",
            "structure",
            "survie",
            "temperature",
            "temperatures",
            "traquet",
            "transect",
            "transects",
            "variable",
            "variables",
            "vegetation",
            "zone",
            "zones",
        }

        self.allowed_relations = {
            "affects",
            "causes",
            "depends_on",
            "influences",
            "associated_with",
            "correlates_with",
            "related_to",
            "interacts_with",
            "located_at",
        }

        self.relation_weights = {
            "causes": 3.0,
            "affects": 3.0,
            "influences": 2.5,
            "depends_on": 2.5,
            "associated_with": 2.0,
            "correlates_with": 2.0,
            "related_to": 1.5,
            "interacts_with": 1.5,
            "located_at": 1.0,
        }

        self.relation_aliases = {
            "affect": "affects",
            "affects": "affects",
            "cause": "causes",
            "causes": "causes",
            "influence": "influences",
            "influences": "influences",
            "influenced_by": "depends_on",
            "depend_on": "depends_on",
            "depends_on": "depends_on",
            "depend": "depends_on",
            "associated_with": "associated_with",
            "associate_with": "associated_with",
            "correlated_with": "correlates_with",
            "correlates_with": "correlates_with",
            "correlate_with": "correlates_with",
            "located_at": "located_at",
            "location": "located_at",
            "located_in": "located_at",
            "located_in_the_administrative_territorial_entity": "located_at",
            "related_to": "related_to",
            "relates_to": "related_to",
            "different_from": "related_to",
            "opposite_of": "related_to",
            "main_subject": "related_to",
            "use": "related_to",
            "uses": "related_to",
            "studies": "related_to",
            "studied_by": "related_to",
            "depicts": "related_to",
            "interacts_with": "interacts_with",
            "interaction_with": "interacts_with",
        }

        self.rejected_relations = {
            "author",
            "continent",
            "country",
            "facet_of",
            "field_of_work",
            "followed_by",
            "follows",
            "instance_of",
            "is_a",
            "is_part_of",
            "parent_taxon",
            "part_of",
            "point_in_time",
            "shares_border_with",
            "spouse",
            "student",
        }

        self.citation_patterns = [
            r"\bet al\.?\b",
            r"\b[A-Z][a-z]+(?:\s+(?:and|&)\s+[A-Z][a-z]+)+\b",
            r"\b[A-Z][a-z]+(?:\s+et\s+al\.?)?\s*\(\d{4}[a-z]?\)",
            r"\b[A-Z][a-z]+(?:\s+and\s+[A-Z][a-z]+)?\s+\d{4}\b",
        ]

        self.metadata_patterns = [
            r"^(tableau|figure|fig|chapitre|section)\s*\d+[a-z]?$",
            r"^\d{4}$",
            r"^(janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)$",
            r"^[pc]?\d+([_\-][pc]?\d+)*$",
        ]

        print("Chargement des modeles specialises...")

        self.ner_pipe = pipeline(
            "ner",
            model=config.NER_MODEL_NAME,
            aggregation_strategy="simple",
            device=self.device_idx,
        )

        self.rebel_tokenizer = AutoTokenizer.from_pretrained(
            config.REBEL_MODEL_NAME
        )
        self.rebel_model = AutoModelForSeq2SeqLM.from_pretrained(
            config.REBEL_MODEL_NAME
        )

        if self.device == "cuda":
            self.rebel_model = self.rebel_model.to("cuda")

        print("Modeles prets pour extraction haute-fidelite.")

    def preprocess_for_tfidf(self, text):
        text = re.sub(
            r"\b[A-Z][A-Za-zÀ-ÿ-]+(?:\s+et\s+al\.?)?\s*\(\d{4}[a-z]?\)",
            " ",
            text,
        )
        text = re.sub(r"\([^)]*\d{4}[^)]*\)", " ", text)
        return text

    def fold_text(self, text):
        folded = unicodedata.normalize("NFKD", str(text))
        folded = folded.encode("ascii", "ignore").decode("ascii")
        return folded.lower().strip()

    def is_valid_node(self, name):
        if not name:
            return False

        name = str(name).strip()
        folded = self.fold_text(name)

        if not folded:
            return False

        if any(token in name for token in ("Ã", "â", "�")):
            return False

        if folded in self.bad_terms:
            return False

        if folded in self.stop_words:
            return False

        for pattern in self.noise_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False

        for pattern in self.citation_patterns:
            if re.search(pattern, name):
                return False

        for pattern in self.metadata_patterns:
            if re.search(pattern, folded):
                return False

        if len(name) < 2 or len(name) > 120:
            return False

        if name.isdigit() or re.search(r"\d", name):
            return False

        if name.endswith("-"):
            return False

        words = name.split()
        if len(words) > 4:
            return False

        folded_words = folded.split()
        if any(word in self.stop_words for word in folded_words):
            return False

        if len(words) == 1 and len(folded) < 5:
            return False

        if any(len(word) == 1 for word in words if word.isalpha()):
            return False

        if not re.search(r"[A-Za-zÀ-ÿ]", name):
            return False

        stop_concepts = [
            "C'est",
            "Il y a",
            "The",
            "And",
            "Est un",
            "Est le",
            "A ete",
        ]
        if any(name.startswith(prefix) for prefix in stop_concepts):
            return False

        if folded.endswith(("ique", "iques")) and len(words) == 1:
            return False

        return True

    def build_semantic_concepts(self, chunks, max_features=650, top_per_chunk=7):
        texts = [self.preprocess_for_tfidf(chunk["text"]) for chunk in chunks]
        vectorizer = TfidfVectorizer(
            lowercase=True,
            strip_accents=None,
            ngram_range=(1, 3),
            min_df=3,
            max_df=0.22,
            max_features=3500,
            stop_words=list(self.stop_words | self.bad_terms),
            token_pattern=r"(?u)\b[^\W\d_][^\W\d_'-]{3,}\b",
        )

        matrix = vectorizer.fit_transform(texts)
        terms = vectorizer.get_feature_names_out()
        column_scores = matrix.sum(axis=0).A1

        allowed_terms = set()
        for index in column_scores.argsort()[::-1]:
            term = terms[index]
            normalized = self.normalize_name(term)
            if not self.is_valid_node(normalized):
                continue
            if not self.is_domain_concept(normalized):
                continue
            folded_words = self.fold_text(normalized).split()
            if any(word in self.bad_terms for word in folded_words):
                continue
            allowed_terms.add(term)
            if len(allowed_terms) >= max_features:
                break

        concepts_by_chunk = {}
        for row_index, chunk in enumerate(chunks):
            row = matrix.getrow(row_index)
            candidates = []
            for feature_index, score in zip(row.indices, row.data):
                term = terms[feature_index]
                if term not in allowed_terms:
                    continue
                candidates.append((float(score), self.normalize_name(term)))

            unique = {}
            for score, name in sorted(candidates, reverse=True):
                key = self.canonical_key(name)
                if key not in unique:
                    unique[key] = (score, name)

            concepts_by_chunk[chunk["id"]] = [
                name for _, name in sorted(unique.values(), reverse=True)[:top_per_chunk]
            ]

        return concepts_by_chunk

    def is_domain_concept(self, name):
        folded_words = self.fold_text(name).split()
        if not folded_words:
            return False

        if len(folded_words) == 1:
            return folded_words[0] in self.domain_terms

        domain_hits = sum(1 for word in folded_words if word in self.domain_terms)
        if domain_hits == 0:
            return False

        generic_words = self.bad_terms | self.stop_words
        meaningful_words = [
            word for word in folded_words if word not in generic_words
        ]
        return len(meaningful_words) >= 2

    def infer_semantic_relation(self, text):
        folded = self.fold_text(text)

        if re.search(r"\b(cause|causent|provoque|provoquent|entraine|entrainent)\b", folded):
            return "causes"

        if re.search(
            r"\b(depend|dependance|necessite|conditionne|conditionnent)\b",
            folded,
        ):
            return "depends_on"

        if re.search(
            r"\b(influence|influencent|impact|impacts|affecte|affectent|modifie|modifient|effet|effets|consequence|contraint|contraintes)\b",
            folded,
        ):
            return "affects"

        if re.search(r"\b(correl|correlation|associe|association|lien|relation)\b", folded):
            return "correlates_with"

        if re.search(r"\b(interaction|interactions|interagit|interagissent)\b", folded):
            return "interacts_with"

        return "associated_with"

    def normalize_name(self, name):
        name = re.sub(r"<.*?>", "", str(name))
        name = name.replace("’", "'").replace("`", "'")
        name = " ".join(name.split()).strip(" -_,;:.")
        name = name.lower().strip()
        name = re.sub(
            r"^(le |la |les |l'|un |une |des )",
            "",
            name,
            flags=re.IGNORECASE,
        )
        name = " ".join(name.split())

        replacements = {
            "climatique": "climat",
            "climatiques": "climat",
            "oiseaux": "oiseau",
            "especes": "espece",
            "espèces": "espece",
            "temporelles": "temporel",
            "temporels": "temporel",
            "changements climatiques": "changement climatique",
            "variations climatiques": "climat",
            "mecanismes locaux": "mecanisme local",
        }
        name = replacements.get(name, name)
        return " ".join(word.capitalize() for word in name.split())

    def canonical_key(self, name):
        normalized = self.normalize_name(name)
        folded = self.fold_text(normalized)
        folded = re.sub(r"[^a-z0-9\s]", " ", folded)
        return re.sub(r"\s+", " ", folded).strip()

    def canonicalize_relation(self, relation):
        raw = str(relation or "").strip().lower()
        raw = raw.replace("-", "_").replace(" ", "_")
        raw = re.sub(r"[^a-z_]", "", raw)

        if not raw or raw in self.rejected_relations:
            return None

        canonical = self.relation_aliases.get(raw)
        if canonical not in self.allowed_relations:
            return None
        return canonical

    def map_node_type(self, raw_type, name):
        raw_type = str(raw_type).upper()

        if "PER" in raw_type or "ORG" in raw_type or "LOC" in raw_type:
            return "entity"

        if "P" in name and "_" in name and "C" in name:
            return "document"

        return "concept"

    def parse_rebel_output(self, text):
        triplets = []
        relation = ""
        subject = ""
        object_ = ""
        current = "x"

        for token in text.replace("<s>", "").replace("</s>", "").split():
            if token == "<triplet>":
                current = "t"
                if relation:
                    triplets.append(
                        {
                            "head": subject.strip(),
                            "type": relation.strip(),
                            "tail": object_.strip(),
                        }
                    )
                    relation = ""
                    subject = ""
                    object_ = ""
                subject = ""
            elif token == "<subj>":
                current = "s"
                if relation:
                    triplets.append(
                        {
                            "head": subject.strip(),
                            "type": relation.strip(),
                            "tail": object_.strip(),
                        }
                    )
                    relation = ""
                    subject = ""
                    object_ = ""
                object_ = ""
            elif token == "<obj>":
                current = "o"
                relation = ""
            else:
                if current == "t":
                    subject += " " + token
                elif current == "s":
                    object_ += " " + token
                elif current == "o":
                    relation += " " + token

        if relation:
            triplets.append(
                {
                    "head": subject.strip(),
                    "type": relation.strip(),
                    "tail": object_.strip(),
                }
            )

        return triplets

    def extract_relations_local(self, text):
        clean_text = re.sub(
            r"ID:.*?Content:",
            "",
            text,
            flags=re.DOTALL,
        ).strip()

        inputs = self.rebel_tokenizer(
            clean_text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        if self.device == "cuda":
            inputs = {key: value.to("cuda") for key, value in inputs.items()}

        gen_tokens = self.rebel_model.generate(
            **inputs,
            max_length=256,
            num_beams=3,
            length_penalty=0,
            early_stopping=True,
        )

        decoded = self.rebel_tokenizer.batch_decode(
            gen_tokens,
            skip_special_tokens=False,
        )[0]

        return self.parse_rebel_output(decoded)

    def clean_graph(self, raw_nodes, raw_edges):
        clean_nodes_map = {}
        clean_edges_map = {}

        for node in raw_nodes:
            raw_name = node["name"]
            if not self.is_valid_node(raw_name):
                continue

            name = self.normalize_name(raw_name)
            node_key = self.canonical_key(name)
            if not node_key:
                continue

            if node_key not in clean_nodes_map:
                node_type = self.map_node_type(node["type"], name)
                clean_nodes_map[node_key] = {
                    "name": name,
                    "type": node_type,
                    "description": (
                        f"Concept scientifique: {name}."
                        if node_type == "concept"
                        else f"Entite identifiee: {name}."
                    ),
                    "chunks": set(),
                    "support": 0,
                }

            clean_nodes_map[node_key]["support"] += 1
            if "chunk_id" in node and node["chunk_id"]:
                clean_nodes_map[node_key]["chunks"].add(node["chunk_id"])

        for edge in raw_edges:
            source_raw = edge["source"]
            target_raw = edge["target"]

            if not self.is_valid_node(source_raw) or not self.is_valid_node(target_raw):
                continue

            source_name = self.normalize_name(source_raw)
            target_name = self.normalize_name(target_raw)
            source_key = self.canonical_key(source_name)
            target_key = self.canonical_key(target_name)

            if not source_key or not target_key or source_key == target_key:
                continue

            relation = self.canonicalize_relation(edge["type"])
            if relation is None:
                continue

            if source_key not in clean_nodes_map or target_key not in clean_nodes_map:
                continue

            edge_key = f"{source_key}|{relation}|{target_key}"
            if edge_key not in clean_edges_map:
                clean_edges_map[edge_key] = {
                    "source": clean_nodes_map[source_key]["name"],
                    "target": clean_nodes_map[target_key]["name"],
                    "relation": relation,
                    "chunk_ids": set(),
                    "evidence_count": 0,
                }

            if edge.get("chunk_id"):
                clean_edges_map[edge_key]["chunk_ids"].add(edge["chunk_id"])
            clean_edges_map[edge_key]["evidence_count"] += 1

        connected_keys = set()
        final_edges = []
        for edge in clean_edges_map.values():
            edge["chunk_ids"] = sorted(edge["chunk_ids"])
            edge["chunk_id"] = edge["chunk_ids"][0] if edge["chunk_ids"] else None
            edge["weight"] = self.relation_weights.get(edge["relation"], 1.0) * max(
                1, min(edge["evidence_count"], 3)
            )
            final_edges.append(edge)
            connected_keys.add(self.canonical_key(edge["source"]))
            connected_keys.add(self.canonical_key(edge["target"]))

        final_nodes = []
        for node_key, node in clean_nodes_map.items():
            if node_key not in connected_keys:
                continue
            node["chunks"] = sorted(node["chunks"])
            node.pop("support", None)
            final_nodes.append(node)

        return final_nodes, final_edges

    def run(self, chunks_path, output_path, limit_chunks=None):
        if not os.path.exists(chunks_path):
            print(f"Erreur : {chunks_path} introuvable.")
            return

        with open(chunks_path, "r", encoding="utf-8") as handle:
            chunks = json.load(handle)

        all_nodes = []
        all_edges = []
        semantic_concepts = self.build_semantic_concepts(chunks)

        n_chunks = limit_chunks if limit_chunks is not None else len(chunks)
        print(f"Extraction Expert sur {n_chunks} chunks...")

        for i, chunk in enumerate(chunks[:n_chunks]):
            text = chunk["text"]
            chunk_id = chunk["id"]
            chunk_concepts = semantic_concepts.get(chunk_id, [])

            for concept in chunk_concepts:
                all_nodes.append(
                    {
                        "name": concept,
                        "type": "CONCEPT",
                        "chunk_id": chunk_id,
                    }
                )

            relation = self.infer_semantic_relation(text)
            for source, target in combinations(chunk_concepts[:6], 2):
                all_edges.append(
                    {
                        "source": source,
                        "target": target,
                        "relation": relation,
                        "chunk_id": chunk_id,
                    }
                )

            try:
                entities = self.ner_pipe(text)
                for entity in entities:
                    all_nodes.append(
                        {
                            "name": entity["word"],
                            "type": entity["entity_group"],
                            "chunk_id": chunk_id,
                        }
                    )
            except Exception as exc:
                print(f"Erreur NER: {exc}")

            try:
                triplets = self.extract_relations_local(text)
                for triplet in triplets:
                    all_nodes.append(
                        {
                            "name": triplet["head"],
                            "type": "CONCEPT",
                            "chunk_id": chunk_id,
                        }
                    )
                    all_nodes.append(
                        {
                            "name": triplet["tail"],
                            "type": "CONCEPT",
                            "chunk_id": chunk_id,
                        }
                    )

                    relation = self.canonicalize_relation(triplet["type"])
                    if relation is None:
                        continue

                    all_edges.append(
                        {
                            "source": triplet["head"],
                            "target": triplet["tail"],
                            "relation": relation,
                            "chunk_id": chunk_id,
                        }
                    )
            except Exception as exc:
                print(f"Erreur REBEL: {exc}")

            if (i + 1) % 10 == 0:
                print(f"Analyse : {i + 1}/{n_chunks} chunks")

        final_nodes, final_edges = self.clean_graph(
            all_nodes,
            [
                {
                    "source": edge["source"],
                    "target": edge["target"],
                    "type": edge["relation"],
                    "chunk_id": edge["chunk_id"],
                }
                for edge in all_edges
            ],
        )

        output_data = {
            "nodes": final_nodes,
            "edges": final_edges,
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(output_data, handle, ensure_ascii=False, indent=4)

        print("\nGraphe Expert termine !")
        print(f"Concepts : {len(final_nodes)}")
        print(f"Relations : {len(final_edges)}")


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"

    extractor = GraphExtractor()
    extractor.run(
        str(DATA_DIR / "corpus_chunks.json"),
        str(DATA_DIR / "knowledge_graph.json"),
        limit_chunks=None,
    )
