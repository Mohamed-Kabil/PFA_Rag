// AUTO-GENERATED cached RAG answers for the quick-access suggestion chips.
// These are real responses captured from the backend /query endpoint so that
// clicking a suggestion shows the answer instantly (no retrieval + LLM wait).
// Regenerate by re-running the 3 questions against POST /query.
import type { Message } from '../../stores/chat-store';

export interface CachedSuggestion {
  question: string;
  answer: string;
  metadata: NonNullable<Message['metadata']>;
}

export const CACHED_SUGGESTIONS: CachedSuggestion[] = [
  {
    "question": "Qu'est-ce que l'échantillonnage adaptatif basé sur un modèle de niche ?",
    "answer": "L'échantillonnage adaptatif basé sur un modèle de niche est une méthode utilisée pour optimiser l'échantillonnage des populations d'espèces dans un espace environnemental spécifique. Cette technique consiste à ajuster progressivement l'échantillon selon les caractéristiques spécifiques de chaque population, en fonction de son habitat et de ses exigences environnementales. Elle a été développée en 2006 par Guisan et al., qui ont proposé une approche d'échantillonnage itératif et itératif, appelée échantillonnage préférentiel, afin d'améliorer l'efficacité des recherches sur les espèces rares et insaisissables.",
    "metadata": {
      "action_taken": "Vector",
      "confidence_score": 0.99,
      "sources": [
        {
          "id": 726,
          "text": "Dans ce quatrième chapitre, avons testé une méthode proposée en 2006 par Guisan et al. (2006), l’échantillonnage basé sur des modèles de niche. Le principe de cette méthode est de développer l’échantillonnage adaptatif, une technique d’échantillonnage « de proche en proche » et itérative, dans un espace environnemental défini par l’estimation de la niche réalisée de l’espèce cible",
          "score": 0.2886573098852359,
          "rerank_score": 8.222946166992188
        },
        {
          "id": 0,
          "text": "Chapitre 4: L’échantillonnage adaptatif à partir d’un modèle de niche, ou échantillonnage préférentiel, pour améliorer l’efficacité des prospections: tests sur la base de simulations et d’expérimentations.\n\nÉchantillonnage adaptatif basé sur des niches pour améliorer les résultats sur les espèces rares et insaisissables : tests sur le terrain et par simulation.\n\nL’efficacité de l’échantillonnage est cruciale pour surmonter la crise des données sur la biodiversité et permettre une meilleure compréhension de ce qui détermine la répartition des espèces rares.",
          "score": 0.3,
          "rerank_score": 7.602695941925049
        }
      ],
      "routing_reason": "Query is mainly contextual or explanatory, so Vector RAG is preferred unless learned Q-values indicate otherwise.",
      "retrieval_summary": {
        "vector_results": 2,
        "graph_used": false,
        "graph_entities_found": 0
      },
      "decision_path": [
        "Query received",
        "Features extracted",
        "Query classified as Semantic",
        "Q-policy selected Vector",
        "Vector retrieval executed",
        "Reward computed: 1.0",
        "Q-table updated"
      ],
      "q_values": {
        "Vector": 0.199,
        "Graph": 0.0,
        "Hybrid": 0.0
      }
    }
  },
  {
    "question": "Comment la pollinisation est-elle liée aux changements environnementaux ?",
    "answer": "La pollinisation est liée aux changements environnementaux de nombreuses manières. En effet, les variations climatiques peuvent affecter la fréquence et la qualité des pollinisateurs, ce qui peut influencer la capacité des plantes à reproduire correctement. De plus, certains types de pollen peuvent être endommagés par les températures extrêmes ou les perturbations atmosphériques, rendant ainsi la pollinisation plus difficile. Ces modifications peuvent entraîner des effets sur la biodiversité et la flore, tout en impactant également la production agricole et la nutrition humaine.",
    "metadata": {
      "action_taken": "Vector",
      "confidence_score": 0.99,
      "sources": [
        {
          "id": 530,
          "text": "La biosphère s’est diversifiée au cours des temps géologiques par l’accumulation lente d’innovations produites par l’évolution des espèces (Darwin 1859, Sepkoski 1998, McShea and Brandon 2010). La sélection par l’environnement est un des moteurs majeurs de l’évolution, avec la sélection sexuelle, car elle favorise l’existence de formes de vies adaptées aux conditions particulières de leur environnement (Darwin 1859, 1871). Les changements globaux, en modifiant rapidement les pressions de sélection environnementales à l’échelle de la planète (Bosse et al",
          "score": 0.2822259864201006,
          "rerank_score": 1.557425618171692
        },
        {
          "id": 151,
          "text": ". 2017)? Est-ce que les individus les plus expérimentés choisissent des sites plus « sûrs » en termes de phénologie du déneigement dès le début de la saison, et repoussent les jeunes inexpérimentés vers des territoires moins prévisibles? La plasticité des populations développée pour répondre à cette imprévisibilité leur permet-elle de répondre aux changements de conditions environnementales induites par les changements climatiques? ll est actuellement difficile de répondre précisément à ces questions avec des techniques d’observation classique, ou avec du marquage individuel qui demanderait",
          "score": 0.2929699710160998,
          "rerank_score": 1.2979215383529663
        },
        {
          "id": 546,
          "text": "De par son aspect synthétique et simple, le concept de niche écologique des espèces est particulièrement intéressant pour étudier la relation d’une espèce à son environnement. Dans le contexte de l’étude de l’effet des changements globaux sur la distribution des espèces, la théorie de la niche de Hutchinson permet d’émettre une prédiction claire sur la réponse générale des espèces à des changements environnementaux simples ou multiples (Pocheville 2015)",
          "score": 0.3,
          "rerank_score": 1.1846166849136353
        }
      ],
      "routing_reason": "Query is mainly contextual or explanatory, so Vector RAG is preferred unless learned Q-values indicate otherwise.",
      "retrieval_summary": {
        "vector_results": 3,
        "graph_used": false,
        "graph_entities_found": 0
      },
      "decision_path": [
        "Query received",
        "Features extracted",
        "Query classified as Semantic",
        "Q-policy selected Vector",
        "Vector retrieval executed",
        "Reward computed: 1.0",
        "Q-table updated"
      ],
      "q_values": {
        "Vector": 0.31535835409,
        "Graph": 0.0,
        "Hybrid": 0.0
      }
    }
  },
  {
    "question": "Quel est l'effet des précipitations sur la phénologie des espèces ?",
    "answer": "Les précipitations ont un effet significatif sur la phénologie des espèces. Elles influencent notamment la survie, la population, la migration et l'adaptation du régime alimentaire des oiseaux alpins. Les variations saisonnières des précipitations peuvent également affecter la distribution spatiale des populations d'oiseaux communs pelouses et de cravides alpins. La corrélation entre les précipitations et la phénologie peut être utilisée pour prévoir les changements climatiques et leurs impacts sur les communautés alpines.",
    "metadata": {
      "action_taken": "Graph",
      "confidence_score": 0.5,
      "sources": [
        {
          "type": "graph",
          "content": "CONTEXTE GRAPHE (Entites et Relations):\n- Phénologie (concept): Concept scientifique: Phénologie.\n  - [affects | w=6.0 | evidence=2] -> Climat\n  - [associated_with | w=4.0 | evidence=2] -> Climat\n  - [affects | w=3.0 | evidence=1] -> Communautés\n  - [affects | w=3.0 | evidence=1] -> Contraintes\n  - [affects | w=3.0 | evidence=1] -> Interactions\n- Précipitations (concept): Concept scientifique: Précipitations.\n  - [associated_with | w=6.0 | evidence=3] -> Climat\n  - [associated_with | w=4.0 | evidence=2] -> Hiver\n  - [affects | w=3.0 | evidence=1] -> Pelouses Alpines\n  - [affects | w=3.0 | evidence=1] -> Printemps\n  - [affects | w=3.0 | evidence=1] -> Température\n- Phénologie Printanière (concept): Concept scientifique: Phénologie Printanière.\n  - [associated_with | w=6.0 | evidence=3] -> Phénologie\n  - [associated_with | w=4.0 | evidence=2] -> Craves Alpins\n  - [associated_with | w=2.0 | evidence=1] -> Alpins\n  - [associated_with | w=2.0 | evidence=1] -> Climat\n  - [associated_with | w=2.0 | evidence=1] -> Neige\n\nTHEME ASSOCIE (Communaute 5):\nOiseau, Sites, Phénologie, Précipitations, Alpin, Effort Échantillonnage, Corrélation, Alpins, Population Oiseaux Alpins, Population Oiseaux, Survie, Neige, Saisonniers Survie, Adapter Régime Alimentaire, Oiseaux Communs Pelouses, Communs Pelouses, Probabilité, Sites Surveillés, Crave, Crave Alpin Pyrrhocorax\n"
        }
      ],
      "routing_reason": "Query is mainly contextual or explanatory, so Vector RAG is preferred unless learned Q-values indicate otherwise.",
      "retrieval_summary": {
        "vector_results": 0,
        "graph_used": true,
        "graph_entities_found": 18
      },
      "decision_path": [
        "Query received",
        "Features extracted",
        "Query classified as Semantic",
        "Q-policy selected Graph",
        "Graph retrieval executed",
        "Reward computed: 1.0",
        "Q-table updated"
      ],
      "q_values": {
        "Vector": 0.4122047705491,
        "Graph": 0.0,
        "Hybrid": 0.0
      }
    }
  }
];
