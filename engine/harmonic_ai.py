"""
Harmonic AI v1.0 — Intelligence ondulatoire unifiée
=====================================================
Une seule classe. Toutes les capacités.

Usage:
  from harmonic_ai import HarmonicAI
  
  ai = HarmonicAI()
  
  # Raisonnement
  ai.ask("explique la lumiere")
  ai.reason("pourquoi le coeur pompe le sang")
  
  # Créativité
  ai.create(n=5)
  ai.metaphor()
  ai.haiku()
  ai.surreal()
  
  # Apprentissage
  ai.learn("Marie Curie a decouvert le radium", "PHYSIQUE_FOND")
  ai.ingest("chemin/vers/corpus/")
  
  # Persistance
  ai.save("mon_modele.hai")
  ai.load("mon_modele.hai")
  
  # Stats
  print(ai.stats)
"""

import os, sys, json, time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

# Chemin du module
_MODULE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_MODULE_DIR))

from harmonic_model import HarmonicModel, build_waves, KNOWLEDGE_BASE
from reasoning_engine import ReasoningEngine
from style_engine import StyleEngine


class HarmonicAI:
    """
    Intelligence Artificielle Harmonique — Interface unifiée.
    
    Capacités :
      - ask()      : réponse factuelle
      - reason()   : chaîne de raisonnement
      - create()   : connexions créatives entre domaines
      - metaphor() : métaphores poétiques
      - haiku()    : poésie japonaise
      - surreal()  : images surréalistes
      - learn()    : apprentissage de nouveaux faits
      - ingest()   : ingestion massive depuis un corpus
      - save()     : persistance complète
      - load()     : restauration complète
    """
    
    def __init__(self, use_memory: bool = True, enable_bootstrapper: bool = True):
        self.model = HarmonicModel(use_memory=use_memory)
        self.engine = ReasoningEngine(self.model)
        self._load_extended_kb()
        self._load_general_knowledge()  # Nouveau : culture générale
        
        # Bootstrapper pour le sevrage progressif du LLM
        self.bootstrapper = None
        if enable_bootstrapper:
            from bootstrapper import HarmonicBootstrapper
            self.bootstrapper = HarmonicBootstrapper(model=self.model)
        
        # Mémoire conversationnelle multi-tours
        import importlib.util, sys
        spec = importlib.util.spec_from_file_location(
            "conversation_memory",
            str(_MODULE_DIR / "memory" / "conversation.py")
        )
        conv_module = importlib.util.module_from_spec(spec)
        sys.modules["conversation_memory"] = conv_module
        spec.loader.exec_module(conv_module)
        self.conversation = conv_module.ConversationMemory(max_messages=50)

        # Enrichisseur de savoir (blocs explicatifs profonds)
        self._enricher = None
        self._composer = None
        self._decoder = None
        try:
            from knowledge_enricher import KnowledgeEnricher
            self._enricher = KnowledgeEnricher()
            self._enricher.load_curated_defaults()
        except Exception:
            pass
    
    def _confidence_score(self, response: str, question: str) -> float:
        """
        Évalue la confiance dans une réponse (0 = pas confiance, 1 = confiance totale).
        
        Stratégie : vérifier que la réponse apporte de l'information NOUVELLE,
        pas juste un echo de la question via les templates.
        """
        if not response or len(response) < 20:
            return 0.0
        low_phrases = ['je ne connais pas', 'je ne trouve pas', 'pas de resonance',
                       'connais pas assez', 'ne comprends pas', 'pas assez de connaissances']
        if any(p in response.lower() for p in low_phrases):
            return 0.0
        
        # Extraire le SUJET NET de la question (sans les mots-outils)
        stopwords = {'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et', 'est', 'a',
                     'que', 'qui', 'quoi', 'dans', 'sur', 'pour', 'avec', 'par', 'en',
                     'the', 'a', 'an', 'is', 'are', 'of', 'in', 'on', 'at', 'to',
                     'what', 'who', 'how', 'why', 'when', 'where', 'which',
                     'invente', 'cree', 'decouvert', 'fonctionne', 'explique', 'trouve',
                     'fait', 'dit', 'donne', 'utilise', 'appelle', 'signifie',
                     'comment', 'pourquoi', 'quand', 'ou', 'combien', 'est-ce'}
        q_words = set(w.strip('.,!?;:()[]{}') for w in question.lower().split()
                     if len(w) > 2 and w not in stopwords)
        
        if not q_words:
            return 0.4
        
        # Identifier les MOTS-CLÉS de la question (les plus longs, les plus spécifiques)
        key_words = sorted(q_words, key=len, reverse=True)[:3]  # top 3 mots les plus longs
        
        # Vérifier que les MOTS-CLÉS n'apparaissent PAS comme simples échos
        # (si un mot-clé apparaît suivi d'un verbe générique → echo du template)
        echo_score = 0
        for kw in key_words:
            # Chercher le mot-clé dans la réponse
            pos = response.lower().find(kw)
            if pos >= 0:
                # Vérifier le contexte : est-ce un echo ?
                context = response.lower()[max(0,pos-20):pos+len(kw)+30]
                echo_patterns = ['éclaire ' + kw, 'comprendre ' + kw, 'cerner ' + kw,
                                'phénomène de ' + kw, 'concept de ' + kw]
                if any(p in context for p in echo_patterns):
                    echo_score += 1  # c'est un echo, pas une vraie réponse
        
        # Si tous les mots-clés sont des échos → très faible confiance
        if len(key_words) > 0 and echo_score >= len(key_words):
            return 0.1
        
        # Si la plupart sont des échos → faible
        if len(key_words) > 0 and echo_score / len(key_words) >= 0.5:
            return 0.2
        
        # Vérifier aussi la présence RÉELLE des mots-clés dans la réponse
        r_words = set(w.strip('.,!?;:()[]{}') for w in response.lower().split() if len(w) > 2)
        key_overlap = set(key_words) & r_words
        key_ratio = len(key_overlap) / len(key_words) if key_words else 1.0
        
        # Si aucun mot-clé n'apparaît → très faible
        if key_ratio == 0:
            return 0.15
        
        # Si peu de mots-clés apparaissent → faible
        if key_ratio < 0.3:
            return 0.25
        
        # Sinon, confiance basée sur la longueur et couverture
        base = 0.35 + key_ratio * 0.3 + min(0.25, len(response) / 400)
        return min(1.0, base)
    
    def _load_extended_kb(self):
        """Charge la base étendue (50K faits) si disponible."""
        # Essayer d'abord le 50K
        kb_50k = _MODULE_DIR / "data" / "bootstrapper_output" / "knowledge_base_50k.npz"
        kb_cleaned = _MODULE_DIR / "data" / "bootstrapper_output" / "knowledge_base_50k_cleaned.npz"
        kb_resonance = _MODULE_DIR / "data" / "bootstrapper_output" / "knowledge_base_resonance.npz"
        
        for kb_path in [kb_resonance, kb_cleaned, kb_50k]:
            if kb_path.exists():
                try:
                    data = np.load(str(kb_path), allow_pickle=True)
                    ingested = list(data['facts'])
                    added = 0
                    for fact in ingested:
                        s, r, o, sec = fact[0], fact[1], fact[2], fact[3]
                        if (s, r, o, sec) not in self.model.knowledge_base:
                            self.model.knowledge_base.append((s, r, o, sec))
                            added += 1
                    if added > 0:
                        self.model.kx, self.model.ky, self.model.w2i = build_waves(
                            self.model.knowledge_base
                        )
                    print(f"Loaded {added} facts from {kb_path.name}")
                    break  # Un seul fichier chargé
                except Exception as e:
                    print(f"Failed to load {kb_path.name}: {e}")
        
        # Fallback: ancien format
        kb_old = _MODULE_DIR.parent / "data" / "bootstrapper_output" / "knowledge_base.npz"
        if kb_old.exists():
            try:
                data = np.load(str(kb_old), allow_pickle=True)
                ingested = list(data['facts'])
                added = 0
                for fact in ingested:
                    s, r, o, sec = fact[0], fact[1], fact[2], fact[3]
                    if (s, r, o, sec) not in self.model.knowledge_base:
                        self.model.knowledge_base.append((s, r, o, sec))
                        added += 1
                if added > 0:
                    self.model.kx, self.model.ky, self.model.w2i = build_waves(
                        self.model.knowledge_base
                    )
            except Exception:
                pass
    
    def _load_general_knowledge(self):
        """Charge la base de culture générale (géographie, histoire, etc.)."""
        added = 0
        try:
            from qualitative_knowledge_extended import extend_knowledge_base
            added += extend_knowledge_base(self.model)
        except Exception:
            pass
        try:
            from kb_massive_extension import extend_all
            added += extend_all(self.model)
        except Exception:
            pass
        if added > 0:
            self.engine = ReasoningEngine(self.model)
    
    # ═══════════════════════════════════════════════════════════════════
    # RAISONNEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def ask(self, question: str) -> str:
        """
        Réponse avec le pipeline RAG Harmonique :
          0. Détection conversation/math/hors-domaine (DomainDetector)
          1. Analyse d'intention (QuestionAnalyzer)
          2. Recherche de faits pertinents (find_paths + recherche étendue)
          3. Récupération du bloc de savoir enrichi (si disponible)
          4. Composition de réponse naturelle (ResponseComposer)
          5. Fallback LLM si confiance faible + apprentissage
        """
        # ── 0. DÉTECTION PRÉCOCE : conversation, math, hors-domaine ──
        try:
            from domain_detector import (
                detect_question_type, handle_greeting, handle_identity,
                handle_out_of_domain, detect_language
            )
            from smart_retriever import smart_math
            
            qtype = detect_question_type(question)
            lang = qtype.get('language', 'fr')
            
            if qtype.get('is_identity'):
                resp = handle_identity(lang=lang)
                if resp:
                    self.conversation.add("user", question)
                    self.conversation.add("assistant", resp)
                    return resp
            
            if qtype.get('is_greeting'):
                resp = handle_greeting(
                    is_mercy=qtype.get('is_mercy', False),
                    is_bye=qtype.get('is_bye', False),
                    lang=lang
                )
                if resp:
                    self.conversation.add("user", question)
                    self.conversation.add("assistant", resp)
                    return resp
            
            # Math : utiliser smart_math (plus complet)
            math_result = smart_math(question)
            if math_result:
                self.conversation.add("user", question)
                self.conversation.add("assistant", math_result)
                return math_result
            
            if qtype.get('is_out_of_domain'):
                resp = handle_out_of_domain(qtype.get('out_category', ''), lang=lang)
                if resp:
                    self.conversation.add("user", question)
                    self.conversation.add("assistant", resp)
                    return resp
                
        except ImportError:
            lang = 'fr'
        
        # Enrichir la question avec le contexte de conversation
        enriched = self._enrich_with_context(question)

        # ── 0. CHEMIN ONDULATOIRE PRIMAIRE ────────────────────────────────
        # Le wave decoder est désactivé pour les questions factuelles.
        # Il reste disponible pour les tâches créatives via ai.create(), ai.metaphor(), etc.
        # Pour les questions de connaissance, le pipeline KB + compositeur est prioritaire.

        # ── 1. Analyse d'intention (fallback si onde insuffisante) ────────
        try:
            from question_analyzer import analyze_question
            intent = analyze_question(enriched)
        except Exception:
            intent = None

        # ── 1b. RAISONNEMENT AVANCÉ : contrefactuel / syllogistique ──────────
        # Si la question est contrefactuelle, router vers le CounterfactualReasoner
        if intent is None or self._is_counterfactual(question):
            try:
                cf_response = self.engine.reason_counterfactual(enriched)
                if cf_response:
                    self.conversation.add("user", question)
                    self.conversation.add("assistant", cf_response)
                    return cf_response
            except Exception:
                pass

        # ── 2-3. Recherche de faits ──────────
        try:
            from inverted_index import InvertedIndex
            from harmonic_quality import rerank
            
            if not hasattr(self, '_idx') or self._idx is None:
                self._idx = InvertedIndex(self.model.knowledge_base)
            
            facts = self._idx.search(enriched, max_results=10)
            if facts:
                facts = rerank(enriched, facts, top_k=3)
        except Exception:
            facts = self._retrieve_facts(enriched, intent)
        bloc = None
        contexte_precedent = getattr(self, '_contexte_precedent', None)
        if self._enricher and intent:
            # Passer le type de question pour le nuancing (blocs segmentés)
            bloc = self._enricher.get_bloc(intent.sujet, intent.type)

        # ── 4. Composition de réponse : composer harmonique (chain-of-thought) ──
        response = None
        eff_lang = lang if 'lang' in dir() else 'fr'
        
        # PRIORITÉ : utiliser le composeur harmonique (chain-of-thought + post-process)
        if facts:
            try:
                from harmonic_quality import compose_answer, post_process
                response = compose_answer(question, facts, lang=eff_lang)
                response = post_process(response, lang=eff_lang)
            except Exception:
                response = None
        
        # FALLBACK : ancien ResponseComposer si le nouveau échoue
        if (not response or len(response) < 10) and intent and (facts or bloc):
            try:
                from response_composer import ResponseComposer
                if self._composer is None:
                    self._composer = ResponseComposer()
                if hasattr(self._composer, 'set_language'):
                    self._composer.set_language(eff_lang)
                response = self._composer.compose(
                    intent, facts, bloc,
                    contexte_precedent=contexte_precedent
                )
            except Exception:
                response = None

        # ── 4b. RAISONNEMENT MULTI-ÉTAPES (coherent_transitivity) ────────
        if not response or len(response) < 20:
            try:
                from coherent_transitivity import coherent_transitive_closure
                paths = coherent_transitive_closure(
                    self.model.knowledge_base, enriched,
                    max_depth=3, min_coherence=0.4
                )
                if paths:
                    # Composer une réponse à partir des chemins trouvés
                    from harmonic_quality import compose_answer
                    flat_facts = []
                    for path in paths[:2]:
                        flat_facts.extend(path)
                    if flat_facts:
                        response = compose_answer(enriched, flat_facts[:5], lang=eff_lang)
            except Exception:
                pass

        # ── 4c. GÉNÉRATION HOLOGRAPHIQUE (fast_resonance_generator) ──────
        if not response or len(response) < 20:
            try:
                from fast_resonance_generator import FastResonanceGenerator
                if not hasattr(self, '_resgen') or self._resgen is None:
                    self._resgen = FastResonanceGenerator(
                        self.model.knowledge_base,
                        encoder=getattr(self.model, '_encoder', None)
                    )
                resp = self._resgen.generate(enriched)
                if resp and len(resp) > 15:
                    response = resp
            except Exception:
                pass
        # Si le compositeur n'a pas produit de réponse satisfaisante,
        # essayer le décodeur ondulatoire pur
        if not response or len(response) < 15:
            try:
                from wave_decoder import WaveDecoder
                if not hasattr(self, '_decoder') or self._decoder is None:
                    encoder = getattr(self.model, '_encoder', None)
                    if encoder is not None:
                        self._decoder = WaveDecoder(
                            encoder, self.model.knowledge_base, vocab_limit=3000
                        )
                    else:
                        self._decoder = None
                if self._decoder is not None:
                    decoded = self._decoder.decode_rich(enriched)
                    if decoded and len(decoded) > 10:
                        response = decoded
            except Exception:
                pass

        # Fallback : ancien pipeline (StyleEngine)
        if not response or len(response) < 15:
            try:
                response = self.engine.reason(enriched, max_depth=2)
            except Exception:
                response = self.model.ask(enriched)

        # ── 5. Fallback LLM si confiance faible ─────────────────────────────
        if self.bootstrapper is not None:
            confidence = self._confidence_score(response, enriched)
            if confidence < 0.35:
                try:
                    llm_text = self.bootstrapper._llm_fallback(enriched)
                    if llm_text:
                        response = llm_text
                        # Apprendre de la réponse LLM
                        from bootstrapper import extract_triples_simple
                        triples = extract_triples_simple(llm_text)
                        for s, r, o, sec in triples:
                            self.model.knowledge_base.append((s, r, o, sec))
                        if triples:
                            self.model.rebuild_waves()
                            self.engine = ReasoningEngine(self.model)
                        # 🔥 AUTO-ENRICHISSEMENT : stocker la réponse LLM comme bloc permanent
                        if self._enricher and intent:
                            # Si le sujet n'a pas encore de bloc → enrichir une fois pour toutes
                            if not self._enricher.has_bloc(intent.sujet):
                                self._enricher.enrich_from_llm(
                                    intent.sujet, llm_text, intent.type
                                )
                except Exception:
                    pass
            # 🔥 AUTO-ENRICHISSEMENT sans LLM : si confiance moyenne (0.35-0.5)
            # et pas de bloc → marquer le sujet pour enrichissement futur
            elif self._enricher and intent:
                if not self._enricher.has_bloc(intent.sujet) and confidence < 0.5:
                    # Stocker la meilleure réponse harmonique comme bloc de base
                    if len(response) > 100:
                        self._enricher.enrich_curated(intent.sujet, response, intent.type)

        # ── POST-PROCESSING QUALITÉ (langue, format, capitalisation) ──
        try:
            from harmonic_quality import post_process
            eff_lang = lang if 'lang' in dir() else 'fr'
            response = post_process(response, lang=eff_lang)
        except Exception:
            pass

        # Enregistrer dans la mémoire conversationnelle
        self.conversation.add("user", question)
        self.conversation.add("assistant", response)

        # Correction orthographique finale
        try:
            from style_engine import _fix_accents
            response = _fix_accents(response)
        except ImportError:
            pass

        return response

    def _is_counterfactual(self, question: str) -> bool:
        """Détecte si une question est contrefactuelle."""
        q = question.lower().strip()
        cf_markers = [
            'que se passerait-il si', 'que se passerait il si',
            'qu arriverait-il si', 'qu arriverait il si',
            'et si ', 'que ferait', 'comment serait',
            'imagine si', 'imaginons si', 'supposons que',
            'si on changeait', 'si on modifiait',
            'what would happen if', 'what if',
            'in a world where',
        ]
        return any(q.startswith(m) for m in cf_markers)

    def _init_decoder(self):
        """Initialise le décodeur ondulatoire avec mémoire holographique enrichie."""
        try:
            from wave_decoder import WaveDecoder
            encoder = getattr(self.model, '_encoder', None)
            if encoder is None:
                from holographic_encoder import HolographicEncoder
                encoder = HolographicEncoder(dim=512)
            
            self._decoder = WaveDecoder(
                encoder, self.model.knowledge_base, vocab_limit=3000
            )
            
            # Injecter les blocs curated dans la mémoire holographique
            self._inject_curated_into_decoder()
            
        except Exception:
            self._decoder = None
    
    def _inject_curated_into_decoder(self):
        """Injecte les blocs curated comme ondes boostées avec leurs segments typés."""
        if not self._decoder or not self._enricher:
            return
        
        try:
            from holographic_memory import HolographicMemory
            hmem = HolographicMemory(self._decoder.encoder, dim=self._decoder.encoder.dim)
            
            curated_subjects = set()
            for sujet, entry in self._enricher._blocs.items():
                sujet_lower = sujet.lower().strip()
                curated_subjects.add(sujet_lower)
                
                # Injecter chaque segment (definition, mecanisme, importance, historique)
                if 'definition' in entry:
                    hmem.inject_curated_block(sujet, entry['definition'], boost=3.0, segment_type='definition')
                    if entry.get('mecanisme'):
                        hmem.inject_curated_block(sujet, entry['mecanisme'], boost=2.5, segment_type='mecanisme')
                    if entry.get('importance'):
                        hmem.inject_curated_block(sujet, entry['importance'], boost=2.5, segment_type='importance')
                    if entry.get('historique'):
                        hmem.inject_curated_block(sujet, entry['historique'], boost=2.0, segment_type='historique')
                elif 'bloc' in entry:
                    hmem.inject_curated_block(sujet, entry['bloc'], boost=3.0, segment_type='definition')
            
            # Stocker la KB avec boost pour les sujets curated
            hmem.store_kb_weighted(
                self.model.knowledge_base,
                curated_subjects=curated_subjects,
                boost=5.0
            )
            
            hmem.build_vocab()
            self._decoder._hmem = hmem
            
        except Exception:
            pass

    def _retrieve_facts(self, question: str, intent=None) -> list:
        """
        Récupère les faits pertinents pour une question.
        Priorise les faits dont le sujet OU l'objet correspond à la question.
        """
        facts = []
        q_keywords = set(intent.mots_cles) if intent else set()
        q_sujet = intent.sujet.lower().strip() if intent else ''

        # 1. Recherche par sujet ET objet (PRIORITAIRE)
        # Extraire les mots de la relation recherchée (capitale, ecrit, decouvert, etc.)
        rel_keywords = set()
        rel_patterns = ['capitale', 'écrit', 'ecrit', 'écrite', 'ecrite', 'decouvert',
                        'découvert', 'inventé', 'invente', 'créé', 'cree', 'fondé',
                        'fonde', 'composé', 'compose', 'peint', 'construit',
                        'capital', 'author', 'wrote', 'discovered', 'invented',
                        'fondateur', 'president', 'roi', 'reine', 'empereur']
        for rp in rel_patterns:
            if rp in question.lower():
                rel_keywords.add(rp)
        
        if q_keywords or q_sujet or rel_keywords:
            scored = []
            for s, r, o, sec in self.model.knowledge_base:
                s_lower = s.lower().strip()
                o_lower = o.lower()
                r_lower = r.lower()
                score = 0
                # Score TRÈS élevé si la relation du fait correspond à la question
                for rk in rel_keywords:
                    if rk in r_lower or rk in s_lower:
                        score += 12  # Fort boost pour la bonne relation
                # Score si le sujet du fait correspond exactement
                if q_sujet and s_lower == q_sujet:
                    score += 10
                # Score si le sujet contient le sujet de la question
                elif q_sujet and q_sujet in s_lower:
                    score += 6
                # Score si l'OBJET contient le sujet de la question
                elif q_sujet and q_sujet in o_lower:
                    score += 5
                # Score si un mot-clé est dans l'objet
                for kw in q_keywords:
                    if kw in o_lower:
                        score += 4
                    elif kw in s_lower:
                        score += 3
                    elif kw in r_lower:
                        score += 2
                if score >= 3:
                    scored.append((score, (s, r, o, sec)))

            if scored:
                scored.sort(key=lambda x: -x[0])
                seen = set()
                for score, fact in scored:
                    if fact[0] not in seen:
                        facts.append(fact)
                        seen.add(fact[0])
                    if len(facts) >= 5:
                        break

        # 2. Compléter avec find_paths si pas assez de faits directs
        if len(facts) < 3:
            try:
                from reasoning_engine import find_paths
                paths = find_paths(self.model.knowledge_base, question,
                                 max_depth=2, max_paths=2,
                                 encoder=getattr(self.model, '_encoder', None))
                if paths:
                    existing_sujets = {f[0] for f in facts}
                    for f in paths[0]:
                        if f[0] not in existing_sujets:
                            facts.append(f)
                            existing_sujets.add(f[0])
                        if len(facts) >= 5:
                            break
            except Exception:
                pass

        return facts[:7]

    def _search_facts_by_keywords(self, keywords: list, existing: list) -> list:
        """Recherche directe de faits par mots-clés (complément à find_paths)."""
        results = []
        existing_sujets = {f[0] for f in existing}
        seen = set()

        for kw in keywords:
            if len(kw) < 3:
                continue
            kw_lower = kw.lower()
            for s, r, o, sec in self.model.knowledge_base:
                if (s, r, o, sec) in seen:
                    continue
                if s in existing_sujets:
                    continue
                # Match si le keyword est dans le sujet, la relation ou l'objet
                if kw_lower in s.lower() or kw_lower in o.lower():
                    results.append((s, r, o, sec))
                    seen.add((s, r, o, sec))
                    existing_sujets.add(s)
                    if len(results) >= 4:
                        return results

        return results
    
    def _enrich_with_context(self, question: str) -> str:
        """
        Enrichit une question avec le sujet de la conversation.
        UNIQUEMENT pour les questions de suivi (follow-up), pas pour
        les nouvelles questions indépendantes.

        Détection de follow-up :
          - La question est très courte (<= 3 mots)
          - OU commence par un connecteur de suivi (et, donc, alors, mais)
        """
        recent = self.conversation.messages[-6:] if self.conversation.messages else []
        if not recent:
            self._contexte_precedent = None
            return question

        q_words = question.lower().split()
        q_clean = question.lower().strip('?.,!;: ')

        # Détecter si c'est un vrai follow-up
        # Une question indépendante (même courte) n'est PAS un follow-up
        # Un follow-up typique : "et comment ?", "pourquoi ?", "donc ?"
        is_followup = False

        # Une question qui commence par un mot interrogatif complet est
        # une NOUVELLE question, pas un follow-up
        new_question_starters = (
            'explique', 'decris', 'parle', 'donne', 'definis',
            'pourquoi', 'comment', 'quand', 'quelle', 'quel', 'quels',
            'qu est', 'qu\'est', 'c est quoi', 'c\'est quoi',
            'what', 'how', 'why', 'who', 'when', 'where', 'explain',
        )
        q_stripped = q_clean.strip('?.,!;: ')
        if any(q_stripped.startswith(s) for s in new_question_starters):
            self._contexte_precedent = None
            return question  # Nouvelle question, pas un follow-up

        if len(q_words) <= 3:
            is_followup = True
        elif q_stripped.startswith(('et ', 'donc ', 'alors ', 'mais ', 'du coup ',
                                    'et comment ', 'et pourquoi ')):
            is_followup = True

        if not is_followup:
            return question

        # Trouver les mots-clés de la dernière question USER
        last_user_q = None
        for msg in reversed(recent):
            if msg.role == "user":
                last_user_q = msg.content
                break

        if last_user_q:
            from question_analyzer import analyze_question
            try:
                prev_intent = analyze_question(last_user_q)
                if prev_intent.sujet:
                    # Stocker le sujet précédent pour l'adaptation contextuelle
                    self._contexte_precedent = prev_intent.sujet
                    # Injecter le sujet précédent dans la question
                    sujet_precedent = prev_intent.sujet
                    # Limiter à 3 mots max
                    sujet_precedent = ' '.join(sujet_precedent.split()[:3])
                    return f"{question} (contexte: {sujet_precedent})"
            except Exception:
                pass
            self._contexte_precedent = None

        return question
    
    def reason(self, question: str) -> str:
        """Chaîne de raisonnement avec style élégant."""
        return self.engine.reason(question)
    
    # ═══════════════════════════════════════════════════════════════════
    # CRÉATIVITÉ (dialogue conscient/inconscient)
    # ═══════════════════════════════════════════════════════════════════
    
    def create(self, n: int = 5) -> List[str]:
        """Connexions créatives entre domaines par dialogue conscient/inconscient."""
        try:
            from creative_dialogue import CreativeDialogue
            from inverted_index import InvertedIndex
            if not hasattr(self, '_creative_dialogue') or self._creative_dialogue is None:
                idx = InvertedIndex(self.model.knowledge_base)
                self._creative_dialogue = CreativeDialogue(self.model.knowledge_base, retriever=idx)
            
            # Le dialogue crée des connexions
            question = "trouve des connexions creatives entre differents domaines de connaissance"
            facts, intention, score = self._creative_dialogue.create(
                question, max_iterations=3
            )
            
            # Composer les réponses créatives
            results = []
            for fact in facts[:n]:
                results.append(self._creative_dialogue.compose_creative(
                    question, [fact], intention
                ))
            return results if results else self.engine.create(n_ideas=n)
        except Exception:
            return self.engine.create(n_ideas=n)
    
    def create_ondulatoire(self, concept_a: str = None, concept_b: str = None, n: int = 3) -> List[str]:
        """Créativité ondulatoire profonde par dialogue conscient/inconscient."""
        try:
            from creative_dialogue import CreativeDialogue
            from inverted_index import InvertedIndex
            if not hasattr(self, '_creative_dialogue') or self._creative_dialogue is None:
                idx = InvertedIndex(self.model.knowledge_base)
                self._creative_dialogue = CreativeDialogue(self.model.knowledge_base, retriever=idx)
            
            question = f"trouve une connexion creative entre {concept_a or 'tout'} et {concept_b or 'tout'}"
            facts, intention, score = self._creative_dialogue.create(
                question, max_iterations=4
            )
            
            results = []
            for fact in facts[:n]:
                results.append(self._creative_dialogue.compose_creative(
                    question, [fact], intention
                ))
            return results if results else self.engine.create_ondulatoire(concept_a, concept_b, n_idees=n)
        except Exception:
            return self.engine.create_ondulatoire(concept_a, concept_b, n_idees=n)
    
    def metaphor(self, n: int = 5) -> List[str]:
        """Métaphores poétiques par interférence créative."""
        try:
            from creative_dialogue import CreativeDialogue
            from inverted_index import InvertedIndex
            if not hasattr(self, '_creative_dialogue') or self._creative_dialogue is None:
                idx = InvertedIndex(self.model.knowledge_base)
                self._creative_dialogue = CreativeDialogue(self.model.knowledge_base, retriever=idx)
            
            question = "trouve des metaphores poetiques entre des concepts eloignes"
            facts, intention, score = self._creative_dialogue.create(
                question, max_iterations=5
            )
            
            results = []
            for fact in facts[:n]:
                s, r, o, sec = fact
                results.append(f"✨ {s} est comme {o} : {r}")
            return results if results else self.engine.metaphor(n_metaphores=n)
        except Exception:
            return self.engine.metaphor(n_metaphores=n)
    
    def haiku(self) -> str:
        """Haïku généré par résonance."""
        return self.engine.haiku()
    
    def surreal(self, n: int = 4) -> List[str]:
        """Images surréalistes par interférence faible."""
        return self.engine.surreal(n_images=n)
    
    # ═══════════════════════════════════════════════════════════════════
    # APPRENTISSAGE
    # ═══════════════════════════════════════════════════════════════════
    
    def learn(self, sujet: str, relation: str = None, objet: str = None,
              secteur: str = "GENERAL"):
        """
        Apprend un nouveau fait.
        
        Forme simple : ai.learn("Marie Curie a decouvert le radium", "PHYSIQUE_FOND")
        Forme complète : ai.learn("lumiere", "est", "onde electromagnetique", "PHYSIQUE_FOND")
        """
        if relation is None:
            # Forme simple : extraire automatiquement
            from bootstrapper import extract_triples_simple
            triples = extract_triples_simple(sujet)
            for s, r, o, sec in triples:
                self.model.learn(s, r, o, sec)
        else:
            self.model.learn(sujet, relation, objet, secteur)
    
    def ingest(self, corpus_dir: str, max_files: int = None):
        """
        Ingestion massive depuis un répertoire de textes.
        Utilise DeepSeek pour l'extraction de triplets.
        """
        from bootstrapper import HarmonicBootstrapper
        boot = HarmonicBootstrapper()
        n = boot.ingest_corpus(corpus_dir, max_files=max_files or 50)
        # Mettre à jour le modèle avec les nouveaux faits
        for s, r, o, sec in boot.model.knowledge_base:
            if (s, r, o, sec) not in self.model.knowledge_base:
                self.model.knowledge_base.append((s, r, o, sec))
        self.model.kx, self.model.ky, self.model.w2i = build_waves(
            self.model.knowledge_base
        )
        return n
    
    # ═══════════════════════════════════════════════════════════════════
    # PERSISTANCE
    # ═══════════════════════════════════════════════════════════════════
    
    def save(self, path: str):
        """Sauvegarde complète du modèle."""
        data = {
            'knowledge_base': self.model.knowledge_base,
            'kx': self.model.kx.tolist() if hasattr(self.model.kx, 'tolist') else self.model.kx,
            'ky': self.model.ky.tolist() if hasattr(self.model.ky, 'tolist') else self.model.ky,
            'word_to_id': self.model.w2i,
            'memoire_H_real': self.model.memoire.H.real.tolist() if self.model.memoire else [],
            'memoire_H_imag': self.model.memoire.H.imag.tolist() if self.model.memoire else [],
            'n_experiences': self.model.memoire.n_experiences if self.model.memoire else 0,
        }
        np.savez(path, **data)
    
    def load(self, path: str):
        """Charge un modèle sauvegardé."""
        data = np.load(path, allow_pickle=True)
        self.model.knowledge_base = list(data['knowledge_base'])
        self.model.kx = np.array(data['kx'])
        self.model.ky = np.array(data['ky'])
        self.model.w2i = dict(data['word_to_id'].item())
        if self.model.memoire and 'memoire_H_real' in data:
            H = np.array(data['memoire_H_real']) + 1j * np.array(data['memoire_H_imag'])
            self.model.memoire.H = H
            self.model.memoire.n_experiences = int(data['n_experiences'])
    
    # ═══════════════════════════════════════════════════════════════════
    # STATS
    # ═══════════════════════════════════════════════════════════════════
    
    @property
    def stats(self) -> dict:
        s = {
            'faits': len(self.model.knowledge_base),
            'vocabulaire': len(self.model.w2i),
            'experiences': self.model.experience_count,
            'energie': round(self.model.memoire.energie, 0) if self.model.memoire and hasattr(self.model.memoire, 'energie') else 0,
        }
        if self.bootstrapper:
            s['autonomie'] = round(self.bootstrapper.autonomie * 100, 1)
            s['llm_calls'] = self.bootstrapper._llm_calls
        return s


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Harmonic AI")
    parser.add_argument('question', nargs='?', help='Question to ask')
    parser.add_argument('--reason', action='store_true', help='Use reasoning mode')
    parser.add_argument('--create', type=int, default=0, help='Generate N creative connections')
    parser.add_argument('--metaphor', type=int, default=0, help='Generate N metaphors')
    parser.add_argument('--haiku', action='store_true', help='Generate a haiku')
    parser.add_argument('--surreal', type=int, default=0, help='Generate N surreal images')
    parser.add_argument('--stats', action='store_true', help='Show stats')
    parser.add_argument('--learn', type=str, help='Learn a fact (text or S|R|O|SEC)')
    parser.add_argument('--save', type=str, help='Save model to path')
    parser.add_argument('--load', type=str, help='Load model from path')
    args = parser.parse_args()
    
    ai = HarmonicAI()
    
    if args.load:
        ai.load(args.load)
        print(f"Model loaded from {args.load}")
    
    if args.learn:
        parts = args.learn.split('|')
        if len(parts) >= 4:
            ai.learn(parts[0], parts[1], parts[2], parts[3])
        else:
            ai.learn(args.learn)
        print(f"Learned: {args.learn[:80]}")
    
    if args.stats:
        print(f"Stats: {ai.stats}")
    
    if args.question:
        if args.reason:
            print(ai.reason(args.question))
        else:
            print(ai.ask(args.question))
    
    if args.create:
        for i, idea in enumerate(ai.create(args.create)):
            print(f"{i+1}. {idea}\n")
    
    if args.metaphor:
        for m in ai.metaphor(args.metaphor):
            print(f"  ✨ {m}")
    
    if args.haiku:
        print(ai.haiku())
    
    if args.surreal:
        for s in ai.surreal(args.surreal):
            print(f"  🎨 {s}")
    
    if args.save:
        ai.save(args.save)
        print(f"Model saved to {args.save}")


if __name__ == '__main__':
    main()
