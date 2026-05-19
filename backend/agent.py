import json
import os
import random
import unicodedata
from pathlib import Path

from backend.graph_retrieval import GraphRetriever
from backend.retrieval import HybridRetriever
from backend import config


class RoutingAgent:
    def __init__(self, data_dir=None, q_table_path=None):
        self.data_dir = Path(data_dir) if data_dir else config.DATA_DIR
        self.q_table_path = Path(q_table_path) if q_table_path else config.Q_TABLE_JSON

        # 0 = Vector, 1 = Graph, 2 = Hybrid
        self.actions = [0, 1, 2]
        self.action_names = {
            0: "Vector",
            1: "Graph",
            2: "Hybrid",
        }

        # Q-Learning params
        self.epsilon = 0.1
        self.alpha = 0.1
        self.gamma = 0.9

        self.vector_retriever = HybridRetriever(str(self.data_dir))
        self.graph_retriever = GraphRetriever()
        self.q_table = self.load_q_table()
        self.last_decisions = []

    # =====================================================
    # Q-TABLE
    # =====================================================
    def load_q_table(self):
        if not self.q_table_path.exists():
            return {}

        try:
            with open(self.q_table_path, "r", encoding="utf-8") as handle:
                content = handle.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except Exception as exc:
            print(f"Erreur chargement Q-table: {exc}")
            return {}

    def save_q_table(self):
        with open(self.q_table_path, "w", encoding="utf-8") as handle:
            json.dump(self.q_table, handle, ensure_ascii=False, indent=4)

    def ensure_state(self, state):
        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(self.actions)

    # =====================================================
    # STATE AND QUERY ANALYSIS
    # =====================================================
    def get_state(self, query):
        """
        Original compact state kept for backward compatibility.
        """
        words = query.lower().split()
        has_entities = len([word for word in words if len(word) > 6]) > 1
        is_long = len(words) > 10
        return f"{int(has_entities)}_{int(is_long)}"

    def fold_text(self, text):
        folded = unicodedata.normalize("NFKD", str(text))
        return folded.encode("ascii", "ignore").decode("ascii").lower()

    def extract_query_features(self, query):
        text = self.fold_text(query)
        words = text.split()

        graph_keywords = {
            "affecte",
            "affectent",
            "cause",
            "causes",
            "chemin",
            "communaute",
            "communautes",
            "connecte",
            "connexion",
            "correlation",
            "depend",
            "graphe",
            "impact",
            "influence",
            "influencent",
            "interaction",
            "interactions",
            "lien",
            "liens",
            "relation",
            "relations",
            "reseau",
        }

        semantic_keywords = {
            "comment",
            "decris",
            "definition",
            "explique",
            "pourquoi",
            "quel",
            "quelle",
            "quelles",
            "quels",
            "quoi",
            "resume",
            "synthese",
        }

        systematic_terms = sum(1 for word in words if word in graph_keywords)
        semantic_terms = sum(1 for word in words if word in semantic_keywords)
        has_relation_pattern = any(
            marker in text
            for marker in (
                " entre ",
                " lie ",
                " lies ",
                " relie ",
                " relies ",
                " par rapport ",
            )
        )

        if len(words) > 14:
            complexity = "high"
        elif len(words) > 7:
            complexity = "medium"
        else:
            complexity = "low"

        return {
            "word_count": len(words),
            "semantic_terms": semantic_terms,
            "systematic_terms": systematic_terms,
            "has_relation_pattern": has_relation_pattern,
            "complexity": complexity,
        }

    def classify_query(self, features):
        semantic_signal = features["semantic_terms"] > 0
        systematic_signal = (
            features["systematic_terms"] > 0
            or features["has_relation_pattern"]
        )

        if semantic_signal and systematic_signal:
            return "Hybrid"
        if systematic_signal:
            return "Systematic"
        return "Semantic"

    def get_metadata_state(self, query_type, features):
        return (
            f"type={query_type}|"
            f"complexity={features['complexity']}|"
            f"semantic={features['semantic_terms']}|"
            f"systematic={features['systematic_terms']}|"
            f"relation={int(features['has_relation_pattern'])}"
        )

    # =====================================================
    # ACTION SELECTION
    # =====================================================
    def preferred_action_for_query_type(self, query_type):
        if query_type == "Semantic":
            return 0
        if query_type == "Systematic":
            return 1
        return 2

    def choose_action(self, state):
        """
        Original API kept for compatibility with scripts expecting run_query().
        Uses epsilon-greedy Q-learning instead of forcing Hybrid.
        """
        self.ensure_state(state)

        if random.random() < self.epsilon:
            return random.choice(self.actions)

        q_values = self.q_table[state]
        max_value = max(q_values)
        best_actions = [
            action
            for action, value in enumerate(q_values)
            if value == max_value
        ]
        return best_actions[-1]

    def choose_action_with_metadata(self, state, query_type):
        self.ensure_state(state)

        q_values = self.q_table[state]
        preferred_action = self.preferred_action_for_query_type(query_type)

        # Cold-start prior keeps routing aligned with query analysis, while
        # learned Q-values can override it over time.
        policy_scores = []
        for action in self.actions:
            prior = 1.0 if action == preferred_action else 0.0
            policy_scores.append(float(q_values[action]) + prior)

        if random.random() < self.epsilon:
            action = random.choice(self.actions)
        else:
            max_score = max(policy_scores)
            best_actions = [
                candidate
                for candidate, score in enumerate(policy_scores)
                if score == max_score
            ]
            action = (
                preferred_action
                if preferred_action in best_actions
                else best_actions[0]
            )

        total_score = sum(abs(score) for score in policy_scores) or 1.0
        confidence = abs(policy_scores[action]) / total_score
        confidence = max(0.5, min(0.99, confidence))

        return action, {
            "q_values": {
                self.action_names[index]: float(q_values[index])
                for index in self.actions
            },
            "policy_scores": {
                self.action_names[index]: float(policy_scores[index])
                for index in self.actions
            },
            "confidence": float(confidence),
            "preferred_action": self.action_names[preferred_action],
        }

    # =====================================================
    # RESULT VALIDATION
    # =====================================================
    def is_good_result(self, results):
        if results is None:
            return False

        if isinstance(results, list):
            if len(results) == 0:
                return False
            return any(len(item.get("text", "").split()) >= 10 for item in results)

        if isinstance(results, str):
            text = results.strip()
            if len(text.split()) < 5:
                return False

            bad_patterns = [
                "Aucune entite",
                "Aucune entité",
                "No results",
                "not found",
                "aucun resultat",
                "aucun résultat",
            ]
            return not any(pattern.lower() in text.lower() for pattern in bad_patterns)

        if isinstance(results, dict):
            vector_ok = self.is_good_result(results.get("vector"))
            graph_ok = self.is_good_result(results.get("graph"))
            return vector_ok or graph_ok

        return False

    # =====================================================
    # GRAPH EXPANSION
    # =====================================================
    def expand_with_graph(self, vector_results):
        if not vector_results:
            return ""

        combined_text = " ".join([result["text"] for result in vector_results])
        graph_context = self.graph_retriever.retrieve_graph_context(combined_text)

        if not isinstance(graph_context, str):
            return ""

        bad_patterns = [
            "Aucune entite",
            "Aucune entité",
            "No results",
            "not found",
        ]
        if any(pattern.lower() in graph_context.lower() for pattern in bad_patterns):
            return ""

        return graph_context

    # =====================================================
    # EXECUTE ACTION
    # =====================================================
    def execute_action(self, action, query):
        if action == 0:
            results = self.vector_retriever.hybrid_search(query, top_k=3)
            return results, "Vector"

        if action == 1:
            results = self.graph_retriever.retrieve_graph_context(query)
            return results, "Graph"

        vector_results = self.vector_retriever.hybrid_search(query, top_k=3)
        graph_results = self.expand_with_graph(vector_results)
        return {
            "vector": vector_results,
            "graph": graph_results,
        }, "Hybrid"

    # =====================================================
    # Q-LEARNING UPDATE
    # =====================================================
    def update_q_table(self, state, action, reward, next_state):
        self.ensure_state(state)
        self.ensure_state(next_state)

        old_value = self.q_table[state][action]
        next_max = max(self.q_table[next_state])
        new_value = (
            (1 - self.alpha) * old_value
            + self.alpha * (reward + self.gamma * next_max)
        )

        self.q_table[state][action] = float(new_value)
        self.save_q_table()

        return {
            "old_value": float(old_value),
            "new_value": float(new_value),
        }

    # =====================================================
    # MAIN QUERY PIPELINES
    # =====================================================
    def run_query(self, query):
        """
        Backward-compatible pipeline used by CLI/debug scripts.
        Returns exactly (results, action_name).
        """
        state = self.get_state(query)
        action = self.choose_action(state)
        results, action_name = self.execute_action(action, query)
        reward = 1.0 if self.is_good_result(results) else -1.0
        self.update_q_table(state, action, reward, state)
        return results, action_name

    def summarize_retrieval(self, results, action_name):
        if action_name == "Vector":
            return {
                "vector_results": len(results) if isinstance(results, list) else 0,
                "graph_used": False,
                "graph_entities_found": 0,
            }

        if action_name == "Graph":
            graph_text = str(results or "")
            return {
                "vector_results": 0,
                "graph_used": bool(graph_text.strip()),
                "graph_entities_found": graph_text.count("- "),
            }

        vector_results = []
        graph_text = ""
        if isinstance(results, dict):
            vector_results = results.get("vector") or []
            graph_text = str(results.get("graph") or "")

        return {
            "vector_results": len(vector_results),
            "graph_used": bool(graph_text.strip()),
            "graph_entities_found": graph_text.count("- "),
        }

    def build_routing_reason(self, query_type):
        if query_type == "Semantic":
            return (
                "Query is mainly contextual or explanatory, so Vector RAG is "
                "preferred unless learned Q-values indicate otherwise."
            )

        if query_type == "Systematic":
            return (
                "Query contains relation or graph-structure signals, so Graph "
                "RAG is preferred unless learned Q-values indicate otherwise."
            )

        return (
            "Query combines semantic and relation-oriented signals, so Hybrid "
            "retrieval is preferred."
        )

    def analyze_query(self, query):
        """
        Deterministic routing preview. It does not execute retrieval and does
        not update the Q-table.
        """
        features = self.extract_query_features(query)
        query_type = self.classify_query(features)
        state = self.get_metadata_state(query_type, features)

        q_values = self.q_table.get(state, [0.0] * len(self.actions))
        preferred_action = self.preferred_action_for_query_type(query_type)
        policy_scores = []
        for action in self.actions:
            prior = 1.0 if action == preferred_action else 0.0
            policy_scores.append(float(q_values[action]) + prior)

        max_score = max(policy_scores)
        best_actions = [
            action
            for action, score in enumerate(policy_scores)
            if score == max_score
        ]
        action = (
            preferred_action
            if preferred_action in best_actions
            else best_actions[0]
        )

        total_score = sum(abs(score) for score in policy_scores) or 1.0
        confidence = abs(policy_scores[action]) / total_score
        confidence = max(0.5, min(0.99, confidence))

        return {
            "query_type": query_type,
            "state": state,
            "features": features,
            "action_taken": self.action_names[action],
            "confidence_score": float(confidence),
            "q_values": {
                self.action_names[index]: float(q_values[index])
                for index in self.actions
            },
            "policy_scores": {
                self.action_names[index]: float(policy_scores[index])
                for index in self.actions
            },
            "routing_reason": self.build_routing_reason(query_type),
            "decision_path": [
                "Query received",
                "Features extracted",
                f"Query classified as {query_type}",
                f"Routing preview selected {self.action_names[action]}",
            ],
        }

    def run_query_with_metadata(self, query):
        """
        API pipeline with routing metadata for the Agentic/Query panels.
        """
        features = self.extract_query_features(query)
        query_type = self.classify_query(features)
        state = self.get_metadata_state(query_type, features)
        action, policy = self.choose_action_with_metadata(state, query_type)
        action_name = self.action_names[action]

        results, action_name = self.execute_action(action, query)
        reward = 1.0 if self.is_good_result(results) else -1.0
        q_update = self.update_q_table(state, action, reward, state)

        metadata = {
            "query_type": query_type,
            "action_taken": action_name,
            "state": state,
            "features": features,
            "q_values": policy["q_values"],
            "policy_scores": policy["policy_scores"],
            "reward": float(reward),
            "q_update": q_update,
            "confidence_score": policy["confidence"],
            "routing_reason": self.build_routing_reason(query_type),
            "retrieval_summary": self.summarize_retrieval(results, action_name),
            "decision_path": [
                "Query received",
                "Features extracted",
                f"Query classified as {query_type}",
                f"Q-policy selected {action_name}",
                f"{action_name} retrieval executed",
                f"Reward computed: {reward}",
                "Q-table updated",
            ],
        }

        self.last_decisions.append(metadata)
        self.last_decisions = self.last_decisions[-10:]

        return results, action_name, metadata

    def get_agent_state(self):
        return {
            "q_table": self.q_table,
            "actions": [self.action_names[action] for action in self.actions],
            "epsilon": self.epsilon,
            "alpha": self.alpha,
            "gamma": self.gamma,
            "known_states": len(self.q_table),
            "last_decisions": self.last_decisions,
        }

    # =====================================================
    # DEBUG
    # =====================================================
    def debug_q_table(self):
        print("\n=== Q-TABLE ===")
        for state, values in self.q_table.items():
            print(
                f"{state} -> "
                f"Vector={values[0]:.3f} | "
                f"Graph={values[1]:.3f} | "
                f"Hybrid={values[2]:.3f}"
            )


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"

    agent = RoutingAgent(DATA_DIR)

    queries = [
        "Quelle est l'influence du paturage sur la biodiversite alpine ?",
        "Comment les especes survivent au changement climatique ?",
        "Hutchinson et la niche ecologique",
    ]

    for query in queries:
        print(f"\n--- Question : {query} ---")
        res, act = agent.run_query(query)
        print(f"Agent a choisi : {act}")
        print(f"Resultats valides : {agent.is_good_result(res)}")

    agent.debug_q_table()
