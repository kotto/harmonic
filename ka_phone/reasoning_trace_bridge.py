#!/usr/bin/env python3
"""
KA-Next — REASONING TRACE BRIDGE (Raisonnement Visible)
==========================================================
Expose la chaîne de pensée holographique en format lisible,
JSON structuré, et prêt pour visualisation 3D.

Problème résolu : Le ResonanceReasoner calcule en silence.
                   Ce module rend chaque saut visible et explicable.

Fonctionnalités :
  - Trace complète du raisonnement (hops, faits, scores, connexions)
  - Graphe de raisonnement (nœuds = faits, arêtes = résonance)
  - Timeline interactive (ordre temporel des activations)
  - Format exportable (JSON, GraphViz DOT, Mermaid)

Usage :
  from reasoning_trace_bridge import ReasoningTraceBridge
  bridge = ReasoningTraceBridge(pipeline)
  trace = bridge.trace("Pourquoi le ciel est-il bleu ?")
  print(trace["story"])  # Histoire narrative du raisonnement
"""

import os, sys, math, json, time, hashlib, re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import numpy as np

BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

PHI = (1 + math.sqrt(5)) / 2


class ReasoningTraceBridge:
    """
    Pont entre le raisonnement holographique et la compréhension humaine.
    
    Transforme le raisonnement multi-hop en :
      1. Histoire narrative (story)
      2. Graphe structuré (graph)
      3. Timeline (timeline)
      4. Export formats (JSON, Mermaid, DOT)
    """
    
    def __init__(self, pipeline=None):
        self.pipeline = pipeline
        self.trace_stats = {
            "total_traces": 0,
            "avg_depth": 0,
            "total_hops": 0
        }
    
    def trace(self, query: str, depth: int = 3, 
              top_k: int = 10, include_story: bool = True) -> Dict[str, Any]:
        """
        Génère une trace complète du raisonnement pour une requête.
        
        Returns:
            Dict avec story, graph, timeline, facts_used, stats
        """
        if not self.pipeline or not self.pipeline.built:
            return {"error": "pipeline_not_built", "query": query}
        
        t0 = time.time()
        self.trace_stats["total_traces"] += 1
        
        # ── Exécution du raisonnement ──
        from hologram_vector_bridge import ResonanceReasoner
        
        reasoner = ResonanceReasoner(self.pipeline)
        reasoning_result = reasoner.reason(query, depth=depth, top_k=top_k)
        
        if not reasoning_result.get("chain"):
            return self._empty_trace(query, t0)
        
        chain = reasoning_result["chain"]
        graph_edges = reasoning_result.get("graph_edges", [])
        all_facts = reasoning_result.get("facts", [])
        
        self.trace_stats["total_hops"] += len(chain)
        self.trace_stats["avg_depth"] = round(
            self.trace_stats["total_hops"] / max(self.trace_stats["total_traces"], 1), 1
        )
        
        # ── Construction du graphe ──
        graph = self._build_reasoning_graph(chain, graph_edges, all_facts, query)
        
        # ── Construction de la timeline ──
        timeline = self._build_timeline(chain)
        
        # ── Génération de l'histoire ──
        story = self._generate_story(query, chain, graph_edges, all_facts) if include_story else ""
        
        # ── Métriques ──
        metrics = self._compute_metrics(chain, all_facts)
        
        elapsed_ms = round((time.time() - t0) * 1000, 1)
        
        return {
            "query": query,
            "story": story,
            "graph": graph,
            "timeline": timeline,
            "facts_used": [
                {
                    "id": f.get("id", ""),
                    "text": f.get("text", "")[:200],
                    "source_hop": self._find_fact_hop(f, chain)
                }
                for f in all_facts[:15]
            ],
            "metrics": metrics,
            "depth_used": depth,
            "total_hops": len([h for h in chain if h.get("n_facts", 0) > 0]),
            "total_facts": len(all_facts),
            "trace_time_ms": elapsed_ms,
            "export_formats": {
                "mermaid": self._to_mermaid(graph),
                "dot": self._to_dot(graph)
            }
        }
    
    def _build_reasoning_graph(self, chain: List[Dict],
                                graph_edges: List[Dict],
                                all_facts: List[Dict],
                                query: str) -> Dict:
        """Construit un graphe de raisonnement structuré."""
        nodes = []
        edges = []
        
        # Nœud racine : la question
        nodes.append({
            "id": "question",
            "label": query[:100],
            "type": "question",
            "level": 0,
            "size": 3.0
        })
        
        # Nœuds : faits par hop
        fact_nodes = {}
        node_id = 0
        for hop in chain:
            hop_num = hop.get("hop", 0)
            for fact in hop.get("facts", []):
                fid = fact.get("id", f"node_{node_id}")
                fact_nodes[fid] = {
                    "id": fid,
                    "label": fact.get("text", "")[:120],
                    "type": f"hop_{hop_num}",
                    "level": hop_num + 1,
                    "size": 1.0 + hop.get("top_score", 0) * 2,
                    "score": hop.get("top_score", 0)
                }
                nodes.append(fact_nodes[fid])
                node_id += 1
        
        # Arêtes : question → hop 0
        hop0 = chain[0] if len(chain) > 0 else {}
        for fact in hop0.get("facts", [])[:3]:
            fid = fact.get("id", "")
            if fid in fact_nodes:
                edges.append({
                    "from": "question",
                    "to": fid,
                    "strength": hop0.get("top_score", 0),
                    "label": "résonance directe"
                })
        
        # Arêtes : hop N → hop N+1
        for edge in graph_edges:
            from_hop_idx = edge.get("from_hop", 0)
            to_hop_idx = edge.get("to_hop", 0)
            if from_hop_idx < len(chain) and to_hop_idx < len(chain):
                from_facts = chain[from_hop_idx].get("facts", [])
                to_facts = chain[to_hop_idx].get("facts", [])
                for ff in from_facts[:3]:
                    ffid = ff.get("id", "")
                    for tf in to_facts[:3]:
                        tfid = tf.get("id", "")
                        if ffid in fact_nodes and tfid in fact_nodes:
                            edges.append({
                                "from": ffid,
                                "to": tfid,
                                "strength": edge.get("strength", 0),
                                "label": f"saut {from_hop_idx}→{to_hop_idx}"
                            })
        
        return {"nodes": nodes, "edges": edges, "query": query}
    
    def _build_timeline(self, chain: List[Dict]) -> List[Dict]:
        """Construit une timeline ordonnée des activations."""
        timeline = []
        cumulative_time = 0  # temps simulé en ms
        
        for hop in chain:
            hop_num = hop.get("hop", 0)
            facts = hop.get("facts", [])
            score = hop.get("top_score", 0)
            
            # Simuler un délai de propagation d'onde
            wave_delay = 10 + hop_num * 15  # ms
            cumulative_time += wave_delay
            
            timeline.append({
                "time_ms": cumulative_time,
                "event": f"hop_{hop_num}_start",
                "description": f"L'onde atteint le niveau {hop_num}",
                "details": {
                    "hop": hop_num,
                    "resonance_score": score,
                    "n_facts_activated": len(facts)
                }
            })
            
            for i, fact in enumerate(facts[:5]):
                cumulative_time += 2  # 2ms par fait
                timeline.append({
                    "time_ms": cumulative_time,
                    "event": f"fact_activated",
                    "description": f"Fait activé au niveau {hop_num}",
                    "details": {
                        "hop": hop_num,
                        "fact_rank": i + 1,
                        "fact_id": fact.get("id", ""),
                        "fact_text": fact.get("text", "")[:100]
                    }
                })
        
        return timeline
    
    def _generate_story(self, query: str, chain: List[Dict],
                         graph_edges: List[Dict],
                         all_facts: List[Dict]) -> str:
        """Génère une histoire narrative du raisonnement."""
        lines = []
        
        lines.append(f'Pour répondre à "{query}", voici le cheminement de la pensée holographique :')
        lines.append('')
        
        for hop in chain:
            hop_num = hop.get("hop", 0)
            score = hop.get("top_score", 0)
            n_facts = hop.get("n_facts", 0)
            facts = hop.get("facts", [])
            
            if hop_num == 0:
                lines.append(f'[Niveau 0 — Résonance directe]')
                lines.append(f'La question est convertie en onde. Cette onde se propage dans')
                lines.append(f'l\'hologramme et entre en résonance avec {n_facts} zones de connaissance')
                lines.append(f'(force de résonance : {score:.0%}).')
            else:
                lines.append(f'')
                lines.append(f'[Niveau {hop_num} — Saut de raisonnement]')
                lines.append(f'Les faits du niveau précédent créent une nouvelle onde composée.')
                lines.append(f'Cette onde rebondit et active {n_facts} nouvelles connexions')
                lines.append(f'(force : {score:.0%}).')
            
            if facts:
                lines.append(f'Faits activés à ce niveau :')
                for i, f in enumerate(facts[:3]):
                    text = f.get("text", "")
                    if text and len(text) > 3:
                        lines.append(f'  {i+1}. {text[:150]}')
        
        lines.append('')
        lines.append(f'[Conclusion]')
        lines.append(f'Le raisonnement a parcouru {len(chain)} niveaux de profondeur')
        lines.append(f'et mobilisé {len(all_facts)} faits au total.')
        lines.append(f'Chaque fait est traçable à sa source dans l\'hologramme.')
        
        # Ajouter les connexions clés
        if graph_edges:
            lines.append('')
            lines.append(f'Connexions découvertes entre niveaux :')
            for edge in graph_edges[:5]:
                lines.append(f'  Niveau {edge["from_hop"]} → Niveau {edge["to_hop"]} '
                           f'(force : {edge.get("strength", 0):.0%})')
        
        return '\n'.join(lines)
    
    def _compute_metrics(self, chain: List[Dict],
                          all_facts: List[Dict]) -> Dict:
        """Calcule les métriques de qualité du raisonnement."""
        active_hops = [h for h in chain if h.get("n_facts", 0) > 0]
        
        # Force de résonance moyenne par hop
        avg_resonance = sum(h.get("top_score", 0) for h in active_hops) / max(len(active_hops), 1)
        
        # Décroissance de la force (doit être progressive, pas brutale)
        decay_rates = []
        for i in range(len(active_hops) - 1):
            s1 = active_hops[i].get("top_score", 0)
            s2 = active_hops[i+1].get("top_score", 0)
            if s1 > 0:
                decay_rates.append(s2 / s1)
        
        avg_decay = sum(decay_rates) / max(len(decay_rates), 1) if decay_rates else 1.0
        
        # Diversité des faits (unicité)
        fact_texts = [f.get("text", "") for f in all_facts]
        unique_texts = len(set(fact_texts))
        diversity = unique_texts / max(len(fact_texts), 1)
        
        # Couverture : nombre de domaines touchés
        domains = set()
        for f in all_facts:
            text = f.get("text", "").lower()
            if any(w in text for w in ["capitale", "pays", "géographie", "continent"]):
                domains.add("geography")
            if any(w in text for w in ["math", "calcul", "équation", "nombre", "="]):
                domains.add("mathematics")
            if any(w in text for w in ["physique", "newton", "einstein", "quantique", "gravité"]):
                domains.add("physics")
            if any(w in text for w in ["histoire", "siècle", "empire", "royaume", "guerre"]):
                domains.add("history")
            if any(w in text for w in ["philosophie", "sagesse", "éthique", "maat", "ubuntu"]):
                domains.add("philosophy")
            if any(w in text for w in ["code", "python", "algorithme", "internet", "turing"]):
                domains.add("computer_science")
        
        return {
            "depth": len(active_hops),
            "avg_resonance_strength": round(avg_resonance, 4),
            "avg_decay_rate": round(avg_decay, 4),
            "fact_diversity": round(diversity, 4),
            "domain_coverage": list(domains),
            "total_facts": len(all_facts),
            "is_coherent": avg_decay > 0.1 and diversity > 0.5,
            "explanation": (
                f"Raisonnement sur {len(active_hops)} niveaux avec force moyenne de {avg_resonance:.0%}. "
                f"{'Bonne' if diversity > 0.7 else 'Moyenne' if diversity > 0.4 else 'Faible'} "
                f"diversité des sources ({diversity:.0%}). "
                f"Décroissance {'progressive' if avg_decay > 0.5 else 'rapide' if avg_decay > 0.2 else 'abrupte'} "
                f"de la force de résonance."
            )
        }
    
    def _find_fact_hop(self, fact: Dict, chain: List[Dict]) -> int:
        """Trouve le hop d'origine d'un fait."""
        fid = fact.get("id", "")
        ftext = fact.get("text", "")
        for hop in chain:
            for hf in hop.get("facts", []):
                if hf.get("id") == fid or hf.get("text") == ftext:
                    return hop.get("hop", 0)
        return -1
    
    def _empty_trace(self, query: str, t0: float) -> Dict:
        """Trace vide quand aucun raisonnement n'est possible."""
        return {
            "query": query,
            "story": f"Aucun chemin de raisonnement trouvé pour '{query[:100]}'.",
            "graph": {"nodes": [{"id": "question", "label": query[:100], "type": "question", "level": 0, "size": 2}], "edges": []},
            "timeline": [],
            "facts_used": [],
            "metrics": {"depth": 0, "avg_resonance_strength": 0, "is_coherent": False,
                       "explanation": "Aucun fait trouvé dans l'hologramme."},
            "depth_used": 0,
            "total_hops": 0,
            "total_facts": 0,
            "trace_time_ms": round((time.time() - t0) * 1000, 1)
        }
    
    def _to_mermaid(self, graph: Dict) -> str:
        """Exporte le graphe au format Mermaid (compatible Markdown/GitHub)."""
        lines = ["graph TD"]
        for node in graph.get("nodes", []):
            nid = node["id"].replace("-", "_").replace(" ", "_")
            label = node["label"][:60].replace('"', "'")
            color = {"question": "#ffd700", "hop_0": "#4CAF50", 
                    "hop_1": "#2196F3", "hop_2": "#9C27B0",
                    "hop_3": "#FF5722"}.get(node.get("type", ""), "#666")
            lines.append(f'    {nid}["{label}"]')
            lines.append(f'    style {nid} fill:{color}')
        
        for edge in graph.get("edges", []):
            src = edge["from"].replace("-", "_").replace(" ", "_")
            dst = edge["to"].replace("-", "_").replace(" ", "_")
            strength = edge.get("strength", 0)
            if strength > 0.7:
                lines.append(f'    {src} ==>|"{strength:.0%}"| {dst}')
            elif strength > 0.4:
                lines.append(f'    {src} -->|"{strength:.0%}"| {dst}')
            else:
                lines.append(f'    {src} -.->|"{strength:.0%}"| {dst}')
        
        return '\n'.join(lines)
    
    def _to_dot(self, graph: Dict) -> str:
        """Exporte le graphe au format DOT (GraphViz)."""
        lines = ["digraph reasoning {"]
        lines.append('    rankdir=TB;')
        lines.append('    node [shape=box, style=rounded];')
        
        for node in graph.get("nodes", []):
            nid = node["id"].replace("-", "_").replace(" ", "_")
            label = node["label"][:80].replace('"', "'")
            color = {"question": "gold", "hop_0": "green", 
                    "hop_1": "blue", "hop_2": "purple",
                    "hop_3": "orange"}.get(node.get("type", ""), "gray")
            lines.append(f'    {nid} [label="{label}", color={color}, penwidth={node.get("size", 1)*2}];')
        
        for edge in graph.get("edges", []):
            src = edge["from"].replace("-", "_").replace(" ", "_")
            dst = edge["to"].replace("-", "_").replace(" ", "_")
            lines.append(f'    {src} -> {dst} [label="{edge.get("strength", 0):.0%}"];')
        
        lines.append("}")
        return '\n'.join(lines)
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques de traçabilité."""
        return dict(self.trace_stats)
    
    def trace_json(self, query: str, depth: int = 3) -> str:
        """Retourne la trace complète en JSON formaté (pour API)."""
        result = self.trace(query, depth=depth, include_story=True)
        # Enlever les clés volumineuses pour l'API
        if "export_formats" in result:
            del result["export_formats"]
        return json.dumps(result, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Reasoning Trace Bridge")
    parser.add_argument("--query", type=str, required=True, help="Question")
    parser.add_argument("--depth", type=int, default=3, help="Profondeur (défaut: 3)")
    parser.add_argument("--format", type=str, default="text",
                       choices=["text", "json", "mermaid", "dot"],
                       help="Format de sortie")
    
    args = parser.parse_args()
    
    try:
        from hologram_vector_bridge import HologramVectorPipeline
        pipeline = HologramVectorPipeline(use_llm=False)
        pipeline.build(force=False)
    except Exception as e:
        print(f"Erreur: {e}")
        sys.exit(1)
    
    bridge = ReasoningTraceBridge(pipeline)
    
    if args.format == "text":
        result = bridge.trace(args.query, depth=args.depth)
        print(result["story"])
        print(f"\n{'='*50}")
        print(f"Métriques : {json.dumps(result['metrics'], indent=2, ensure_ascii=False)}")
        print(f"Temps : {result['trace_time_ms']}ms")
    elif args.format == "json":
        print(bridge.trace_json(args.query, depth=args.depth))
    elif args.format == "mermaid":
        result = bridge.trace(args.query, depth=args.depth)
        print(result.get("export_formats", {}).get("mermaid", "Pas de graphe"))
    elif args.format == "dot":
        result = bridge.trace(args.query, depth=args.depth)
        print(result.get("export_formats", {}).get("dot", "Pas de graphe"))


if __name__ == "__main__":
    main()