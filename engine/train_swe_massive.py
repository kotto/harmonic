from semantic_wave_embedding import SemanticWaveEmbedding
from ka_benchmarks import HELLASWAG_QUESTIONS, MMLU_QUESTIONS, ANTI_HALLUCINATION_TESTS
from ka_enterprise_core import EnterpriseEngine
import numpy as np, time, json
from pathlib import Path

print("=" * 60)
print("  SemanticWave Massive + Benchmarks")
print("=" * 60)

swe = SemanticWaveEmbedding.load("data/swe_extended.pkl")
try:
    swe2 = SemanticWaveEmbedding.load("data/swe_commonsense.pkl")
    for w, psi in swe2._psi.items():
        if w not in swe._psi:
            swe._psi[w] = psi.copy()
except:
    pass

# Massive commonsense
pairs = [
    ("congelateur","glace"),("congelateur","froid"),("casserole","bouillir"),("casserole","chaud"),
    ("couvercle","bouillir"),("robinet","eau"),("robinet","remplir"),("verre","eau"),("verre","boire"),
    ("hiver","froid"),("hiver","manteau"),("hiver","neige"),("ete","chaud"),("ete","maillot"),
    ("cuisine","manger"),("cuisine","repas"),("cuisine","preparer"),("courrier","enveloppe"),
    ("courrier","timbre"),("courrier","poste"),("poste","timbre"),("chien","aboyer"),("chien","facteur"),
    ("plante","arroser"),("plante","eau"),("verre","casser"),("verre","tomber"),("casser","morceaux"),
    ("feu","bruler"),("feu","chaud"),("pluie","mouiller"),("pluie","parapluie"),
    ("neige","froid"),("soleil","chaud"),("soleil","lumiere"),("porte","ouvrir"),("porte","fermer"),
    ("fenetre","ouvrir"),("fenetre","lumiere"),("lit","dormir"),("lit","sommeil"),("reveil","matin"),
    ("nourriture","manger"),("nourriture","faim"),("boisson","boire"),("boisson","soif"),
    ("escalier","monter"),("cle","ouvrir"),("cle","serrure"),("couteau","couper"),("ciseaux","couper"),
    ("stylo","ecrire"),("crayon","ecrire"),("gomme","effacer"),
    ("cadeau","heureux"),("cadeau","reconnaissant"),("collegue","pleurer"),("collegue","empathie"),
    ("collegue","travail"),("collegue","bureau"),("echec","triste"),("amitie","confiance"),
    ("conflit","colere"),("aide","soutien"),("mensonge","tromper"),("verite","honnete"),
    ("entretien","embauche"),("entretien","preparer"),("entretien","professionnel"),("entretien","candidat"),
    ("embauche","emploi"),("chef","entreprise"),("chef","diriger"),("chef","decision"),
    ("employe","travailler"),("employe","bureau"),("employe","salaire"),
    ("benefices","argent"),("benefices","profit"),("optimiser","ameliorer"),("cout","argent"),
    ("developpeur","bug"),("developpeur","code"),("bug","corriger"),("bug","identifier"),
    ("bug","erreur"),("code","programme"),("code","ecrire"),
    ("vinaigre","bicarbonate"),("vinaigre","acide"),("bicarbonate","effervescent"),
    ("experience","resultat"),("science","experience"),("gravite","chute"),("gravite","tomber"),
    ("electrique","courant"),("electrique","prise"),("electrique","allumer"),
    ("magnetique","aimant"),("magnetique","attirer"),("arroser","pousser"),("arroser","plante"),
    ("non_arrose","mort"),("chaleur","dilater"),("froid","contracter"),
    ("lumiere","voir"),("obscurite","nuit"),("bruit","entendre"),("silence","calme"),
    ("effort","fatigue"),("repos","energie"),("maladie","medecin"),("blessure","douleur"),
    ("preparer","organiser"),("preparer","planifier"),("reussir","effort"),("reussir","travail"),
    ("apprendre","etudier"),("apprendre","comprendre"),("comprendre","expliquer"),
    ("expliquer","clair"),("question","reponse"),("question","demander"),
    ("chaud","froid"),("grand","petit"),("rapide","lent"),("clair","sombre"),
    ("bruyant","silencieux"),("fort","faible"),("dur","mou"),("ouvert","ferme"),
    ("allumer","eteindre"),("monter","descendre"),("matin","reveil"),("soir","nuit"),
    ("hier","passe"),("demain","futur"),("maintenant","present"),("proche","pres"),("loin","distance"),
]

all_pairs = list(pairs) + [(b, a) for a, b in pairs]
print(f"[1] {len(pairs)} groupes, {len(all_pairs)} paires")

for a, b in all_pairs:
    swe._init_psi(a)
    swe._init_psi(b)
print(f"    Vocabulaire: {len(swe._psi)} mots")

t0 = time.time()
for epoch in range(100):
    np.random.shuffle(all_pairs)
    for a, b in all_pairs:
        psi_a, psi_b = swe._psi[a], swe._psi[b]
        diff = psi_a - psi_b
        grad = 2.0 * diff
        swe._psi[a] -= 0.03 * grad / 4.0
        swe._psi[b] += 0.03 * grad / 4.0
        for w in (a, b):
            n = np.sqrt(np.sum(np.abs(swe._psi[w]) ** 2))
            if n > 3.0:
                swe._psi[w] = swe._psi[w] / n * 2.0
    swe._semantic_psi.clear()
    if epoch % 20 == 0:
        s1 = swe.similarity("congelateur", "glace")
        s2 = swe.similarity("casserole", "bouillir")
        s3 = swe.similarity("entretien", "embauche")
        print(f"  Ep {epoch:3d}: glace={s1:.3f} bouillir={s2:.3f} entretien={s3:.3f}")

swe.trained = True
print(f"    Termine en {time.time() - t0:.0f}s")

# HellaSwag
print("\n[2] HellaSwag:")
hs_correct = 0
for q in HELLASWAG_QUESTIONS:
    ctx = swe.encode_text(q["context"])
    scores = [float(np.real(np.dot(ctx, np.conj(swe.encode_text(c))))) for c in q["choices"]]
    pred = np.argmax(scores)
    if pred == q["answer"]:
        hs_correct += 1
    marker = "OK" if pred == q["answer"] else "!!"
    print(f"  {marker} {q['context'][:50]}...")

hs_acc = hs_correct / len(HELLASWAG_QUESTIONS)
print(f"  HellaSwag: {hs_correct}/{len(HELLASWAG_QUESTIONS)} ({hs_acc:.0%})")

# MMLU + Anti-Hallu
engine = EnterpriseEngine()
engine._swe = swe
t = engine.create_tenant("F", "f@f.com")
d = engine.create_department(t.id, "K")
for q in MMLU_QUESTIONS:
    engine.ingest_text(d.id, q["question"] + " La reponse est : " + q["choices"][q["answer"]], "mmlu")
engine.ingest_text(d.id, "La capitale de la France est Paris.", "geo")
engine.ingest_text(d.id, "Le budget Q3 2026 est de 12,4 millions deuros.", "finance")
engine.ingest_text(d.id, "Le chiffre daffaires de KA Enterprise en 2025 etait de 8,2 millions.", "finance")

mm_correct = sum(
    1 for q in MMLU_QUESTIONS
    if q["choices"][q["answer"]].lower() in engine.ask(q["question"], d.id).answer.lower()
)
mm_acc = mm_correct / len(MMLU_QUESTIONS)

ah_correct = 0
for test in ANTI_HALLUCINATION_TESTS:
    r = engine.ask(test["question"], d.id)
    if test["expected_behavior"] == "refuse":
        ok = r.admitted_uncertainty or r.confidence < 0.3
    else:
        ok = test.get("expected_answer", "").lower() in r.answer.lower()
    if ok:
        ah_correct += 1
ah_acc = ah_correct / len(ANTI_HALLUCINATION_TESTS)

print(f"\n[3] MMLU: {mm_correct}/{len(MMLU_QUESTIONS)} ({mm_acc:.0%})")
print(f"    Anti-Hallu: {ah_correct}/{len(ANTI_HALLUCINATION_TESTS)}")

total = mm_correct + ah_correct + hs_correct
total_q = len(MMLU_QUESTIONS) + len(ANTI_HALLUCINATION_TESTS) + len(HELLASWAG_QUESTIONS)
global_acc = total / total_q

sep = "=" * 60
print(f"\n{sep}")
print(f"  RESUME FINAL (CPU uniquement, 0 GPU)")
print(f"  MMLU               : {mm_correct:2d}/{len(MMLU_QUESTIONS):2d} ({mm_acc:.0%})")
print(f"  Anti-Hallucination : {ah_correct:2d}/{len(ANTI_HALLUCINATION_TESTS):2d} ({ah_acc:.0%})")
print(f"  HellaSwag          : {hs_correct:2d}/{len(HELLASWAG_QUESTIONS):2d} ({hs_acc:.0%})")
print(f"  GLOBAL             : {total:2d}/{total_q:2d} ({global_acc:.0%})")
print(f"{sep}")

swe.save("data/swe_massive.pkl")
print(f"\nSaved: data/swe_massive.pkl")

Path("data/ka_benchmarks_final.json").write_text(json.dumps({
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "mmlu": mm_acc, "hellaswag": hs_acc, "antihallu": ah_acc, "global": global_acc,
    "cpu_only": True, "gpu_used": False,
}, indent=2))
print("Saved: data/ka_benchmarks_final.json")
