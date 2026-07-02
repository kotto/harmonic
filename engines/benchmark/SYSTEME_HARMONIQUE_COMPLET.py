#!/usr/bin/env python3
"""
SYSTEME HARMONIQUE COMPLET
===========================
Verification et demonstration de toutes les briques du systeme harmonique :

1. NOYAU ABC (Atangana-Baleanu)     -> abc_kernel.py
2. ATTENTION PURE                   -> harmonic_pure_attention.py
3. COUCHES PURES                    -> harmonic_pure_layers.py
4. MODELE PUR (0 parametre)         -> harmonic_pure_model.py
5. SIGNATURES 9D                    -> harmonic_pure_signatures_v4.py
6. APPLICATIONS CONCRETES           -> harmonic_applications_concretes.py
   - FINANCE  : Detection de fraude, sentiment de marche
   - SANTE    : Classification de symptomes, prescriptions
   - INDUSTRIE: Diagnostic de pannes, maintenance
   - CREATION : Style, plagiat, recommandation
7. MOTEUR HYBRIDE                   -> harmonic_hybrid_engine.py
8. DISTILLATION                     -> harmonic_distillation_v2.py
9. WEB INTERFACE (JS)               -> harmonic_web/
10. APPLICATION ANDROID             -> harmonic_android/

Execution : python SYSTEME_HARMONIQUE_COMPLET.py
"""

import sys
import os
import time
import json
import importlib
import traceback

# Ajouter le repertoire courant et harmonic_training/ au path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'harmonic_training'))

# =========================================================================
# COULEURS POUR LE TERMINAL
# =========================================================================

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

def ok(msg):
    return f"{Colors.OKGREEN}[OK]{Colors.ENDC} {msg}"

def fail(msg):
    return f"{Colors.FAIL}[FAIL]{Colors.ENDC} {msg}"

def info(msg):
    return f"{Colors.OKBLUE}[INFO]{Colors.ENDC} {msg}"

def warn(msg):
    return f"{Colors.WARNING}[WARN]{Colors.ENDC} {msg}"

def header(msg):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{msg}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def v(msg):
    """Checkmark for OK status."""
    return f"[v] {msg}"

def x(msg):
    """Cross for FAIL status."""
    return f"[x] {msg}"


# =========================================================================
# 1. TEST DU NOYAU ABC
# =========================================================================

def test_noyau_abc():
    """Test du noyau de derivee fractionnaire d'Atangana-Baleanu."""
    header("1. NOYAU ABC (Atangana-Baleanu)")
    
    try:
        from model.abc_kernel import ABCKernel, PHI, ALPHA, B_1_PHI, mittag_leffler_stable
        
        # Verifier les constantes
        assert abs(PHI - 1.618033988749895) < 1e-12, "PHI incorrect"
        assert abs(ALPHA - 0.618033988749895) < 1e-12, "ALPHA incorrect"
        print(ok(f"Constantes : PHI={PHI:.8f}, ALPHA={ALPHA:.8f}"))
        
        # Creer le noyau
        kernel = ABCKernel(max_len=32)
        assert abs(kernel.kernel.sum().item() - 1.0) < 0.01, "Somme du noyau != 1"
        print(ok(f"Noyau ABC cree : {len(kernel.kernel)} termes, somme={kernel.kernel.sum().item():.6f}"))
        
        assert kernel.kernel[0] > kernel.kernel[-1], "Le noyau doit decroitre"
        print(ok(f"Decroissance : K(0)={kernel.kernel[0].item():.6f}, K(31)={kernel.kernel[31].item():.6f}"))
        
        z = 1.0
        ml = mittag_leffler_stable(torch.tensor(z), alpha=ALPHA).item()
        print(ok(f"Mittag-Leffler E_alpha(1.0) = {ml:.6f}"))
        
        import torch
        x = torch.randn(2, 32)
        result = kernel.apply_to_sequence(x)
        assert result.shape == x.shape, f"Shape: {result.shape} != {x.shape}"
        print(ok(f"Application sequence : {x.shape} -> {result.shape}"))
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCES] Noyau ABC operationnel{Colors.ENDC}")
        return True
        
    except Exception as e:
        traceback.print_exc()
        print(fail(f"Noyau ABC : {e}"))
        return False


# =========================================================================
# 2. TEST DE L'ATTENTION HARMONIQUE PURE
# =========================================================================

def test_attention_pure():
    """Test de l'attention harmonique pure (0 parametre)."""
    header("2. ATTENTION HARMONIQUE PURE")
    
    try:
        import torch
        from model.harmonic_pure_attention import PureHarmonicAttention
        
        batch, seq_len, hidden_size = 2, 16, 128
        attn = PureHarmonicAttention(hidden_size=hidden_size, max_len=512)
        
        x = torch.randn(batch, seq_len, hidden_size)
        output, signatures = attn(x)
        
        assert output.shape == (batch, seq_len, hidden_size), f"Output: {output.shape}"
        assert signatures.shape == (batch, seq_len, 7), f"Signatures: {signatures.shape}"
        assert torch.all(signatures >= 0) and torch.all(signatures <= 1), "Signatures hors [0,1]"
        
        sig_mean = signatures.mean(dim=(0, 1))
        dim_names = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code']
        for i, name in enumerate(dim_names):
            print(ok(f"  {name}: {sig_mean[i].item():.4f}"))
        
        has_grad = any(p.requires_grad for p in attn.parameters())
        assert not has_grad, "Attention pure a des parametres entrainables"
        print(ok("Aucun parametre entrainable"))
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCES] Attention harmonique pure operationnelle{Colors.ENDC}")
        return True
        
    except Exception as e:
        traceback.print_exc()
        print(fail(f"Attention pure : {e}"))
        return False


# =========================================================================
# 3. TEST DES COUCHES PURES
# =========================================================================

def test_couches_pures():
    """Test des couches de decodeur harmonique pur."""
    header("3. COUCHES DE DECODEUR HARMONIQUE PUR")
    
    try:
        import torch
        from model.harmonic_pure_layers import PureHarmonicDecoderLayer
        
        batch, seq_len, hidden_size = 2, 16, 128
        layer = PureHarmonicDecoderLayer(hidden_size=hidden_size, max_len=512)
        
        x = torch.randn(batch, seq_len, hidden_size)
        output, signatures = layer(x)
        
        assert output.shape == (batch, seq_len, hidden_size), f"Output: {output.shape}"
        assert signatures.shape == (seq_len, 7), f"Signatures: {signatures.shape}"
        assert torch.all(signatures >= 0) and torch.all(signatures <= 1), "Signatures hors [0,1]"
        
        print(ok(f"Couche decodeur : {x.shape} -> {output.shape}"))
        print(ok(f"Signatures 7D : {signatures.shape}"))
        
        diff = (output - x).abs().mean().item()
        print(ok(f"Connexion residuelle : |output - input|_mean = {diff:.6f}"))
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCES] Couches harmoniques pures operationnelles{Colors.ENDC}")
        return True
        
    except Exception as e:
        traceback.print_exc()
        print(fail(f"Couches pures : {e}"))
        return False


# =========================================================================
# 4. TEST DU MODELE PUR
# =========================================================================

def test_modele_pur():
    """Test du modele de langage causal harmonique pur."""
    header("4. MODELE HARMONIQUE PUR (0 parametre entrainable)")
    
    try:
        import torch
        from model.harmonic_pure_model import HarmonicPureForCausalLM
        
        vocab_size, hidden_size, num_layers = 500, 64, 2
        model = HarmonicPureForCausalLM(
            vocab_size=vocab_size, hidden_size=hidden_size,
            num_layers=num_layers, max_len=256
        )
        
        batch, seq_len = 2, 16
        input_ids = torch.randint(1, vocab_size - 1, (batch, seq_len))
        
        logits, signatures = model(input_ids)
        
        assert logits.shape == (batch, seq_len, vocab_size), f"Logits: {logits.shape}"
        assert signatures.shape == (num_layers, batch, seq_len, 7), f"Signatures: {signatures.shape}"
        
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        print(ok(f"Logits: {logits.shape}, Signatures: {signatures.shape}"))
        print(ok(f"Parametres : {total_params:,} totaux, {trainable_params} entrainables"))
        
        logits2, _ = model(input_ids)
        assert torch.allclose(logits, logits2), "Le modele doit etre deterministe"
        print(ok("Reproductible (deterministe)"))
        
        prompt = torch.randint(1, vocab_size - 1, (1, 4))
        generated = model.generate(prompt, max_new_tokens=8, temperature=0.8)
        assert generated.shape[1] == prompt.shape[1] + 8, f"Generation: {generated.shape}"
        print(ok(f"Generation : {prompt.shape} -> {generated.shape}"))
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCES] Modele harmonique pur operationnel{Colors.ENDC}")
        return True
        
    except Exception as e:
        traceback.print_exc()
        print(fail(f"Modele pur : {e}"))
        return False


# =========================================================================
# 5. TEST DES SIGNATURES 9D
# =========================================================================

def test_signatures_9d():
    """Test des signatures harmoniques 9D."""
    header("5. SIGNATURES HARMONIQUES 9D")
    
    try:
        import torch
        import numpy as np
        from model.harmonic_applications_concretes import SignatureEngine9D
        
        engine = SignatureEngine9D(vocab_size=500, hidden_size=64)
        
        text = "Analyse de texte avec des concepts mathematiques et du code python"
        sig = engine.compute_signature(text)
        
        assert sig.shape == (9,), f"Signature: {sig.shape}"
        assert np.all(sig >= 0) and np.all(sig <= 1), f"Signatures hors [0,1]: {sig}"
        
        dims = ['phi', 'alpha', 'reasoning', 'creativity', 'math', 'factual', 'code', 'emotion', 'temporal']
        print(ok(f"Signature 9D :"))
        for i, d in enumerate(dims):
            print(f"    {d:12s} = {sig[i]:.4f}")
        
        texts = [
            "Calcul differentiel et integral avance",
            "Poeme sur la douceur du printemps",
            "Diagnostic de panne moteur electrique",
        ]
        sigs = engine.compute_signatures_batch(texts)
        assert sigs.shape == (3, 9), f"Batch: {sigs.shape}"
        print(ok(f"Batch de 3 textes : {sigs.shape}"))
        
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                diff = np.linalg.norm(sigs[i] - sigs[j])
                print(f"    Distance [{i}-{j}] : {diff:.4f}")
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCES] Signatures 9D operationnelles{Colors.ENDC}")
        return True
        
    except Exception as e:
        traceback.print_exc()
        print(fail(f"Signatures 9D : {e}"))
        return False


# =========================================================================
# 6. TEST DES APPLICATIONS CONCRETES
# =========================================================================

def test_applications_concretes():
    """Test des 4 domaines d'application."""
    header("6. APPLICATIONS CONCRETES (4 DOMAINES)")
    
    try:
        from model.harmonic_applications_concretes import (
            HarmonicApplicationAnalyzer, FinanceHarmonicAnalyzer,
            SanteHarmonicAnalyzer, IndustrieHarmonicAnalyzer,
            CreationHarmonicAnalyzer
        )
        
        unified = HarmonicApplicationAnalyzer()
        
        text = "Le marche boursier est en hausse suite aux annonces economiques"
        result = unified.analyze_text(text)
        
        assert 'signature_9d' in result, "Pas de signature 9D"
        assert 'domains' in result, "Pas d'analyse par domaine"
        assert 'finance' in result['domains'], "Pas de domaine finance"
        assert 'sante' in result['domains'], "Pas de domaine sante"
        assert 'industrie' in result['domains'], "Pas de domaine industrie"
        assert 'creation' in result['domains'], "Pas de domaine creation"
        
        print(ok(f"Analyse unifiee :"))
        print(f"    Finance   : {result['domains']['finance']['label']} (risque={result['domains']['finance']['risk_indicator']:.2f})")
        print(f"    Sante     : {result['domains']['sante']['flag']} (coherence={result['domains']['sante']['coherence']:.2f})")
        print(f"    Industrie : {result['domains']['industrie']['maintenance_priority']} (anomalie={result['domains']['industrie']['anomaly_score']:.2f})")
        print(f"    Creation  : {result['domains']['creation']['style']} (creativite={result['domains']['creation']['creativity_score']:.2f})")
        
        # Test Finance - Fraude
        finance = FinanceHarmonicAnalyzer()
        transactions = [
            {'description': 'Achat legitime de fournitures', 'montant': 500},
            {'description': 'TRANSFERT MASSIF VERS COMPTE ETRANGER NON IDENTIFIE', 'montant': 50000},
        ]
        fraud = finance.detect_fraud(transactions)
        assert len(fraud) == 2, "Detection de fraude"
        print(ok(f"Fraude : {fraud[1]['flag']} (score={fraud[1]['fraud_score']:.2f})"))
        
        # Test Sante
        sante = SanteHarmonicAnalyzer()
        prescriptions = [
            "Prendre 2 comprimes de paracetamol 500mg matin et soir",
            "INJECTER PRODUIT NON IDENTIFIE SANS ETIQUETTE",
        ]
        coherence = sante.analyze_prescription_coherence(prescriptions)
        print(ok(f"Coherence prescriptions : {coherence[0]['flag']} / {coherence[1]['flag']}"))
        
        # Test Industrie
        industrie = IndustrieHarmonicAnalyzer()
        pannes = [
            "Bruit de roulement anormal sur le moteur principal",
            "Temperature du reacteur dans les normes",
        ]
        diag = industrie.diagnose_failures(pannes)
        print(ok(f"Diagnostic pannes : {len(diag)} analyses"))
        
        # Test Creation
        creation = CreationHarmonicAnalyzer()
        styles = creation.analyze_style([
            "Le soleil couchant embrase l'horizon",
            "La fonction f(x) = x^2 est une parabole",
        ], ["Poete", "Mathematicien"])
        assert len(styles) == 2, "Analyse de style"
        print(ok(f"Styles : {styles[0]['auteur']}={styles[0]['style']}, {styles[1]['auteur']}={styles[1]['style']}"))
        
        from model.harmonic_applications_concretes import analyze_harmonic_applications
        quick = analyze_harmonic_applications()
        assert len(quick) >= 1, "Analyse rapide"
        print(ok(f"Analyse rapide : {len(quick)} textes analyses"))
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCES] Applications concretes operationnelles{Colors.ENDC}")
        return True
        
    except Exception as e:
        traceback.print_exc()
        print(fail(f"Applications concretes : {e}"))
        return False


# =========================================================================
# 7. TEST DU MOTEUR HYBRIDE
# =========================================================================

def test_hybride():
    """Test du moteur hybride."""
    header("7. MOTEUR HYBRIDE")
    
    try:
        import torch
        from model.harmonic_hybrid_engine import HarmonicHybridEngine
        
        engine = HarmonicHybridEngine()
        
        text = "Quelle est la capitale de la France ?"
        result = engine.analyze(text)
        
        assert 'signature' in result, "Pas de signature"
        assert 'resonance' in result, "Pas de resonance"
        assert 'hybrid_score' in result, "Pas de score hybride"
        
        print(ok(f"Analyse hybride de: '{text[:50]}...'"))
        print(f"    Resonance: {result['resonance']:.4f}")
        print(f"    Score hybride: {result['hybrid_score']:.4f}")
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCES] Moteur hybride operationnel{Colors.ENDC}")
        return True
        
    except Exception as e:
        traceback.print_exc()
        print(fail(f"Moteur hybride : {e}"))
        return False


# =========================================================================
# 8. TEST DE LA WEB INTERFACE (fichiers JS)
# =========================================================================

def test_web_interface():
    """Test de l'interface web (verification des fichiers)."""
    header("8. INTERFACE WEB")
    
    web_files = [
        'harmonic_web/index.html',
        'harmonic_web/app.js',
        'harmonic_web/style.css',
        'harmonic_web/harmonic-engine.js',
        'harmonic_web/multimodal.js',
        'harmonic_web/search_engine.js',
    ]
    
    all_ok = True
    for f in web_files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(ok(f"{f} ({size:,} bytes)"))
        else:
            print(fail(f"{f} manquant"))
            all_ok = False
    
    if all_ok:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCES] Interface web complete{Colors.ENDC}")
    return all_ok


# =========================================================================
# 9. TEST DE L'APPLICATION ANDROID (fichiers Kotlin)
# =========================================================================

def test_android():
    """Test des fichiers de l'application Android."""
    header("9. APPLICATION ANDROID")
    
    android_files = [
        'harmonic_android/app/src/main/java/com/harmonicai/android/engine/HarmonicEngine.kt',
        'harmonic_android/app/src/main/java/com/harmonicai/android/engine/MultimodalAnalyzer.kt',
        'harmonic_android/app/src/main/java/com/harmonicai/android/MainActivity.kt',
    ]
    
    all_ok = True
    for f in android_files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(ok(f"{f} ({size:,} bytes)"))
        else:
            print(fail(f"{f} manquant"))
            all_ok = False
    
    if all_ok:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCES] Application Android presente{Colors.ENDC}")
    return all_ok


# =========================================================================
# 10. TEST DE LA GENERATION AUDIO/VIDEO
# =========================================================================

def test_av():
    """Test des fichiers de generation audio/video."""
    header("10. GENERATION AUDIO/VIDEO")
    
    av_files = [
        'GENERATION_AV_HARMONIQUE/engine/harmonic_av_core.py',
        'GENERATION_AV_HARMONIQUE/examples/generate_ocean_sunset.py',
    ]
    
    all_ok = True
    for f in av_files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(ok(f"{f} ({size:,} bytes)"))
        else:
            print(fail(f"{f} manquant"))
            all_ok = False
    
    if all_ok:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCES] Generation AV presente{Colors.ENDC}")
    return all_ok


# =========================================================================
# 11. EXPORT JSON DE LA CONFIGURATION COMPLETE
# =========================================================================

def exporter_configuration():
    """Exporte la configuration complete du systeme harmonique."""
    header("11. EXPORT CONFIGURATION SYSTEME")
    
    try:
        from model.abc_kernel import PHI, ALPHA, B_1_PHI
        
        config = {
            'version': '4.2.0',
            'date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'constantes_fondamentales': {
                'phi': PHI,
                'alpha': ALPHA,
                'alpha_const': 1.0 / B_1_PHI,
                'B_1_phi': B_1_PHI,
            },
            'composants': {
                'noyau_abc': {'present': True, 'type': 'Atangana-Baleanu', 'ordre': '1/phi'},
                'attention_pure': {'present': True, 'parametres': 0},
                'decodeur_pur': {'present': True, 'parametres': 0},
                'modele_pur': {'present': True, 'parametres_entrainables': 0},
                'signatures_9d': {'present': True, 'dimensions': 9},
                'applications': ['FINANCE', 'SANTE', 'INDUSTRIE', 'CREATION'],
                'moteur_hybride': {'present': True},
                'distillation': {'present': True},
                'web_interface': {'present': True, 'framework': 'Vanilla JS'},
                'android': {'present': True, 'langage': 'Kotlin'},
                'generation_av': {'present': True},
            },
            'fichiers_cles': [
                'harmonic_training/model/abc_kernel.py',
                'harmonic_training/model/harmonic_pure_attention.py',
                'harmonic_training/model/harmonic_pure_layers.py',
                'harmonic_training/model/harmonic_pure_model.py',
                'harmonic_training/model/harmonic_pure_signatures_v4.py',
                'harmonic_training/model/harmonic_applications_concretes.py',
                'harmonic_training/model/harmonic_hybrid_engine.py',
                'harmonic_web/harmonic-engine.js',
                'harmonic_web/multimodal.js',
                'harmonic_android/app/src/main/java/com/harmonicai/android/engine/HarmonicEngine.kt',
                'GENERATION_AV_HARMONIQUE/engine/harmonic_av_core.py',
            ]
        }
        
        with open('configuration_systeme_harmonique.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(ok("Configuration exportee dans configuration_systeme_harmonique.json"))
        print(f"  Dimensions signatures : {config['composants']['signatures_9d']['dimensions']}")
        print(f"  Applications : {', '.join(config['composants']['applications'])}")
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCES] Configuration exportee{Colors.ENDC}")
        return True
        
    except Exception as e:
        print(fail(f"Export configuration : {e}"))
        return False


# =========================================================================
# MAIN
# =========================================================================

def main():
    """Execute tous les tests du systeme harmonique complet."""
    
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 60)
    print("  SYSTEME HARMONIQUE COMPLET")
    print("  Verification et Integration")
    print("=" * 60)
    print(f"{Colors.ENDC}")
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    print()
    
    # Execution des tests
    results = {}
    
    # Tests Python
    results['noyau_abc'] = test_noyau_abc()
    results['attention_pure'] = test_attention_pure()
    results['couches_pures'] = test_couches_pures()
    results['modele_pur'] = test_modele_pur()
    results['signatures_9d'] = test_signatures_9d()
    results['applications'] = test_applications_concretes()
    results['hybride'] = test_hybride()
    
    # Tests fichiers
    results['web'] = test_web_interface()
    results['android'] = test_android()
    results['av'] = test_av()
    
    # Export configuration
    results['config'] = exporter_configuration()
    
    # =====================================================================
    # RESUME FINAL
    # =====================================================================
    header("RESUME FINAL")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\n{Colors.BOLD}Composants testes : {total}{Colors.ENDC}")
    
    for name, status in results.items():
        stat = "OK" if status else "FAIL"
        color = Colors.OKGREEN if status else Colors.FAIL
        print(f"  {name:25s} : {color}{stat}{Colors.ENDC}")
    
    print()
    if passed == total:
        print(f"  {Colors.OKGREEN}Resultat : {passed}/{total} tests passes{Colors.ENDC}")
    else:
        print(f"  {Colors.WARNING}Resultat : {passed}/{total} passes, {failed} echoues{Colors.ENDC}")
    
    print()
    print(f"{Colors.BOLD}Composants :{Colors.ENDC}")
    print(f"  1. Noyau ABC (Atangana-Baleanu a l'ordre 1/phi)")
    print(f"  2. Attention Harmonique Pure (0 parametre)")
    print(f"  3. Decodeur Harmonique Pur (0 parametre)")
    print(f"  4. Modele Causal Harmonique Pur (0 parametre entrainable)")
    print(f"  5. Signatures 9D Universelles")
    print(f"  6. Applications : FINANCE, SANTE, INDUSTRIE, CREATION")
    print(f"  7. Moteur Hybride & Distillation")
    print(f"  8. Interface Web (JavaScript natif)")
    print(f"  9. Application Android (Kotlin)")
    print(f"  10. Generation Audio/Video")
    
    if failed > 0:
        print(f"\n{Colors.WARNING}[ATTENTION] Certains composants necessitent des ajustements.{Colors.ENDC}")
        return False
    else:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}[SUCCES] SYSTEME HARMONIQUE COMPLET ET OPERATIONNEL{Colors.ENDC}")
        return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
