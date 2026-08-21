"""
KA Server — Service SQL Querier
================================
Text-to-SQL (MVP) : interroger des données structurées par langage naturel,
sans LLM — pattern matching déterministe comme detect_and_solve_math.

Le service :
  1. Maintient une base SQLite exemple en mémoire (ventes, produits, régions, employés)
  2. Détecte l'intention SQL dans une question en français/anglais
  3. Génère et exécute la requête SQL dans un bac à sable (lecture seule)
  4. Retourne les résultats structurés

Pattern : {'handled': True/False, 'sql': str, 'result': list, 'columns': list}
"""

import logging
import re
import sqlite3
from datetime import datetime, date, timedelta
import calendar
from typing import Optional, List, Dict, Any

log = logging.getLogger(__name__)

# ── Base exemple (créée en mémoire au premier appel) ──────────────────────
_DB_CONN: Optional[sqlite3.Connection] = None


def get_sample_db() -> sqlite3.Connection:
    """Crée et peuple une base SQLite exemple en mémoire."""
    global _DB_CONN
    if _DB_CONN is not None:
        return _DB_CONN

    conn = sqlite3.connect(':memory:', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE produits (
            id INTEGER PRIMARY KEY,
            nom TEXT NOT NULL,
            categorie TEXT,
            prix_unitaire REAL
        );
        CREATE TABLE regions (
            id INTEGER PRIMARY KEY,
            nom TEXT NOT NULL,
            pays TEXT
        );
        CREATE TABLE ventes (
            id INTEGER PRIMARY KEY,
            produit_id INTEGER REFERENCES produits(id),
            region_id INTEGER REFERENCES regions(id),
            quantite INTEGER NOT NULL,
            montant REAL NOT NULL,
            date_vente TEXT NOT NULL,
            client TEXT
        );
        CREATE TABLE employes (
            id INTEGER PRIMARY KEY,
            nom TEXT NOT NULL,
            departement TEXT NOT NULL,
            salaire REAL,
            date_embauche TEXT
        );
    """)

    # Produits
    produits = [
        ('Laptop Pro X', 'Électronique', 1299.99),
        ('Smartphone Z3', 'Électronique', 899.99),
        ('Casque Audio', 'Électronique', 149.99),
        ('Tablette Graphite', 'Électronique', 449.99),
        ('Clavier Mécanique', 'Accessoires', 89.99),
        ('Souris Sans Fil', 'Accessoires', 49.99),
        ('Écran 27 pouces', 'Électronique', 349.99),
        ('Chaise Ergonomique', 'Mobilier', 599.99),
        ('Bureau Assis-Debout', 'Mobilier', 899.99),
        ('Lampe Bureau LED', 'Accessoires', 39.99),
        ('Imprimante Laser', 'Électronique', 249.99),
        ('Disque SSD 1To', 'Électronique', 129.99),
    ]
    cur.executemany("INSERT INTO produits (nom, categorie, prix_unitaire) VALUES (?,?,?)", produits)

    # Régions
    regions = [
        ('Île-de-France', 'France'),
        ('Auvergne-Rhône-Alpes', 'France'),
        ('Nouvelle-Aquitaine', 'France'),
        ('Occitanie', 'France'),
        ('Hauts-de-France', 'France'),
        ('Bretagne', 'France'),
        ('Grand Est', 'France'),
        ('Provence-Alpes-Côte d\'Azur', 'France'),
        ('Brussels-Capital', 'Belgique'),
        ('Flanders', 'Belgique'),
        ('Wallonia', 'Belgique'),
        ('Geneva', 'Suisse'),
        ('Vaud', 'Suisse'),
        ('Zurich', 'Suisse'),
        ('Montreal', 'Canada'),
        ('Toronto', 'Canada'),
        ('Casablanca', 'Maroc'),
        ('Rabat', 'Maroc'),
    ]
    cur.executemany("INSERT INTO regions (nom, pays) VALUES (?,?)", regions)

    # Ventes (3 ans de données)
    import random
    random.seed(42)
    today = date.today()
    ventes_data = []
    for i in range(1, 501):
        pid = random.randint(1, len(produits))
        rid = random.randint(1, len(regions))
        qty = random.randint(1, 50)
        unit_price = produits[pid - 1][2]
        amount = round(qty * unit_price * random.uniform(0.9, 1.1), 2)
        days_ago = random.randint(0, 365 * 3)
        dt = today - timedelta(days=days_ago)
        client = random.choice(['', 'Client A', 'Client B', 'Client C', 'SARL Dupont', 'TechCorp', 'GreenLab', 'MédiSanté'])
        ventes_data.append((pid, rid, qty, amount, dt.isoformat(), client))
    cur.executemany("INSERT INTO ventes (produit_id, region_id, quantite, montant, date_vente, client) VALUES (?,?,?,?,?,?)", ventes_data)

    # Employés
    employes = [
        ('Alice Martin', 'Informatique', 65000.0, '2020-03-15'),
        ('Bob Dubois', 'Informatique', 58000.0, '2021-06-01'),
        ('Claire Lefebvre', 'Finance', 72000.0, '2019-09-10'),
        ('David Moreau', 'Finance', 62000.0, '2020-11-20'),
        ('Emma Petit', 'Ressources Humaines', 55000.0, '2022-01-05'),
        ('François Bernard', 'Marketing', 59000.0, '2021-04-12'),
        ('Gabrielle Roux', 'Marketing', 51000.0, '2022-08-22'),
        ('Hugo Lambert', 'Informatique', 70000.0, '2018-05-30'),
        ('Isabelle Mercier', 'Finance', 68000.0, '2019-12-01'),
        ('Jules Girard', 'Ressources Humaines', 52000.0, '2023-02-14'),
        ('Karim Benali', 'Informatique', 63000.0, '2020-07-08'),
        ('Laura Fontaine', 'Marketing', 54000.0, '2021-10-18'),
        ('Marc Delacroix', 'Finance', 75000.0, '2018-01-22'),
        ('Nathalie Chevalier', 'Ressources Humaines', 57000.0, '2020-04-05'),
        ('Olivier Dupont', 'Informatique', 66000.0, '2019-08-15'),
        ('Patricia Gauthier', 'Marketing', 53000.0, '2022-06-28'),
    ]
    cur.executemany("INSERT INTO employes (nom, departement, salaire, date_embauche) VALUES (?,?,?,?)", employes)

    conn.commit()
    _DB_CONN = conn
    log.info(f"  🗄️  SQL Querier — base exemple créée (4 tables, 500 ventes, 16 employés, 18 régions)")
    return conn


def get_demo_schema() -> list:
    """Retourne le schéma des tables disponibles (nom + colonnes)."""
    conn = get_sample_db()
    cur = conn.cursor()
    tables = []
    for tname in ('ventes', 'produits', 'regions', 'employes'):
        cur.execute(f"PRAGMA table_info({tname})")
        columns = [{'name': row[1], 'type': row[2]} for row in cur.fetchall()]
        tables.append({'table': tname, 'columns': columns})
    return tables


def get_friendly_schema() -> str:
    """Retourne une description lisible du schéma pour le débogage."""
    lines = []
    for t in get_demo_schema():
        cols = ', '.join(f"{c['name']} ({c['type']})" for c in t['columns'])
        lines.append(f"  {t['table']}: {cols}")
    return '\n'.join(lines)


# ── Détection d'intention SQL ─────────────────────────────────────────────

_MOTS_CLES_TABLES = {
    'vente': 'ventes',
    'ventes': 'ventes',
    'chiffre d\'affaire': 'ventes',
    'chiffre d\'affaires': 'ventes',
    'ca': 'ventes',
    'montant': 'ventes',
    'vendu': 'ventes',
    'vente': 'ventes',
    'client': 'ventes',
    'produit': 'produits',
    'produits': 'produits',
    'categorie': 'produits',
    'catégorie': 'produits',
    'region': 'regions',
    'région': 'regions',
    'regions': 'regions',
    'pays': 'regions',
    'employe': 'employes',
    'employés': 'employes',
    'employe': 'employes',
    'salarié': 'employes',
    'salariés': 'employes',
    'salaire': 'employes',
    'departement': 'employes',
    'département': 'employes',
}


def _detect_table(question: str) -> Optional[str]:
    """Détecte la table principale concernée par la question."""
    ql = question.lower()

    # D'abord : si la question mentionne un montant/CA, c'est forcément ventes
    if any(w in ql for w in ['ca', 'chiffre d\'affaire', 'chiffre d\'affaires',
                               'montant', 'vente', 'ventes', 'revenue', 'chiffre',
                               'total des ventes', 'prix']):
        return 'ventes'

    # Sinon : détection par mot-clé
    for mot, table in sorted(_MOTS_CLES_TABLES.items(), key=lambda x: -len(x[0])):
        if mot in ql:
            return table
    return 'ventes'  # fallback


def _normalize_number_expr(expr: str) -> str:
    """Normalise les expressions numériques françaises."""
    # "1 000" → "1000", "1,5" → "1.5"
    expr = re.sub(r'(\d)\s+(\d)', r'\1\2', expr)
    expr = expr.replace(',', '.')
    return expr


def _parse_condition(question: str, table: str) -> tuple:
    """Parse les conditions WHERE depuis la question.

    Retourne (clause_sql, params) où params est une liste de valeurs.
    """
    ql = question.lower()
    clauses = []
    params = []
    today = date.today()

    # ── Périodes temporelles ──
    if any(w in ql for w in ['ce mois', 'ce mois-ci', 'mois dernier', 'mois en cours']):
        debut = today.replace(day=1)
        fin = today
        if 'mois dernier' in ql:
            debut = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            fin = today.replace(day=1) - timedelta(days=1)
        clauses.append('date_vente >= ?')
        params.append(debut.isoformat())
        clauses.append('date_vente <= ?')
        params.append(fin.isoformat())
    elif any(w in ql for w in ['cette année', 'cette annee', 'année en cours', 'annee en cours']):
        debut = today.replace(month=1, day=1)
        clauses.append('date_vente >= ?')
        params.append(debut.isoformat())
    elif 'trimestre' in ql:
        # Dernier trimestre
        m = today.month
        q_start = ((m - 1) // 3) * 3 + 1
        debut = today.replace(month=q_start, day=1)
        clauses.append('date_vente >= ?')
        params.append(debut.isoformat())
    elif any(w in ql for w in ['dernier mois', 'le mois dernier', 'mois passé']):
        debut = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        fin = today.replace(day=1) - timedelta(days=1)
        clauses.append('date_vente >= ?')
        params.append(debut.isoformat())
        clauses.append('date_vente <= ?')
        params.append(fin.isoformat())

    # ── Conditions de table ──
    if table == 'employes':
        dept_match = re.search(r'(?:dans? le?|du|de la)?\s*([a-zéèêëàâäùûüôîïç\s-]+?)(?: où| qui| avec| de|$)', ql)
        known_depts = ['informatique', 'finance', 'marketing', 'ressources humaines', 'rh']
        if dept_match:
            dept = dept_match.group(1).strip().lower()
            for kd in known_depts:
                if kd in dept:
                    clauses.append('departement = ?')
                    params.append(kd.capitalize())
                    break

    return ' AND '.join(clauses), params


def _is_sql_like(question: str) -> tuple:
    """Détecte si une question est de type SQL-requêtable.

    Retourne (agg: str|None, group_by: str|None, order: str|None, limit: int|None)
    """
    ql = question.lower()
    agg = None
    group_by = None
    order = None
    limit = None

    # Agrégations
    if any(w in ql for w in ['total', 'montant total', 'ca', 'chiffre d\'affaire', 'sum', 'somme']):
        agg = 'SUM'
    elif any(w in ql for w in ['moyenne', 'moyen', 'moy', 'average', 'avg']):
        agg = 'AVG'
    elif any(w in ql for w in ['nombre', 'combien', 'count', 'compte']):
        agg = 'COUNT'
    elif any(w in ql for w in ['maximum', 'max', 'plus grand', 'plus élevé']):
        agg = 'MAX'
    elif any(w in ql for w in ['minimum', 'min', 'plus petit', 'plus faible']):
        agg = 'MIN'

    # GROUP BY (par région, par catégorie, par mois, etc.)
    if any(w in ql for w in ['par région', 'par region', 'par pays', 'par catégorie', 'par categorie',
                              'par produit', 'par mois', 'par département', 'par departement',
                              'par client']):
        if 'région' in ql or 'region' in ql:
            group_by = 'regions.nom'
        elif 'pays' in ql:
            group_by = 'regions.pays'
        elif 'catégorie' in ql or 'categorie' in ql:
            group_by = 'produits.categorie'
        elif 'produit' in ql:
            group_by = 'produits.nom'
        elif 'mois' in ql:
            group_by = "substr(date_vente, 1, 7)"
        elif 'département' in ql or 'departement' in ql:
            group_by = 'employes.departement'
        elif 'client' in ql:
            group_by = 'ventes.client'

    # ORDER BY (top, meilleur, pire, etc.)
    if any(w in ql for w in ['top', 'meilleur', 'plus grand', 'plus élevé']):
        order = 'DESC'
        limit = 5
    elif any(w in ql for w in ['pire', 'moins bon', 'plus faible']):
        order = 'ASC'
        limit = 5

    # Limite explicite
    if limit is None:
        m = re.search(r'(?:top|limite?)\s*(\d+)', ql)
        if m:
            limit = int(m.group(1))

    return agg, group_by, order, limit


def _build_sql(question: str, table: str, agg: str, group_by: str, order: str, limit: int,
               where_clause: str, where_params: list) -> str:
    """Construit la requête SQL à partir des paramètres détectés."""
    field = '*'

    if table == 'ventes':
        if agg:
            if group_by:
                if group_by.startswith('produits') or group_by.startswith('regions'):
                    field = f"{group_by} AS groupe, {agg}(ventes.montant) AS valeur"
                else:
                    field = f"{group_by} AS groupe, {agg}(ventes.montant) AS valeur"
            else:
                field = f"{agg}(ventes.montant) AS valeur"
        col = 'ventes.*'

    elif table == 'produits':
        if agg == 'COUNT':
            field = 'COUNT(*) AS nombre_produits'
        col = 'produits.*'

    elif table == 'employes':
        if agg:
            if group_by:
                field = f"{group_by} AS groupe, {agg}(employes.salaire) AS valeur"
            else:
                field = f"{agg}(employes.salaire) AS valeur"
        col = 'employes.*'

    else:
        col = f'{table}.*'

    # Construction de la requête
    select = field if agg else col
    from_clause = table
    joins = []
    group_by_clause = ''
    order_by_clause = ''
    limit_clause = ''

    # Jointures pour ventes
    if table == 'ventes' and (group_by or 'produit' in question.lower() or 'catégorie' in question.lower()
                              or 'categorie' in question.lower() or 'région' in question.lower()
                              or 'region' in question.lower() or 'pays' in question.lower()):
        joins.append('JOIN produits ON ventes.produit_id = produits.id')
        joins.append('JOIN regions ON ventes.region_id = regions.id')
        if 'produits.nom' in (field or '') or 'regions.nom' in (field or '') or 'regions.pays' in (field or '') or 'produits.categorie' in (field or ''):
            pass  # already in field

    # FROM avec JOINs
    if joins:
        from_clause = f"{table} {' '.join(joins)}"
    else:
        from_clause = table

    if group_by:
        group_by_clause = f'GROUP BY {group_by}'
    if order:
        order_by_clause = f'ORDER BY valeur {order}'
    if limit:
        limit_clause = f'LIMIT {limit}'

    sql = f'SELECT {select} FROM {from_clause}'
    if where_clause:
        sql += f' WHERE {where_clause}'
    if group_by_clause:
        sql += f' {group_by_clause}'
    if order_by_clause:
        sql += f' {order_by_clause}'
    if limit_clause:
        sql += f' {limit_clause}'
    sql += ';'

    return sql


def detect_and_solve_sql(question: str, schema: list = None) -> dict:
    """Point d'entrée principal : détecte l'intention SQL, génère et exécute.

    Args:
        question: Question en langage naturel (FR ou EN).
        schema: Description optionnelle des tables (utilisée pour validation).

    Returns:
        {'handled': True/False, 'sql': str, 'result': list, 'columns': list,
         'row_count': int, 'error': str|None, 'explanation': str}
    """
    if not question or len(question.strip()) < 3:
        return {'handled': False, 'reason': 'question trop courte'}

    # Vérifier si la question est SQL-requêtable
    table = _detect_table(question)
    agg, group_by, order, limit = _is_sql_like(question)
    where_clause, where_params = _parse_condition(question, table)

    # Si pas d'agrégation et pas de condition, on fait un SELECT simple
    sql = _build_sql(question, table, agg, group_by, order, limit, where_clause, where_params)

    # Exécution
    try:
        conn = get_sample_db()
        cur = conn.cursor()
        cur.execute(sql, where_params)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in rows]

        # Résumé
        if agg:
            val = result[0]['valeur'] if result else 0
            agg_label = {'SUM': 'Total', 'AVG': 'Moyenne', 'COUNT': 'Nombre', 'MAX': 'Maximum', 'MIN': 'Minimum'}
            explanation = f"{agg_label.get(agg, agg)} : {val}"
            if group_by:
                explanation += f" (groupé par {group_by})"
        else:
            explanation = f"{len(result)} résultat(s)"

        return {
            'handled': True,
            'sql': sql,
            'result': result,
            'columns': columns,
            'row_count': len(result),
            'explanation': explanation,
            'error': None,
        }
    except Exception as e:
        log.error(f"SQL execution error: {e}")
        return {
            'handled': True,
            'sql': sql,
            'result': [],
            'columns': [],
            'row_count': 0,
            'explanation': 'Erreur d\'exécution SQL',
            'error': str(e),
        }


def _test():
    """Test rapide."""
    print("=== Tests SQL Querier ===")
    questions = [
        "quel est le CA du mois dernier ?",
        "quel est le nombre d'employés ?",
        "moyenne des ventes par région",
        "top 5 produits par chiffre d'affaires",
        "CA par catégorie",
        "nombre d'employés par département",
        "quel est le total des ventes par région",
    ]
    for q in questions:
        res = detect_and_solve_sql(q)
        status = "✅" if res['handled'] and not res.get('error') else "❌"
        print(f"\n{status} {q}")
        print(f"  SQL: {res.get('sql')}")
        print(f"  Résultat: {res.get('row_count')} lignes | {res.get('explanation')}")
        if res.get('result'):
            print(f"  Premier: {res['result'][0]}")


if __name__ == '__main__':
    _test()