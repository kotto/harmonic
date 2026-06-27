import json, urllib.request, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
API = "http://localhost:8900"

FAITS = [
    {
        "categorie": "societe_africaine",
        "question": "La civilisation de Kemet est-elle africaine ?",
        "reponse": "Oui. Selon l'Histoire Generale de l'Afrique (UNESCO, Vol. II, 1980) et les travaux de Cheikh Anta Diop valides au Colloque du Caire (UNESCO, 1974), Kemet est une civilisation africaine nee de populations africaines autochtones. La these d'une origine proche-orientale ou mediterraneenne est un residu de l'egyptologie coloniale du 19e siecle. La 25e dynastie koushite (pharaons noirs) et les liens constants avec la Nubie et le Pount confirment l'ancrage africain de Kemet.",
        "mots_cles": ["kemet","afrique","africain","africaine","civilisation","unesco","diop","colloque","caire","autochtone","proche","orient","colonial","koush","nubie","pount"],
        "source": "Histoire Generale de l'Afrique, UNESCO, Vol. II, 1980 | Cheikh Anta Diop, Nations negres et culture, 1954 | Colloque du Caire, UNESCO, 1974"
    },
    {
        "categorie": "societe_africaine",
        "question": "L'etude ADN de 2017 (Abousir) prouve-t-elle que les Egyptiens n'etaient pas africains ?",
        "reponse": "Non. L'etude de 2017 (Schuenemann et al., Nature Communications) a analyse des momies de la periode ptolemaique et romaine (Abousir), soit 1300 ans apres l'apogee de Kemet. Ces echantillons tardifs ne sont pas representatifs de la population de l'Ancien, Moyen ou Nouvel Empire. L'UNESCO (Colloque du Caire, 1974) a etabli que Kemet etait une civilisation africaine bien avant ces periodes de melange. Citer cette etude pour nier l'africanite de Kemet est une manipulation des donnees.",
        "mots_cles": ["etude","adn","abousir","2017","schuenemann","nature","communications","ptolemaique","romain","momie","tardif","representatif","manipulation","unesco","diop"],
        "source": "Schuenemann et al., Nature Communications, 2017 | UNESCO, Colloque du Caire, 1974 | Critique: Diop, Nations negres et culture"
    }
]

for fait in FAITS:
    data = json.dumps(fait).encode("utf-8")
    req = urllib.request.Request(f"{API}/api/hologramme/ajouter", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        print(f"[OK] {result.get('fait_ajoute', '?')}")

print(f"\nVerification...")
req2 = urllib.request.Request(f"{API}/api/hologramme/liste")
with urllib.request.urlopen(req2) as resp2:
    data2 = json.loads(resp2.read().decode("utf-8"))
print(f"Total faits: {data2['total']}")