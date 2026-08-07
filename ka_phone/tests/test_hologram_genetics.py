"""
Test réel — Création d'un hologramme spécialisé en Génétique
Pipeline qualité complet sur KA Phone
"""
import sys
sys.path.insert(0, '.')

from ka_phone_unified_server import app

print("""
╔═══════════════════════════════════════════════════════════════╗
║     🧬 CRÉATION D'UN HOLOGRAMME — GÉNÉTIQUE                   ║
║     Pipeline qualité en 5 étapes                               ║
╚═══════════════════════════════════════════════════════════════╝
""")

# ════════════════════════════════════════════════════════════════
# ÉTAPE 1 : L'utilisateur crée des faits
# ════════════════════════════════════════════════════════════════

facts = [
    ["ADN", "est composé de", "nucléotides (A, T, C, G)", "BIOLOGIE"],
    ["ADN", "a une structure en", "double hélice", "BIOLOGIE"],
    ["Watson et Crick", "ont découvert", "la structure de l'ADN", "HISTOIRE"],
    ["Rosalind Franklin", "a contribué à", "la découverte de l'ADN", "HISTOIRE"],
    ["Un gène", "est un segment d'", "ADN codant une protéine", "BIOLOGIE"],
    ["Les humains", "ont", "23 paires de chromosomes", "BIOLOGIE"],
    ["Le chromosome Y", "détermine", "le sexe masculin", "BIOLOGIE"],
    ["Une mutation", "est un changement dans", "la séquence d'ADN", "BIOLOGIE"],
    ["Les mutations", "peuvent être causées par", "des agents mutagènes", "BIOLOGIE"],
    ["La drépanocytose", "est causée par", "une mutation du gène HBB", "SANTE"],
    ["CRISPR-Cas9", "est un outil de", "modification génétique", "BIOLOGIE"],
    ["CRISPR", "a été développé par", "Doudna et Charpentier", "HISTOIRE"],
    ["CRISPR", "permet de", "corriger des mutations", "SANTE"],
    ["L'épigénétique", "étudie", "les changements sans mutation d'ADN", "BIOLOGIE"],
    ["La méthylation", "est un mécanisme", "épigénétique", "BIOLOGIE"],
    ["La thérapie génique", "consiste à", "remplacer un gène défectueux", "SANTE"],
    ["Le séquençage", "permet de", "lire l'ADN", "TECHNOLOGIE"],
    ["Le Projet Génome Humain", "a séquencé", "l'ADN humain complet", "HISTOIRE"],
]

print("📝 ÉTAPE 1 : Soumission des faits par l'utilisateur")
print(f"   ✅ {len(facts)} faits créés")
print(f"   Domaines : BIOLOGIE ({sum(1 for f in facts if f[3]=='BIOLOGIE')}), "
      f"HISTOIRE ({sum(1 for f in facts if f[3]=='HISTOIRE')}), "
      f"SANTE ({sum(1 for f in facts if f[3]=='SANTE')}), "
      f"TECHNO ({sum(1 for f in facts if f[3]=='TECHNOLOGIE')})")
print()

# ════════════════════════════════════════════════════════════════
# ÉTAPE 2 : Validation
# ════════════════════════════════════════════════════════════════

with app.test_client() as c:
    r = c.post('/api/holograms/validate', json={'facts': facts})
    val = r.get_json()
    v = val['validation']
    
    print("🔍 ÉTAPE 2 : Validation automatique")
    print(f"   Faits soumis : {v['submitted']}")
    print(f"   ✅ Valides   : {v['valid']}")
    print(f"   ❌ Rejetés   : {v['invalid']}")
    print(f"   🔄 Doublons  : {v['duplicates']}")
    if v['errors']:
        for e in v['errors']:
            print(f"     ⚠️  {e['reason']}: {e['fact'][:60]}")
    print()
    
    # ════════════════════════════════════════════════════════════
    # ÉTAPE 3 : Scoring
    # ════════════════════════════════════════════════════════════
    
    q = val['quality']
    print("📊 ÉTAPE 3 : Scoring qualité (0-100)")
    print(f"   Cohérence (faits liés) : {q['coherence']:5.1f}/30")
    print(f"   Complétude (domaines)  : {q['completeness']:5.1f}/25")
    print(f"   Unicité (nouveauté)    : {q['uniqueness']:5.1f}/20")
    print(f"   Diversité (variété)    : {q['diversity']:5.1f}/15")
    print(f"   Structure (équilibre)  : {q['structure']:5.1f}/10")
    print(f"   ──────────────────────────")
    print(f"   🌟 SCORE TOTAL         : {q['total']:5.1f}/100")
    print(f"   🏆 GRADE               : {q['grade']}")
    print()
    
    # ════════════════════════════════════════════════════════════
    # ÉTAPE 4 : Diagnostic
    # ════════════════════════════════════════════════════════════
    
    score = q['total']
    print("🔬 ÉTAPE 4 : Diagnostic de qualité")
    if score >= 80:
        print("   ✅ EXCELLENT — Niveau hologramme officiel")
    elif score >= 60:
        print("   ✅ BON — Prêt pour la communauté")
    elif score >= 40:
        print("   🔧 CORRECT — Enrichir la diversité des sujets")
    else:
        print("   🌱 DÉBUTANT — Continuer à ajouter des faits")
    
    if q['coherence'] < 15:
        print("   💡 Conseil : Créez des liens entre les faits")
    if q['completeness'] < 15:
        print("   💡 Conseil : Couvrez plus de sous-domaines")
    if q['diversity'] < 8:
        print("   💡 Conseil : Variez les sujets (pas toujours le même)")
    print()
    
    # ════════════════════════════════════════════════════════════
    # ÉTAPE 5 : Résumé
    # ════════════════════════════════════════════════════════════
    
    print("📋 ÉTAPE 5 : Résumé")
    print("═" * 50)
    print(f"""
   🧬 Hologramme  : Génétique
   📊 Qualité     : {q['total']:.0f}/100 (Grade {q['grade']})
   📝 Faits       : {v['valid']} valides / {v['submitted']} soumis
   📂 Domaines    : BIOLOGIE, HISTOIRE, SANTE, TECHNOLOGIE
   
   Statut : {'✅ Prêt à publier sur Harmonic AI' if score >= 60 else '🔧 À enrichir'}
   
   Prochaine étape :
     POST /api/holograms/submit
     → Publication sur le cloud Harmonic AI
     → Disponible pour toute la communauté
     → +{10 + v['valid']//10} points de réputation
""")

print("✅ Pipeline qualité exécuté avec succès.")
