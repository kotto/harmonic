"""Merge 110K NPZ + structured factual facts → knowledge_base_merged_v3.npz"""
import numpy as np
from collections import defaultdict

d = np.load('data/bootstrapper_output/knowledge_base_100k.npz', allow_pickle=True)
facts = [(str(f[0]), str(f[1]), str(f[2]), str(f[3])) for f in d['facts']]
print(f'Base: {len(facts):,}')

# Faits structurés FACTUELS
S = []

# 50 capitales
for country, city in [
    ('France','Paris'),('Japon','Tokyo'),('Allemagne','Berlin'),('Royaume-Uni','Londres'),
    ('Bresil','Brasilia'),('Canada','Ottawa'),('Australie','Canberra'),('Inde','New Delhi'),
    ('Chine','Pekin'),('Russie','Moscou'),('Italie','Rome'),('Espagne','Madrid'),
    ('Portugal','Lisbonne'),('Grece','Athenes'),('Turquie','Ankara'),('Egypte','Le Caire'),
    ('Nigeria','Abuja'),('Kenya','Nairobi'),('Afrique du Sud','Pretoria'),('Senegal','Dakar'),
    ('Coree du Sud','Seoul'),('Argentine','Buenos Aires'),('Mexique','Mexico'),('Perou','Lima'),
    ('Colombie','Bogota'),('Chili','Santiago'),('Maroc','Rabat'),('Tunisie','Tunis'),
    ('Algerie','Alger'),('Ethiopie','Addis-Abeba'),('Ghana','Accra'),('Cote d Ivoire','Abidjan'),
    ('Suede','Stockholm'),('Norvege','Oslo'),('Danemark','Copenhague'),('Finlande','Helsinki'),
    ('Pologne','Varsovie'),('Ukraine','Kiev'),('Autriche','Vienne'),('Suisse','Berne'),
    ('Belgique','Bruxelles'),('Pays-Bas','Amsterdam'),('Irlande','Dublin'),('Thailande','Bangkok'),
    ('Vietnam','Hanoi'),('Indonesie','Jakarta'),('Philippines','Manille'),('Iran','Teheran'),
    ('Irak','Bagdad'),('Arabie Saoudite','Riyad'),
]:
    S.append((country, 'a pour capitale', city, 'GEOGRAPHIE'))

# Continents
for country, continent in [
    ('France','Europe'),('Japon','Asie'),('Bresil','Amerique du Sud'),('Kenya','Afrique'),
    ('Canada','Amerique du Nord'),('Australie','Oceanie'),('Inde','Asie'),('Chine','Asie'),
    ('Egypte','Afrique'),('Nigeria','Afrique'),('Maroc','Afrique'),('Thailande','Asie'),
    ('Mexique','Amerique du Nord'),('Perou','Amerique du Sud'),('Suede','Europe'),
    ('Indonesie','Asie'),('Arabie Saoudite','Asie'),('Algerie','Afrique'),('Senegal','Afrique'),
    ('Afrique du Sud','Afrique'),('Ethiopie','Afrique'),('Ghana','Afrique'),
]:
    S.append((country, 'est situe en', continent, 'GEOGRAPHIE'))

# Éléments
for name, sym, num in [
    ('Hydrogene','H',1),('Helium','He',2),('Lithium','Li',3),('Beryllium','Be',4),
    ('Bore','B',5),('Carbone','C',6),('Azote','N',7),('Oxygene','O',8),('Fluor','F',9),
    ('Neon','Ne',10),('Sodium','Na',11),('Magnesium','Mg',12),('Aluminium','Al',13),
    ('Silicium','Si',14),('Phosphore','P',15),('Soufre','S',16),('Chlore','Cl',17),
    ('Argon','Ar',18),('Potassium','K',19),('Calcium','Ca',20),('Fer','Fe',26),
    ('Cuivre','Cu',29),('Zinc','Zn',30),('Argent','Ag',47),('Or','Au',79),
    ('Mercure','Hg',80),('Plomb','Pb',82),('Uranium','U',92),('Plutonium','Pu',94),
    ('Radium','Ra',88),('Iode','I',53),('Titane','Ti',22),('Nickel','Ni',28),
    ('Platine','Pt',78),('Cobalt','Co',27),('Manganese','Mn',25),
]:
    S.append((name, 'a pour symbole chimique', sym, 'SCIENCES'))
    S.append((name, 'a pour numero atomique', str(num), 'SCIENCES'))

# Scientifiques
for s, r, o, sec in [
    ('Albert Einstein','a decouvert','la relativite','SCIENCES'),
    ('Marie Curie','a decouvert','le radium','SCIENCES'),
    ('Isaac Newton','a decouvert','la gravitation universelle','SCIENCES'),
    ('Charles Darwin','a propose','la theorie de l evolution','SCIENCES'),
    ('Louis Pasteur','a developpe','la pasteurisation','SCIENCES'),
    ('Niels Bohr','a propose','le modele atomique','SCIENCES'),
    ('Max Planck','a decouvert','les quanta','SCIENCES'),
    ('Galileo Galilei','a decouvert','les satellites de Jupiter','SCIENCES'),
    ('James Watson','a co-decouvert','la structure de l ADN','SCIENCES'),
    ('Francis Crick','a co-decouvert','la structure de l ADN','SCIENCES'),
    ('Dmitri Mendeleiev','a cree','le tableau periodique','SCIENCES'),
    ('Alfred Nobel','a invente','la dynamite','SCIENCES'),
    ('Alexander Fleming','a decouvert','la penicilline','SCIENCES'),
    ('Nikola Tesla','a invente','le courant alternatif','SCIENCES'),
    ('Thomas Edison','a invente','l ampoule electrique','SCIENCES'),
    ('Alan Turing','a invente','la machine de Turing','SCIENCES'),
    ('Stephen Hawking','a etudie','les trous noirs','SCIENCES'),
    ('Gregor Mendel','a decouvert','les lois de l heredite','SCIENCES'),
]:
    S.append((s, r, o, sec))

# Artistes
for s, r, o, sec in [
    ('Leonard de Vinci','a peint','la Joconde','CULTURE'),
    ('Vincent van Gogh','a peint','la Nuit etoilee','CULTURE'),
    ('Pablo Picasso','a peint','Guernica','CULTURE'),
    ('Claude Monet','a peint','les Nympheas','CULTURE'),
    ('Michel-Ange','a sculpte','David','CULTURE'),
    ('Rembrandt','a peint','la Ronde de nuit','CULTURE'),
    ('Salvador Dali','a peint','la Persistance de la memoire','CULTURE'),
    ('Edvard Munch','a peint','le Cri','CULTURE'),
    ('Frida Kahlo','a peint','les Deux Fridas','CULTURE'),
    ('Johannes Vermeer','a peint','la Jeune Fille a la perle','CULTURE'),
    ('Hokusai','a cree','la Grande Vague de Kanagawa','CULTURE'),
    ('Gustav Klimt','a peint','le Baiser','CULTURE'),
    ('Eugene Delacroix','a peint','la Liberte guidant le peuple','CULTURE'),
    ('Henri Matisse','a peint','la Danse','CULTURE'),
]:
    S.append((s, r, o, sec))

# Écrivains
for s, r, o in [
    ('Victor Hugo','a ecrit','Les Miserables'),('Marcel Proust','a ecrit','A la recherche du temps perdu'),
    ('Albert Camus','a ecrit','L Etranger'),('Jules Verne','a ecrit','Vingt mille lieues sous les mers'),
    ('William Shakespeare','a ecrit','Romeo et Juliette'),('Jane Austen','a ecrit','Orgueil et Prejuges'),
    ('Fiodor Dostoievski','a ecrit','Crime et Chatiment'),('Leo Tolstoi','a ecrit','Guerre et Paix'),
    ('Gabriel Garcia Marquez','a ecrit','Cent ans de solitude'),('George Orwell','a ecrit','1984'),
    ('Homere','a ecrit','l Odyssee'),('Dante Alighieri','a ecrit','la Divine Comedie'),
    ('Cervantes','a ecrit','Don Quichotte'),('Franz Kafka','a ecrit','La Metamorphose'),
]:
    S.append((s, r, o, 'CULTURE'))

# Monuments
for s, r, o in [
    ('Tour Eiffel','est situee a','Paris'),('Statue de la Liberte','est situee a','New York'),
    ('Colisee','est situe a','Rome'),('Taj Mahal','est situe a','Agra'),
    ('Grande Muraille','est situee en','Chine'),('Machu Picchu','est situe au','Perou'),
    ('Big Ben','est situe a','Londres'),('Opera de Sydney','est situe a','Sydney'),
    ('Sagrada Familia','est situee a','Barcelone'),('Acropole','est situee a','Athenes'),
    ('Mont Saint-Michel','est situe en','France'),('Angkor Vat','est situe au','Cambodge'),
    ('Petra','est situee en','Jordanie'),('Christ Redempteur','est situe a','Rio de Janeiro'),
]:
    S.append((s, r, o, 'GEOGRAPHIE'))

# Prix Nobel
for s, r, o in [
    ('Marie Curie','a recu le prix Nobel de physique','physique'),
    ('Marie Curie','a recu le prix Nobel de chimie','chimie'),
    ('Albert Einstein','a recu le prix Nobel de','physique'),
    ('Martin Luther King','a recu le prix Nobel de','la paix'),
    ('Nelson Mandela','a recu le prix Nobel de','la paix'),
    ('Mere Teresa','a recu le prix Nobel de','la paix'),
    ('Bob Dylan','a recu le prix Nobel de','litterature'),
    ('Winston Churchill','a recu le prix Nobel de','litterature'),
    ('Ernest Hemingway','a recu le prix Nobel de','litterature'),
]:
    sec = 'SCIENCES' if 'physique' in o or 'chimie' in o else ('POLITIQUE' if 'paix' in o else 'CULTURE')
    S.append((s, r, o, sec))

print(f'Structures: {len(S):,}')

# Fusion
seen = set()
for s, r, o, _ in facts:
    seen.add((s.lower()[:60], r.lower()[:60], str(o).lower()[:60]))

added = 0
for s, r, o, sec in S:
    key = (s.lower()[:60], r.lower()[:60], str(o).lower()[:60])
    if key not in seen:
        seen.add(key)
        facts.append((s, r, o, sec))
        added += 1

print(f'Ajoutes: {added}')
print(f'Total: {len(facts):,}')

np.savez_compressed('data/bootstrapper_output/knowledge_base_merged_v3.npz',
    facts=np.array(facts, dtype=object))
print('Saved: knowledge_base_merged_v3.npz')

# Secteurs
sectors = defaultdict(int)
for _, _, _, sec in facts:
    sectors[sec] += 1
for sec, n in sorted(sectors.items(), key=lambda x: -x[1])[:12]:
    print(f'  {sec:25} {n:>8,}')
