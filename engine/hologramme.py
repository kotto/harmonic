#!/usr/bin/env python3
"""
hologramme.py — Architecture de spécialisation à la volée par hologrammes
=========================================================================

PRINCIPE :
  Le codec ψ est un moteur de raisonnement UNIVERSEL (41 primitives, 7 domaines).
  Un HOLOGRAMME est un adaptateur (LoRA, ~2MB) qui spécialise le moteur pour
  le VOCABULAIRE d'un domaine spécifique — pas pour le raisonnement lui-même.

  L'utilisateur fournit 5-20 exemples dans son domaine → le système :
    1. Extrait les opérations via le codec ψ
    2. Identifie les primitives utilisées
    3. Crée un hologramme (LoRA) en 30-60 secondes
    4. L'utilisateur peut interroger le système avec son hologramme

  TRANSVERTICALITÉ : le modèle de base connaît déjà les 41 primitives.
  L'hologramme n'apprend que le vocabulaire → ultra-efficace.

ARCHITECTURE :
  ┌─────────────────────────────────────────────────────────────┐
  │  Couche 1 : Moteur harmonique (codec ψ) — 0 paramètre      │
  │  • 41 primitives universelles                              │
  │  • Somme cumulative exacte                                 │
  │  • Invariant quelque soit le domaine                       │
  ├─────────────────────────────────────────────────────────────┤
  │  Couche 2 : Modèle de base transvertical — 60M params      │
  │  • Pré-entraîné sur 7 domaines (20k exemples)              │
  │  • Connaît les gestes universels (SUB, ADD, MUL, DIV...)   │
  │  • Partage entre tous les hologrammes                      │
  ├─────────────────────────────────────────────────────────────┤
  │  Couche 3 : Hologrammes (adaptateurs LoRA) — ~2MB chacun   │
  │  • Domaine juridique, médical, financier...                │
  │  • Apprend le vocabulaire spécifique (5-20 exemples)       │
  │  • Entraînement en 30-60 secondes sur CPU                  │
  │  • Stocké dans le registre des hologrammes                 │
  └─────────────────────────────────────────────────────────────┘

USAGE :
  from hologramme import Hologramme, HologramStore
  
  store = HologramStore()
  
  # Créer un hologramme pour un nouveau domaine
  store.creer('droit_des_contrats', exemples=[
      "Le contrat prévoit 100 000€, le défendeur déduit 30 000€",
      "La clause pénale est de 10% du montant total de 50 000€",
  ])
  
  # Interroger avec l'hologramme
  resultat = store.soudre('droit_des_contrats',
      "Le contrat prévoit 200 000€, 20% de pénalités")
  # → 200000 × 0.2 = 40000
"""

import sys, os, json, time, re, shutil
from typing import List, Dict, Optional, Tuple
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parseur_annotations import anot2ops, reponse_finale
from codec_binding import encoder_operations_v2, decoder_trames

# ═══════════════════════════════════════════════════════════════════════════
# 1. CŒUR DU SYSTÈME : modèle de base + codec
# ═══════════════════════════════════════════════════════════════════════════

# Modèle de base (modèle transvertical V2 pré-entraîné)
_MODELE_BASE = None
_TOK = None
_REGISTRE = {}


def charger_base():
    """Charge le modèle transvertical V2 (fait une fois pour tous les hologrammes)."""
    global _MODELE_BASE, _TOK
    if _MODELE_BASE is not None:
        return
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    from peft import PeftModel
    _TOK = AutoTokenizer.from_pretrained('google/flan-t5-small')
    base = AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-small',
                                                  low_cpu_mem_usage=True)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'data/t5_transvertical_v2/final')
    _MODELE_BASE = PeftModel.from_pretrained(base, path)
    _MODELE_BASE.eval()
    print(f"  ✓ Modèle de base chargé (transvertical V2)")


# ═══════════════════════════════════════════════════════════════════════════
# 2. HOLOGRAMME : un adaptateur LoRA pour un domaine spécifique
# ═══════════════════════════════════════════════════════════════════════════

class Hologramme:
    """Un hologramme = un adaptateur LoRA pour un domaine.

    Caractéristiques :
      - Taille : ~2MB (adaptateurs LoRA seuls)
      - Entraînement : 30-60 secondes sur CPU (5-20 exemples)
      - Inférence : ~2 secondes par problème
      - Stockage : dossier dans data/hologram_store/{nom}/
    """

    def __init__(self, nom: str, domaine: str = "inconnu"):
        self.nom = nom
        self.domaine = domaine
        self.chemin = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f'data/hologram_store/{nom}')
        self.statistiques = {
            'exemples': 0,
            'primitives': Counter(),
            'temps_entrainement': 0,
            'score': 0,
        }
        self._modele = None

    def entrainer(self, exemples: List[Dict[str, str]]) -> Dict:
        """Entraîne l'hologramme sur des exemples (question, operations).

        Args:
            exemples: liste de {'input': str, 'target': str}
                      où target est une séquence d'ops (INIT(20) SUB(8)...)

        Retourne:
            statistiques d'entraînement
        """
        import torch
        from transformers import (
            TrainingArguments, Trainer, DataCollatorForSeq2Seq)
        from peft import LoraConfig, get_peft_model, TaskType, PeftModel
        from datasets import Dataset

        t0 = time.time()
        charger_base()

        # Vérifier les exemples
        if not exemples:
            return {'erreur': 'Aucun exemple fourni'}

        # Préparer le dataset
        data = []
        for ex in exemples:
            if isinstance(ex, str):
                # Format texte seul → on le parse
                data.append({'input': ex, 'target': ''})
            else:
                data.append({'input': ex['input'],
                             'target': ex.get('target', '')})

        # Statut des primitives utilisées
        for ex in data:
            ops = re.findall(r'(INIT|SUB|ADD|MUL|DIV)', ex['target'])
            for op in ops:
                self.statistiques['primitives'][op] += 1

        # Créer un adaptateur LoRA pour ce domaine
        # On part du modèle de base transvertical et on ajoute un nouvel adaptateur
        base_model = _MODELE_BASE
        lora_config = LoraConfig(
            task_type=TaskType.SEQ_2_SEQ_LM,
            r=8,  # plus petit = plus rapide
            lora_alpha=16,
            lora_dropout=0.05,
            target_modules=['q', 'v'],
        )
        # Ajouter un nouvel adaptateur LoRA par-dessus le modèle de base
        base_model.add_adapter(self.nom, lora_config)
        base_model.set_adapter(self.nom)
        base_model.train()
        modele = base_model

        # Tokenizer
        ds = Dataset.from_list(data)
        if 'target' in ds.column_names and all(ds['target']):
            def tok_fn(b):
                inp = _TOK(b['input'], max_length=256,
                           truncation=True, padding=False)
                tgt = _TOK(b['target'], max_length=64,
                           truncation=True, padding=False)
                inp['labels'] = tgt['input_ids']
                return inp
            ds = ds.map(tok_fn, batched=True,
                        remove_columns=ds.column_names)

        # Entraînement ultra-rapide (quelques minutes)
        args = TrainingArguments(
            output_dir=self.chemin,
            num_train_epochs=min(10, max(3, 20 // len(data))),
            per_device_train_batch_size=2,
            gradient_accumulation_steps=2,
            learning_rate=5e-4,
            logging_steps=10,
            save_strategy='no',
            fp16=False,
            report_to='none',
            dataloader_num_workers=0,
            remove_unused_columns=False,
        )

        trainer = Trainer(
            model=modele,
            args=args,
            train_dataset=ds if 'target' in ds.column_names else None,
            data_collator=DataCollatorForSeq2Seq(
                _TOK, model=modele, padding=True),
            tokenizer=_TOK,
        )

        if trainer.train_dataset is not None:
            trainer.train()

        # Sauvegarder
        os.makedirs(self.chemin, exist_ok=True)
        # Ne sauvegarder que l'adaptateur (pas tout le modèle de base)
        modele.save_pretrained(self.chemin, safe_serialization=True)
        _TOK.save_pretrained(self.chemin)
        # Statistiques
        self.statistiques['exemples'] = len(data)
        self.statistiques['temps_entrainement'] = time.time() - t0
        self._modele = modele

        # Sauvegarder les métadonnées
        with open(os.path.join(self.chemin, 'hologramme.json'), 'w') as f:
            json.dump({
                'nom': self.nom,
                'domaine': self.domaine,
                'statistiques': {
                    'exemples': self.statistiques['exemples'],
                    'primitives': dict(self.statistiques['primitives']),
                    'temps_entrainement': self.statistiques['temps_entrainement'],
                }
            }, f, ensure_ascii=False, indent=2)

        return self.statistiques

    def charger(self):
        """Charge un hologramme sauvegardé."""
        charger_base()
        base = _MODELE_BASE
        # Charger l'adaptateur depuis le dossier
        base.load_adapter(self.chemin, adapter_name=self.nom)
        base.set_adapter(self.nom)
        base.eval()
        self._modele = base
        # Charger les métadonnées
        meta_path = os.path.join(self.chemin, 'hologramme.json')
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
                self.statistiques.update(meta.get('statistiques', {}))
                self.domaine = meta.get('domaine', 'inconnu')

    def resoudre(self, question: str) -> Optional[float]:
        """Résout un problème avec l'hologramme.

        Pipeline : question → T5 (hologramme) → ops → codec ψ → résultat
        """
        if self._modele is None:
            self.charger()

        from codec_binding import encoder_operations_v2, decoder_trames

        # Générer les ops avec le modèle spécialisé
        inp = _TOK('translate to operations: ' + question,
                   return_tensors='pt', max_length=256, truncation=True)
        import torch
        with torch.no_grad():
            out = self._modele.generate(
                **inp, max_new_tokens=64, num_beams=1)
        pred = _TOK.decode(out[0], skip_special_tokens=True)

        # Parser les ops
        OM = {'MUL': 'MULTIPLY', 'SUB': 'SUBTRACT',
              'ADD': 'ADD', 'DIV': 'DIVIDE', 'INIT': 'INIT'}
        ops = []
        for token in pred.replace('\n', ' ').split():
            m = re.match(r'(INIT|MUL|SUB|ADD|DIV)\(([^)]+)\)', token.strip())
            if not m:
                continue
            op, v = m.group(1), m.group(2)
            try:
                v = float(v)
            except ValueError:
                continue
            mapped = OM.get(op)
            if not mapped:
                continue
            if mapped == 'INIT':
                ops.append({'op': 'INIT', 'value': v})
            elif mapped == 'MULTIPLY':
                ops.append({'op': 'MULTIPLY', 'multiplier': v})
            elif mapped == 'DIVIDE':
                ops.append({'op': 'DIVIDE', 'divisor': v})
            elif mapped == 'SUBTRACT':
                ops.append({'op': 'SUBTRACT', 'value': v})
            elif mapped == 'ADD':
                ops.append({'op': 'ADD', 'value': v})

        if not ops:
            return None

        try:
            return decoder_trames(encoder_operations_v2(
                ops, True, True, False, True))
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════════════════════
# 3. STORE : gestion des hologrammes
# ═══════════════════════════════════════════════════════════════════════════

class HologramStore:
    """Gère le cycle de vie des hologrammes : création, stockage, interrogation."""

    def __init__(self):
        self.base_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data/hologram_store')
        os.makedirs(self.base_path, exist_ok=True)
        self._hologrammes = {}

    def lister(self) -> List[Dict]:
        """Liste tous les hologrammes disponibles."""
        resultats = []
        for d in os.listdir(self.base_path):
            chemin = os.path.join(self.base_path, d)
            meta_path = os.path.join(chemin, 'hologramme.json')
            if os.path.isdir(chemin) and os.path.exists(meta_path):
                with open(meta_path) as f:
                    meta = json.load(f)
                resultats.append(meta)
        return resultats

    def creer(self, nom: str, exemples: List[Dict[str, str]],
              domaine: str = "personnalise") -> Hologramme:
        """Crée un nouvel hologramme.

        Args:
            nom: nom unique de l'hologramme
            exemples: liste de {'input': str, 'target': str}
            domaine: domaine de l'hologramme

        Retourne:
            Hologramme entraîné
        """
        print(f"  🌀 Création de l'hologramme '{nom}' ({len(exemples)} exemples)...")
        h = Hologramme(nom, domaine)
        stats = h.entrainer(exemples)
        print(f"  ✓ Hologramme '{nom}' créé en {stats['temps_entrainement']:.1f}s")
        print(f"    Primitives : {dict(stats['primitives'])}")
        self._hologrammes[nom] = h
        return h

    def charger(self, nom: str) -> Optional[Hologramme]:
        """Charge un hologramme existant."""
        if nom in self._hologrammes:
            return self._hologrammes[nom]
        h = Hologramme(nom)
        chemin = os.path.join(self.base_path, nom)
        if os.path.exists(chemin):
            h.charger()
            self._hologrammes[nom] = h
            return h
        return None

    def resoudre(self, nom: str, question: str) -> Optional[float]:
        """Résout un problème avec l'hologramme spécifié."""
        h = self.charger(nom)
        if h is None:
            print(f"  ❌ Hologramme '{nom}' introuvable")
            return None
        return h.resoudre(question)


# ═══════════════════════════════════════════════════════════════════════════
# 4. DÉMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═══ ARCHITECTURE HOLOGRAMMES — DÉMONSTRATION ═══\n")

    # Créer un hologramme pour le droit des contrats
    store = HologramStore()

    exemples_droit = [
        {'input': 'Le contrat prévoit 100 000€. Le défendeur déduit 30 000€.',
         'target': 'INIT(100000) SUB(30000)'},
        {'input': 'La clause pénale est de 10% du montant total de 50 000€.',
         'target': 'INIT(50000) MUL(0.1)'},
        {'input': 'Le plaignant demande 75 000€. Le tribunal accorde 60 000€.',
         'target': 'INIT(75000) SUB(15000)'},
    ]

    store.creer('droit_contrats', exemples_droit, 'juridique')

    # Tester
    print("\n🔍 Tests :")
    tests = [
        "Le contrat prévoit 200 000€, 20% de pénalités",
        "Le montant du litige est de 50 000€, le défendeur déduit 10 000€",
    ]
    for q in tests:
        r = store.resoudre('droit_contrats', q)
        print(f"  {q}")
        print(f"  → {r:.2f}")

    # Lister les hologrammes disponibles
    print(f"\n📋 Hologrammes disponibles :")
    for h in store.lister():
        print(f"  • {h['nom']} ({h['domaine']}) — {h['statistiques']['exemples']} exemples")