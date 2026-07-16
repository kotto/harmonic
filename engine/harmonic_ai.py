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

import os, sys, json, time, re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

# Chemin du module
_MODULE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_MODULE_DIR))

from harmonic_model import HarmonicModel, build_waves, KNOWLEDGE_BASE
from reasoning_engine import ReasoningEngine
from style_engine import StyleEngine
from harmonic_brain import HarmonicBrain, BrainResult

# 🐛 Debug du seuil de refus : KA_DEBUG_REFUSAL=1 active des traces stderr
import os as _os, sys as _sys
_KA_DEBUG = bool(_os.environ.get('KA_DEBUG_REFUSAL'))

# 🌐 Web Retriever (optionnel)
_WEB_RETRIEVER = None
try:
    from web_retriever import WebRetriever
    _WEB_RETRIEVER = WebRetriever()
except Exception:
    pass


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
    
    def __init__(self, use_memory: bool = True, enable_bootstrapper: bool = True,
                 fast_mode: bool = True):
        """
        Args:
            use_memory: active la mémoire conversationnelle
            enable_bootstrapper: active le bootstrapper LLM (fallback payant)
            fast_mode: skip le chargement du KB étendu (utilise PageForge à la place)
        """
        self.model = HarmonicModel(use_memory=use_memory)
        self.engine = ReasoningEngine(self.model)
        
        if not fast_mode:
            self._load_extended_kb()
            self._load_general_knowledge()
        
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

        # 🔥 CERVEAU HARMONIQUE (Inconscient massif + Conscient filtre) — lazy init
        self._brain = None
        self._brain_init_attempted = False

        # 📄 PAGEFORGE — génération de pages longues (lazy init)
        self._page_forge = None
        self._current_page = None  # Page en cours d'édition conversationnelle
        self._current_page_topic = None

        # 🌊 J-LENS — visualisation de l'espace de raisonnement
        self.jlens = None
        try:
            from harmonic_jlens import JLens
            self.jlens = JLens()
        except ImportError:
            pass

    def _get_brain(self):
        """Initialise paresseusement le cerveau harmonique."""
        if self._brain is not None:
            return self._brain
        if self._brain_init_attempted:
            return None
        self._brain_init_attempted = True
        try:
            self._brain = HarmonicBrain(self.model.knowledge_base)
        except Exception:
            self._brain = None
        return self._brain

    def _rebuild_brain(self):
        """Reconstruit le cerveau après apprentissage."""
        self._brain_init_attempted = False
        self._brain = None
        return self._get_brain()

    def _get_page_forge(self):
        """Initialise paresseusement PageForge."""
        if self._page_forge is None:
            try:
                from page_forge import PageForge
                self._page_forge = PageForge()
            except Exception:
                self._page_forge = False
        return self._page_forge if self._page_forge is not False else None

    def _fast_retrieve(self, question: str, lang: str = 'fr') -> tuple:
        """
        Requête rapide : SFT d'abord, puis FastRetriever.
        Retourne (réponse, liste_de_faits) — les faits servent au J-Lens.
        """
        q_lower = question.lower().strip()
        
        # Stopwords à ignorer
        _sw = {'le','la','les','de','des','du','un','une','et','est','a','que','qui',
               'quoi','dans','sur','pour','avec','par','en','the','is','are','of','in',
               'on','at','to','and','it','its','pas','plus','tout','tous','ce','cet',
               'cette','ces','son','sa','ses','leur','leurs','au','aux','ou','donc',
               'car','aussi','mais','comme','bien','très','trop','peu','alors','the',
               'à','a','y','en','se','ne','me','te','lui','nous','vous'}
        
        # 1. SFT DIRECT MATCH
        try:
            from harmonic_quality import HIGH_AMPLITUDE_FACTS
            best_sft = None
            best_score = 0
            
            q_words = {w.strip('?!.,;:()[]{}»«\"\'') for w in q_lower.split() 
                      if w.strip('?!.,;:()[]{}»«\"\'') not in _sw 
                      and len(w.strip('?!.,;:()[]{}»«\"\'')) > 1}
            
            for (s, r, o), amp in HIGH_AMPLITUDE_FACTS.items():
                s_low = s.lower()
                o_low = o.lower()
                o_words = {w.strip('?!.,;:()[]{}»«\"\'') for w in o_low.split() 
                          if w.strip('?!.,;:()[]{}»«\"\'') not in _sw 
                          and len(w.strip('?!.,;:()[]{}»«\"\'')) > 1}
                
                common = o_words & q_words
                if not common:
                    continue
                
                score = len(common) * amp * 2
                
                s_words = {w.strip('?!.,;:()[]{}»«\"\'') for w in s_low.split() 
                          if w.strip('?!.,;:()[]{}»«\"\'') not in _sw 
                          and len(w.strip('?!.,;:()[]{}»«\"\'')) > 1}
                if s_words & q_words:
                    score += amp
                
                if score > best_score:
                    best_score = score
                    best_sft = (s, r, o)
            
            if best_sft and best_score >= 10:
                s, r, o = best_sft
                facts = [(s, r, o, 'SFT', best_score)]
                return f"{s} {r} {o}.", facts
        except ImportError:
            pass
        
        # 2. FastRetriever fallback
        try:
            from page_forge import _init_fast_retriever, _FAST_RETRIEVER
            _init_fast_retriever()
            if _FAST_RETRIEVER is None:
                return None, []
            
            results = _FAST_RETRIEVER.retrieve(question, max_facts=3, min_score=0.6)
            if not results:
                return None, []

            facts = [(s, r, o, sec, score) for s, r, o, sec, score in results[:3]]
            s, r, o, sec, score = results[0]
            return f"{s} {r} {o}.", facts
        except Exception:
            pass

        return None, []

    def _deep_reason(self, question: str, facts: list, lang: str = 'fr') -> str:
        """
        Raisonnement profond multi-couche :
        1. WaveLogic — syllogismes (7 types)
        2. PhaseAmplifier — propagation multi-sauts via FastRetriever
        3. JLens feedback — renforcement des faits utiles
        """
        response = None
        
        # 1. SYLLOGISMES ONDULATOIRES (WaveLogic)
        if len(facts) >= 2:
            try:
                from wave_logic import WaveLogic
                wl = WaveLogic()
                premises = [(str(s), str(r), str(o)) for s, r, o, _ in facts[:2]]
                result = wl.solve(premises, question)
                if result and len(str(result)) > 20:
                    response = f"🧠 {result}"
            except Exception:
                pass
        
        # 2. PROPAGATION MULTI-SAUTS via FastRetriever
        if not response and len(facts) >= 3:
            try:
                # Propagation simple : chaîne à travers les faits trouvés
                chain = []
                visited = set()
                current = str(facts[0][2])  # objet du premier fait
                
                for _ in range(5):  # max 5 sauts
                    if current in visited:
                        break
                    visited.add(current)
                    
                    # Chercher un fait dont le sujet contient le concept courant
                    from page_forge import _init_fast_retriever, _FAST_RETRIEVER
                    _init_fast_retriever()
                    if _FAST_RETRIEVER:
                        results = _FAST_RETRIEVER.retrieve(current, max_facts=1, min_score=0.4)
                        if results:
                            s, r, o, sec, score = results[0]
                            chain.append(f"{s} {r} {o}")
                            current = str(o)
                        else:
                            break
                
                if len(chain) >= 2:
                    response = (
                        f"🔍 Raisonnement en {len(chain)} sauts: "
                        + ' → '.join(chain[:5])
                    )
            except Exception:
                pass
        
        # 3. J-LENS FEEDBACK
        # ⚠️ AVANT : on mutait HIGH_AMPLITUDE_FACTS en place, ce qui (a) rendait les
        # réponses non-déterministes selon l'ordre des questions, et (b) écrasait les
        # amplitudes SFT originales (ex: 20.0, 50.0) vers le plafond 10.0 — sous le
        # seuil de 15.0 de l'exemption SFT, provoquant des over-refusals en cascade
        # sur "capitale du Japon", "plus grand océan", etc.
        # On logge désormais le renforcement dans jlens sans toucher au dictionnaire
        # source curé. Le renforcement réel (si voulu) doit aller dans un store séparé.
        if self.jlens and facts:
            try:
                if hasattr(self.jlens, 'record_reinforcement'):
                    for s, r, o, sec, score in facts:
                        self.jlens.record_reinforcement(
                            (str(s), str(r), str(o)), float(score))
            except Exception:
                pass
        
        return response

    def _simple_code(self, question: str) -> str:
        """Generation de code par patterns simples (fallback rapide)."""
        q = question.lower()
        if 'fibonacci' in q:
            return '```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n\nfor i in range(10):\n    print(fibonacci(i), end=\" \")\n# 0 1 1 2 3 5 8 13 21 34\n```'
        if 'factorielle' in q or 'factorial' in q:
            return '```python\ndef factorielle(n):\n    if n <= 1:\n        return 1\n    return n * factorielle(n-1)\n\nprint(factorielle(5))  # 120\n```'
        if 'tri ' in q or 'trier' in q or 'sort' in q:
            return '```python\ndef tri_rapide(arr):\n    if len(arr) <= 1:\n        return arr\n    pivot = arr[len(arr)//2]\n    gauche = [x for x in arr if x < pivot]\n    milieu = [x for x in arr if x == pivot]\n    droite = [x for x in arr if x > pivot]\n    return tri_rapide(gauche) + milieu + tri_rapide(droite)\n\nprint(tri_rapide([3,6,8,10,1,2,1]))\n# [1,1,2,3,6,8,10]\n```'
        if 'palindrome' in q:
            return '```python\ndef est_palindrome(s):\n    s = \"\".join(c.lower() for c in s if c.isalnum())\n    return s == s[::-1]\n\nprint(est_palindrome(\"Radar\"))  # True\n```'
        if 'python' in q or 'code' in q:
            return '```python\ndef exemple():\n    return \"Hello, Monde Harmonique!\"\nprint(exemple())\n```'
        return None

    def _route_specialized(self, question: str, lang: str = 'fr') -> str:
        """
        Route la question vers le composant spécialisé approprié :
        - Code → code_generator.py
        - Maths → wave_math.py
        - Logique → wave_logic.py
        """
        q = question.lower().strip()
        
        # 1. CODE — détection de demande de code
        code_markers = ['écris du code', 'ecris du code', 'génère du code', 'genere du code',
                       'code pour', 'fonction qui', 'classe qui', 'algorithme',
                       'write code', 'generate code', 'function that', 'class that',
                       'python', 'javascript', 'html', 'css', 'sql',
                       'crée un programme', 'cree un programme', 'programme qui']
        if any(m in q for m in code_markers) or q.startswith(('code ', 'programme ')):
            try:
                from code_generator import CodeGenerator
                cg = CodeGenerator()
                result = cg.generate(question, lang)
                if result and result.code:
                    return f"```{result.language or 'python'}\n{result.code}\n```\n\n{result.explanation or ''}"
            except Exception:
                pass
        
        # 2. MATHS — résolution d'expressions
        math_markers = ['calcule', 'combien font', 'résous', 'resous', 'solve',
                       'racine carrée', 'factorielle', 'puissance',
                       '+', '-', '*', '/', '×', '÷', '^',
                       'équation', 'equation', 'pourcentage', 'convertir']
        has_numbers = any(c.isdigit() for c in q)
        has_math_symbols = any(s in q for s in ['+', '-', '*', '/', '×', '÷', '=', '^'])
        if has_numbers or has_math_symbols or any(m in q for m in math_markers):
            try:
                from wave_math import wave_solve
                result = wave_solve(question, lang)
                if result:
                    return result
            except Exception:
                pass
            # Fallback: smart_math déjà appelé dans ask(), mais wave_solve est plus complet
        
        # 3. SYLLOGISMES — si la question implique une déduction logique
        logic_markers = ['si ', 'alors ', 'donc ', 'implique', 'par conséquent',
                        'si...alors', 'déduis', 'deduis', 'conclus', 'raisonne']
        if any(m in q for m in logic_markers) or q.count('si ') >= 1:
            try:
                from wave_logic import WaveLogic
                wl = WaveLogic()
                # Extraire les prémisses potentielles
                parts = re.split(r'[?.!]', question)
                premises = [p.strip() for p in parts if len(p.strip()) > 10]
                if len(premises) >= 2:
                    result = wl.solve(premises[:2], question)
                    if result and len(str(result)) > 15:
                        return f"🧠 {result}"
            except Exception:
                pass
        
        return None

    def _merite_page(self, question: str) -> bool:
        """
        Détecte si une question mérite une réponse longue (page) 
        plutôt qu'une réponse courte (2-3 phrases).
        """
        q = question.lower().strip()
        
        # Marqueurs explicites de demande de page longue
        page_markers = [
            'explique', 'décris', 'decris', 'parle-moi de', 'parle moi de',
            'dis-moi tout', 'dis moi tout', 'raconte', 'détaille', 'detaille',
            'tout sur', 'tout savoir sur', 'comment fonctionne',
            'qu\'est-ce que', 'qu est-ce que', 'c\'est quoi', 'c est quoi',
            'en quoi consiste', 'pourquoi', 'comment',
        ]
        if any(m in q for m in page_markers):
            return True
        
        # Questions longues (> 40 caractères) = probablement complexes
        if len(q) > 60:
            return True
        
        # Questions avec plusieurs points d'interrogation ou plusieurs phrases
        if q.count('?') >= 2 or q.count('.') >= 2:
            return True
        
        return False

    def page(self, topic: str, doc_type: str = 'article') -> str:
        """
        Génère une page complète sur un sujet.
        """
        forge = self._get_page_forge()
        if forge is None:
            return None
        try:
            self._current_page = forge.generate(topic, doc_type)
            self._current_page_topic = topic
            return forge.to_markdown(self._current_page)
        except Exception:
            return None

    def _detect_edit_command(self, question: str) -> dict:
        """
        Détecte si la question est une commande d'édition sur la page en cours.
        Retourne un dict {action, target, params} ou None.
        """
        q = question.lower().strip()
        
        # Commandes d'édition
        patterns = [
            (r"(?:développe|developpe|détaille|detail|plus sur)\s+(?:la\s+)?(?:section\s+)?(.+)", 'expand'),
            (r"(?:résume|resume|condense|raccourci)\s+(?:la\s+)?(?:section\s+)?(.+)", 'condense'),
            (r"(?:reformule|réécris|reecris|change)\s+(?:la\s+)?(?:section\s+)?(.+)", 'rephrase'),
            (r"(?:ajoute|ajouter|nouvelle)\s+(?:une\s+)?(?:section\s+)?(.+)", 'add_section'),
            (r"(?:supprime|enlève|enleve|retire)\s+(?:la\s+)?(?:section\s+)?(.+)", 'remove'),
            (r"(?:exporte?|sauvegarde?)\s+(?:en\s+)?(md|markdown|html)?", 'export'),
            (r"(?:affiche|montre|voir|lis)\s+(?:la\s+)?(?:page|contenu)", 'show'),
            (r"(?:rends?|fais)\s+(?:le|la|plus|moins)\s*(.+)", 'restyle'),
        ]
        
        import re
        for pattern, action in patterns:
            m = re.search(pattern, q)
            if m:
                return {'action': action, 'target': m.group(1).strip() if m.lastindex else None}
        
        # Si la question est un follow-up court sur le même sujet
        if self._current_page_topic:
            _sw = {'le','la','les','de','des','du','un','une','et','est','a','que','qui',
                   'quoi','dans','sur','pour','avec','par','en','the','is','are','of','in',
                   'pas','plus','tout','ce','cet','cette','ces','son','sa','ses'}
            topic_words = {w for w in self._current_page_topic.lower().split() if w not in _sw and len(w) > 2}
            q_words = {w for w in q.split() if w not in _sw and len(w) > 2}
            overlap = topic_words & q_words
            if len(overlap) >= 2 and len(q) < 50:
                return {'action': 'append_context', 'target': q}
        
        return None

    def _handle_page_edit(self, forge, cmd: dict, question: str) -> str:
        """
        Exécute une commande d'édition sur la page en cours.
        """
        if not self._current_page:
            return None
        
        action = cmd['action']
        target = cmd.get('target', '')
        page = self._current_page
        
        if action == 'expand':
            section = page.get_section(target)
            if section:
                forge.weaver.weave(section, page)
                return f"✅ Section '{section.title}' développée.\n\n{section.content[:300]}..."
            # Si la cible n'est pas une section, générer la page entière
            forge.weaver.weave(page.sections[0], page) if page.sections else None
            return forge.to_markdown(page)
        
        elif action == 'condense':
            section = page.get_section(target)
            if section and section.content:
                sentences = [s.strip() for s in section.content.split('.') if s.strip()]
                section.content = '. '.join(sentences[:2]) + '.'
                section.word_count = len(section.content.split())
                return f"✅ Section '{section.title}' condensée."
            return f"Section '{target}' non trouvée."
        
        elif action == 'rephrase':
            section = page.get_section(target)
            if section:
                forge.weaver.weave(section, page)
                return f"✅ Section '{section.title}' reformulée.\n\n{section.content[:300]}..."
            return f"Section '{target}' non trouvée."
        
        elif action == 'add_section':
            if target:
                new_id = target.lower().replace(' ', '_')[:30]
                from page_forge import Section
                new_sec = Section(id=new_id, title=target, position_angle=1.57)
                concl_idx = page.section_index('conclusion')
                if concl_idx >= 0:
                    page.sections.insert(concl_idx, new_sec)
                else:
                    page.sections.append(new_sec)
                forge.weaver.weave(new_sec, page)
                return f"✅ Section '{target}' ajoutée et générée.\n\n{new_sec.content[:200]}..."
            return "Précisez le titre de la section."
        
        elif action == 'remove':
            idx = page.section_index(target)
            if idx >= 0:
                removed = page.sections.pop(idx)
                return f"✅ Section '{removed.title}' supprimée."
            return f"Section '{target}' non trouvée."
        
        elif action == 'export':
            fmt = target or 'md'
            if fmt in ('html', 'htm'):
                output = forge.to_html(page)
                ext = 'html'
            else:
                output = forge.to_markdown(page)
                ext = 'md'
            filename = f"page_{self._current_page_topic.lower().replace(' ', '_')[:30]}.{ext}"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(output)
            return f"✅ Page exportée : {filename} ({page.total_words()} mots)"
        
        elif action == 'show':
            return forge.to_markdown(page)
        
        elif action == 'restyle':
            style_map = {
                'académique': 'academique', 'academique': 'academique',
                'vulgarisé': 'vulgarise', 'vulgarise': 'vulgarise',
                'poétique': 'poetique', 'poetique': 'poetique',
                'technique': 'technique', 'simple': 'vulgarise',
                'formel': 'academique', 'créatif': 'poetique', 'creatif': 'poetique',
            }
            # Chercher si le target contient un style connu
            found_style = None
            if target:
                for kw, style_val in style_map.items():
                    if kw in target.lower():
                        found_style = style_val
                        break
            if found_style:
                from page_forge import StyleLevel
                page.style.level = StyleLevel(found_style)
                return f"✅ Style changé en '{found_style}'. Ré-générez les sections pour appliquer."
            return f"Styles : académique, vulgarisé, poétique, technique. Actuel : {page.style.level.value}"
        
        elif action == 'append_context':
            # Ajouter du contexte à la page : générer une nouvelle section ou étendre l'intro
            if page.sections:
                intro = page.sections[0]
                intro.content += f"\n\nPrécision : {question}"
                intro.word_count = len(intro.content.split())
                return f"✅ Contexte ajouté à l'introduction."
        
        return None
    
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

        # 🆕 ANTI-HALLUCINATION — détecter les "bon mot, mauvaise entité".
        # Cas type : "capitale du royaume imaginaire de Karpathie" → "Londres est
        # la capitale du royaume uni." Le mot-outil "royaume" matche, mais
        # l'ENTITÉ (le sujet propre, long et spécifique : "karpathie") est absente
        # de la réponse. C'est le pattern #1 d'hallucination par partial-match.
        # On isole les mots-spécifiques longs (>=8 chars, hors lexique générique)
        # et on exige qu'au moins un apparaisse réellement dans la réponse.
        # Seuil >=8 (pas 7) pour ne pas écraser les vraies réponses courtes
        # ("Japon", 5 lettres, n'est pas une "entité longue" → pas de pénalité).
        _GENERIC = {'capitale', 'symbole', 'chimique', 'decouvert', 'ecrit',
                    'compose', 'peint', 'annee', 'population', 'distance',
                    'vitesse', 'temperature', 'masse', 'nombre', 'pourcent',
                    'pourcentage', 'reduction', 'acceleration', 'courant',
                    'force', 'puissance', 'auteur', 'fondateur',
                    'histoire', 'philosophe', 'roman', 'traite',
                    'theorie', 'metal', 'element', 'planete', 'nebuleuse',
                    'ville', 'commune', 'region', 'continent', 'royaume',
                    'republique', 'dynastie', 'opera', 'directeur', 'president',
                    'imaginaire', 'fictive', 'fictif', 'inexistant'}
        entities = [w for w in q_words if len(w) >= 8 and w not in _GENERIC]
        if entities:
            resp_text = response.lower()
            entity_hits = sum(1 for e in entities if e in resp_text)
            # Si AUCUNE entité longue spécifique n'apparaît dans la réponse →
            # très probablement un fait générique récupéré sur un mot-outil.
            # Confiance écrasée pour déclencher le refus calibré (étape 5).
            if entity_hits == 0:
                return 0.15

        # Sinon, confiance basée sur la longueur et couverture
        base = 0.35 + key_ratio * 0.3 + min(0.25, len(response) / 400)
        return min(1.0, base)
    
    def _load_extended_kb(self):
        """Charge la base étendue (100K faits) si disponible."""
        kb_paths = [
            _MODULE_DIR / "data" / "bootstrapper_output" / "knowledge_base_100k.npz",
            _MODULE_DIR / "data" / "bootstrapper_output" / "knowledge_base_resonance.npz",
            _MODULE_DIR / "data" / "bootstrapper_output" / "knowledge_base_50k_cleaned.npz",
            _MODULE_DIR / "data" / "bootstrapper_output" / "knowledge_base_50k.npz",
        ]
        
        for kb_path in kb_paths:
            if kb_path.exists():
                try:
                    data = np.load(str(kb_path), allow_pickle=True)
                    ingested = list(data['facts'])
                    added = 0
                    for fact in ingested:
                        s, r, o, sec = str(fact[0]), str(fact[1]), str(fact[2]), str(fact[3])
                        if (s, r, o, sec) not in self.model.knowledge_base:
                            self.model.knowledge_base.append((s, r, o, sec))
                            added += 1
                    if added > 0:
                        self.model.kx, self.model.ky, self.model.w2i = build_waves(
                            self.model.knowledge_base
                        )
                    print(f"Loaded {added} facts from {kb_path.name}")
                    break
                except Exception as e:
                    print(f"Failed to load {kb_path.name}: {e}")
    
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
        Réponse avec le Pipeline Sémantique Harmonique Unifié.

        Architecture 4-couches :
          0. DomainDetector → fast path (conversation, math, identité)
          1. Retrieval Inconscient (I×P×H×D)
          2. Vérification Consciente + Synthèse ψ_R
          3. Décodage Ondulatoire → langage naturel
          4. Fallback LLM si confiance faible (sevrage progressif)
        """
        # ── 0. DÉTECTION PRÉCOCE ──
        try:
            from domain_detector import (
                detect_question_type, handle_greeting, handle_identity,
                handle_out_of_domain
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
                    is_bye=qtype.get('is_bye', False), lang=lang
                )
                if resp:
                    self.conversation.add("user", question)
                    self.conversation.add("assistant", resp)
                    return resp

            math_result = smart_math(question)
            if math_result:
                self.conversation.add("user", question)
                self.conversation.add("assistant", math_result)
                return math_result

            # 🧠 ROUTAGE SPÉCIALISÉ (code, logique) — avant out_of_domain
            q_lower = question.lower()
            
            # Code
            if any(m in q_lower for m in ['code ', 'programme ', 'fonction ', 'classe ',
                   'écris du code', 'ecris du code', 'python', 'javascript',
                   'algorithme', 'génère du code', 'genere du code']):
                try:
                    from code_generator import CodeGenerator
                    brain = self._get_brain()
                    if brain:
                        cg = CodeGenerator(brain)
                        result = cg.generate(question, lang)
                        if result and result.code:
                            resp = f"```{result.language or 'python'}\n{result.code}\n```"
                            if result.explanation:
                                resp += f"\n\n{result.explanation}"
                            self.conversation.add("user", question)
                            self.conversation.add("assistant", resp[:500])
                            return resp
                except Exception:
                    pass
                # Fallback: code généré par patterns simples
                resp = self._simple_code(question)
                if resp:
                    self.conversation.add("user", question)
                    self.conversation.add("assistant", resp[:500])
                    return resp
            
            # Maths avancées (wave_math en complément de smart_math)
            if not math_result and any(c.isdigit() for c in q_lower):
                try:
                    from wave_math import wave_solve
                    wm_result = wave_solve(question, lang)
                    if wm_result and len(wm_result) > 2:
                        self.conversation.add("user", question)
                        self.conversation.add("assistant", wm_result)
                        return wm_result
                except Exception:
                    pass

            # Logique/Syllogismes
            if any(m in q_lower for m in ['si ', 'alors ', 'donc ', 'implique',
                   'déduis', 'deduis', 'conclus', 'raisonne', 'syllogisme']):
                try:
                    from wave_logic import WaveLogic
                    brain = self._get_brain()
                    wl = WaveLogic(brain) if brain else None
                    if wl:
                        parts = __import__('re').split(r'[?.!]|\bet\b|, que\b|, alors\b', question)
                        premises = [p.strip() for p in parts if len(p.strip()) > 10]
                        if len(premises) >= 2:
                            result = wl.solve(premises[:2], question)
                            if result and len(str(result)) > 10:
                                resp = '🧠 ' + str(result)
                                self.conversation.add('user', question)
                                self.conversation.add('assistant', resp[:500])
                                return resp
                    # Fallback: analyse logique simple sans WaveLogic
                    if 'si ' in q_lower and 'alors' in q_lower:
                        resp = '🧠 Raisonnement déductif détecté. La conclusion logique découle des prémisses.'
                    else:
                        resp = '🧠 Question de logique détectée. Le raisonnement syllogistique nécessite le chargement du cerveau harmonique.'
                    self.conversation.add('user', question)
                    self.conversation.add('assistant', resp[:500])
                    return resp
                except Exception:
                    pass

            if qtype.get('is_out_of_domain'):
                resp = handle_out_of_domain(qtype.get('out_category', ''), lang=lang)
                if resp:
                    self.conversation.add("user", question)
                    self.conversation.add("assistant", resp)
                    return resp
        except ImportError:
            lang = 'fr'

        # ── 0.2. COMMANDE « apprends : » — apprentissage direct ──
        # C'est la boucle de feedback promise par le refus calibré : quand KA dit
        # « Je ne sais pas, apprends-moi », l'utilisateur répond « apprends : <fait> »
        # et le fait est ingéré immédiatement. Prochaine question → KA sait.
        learn_cmd = self._parse_learn_command(question)
        if learn_cmd:
            try:
                self.learn(learn_cmd)
                ack = self._build_learn_ack(learn_cmd, lang)
                self.conversation.add("user", question)
                self.conversation.add("assistant", ack)
                # Notifier le PersonalHologram si câblé
                _ph = getattr(self, '_personal', None)
                if _ph is not None:
                    try:
                        _ph.observe_correction("", learn_cmd)
                    except Exception:
                        pass
                return ack
            except Exception:
                pass  # fall through to normal pipeline

        # Enrichir avec le contexte conversationnel
        enriched = self._enrich_with_context(question)

        # ── 0.3. ROUTAGE INTELLIGENT — code, maths, logique ──
        routed = self._route_specialized(enriched, lang)
        if routed:
            self.conversation.add("user", question)
            self.conversation.add("assistant", routed[:500])
            return routed

        # ── 0.5. PAGEFORGE — page longue ou édition conversationnelle ──
        forge = self._get_page_forge()
        if forge is not None:
            # Détecter si c'est une commande d'édition sur la page en cours
            edit_cmd = self._detect_edit_command(enriched)
            
            if edit_cmd and self._current_page is not None:
                # Commande d'édition sur la page existante
                response = self._handle_page_edit(forge, edit_cmd, enriched)
                if response:
                    self.conversation.add("user", question)
                    self.conversation.add("assistant", response[:500])
                    return response
            
            elif self._merite_page(enriched):
                # Nouvelle demande de page
                try:
                    self._current_page = forge.generate(enriched, 'article')
                    self._current_page_topic = enriched
                    page_text = forge.to_markdown(self._current_page)
                    if page_text and len(page_text) > 150:
                        self.conversation.add("user", question)
                        self.conversation.add("assistant", page_text[:500] + '...')
                        return page_text
                except Exception:
                    pass

        # ── 1-3. PIPELINE SÉMANTIQUE UNIFIÉ ──
        response = None
        confidence = 0.0
        model_trusted = False  # 🆕 True si réponse du modèle direct (KB retrieval)

        # ── 1.0 FAST RETRIEVER — requête directe dans les 28K faits enrichis ──
        # 🆕 Pour les questions "qui" (recherche d'entité spécifique),
        # model.ask() est plus fiable que FastRetriever car il a accès
        # à TOUTE la KB y compris les faits appris récemment.
        is_who_question = any(enriched.lower().strip().startswith(w) for w in
            ('qui ', 'who ', 'qui a ', 'who is ', 'qui est '))
        
        fast_answer, fast_facts = self._fast_retrieve(enriched, lang)
        facts_backed = False
        sft_direct_match = False
        if fast_answer and not is_who_question:
            response = fast_answer
            confidence = 0.60
            facts_backed = bool(fast_facts)
            for f in (fast_facts or []):
                if len(f) >= 5 and f[3] == 'SFT' and f[4] >= 15.0:
                    sft_direct_match = True
                    break
            
            # 🆕 Comparer avec model.ask() qui a la KB complète
            if not sft_direct_match:
                model_resp = self.model.ask(enriched)
                if model_resp and len(model_resp) > 30:
                    q_words = set(enriched.lower().split())
                    fast_words = set(response.lower().split()) if response else set()
                    model_words = set(model_resp.lower().split())
                    missing = q_words - fast_words - {'le','la','les','de','des','du','un','une','et','est','a','que','qui','quoi','dans','sur','pour','avec','par','en'}
                    found_by_model = missing & model_words
                    if len(found_by_model) >= 1 or len(model_resp) > len(response) * 1.3:
                        response = model_resp
                        confidence = 0.55
                        model_trusted = True
                        facts_backed = True
        
        # 🆕 Pour les questions "qui", utiliser directement model.ask()
        if is_who_question:
            model_resp = self.model.ask(enriched)
            if model_resp and len(model_resp) > 20:
                response = model_resp
                confidence = 0.55
                model_trusted = True
                facts_backed = True

        # 🌊 J-LENS : capturer l'instantané
        if self.jlens and fast_facts:
            self.jlens.capture(enriched, facts=fast_facts, confidence=confidence,
                              response=response[:200] if response else '')

        # 🧠 DEEP REASON — raisonnement profond si la réponse est simple.
        # ⚠️ Ne PAS appliquer aux réponses SFT (haute amplitude) : elles sont déjà
        # exactes et complètes. _deep_reason ajoute parfois du bruit (chaîne
        # multi-sauts hors-sujet) qui dégrade le _confidence_score et déclenche
        # un refus abusif (over-refusal) sur des questions légitimes comme
        # "plus grand océan" ou "capitale du Sénégal".
        sft_fact = any(len(f) >= 5 and f[4] >= 15.0 for f in fast_facts) if fast_facts else False
        if (response and fast_facts and len(response.split()) < 15
                and not sft_fact):
            deep = self._deep_reason(enriched, fast_facts, lang)
            if deep:
                response = response + '\n\n' + deep

        # ── 1.5 Cerveau harmonique (fallback si FastRetriever n'a rien trouvé) ──
        if not response and self._get_brain() is not None:
            try:
                result = self._get_brain().process(enriched, lang=lang)
                response = result.response
                confidence = result.confidence
                facts_backed = bool(result.facts_used)  # 🆕

                # Apprentissage automatique si la réponse est bonne
                if result.is_confident and result.facts_used and self._enricher:
                    for s, r, o, sec in result.facts_used[:2]:
                        if not self._enricher.has_bloc(s):
                            # Marquer pour enrichissement futur
                            pass
            except Exception:
                response = None
                confidence = 0.0

        # ── 4. FALLBACK : Web → Raisonnement → LLM (sevrage progressif) ──
        # 🆕 trusted_external : True si la réponse finale vient d'une source externe
        # fiable (web ou LLM). Le seuil de refus (étape 5) ne s'applique PAS à ces
        # réponses — elles portent leur propre provenance. Il ne refuse QUE le
        # retrieval interne non fiable, ce qui rend l'anti-hallucination réelle.
        # 🆕 model_trusted : True si la réponse vient du modèle direct (KB retrieval),
        # ce qui est déterministe et fiable par construction.
        trusted_external = False
        if not response or len(response) < 15 or confidence < 0.35:
            # 4a. Essayer d'abord le raisonnement harmonique classique
            if not response or len(response) < 15:
                try:
                    response = self.engine.reason(enriched, max_depth=2)
                except Exception:
                    response = self.model.ask(enriched)
            
            # 🆕 Si engine.reason() n'a rien donné ou réponse trop courte,
            # essayer model.ask() directement (KB retrieval déterministe)
            if not response or len(response) < 15:
                response = self.model.ask(enriched)
            
            # 🆕 Si model.ask() a trouvé une réponse non triviale, c'est fiable
            if response and len(response) > 30:
                model_trusted = True
                confidence = max(confidence, 0.55)
                facts_backed = True

            # 4b. 🌐 FALLBACK WEB — recherche Internet gratuite
            conf = self._confidence_score(response, enriched) if response else 0.0
            if conf < 0.35 and _WEB_RETRIEVER is not None:
                try:
                    web_summary = _WEB_RETRIEVER.search_quick(enriched)
                    if web_summary and len(web_summary) > 40:
                        response = f"🌐 D'après une recherche web : {web_summary}"
                        confidence = 0.55
                        trusted_external = True
                except Exception:
                    pass

            # 4c. Si toujours pas satisfaisant → LLM (payant, dernière option)
            if self.bootstrapper is not None:
                conf = self._confidence_score(response, enriched) if response else 0.0
                if conf < 0.35:
                    try:
                        llm_text = self.bootstrapper._llm_fallback(enriched)
                        if llm_text:
                            response = llm_text
                            trusted_external = True
                            # Apprendre de la réponse LLM
                            from bootstrapper import extract_triples_simple
                            triples = extract_triples_simple(llm_text)
                            for s, r, o, sec in triples:
                                if (s, r, o, sec) not in self.model.knowledge_base:
                                    self.model.knowledge_base.append((s, r, o, sec))
                            if triples:
                                self.model.rebuild_waves()
                                self.engine = ReasoningEngine(self.model)
                                self._rebuild_brain()
                    except Exception:
                        pass

        # ── POST-PROCESSING ──
        try:
            from harmonic_quality import post_process
            response = post_process(response, lang=lang)
        except Exception:
            pass

        # Correction orthographique
        try:
            from style_engine import _fix_accents
            response = _fix_accents(response)
        except ImportError:
            pass

        # ── 5. SEUIL DE REFUS CALIBRÉ — anti-hallucination structurelle ──
        # C'est le mécanisme qui rend "zéro hallucination" vrai et mesurable :
        # si, après tous les fallbacks, la réponse vient du retrieval interne ET
        # sa confiance est faible → KA refuse d'inventer et propose d'apprendre.
        # Sont EXEMPTÉS du refus (fiables par construction) :
        #   - les sources externes (web 🌐, LLM) — trusted_external
        #   - les matchs SFT directs (capitales, symboles curés) — sft_direct_match.
        #     Un fait SFT qui matche directement la question est vérifié par
        #     construction ; on ne le soumet PAS au re-scoring heuristique
        #     (_confidence_score), qui est instable selon le contexte conversationnel
        #     et peut écraser une bonne réponse exacte.
        recomputed = self._confidence_score(response, enriched) if response else 0.0
        if _KA_DEBUG:
            print(f"[DBG] response={response!r}", file=_sys.stderr)
            print(f"[DBG] sft_direct_match={sft_direct_match} trusted_external={trusted_external} recomputed={recomputed:.3f}", file=_sys.stderr)
        if (not trusted_external and not model_trusted and not sft_direct_match and response):
            # 🆕 Si la réponse est appuyée par des faits réels (retrieval réussi)
            # ET le re-scoring n'est pas catastrophique, on fait confiance à la
            # confiance du pipeline plutôt qu'au re-scoring heuristique (qui peut
            # écraser de bonnes réponses courtes, ex: capitales).
            # MAIS si le re-scoring est très bas (< 0.20), c'est le signal d'une
            # hallucination par partial-match (entité absente) → on garde le score
            # faible pour déclencher le refus.
            if facts_backed and recomputed >= 0.20:
                final_conf = max(recomputed, confidence)
            else:
                final_conf = recomputed
            if final_conf < self.REFUSAL_THRESHOLD:
                refusal = self._build_refusal(enriched, lang)
                self.conversation.add("user", question)
                self.conversation.add("assistant", refusal)
                # Observer le refus dans l'hologramme personnel (centre d'intérêt).
                # getattr : PersonalHologram n'est pas toujours câblé (tests légers),
                # on ne doit jamais planter sur un refus.
                _ph = getattr(self, '_personal', None)
                if _ph is not None:
                    try:
                        _ph.observe_question(question)
                    except Exception:
                        pass
                return refusal

        # Mémoire conversationnelle
        self.conversation.add("user", question)
        self.conversation.add("assistant", response)

        return response

    # Seuil de confiance en dessous duquel KA refuse de répondre (cf. étape 5).
    # Calibration : aligné sur _confidence_score() — sous 0.30, la réponse
    # n'apporte pas d'information fiable au-delà d'un echo de la question.
    REFUSAL_THRESHOLD = 0.30

    def _build_refusal(self, question: str, lang: str = 'fr') -> str:
        """Construit un refus honnête qui invite l'utilisateur à enseigner KA.

        C'est l'inverse d'une hallucination : KA reconnaît explicitement qu'il
        ne sait pas, et transforme l'ignorance en opportunité d'apprentissage
        continu (le principe fondateur du compagnon personnel).
        """
        if lang == 'en':
            return ("I don't know that yet — I'd rather tell you than guess.\n\n"
                    "Teach me: type  « learn: <fact> »  and I'll remember it "
                    "for next time.")
        return ("Je ne sais pas encore cela — je préfère te le dire plutôt "
                "qu'inventer.\n\n"
                "Apprends-moi : tape  « apprends : <fait> »  et je le "
                "mémoriserai pour la prochaine fois.")

    @staticmethod
    def _parse_learn_command(question: str) -> str:
        """Extrait un fait d'une commande d'apprentissage.

        Formes reconnues :
          « apprends : Kigali est la capitale du Rwanda »
          « apprends: <fait> »
          « learn: <fact> »
          « apprend : <fait> »
          « apprends moi : <fait> »

        Retourne le texte du fait (str) ou None si ce n'est pas une commande learn.
        """
        q = question.strip()
        # Patterns classés du plus spécifique au moins spécifique
        patterns = [
            (r'^apprends\s*:\s*', 'apprends :'),
            (r'^apprend\s*:\s*', 'apprend :'),
            (r'^apprends\s+moi\s*:\s*', 'apprends moi :'),
            (r'^learn\s*:\s*', 'learn:'),
            (r'^apprends-moi\s*:\s*', 'apprends-moi :'),
        ]
        import re
        q_lower = q.lower()
        for pattern, _prefix in patterns:
            m = re.match(pattern, q_lower)
            if m:
                fact = q[m.end():].strip()
                if len(fact) >= 5:
                    return fact
        return None

    def _build_learn_ack(self, fact: str, lang: str = 'fr') -> str:
        """Accusé de réception après un apprentissage réussi."""
        short = fact[:80] + ('…' if len(fact) > 80 else '')
        if lang == 'en':
            return (f"✅ I've learned: « {short} ».\n"
                    f"I'll remember it for next time — thank you for teaching me.")
        return (f"✅ J'ai appris : « {short} ».\n"
                f"Je m'en souviendrai la prochaine fois — merci de m'avoir appris !")

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
            if results and any(len(r) > 20 for r in results):
                return results[:n]
        except Exception:
            pass
        
        # Fallback: engine.create
        try:
            engine_results = self.engine.create(n_ideas=n)
            if engine_results and any(len(r) > 20 for r in engine_results):
                return engine_results[:n]
        except Exception:
            pass
        
        # 🆕 Fallback ultime: génération créative directe depuis la KB
        return self._creative_from_kb(n=n)
    
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
            if results and any(len(r) > 10 for r in results):
                return results[:n]
        except Exception:
            pass
        
        # Fallback: engine.metaphor
        try:
            engine_results = self.engine.metaphor(n_metaphores=n)
            if engine_results and any(len(r) > 10 for r in engine_results):
                return engine_results[:n]
        except Exception:
            pass
        
        # 🆕 Fallback ultime: métaphores directes depuis la KB
        return self._creative_from_kb(n=n, mode='metaphor')
    
    def _creative_from_kb(self, n: int = 5, mode: str = 'create') -> List[str]:
        """
        Génération créative/métaphorique directe depuis la KB,
        sans dépendance à l'encodeur ou à ConsciousCreator.
        
        Args:
            n: nombre de résultats
            mode: 'create' (connexions) ou 'metaphor' (métaphores)
        """
        import random
        kb = self.model.knowledge_base
        if len(kb) < 4:
            return ["Pas assez de connaissances pour créer des connexions."]
        
        # Grouper les faits par secteur
        by_sector = {}
        for s, r, o, sec in kb:
            if sec not in by_sector:
                by_sector[sec] = []
            by_sector[sec].append((s, r, o))
        
        sectors = list(by_sector.keys())
        if len(sectors) < 2:
            return ["Pas assez de domaines varies pour créer."]
        
        results = []
        attempts = 0
        while len(results) < n and attempts < n * 10:
            attempts += 1
            # Choisir deux secteurs différents
            sec1, sec2 = random.sample(sectors, 2)
            f1 = random.choice(by_sector[sec1])
            f2 = random.choice(by_sector[sec2])
            s1, r1, o1 = f1
            s2, r2, o2 = f2
            
            if mode == 'metaphor':
                templates = [
                    f"✨ {s1} ({sec1}) est comme {s2} ({sec2}) — tous deux {r1}",
                    f"✨ {s1} et {s2} dansent la meme onde : {r1} rencontre {r2}",
                    f"✨ Si {s1} etait un poeme, {s2} serait sa rime — {r1}",
                    f"✨ L'univers a glisse un secret : {s1} et {s2} partagent l'essence de {r1}",
                ]
                result = random.choice(templates)
            else:
                templates = [
                    f"🌊 Connexion inedite : {s1} ({sec1}) et {s2} ({sec2}). "
                    f"En {sec1}, {s1} {r1} {o1}. En {sec2}, {s2} {r2} {o2}. "
                    f"L'interference de ces deux ondes suggere un pont entre ces univers.",
                    f"🌊 Une resonance inattendue emerge entre {s1} ({sec1}) et {s2} ({sec2}). "
                    f"D'un cote, {s1} {r1} {o1}. De l'autre, {s2} {r2} {o2}. "
                    f"Ces deux concepts vibrent sur des frequences complementaires.",
                ]
                result = random.choice(templates)
            
            if result not in results:
                results.append(result)
        
        return results if results else ["L'univers harmonique est en perpetuelle creation."]

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

    # ═══════════════════════════════════════════════════════════════════
    # 🌐 RECHERCHE WEB
    # ═══════════════════════════════════════════════════════════════════

    def search_web(self, query: str, max_results: int = 5) -> list:
        """
        Recherche sur Internet via DuckDuckGo + Wikipedia.

        Retourne une liste de résultats [{source, title, url, snippet, summary}, ...].
        """
        if _WEB_RETRIEVER is None:
            return [{'error': 'Web retriever non disponible'}]
        return _WEB_RETRIEVER.search_web(query, max_results=max_results)

    def get_news(self, topic: str = None, max_results: int = 5) -> list:
        """Récupère les actualités récentes."""
        if _WEB_RETRIEVER is None:
            return [{'error': 'Web retriever non disponible'}]
        return _WEB_RETRIEVER.get_current_news(topic=topic, max_results=max_results)


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
    parser.add_argument('--web', type=str, help='Search the web for a query')
    parser.add_argument('--news', type=str, help='Get current news (optional topic)')
    parser.add_argument('--stats', action='store_true', help='Show stats')
    parser.add_argument('--learn', type=str, help='Learn a fact (text or S|R|O|SEC)')
    parser.add_argument('--save', type=str, help='Save model to path')
    parser.add_argument('--load', type=str, help='Load model from path')
    args = parser.parse_args()

    # 🌐 --web / --news : rapide, pas besoin de charger le modèle complet
    if args.web or args.news:
        from web_retriever import WebRetriever
        wr = WebRetriever(timeout=10)
        if args.web:
            results = wr.search_web(args.web, max_results=5)
            for i, r in enumerate(results):
                print(f"\n{i+1}. [{r.get('source', 'web')}] {r.get('title', 'Sans titre')}")
                if r.get('snippet'):
                    print(f"   {r['snippet'][:200]}")
                if r.get('url'):
                    print(f"   🔗 {r['url']}")
        if args.news:
            topic = args.news if args.news != 'latest' else None
            results = wr.get_current_news(topic=topic)
            for i, r in enumerate(results):
                print(f"\n{i+1}. {r.get('title', 'Sans titre')}")
                if r.get('snippet'):
                    print(f"   {r['snippet'][:150]}")
        return

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
