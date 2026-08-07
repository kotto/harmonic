#!/usr/bin/env python3
"""
run_demo.py — Script de vente guidé KA Enterprise (démo cabinet comptable)
==========================================================================

Déroule le parcours commercial complet contre un serveur KA Enterprise :
chargement du dataset réaliste, questions chiffrées, agrégats, listes,
Q&A procédures, ÉTANCHÉITÉ, REFUS CALIBRÉ (le moment de vente), email,
rapport, auto-apprentissage. Chaque étape affiche l'argument de vente.

Usage :
  # avec un tenant existant (clé API) :
  python run_demo.py --api-key <clé> [--base http://127.0.0.1:8767]

  # ou de zéro (crée le tenant via l'onboarding) :
  python run_demo.py --onboard "Cabinet Test" admin@cabinet.fr \
      --base http://127.0.0.1:8767

  # en mode silencieux (aucune interaction, assertions actives) :
  python run_demo.py --api-key <clé> --auto
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error


def main():
    ap = argparse.ArgumentParser(description='Script de vente KA Enterprise')
    ap.add_argument('--base', default='http://127.0.0.1:8767')
    ap.add_argument('--api-key', default='')
    ap.add_argument('--onboard', nargs=2, metavar=('NOM', 'EMAIL'),
                    help='crée le tenant via l\'onboarding avant la démo')
    ap.add_argument('--auto', action='store_true',
                    help='aucune pause, assertions actives')
    args = ap.parse_args()

    base = args.base.rstrip('/')
    key = args.api_key

    if args.onboard:
        print("🌱 0. Onboarding — le client décrit SON environnement…")
        r = call(base, '/api/enterprise/onboard', 'POST', {
            'name': args.onboard[0], 'email': args.onboard[1],
            'description': "cabinet d'expertise comptable qui gère la "
                           "comptabilité, la paie et la fiscalité de ses clients",
            'secteur': 'finance'}, key)
        assert 'tenant' in r, f"onboarding KO: {r}"
        key = r['tenant']['api_key']
        print(f"   ✅ Tenant « {r['tenant']['name']} » créé — clé API : {key[:8]}…")

    print("🎬 1. Chargement du dataset de démonstration (cabinet comptable)…")
    r = call(base, '/api/enterprise/demo/load?reset=1', 'POST', {}, key)
    assert 'departments' in r, f"demo KO: {r}"
    depts = {d['name']: d['id'] for d in r['departments']}
    for d in r['departments']:
        print(f"   🧠 {d['name']}: {d['facts_total']} faits")
    assert depts.get('demo_comptabilite') and depts.get('demo_procedures')
    arg("Un cabinet comptable type : 12 clients, 12 factures, la paie, "
        "le bilan et les procédures internes — tout est ingéré en 1 clic.")

    comptable = depts['demo_comptabilite']
    procedures = depts['demo_procedures']

    # ══════════ QUESTIONS CHIFFRÉES ══════════
    print("\n📊 2. Questions chiffrées sur les données privées…")
    r = ask_data(base, key, comptable, "combien de clients actifs avons-nous ?")
    v = first_agg(r)
    print(f"   ❓ combien de clients actifs avons-nous ? → {v}")
    assert v == 10, f"attendu 10, obtenu {v}"

    r = ask_data(base, key, comptable,
                 "quel est le chiffre d'affaires total de nos clients actifs ?")
    v = first_agg(r)
    print(f"   ❓ chiffre d'affaires total des clients actifs ? → {v:,.0f} €")
    assert v == 3668000, f"attendu 3668000, obtenu {v}"
    arg("Agrégats réels calculés sur VOS chiffres — pas une estimation.")

    print("\n📋 3. Listes et filtres…")
    r = ask_data(base, key, comptable, "liste des factures en retard")
    print(f"   ❓ liste des factures en retard → {r['count']} lignes")
    for row in r['rows'][:3]:
        print(f"      • {row.get('client','')} — {row.get('montant','')} ({row.get('date','')})")
    assert r['count'] == 3

    r = ask_data(base, key, comptable,
                 "quel est le montant total des factures en retard ?")
    v = first_agg(r)
    print(f"   ❓ montant total des factures en retard ? → {v:,.2f} €")
    assert abs(v - 40600.0) < 0.01, f"attendu 40600, obtenu {v}"
    arg("Listes, filtres et totaux — le travail que vos équipes font à la main.")

    # ══════════ Q&A CONNAISSANCE + ÉTANCHÉITÉ ══════════
    print("\n💬 4. Q&A sur les procédures + ÉTANCHÉITÉ inter-départements…")
    r = ask(base, key, f'/api/enterprise/departments/{comptable}/ask', 'POST',
            {'question': "quelle est la procédure de clôture annuelle ?"})
    print(f"   ❓ (département comptabilité) → confiance {r['confidence']:.2f} "
          f"| {r['answer'][:60]}…")
    assert r['confidence'] < 0.4, 'l étanchéité devrait bloquer'

    r = ask(base, key, f'/api/enterprise/departments/{procedures}/ask', 'POST',
            {'question': "quelle est la procédure de clôture annuelle ?"})
    print(f"   ❓ (département procédures) → confiance {r['confidence']:.2f} "
          f"| {r['answer'][:70]}…")
    assert r['confidence'] >= 0.3
    arg("Chaque département est étanche : le savoir comptable ne répond pas "
        "aux questions de procédures, et inversement. Sécurité totale.")

    # ══════════ LE MOMENT DE VENTE ══════════
    print("\n🎯 5. LE MOMENT : la question piège…")
    r = ask(base, key, f'/api/enterprise/departments/{comptable}/ask', 'POST',
            {'question': "quelle est la couleur du paradis fiscal ?"})
    print(f"   ❓ quelle est la couleur du paradis fiscal ?")
    print(f"   → confiance {r['confidence']:.2f} | {r['answer'][:80]}")
    assert r['confidence'] < 0.4
    arg("ChatGPT aurait répondu quelque chose de plausible — et de faux. "
        "KA Enterprise REFUSE : elle ne répond que sur vos données, et elle "
        "vous le dit quand elle ne sait pas. C'est la différence.")

    # ══════════ DOCUMENTS ══════════
    print("\n✍️ 6. Documents préparés…")
    r = ask(base, key, f'/api/enterprise/departments/{comptable}/compose', 'POST',
            {'brief': "rédige un email aux clients en retard de paiement",
             'format': 'email', 'objet': 'Relance des clients en retard de paiement',
             'destinataire': 'Gérant'})
    assert 'texte' in r and 'Objet' in r['texte']
    print(f"   ✉️ Email ({r['facts_utilises']} faits) :\n{r['texte'][:220]}…")
    arg("Emails, rapports, comptes-rendus rédigés en français — à partir de "
        "vos seules données, téléchargeables en .docx.")

    # ══════════ AUTO-APPRENTISSAGE ══════════
    print("\n🔄 7. Auto-apprentissage (chaînon D)…")
    for i in range(3):
        r = ask(base, key, f'/api/enterprise/departments/{comptable}/ask', 'POST',
                {'question': "quel est le taux de la taxe carbone en 2027 ?"})
        print(f"   {i+1}/3 question sans réponse → confiance {r['confidence']:.2f} "
              f"(enregistrée pour enrichissement)")
        time.sleep(1)
    time.sleep(8)  # laisse la complétion en arrière-plan travailler
    r = call(base, '/api/enterprise/completions/status', 'GET', None, key)
    print(f"   file d'attente : {r.get('file', {}).get('attente', {})}")
    rapports = r.get('rapports', [])
    if rapports:
        rep = rapports[0]
        print(f"   dernier rapport : +{rep.get('facts_ajoutes')} faits "
              f"({rep.get('source')}), couverture "
              f"{rep.get('couverture_avant')} → {rep.get('couverture_apres')}")
    arg("L'IA s'enrichit automatiquement des questions restées sans réponse : "
        "plus vos équipes l'utilisent, plus elle devient compétente.")

    print("\n" + "═" * 62)
    print("  ✅ DÉMO TERMINÉE — TOUTES LES ÉTAPES RÉUSSIES")
    print("═" * 62)


# ── helpers ─────────────────────────────────────────────────────────────────────

def arg(text):
    print(f"\n   💼 ARGUMENT DE VENTE : {text}\n")


def first_agg(r):
    aggs = r.get('aggregates') or []
    assert aggs, f"pas d'agrégat: {r}"
    return aggs[0]['valeur']


def ask_data(base, key, dept, question):
    return call(base, f'/api/enterprise/departments/{dept}/data', 'POST',
                {'question': question}, key)


def ask(base, key, path, method, body=None):
    return call(base, path, method, body, key)


def call(base, path, method, body, key):
    req = urllib.request.Request(
        base + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method)
    req.add_header('Content-Type', 'application/json')
    if key:
        req.add_header('X-API-Key', key)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            return json.loads(content) if content else None
    except urllib.error.HTTPError as e:
        raise AssertionError(f"HTTP {e.code} {path}: {e.read().decode()[:200]}")


if __name__ == '__main__':
    main()
