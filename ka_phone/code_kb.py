#!/usr/bin/env python3
"""
CODE KB — Base de connaissances pour langages informatiques
==============================================================
40 patterns de code pour 7 langages.
Fonctionne comme QuickFacts : chaque entree = (id, code, [mots-cles]).
Zero hallucination - code verifie, syntaxe correcte.
"""

CODE_FACTS = [
    ("py_read_file", "```python\nwith open('fichier.txt', 'r', encoding='utf-8') as f:\n    contenu = f.read()\n```", ["python", "lire", "fichier", "open", "read"]),
    ("py_write_file", "```python\nwith open('sortie.txt', 'w', encoding='utf-8') as f:\n    f.write('Hello world')\n```", ["python", "ecrire", "fichier", "write", "save"]),
    ("py_list_comprehension", "```python\ncarres = [x**2 for x in range(10)]\npairs = [x for x in range(20) if x % 2 == 0]\n```", ["python", "list", "comprehension", "liste"]),
    ("py_dict", "```python\ninfos = {'nom': 'KA', 'version': 1.0}\nfor cle, valeur in infos.items():\n    print(f'{cle}: {valeur}')\n```", ["python", "dict", "dictionnaire", "dictionary"]),
    ("py_requests_get", "```python\nimport requests\nr = requests.get('https://api.example.com/data', timeout=10)\nif r.status_code == 200:\n    data = r.json()\n```", ["python", "requests", "api", "http", "get"]),
    ("py_requests_post", "```python\nimport requests\nr = requests.post('https://api.example.com/submit', json={'nom':'KA'})\nprint(r.json())\n```", ["python", "requests", "post", "api", "send"]),
    ("py_try_except", "```python\ntry:\n    resultat = 10 / 0\nexcept ZeroDivisionError:\n    print('Division par zero !')\nexcept Exception as e:\n    print(f'Erreur: {e}')\n```", ["python", "try", "except", "erreur", "exception"]),
    ("py_class", "```python\nclass Animal:\n    def __init__(self, nom):\n        self.nom = nom\n    def parler(self):\n        raise NotImplementedError\n\nclass Chien(Animal):\n    def parler(self):\n        return f'{self.nom} dit Wouf!'\n```", ["python", "class", "objet", "heritage", "oop"]),
    ("py_lambda", "```python\ndouble = lambda x: x * 2\nprint(double(5))\n```", ["python", "lambda", "fonction", "anonyme"]),
    ("py_fstring", "```python\nnom = 'KA'\nprint(f'{nom} version 1.0 est pret.')\npi = 3.14159\nprint(f'Pi = {pi:.2f}')\n```", ["python", "f-string", "format", "string"]),
    ("py_numpy", "```python\nimport numpy as np\narr = np.array([1, 2, 3, 4, 5])\nprint(arr * 2)\nA = np.array([[1,2],[3,4]])\nB = np.array([[5,6],[7,8]])\nprint(A @ B)\n```", ["python", "numpy", "array", "matrice"]),
    ("py_pandas", "```python\nimport pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df.head())\nprint(df.describe())\n```", ["python", "pandas", "csv", "dataframe"]),
    ("py_venv", "```bash\npython -m venv mon_env\n# Windows: mon_env\\\\Scripts\\\\activate\n# Linux: source mon_env/bin/activate\npip install numpy pandas\npip freeze > requirements.txt\n```", ["python", "venv", "environnement", "virtuel", "install", "pip"]),
    ("py_decorator", "```python\nimport time\ndef timer(func):\n    def wrapper(*args, **kwargs):\n        debut = time.time()\n        resultat = func(*args, **kwargs)\n        print(f'{func.__name__} en {time.time()-debut:.2f}s')\n        return resultat\n    return wrapper\n\n@timer\ndef calcul_long():\n    return sum(range(10**6))\n```", ["python", "decorator", "decorateur", "timer"]),
    ("py_async", "```python\nimport asyncio\nasync def fetch(url):\n    await asyncio.sleep(1)\n    return f'Data from {url}'\nasync def main():\n    resultats = await asyncio.gather(fetch('a'), fetch('b'))\nasyncio.run(main())\n```", ["python", "async", "asyncio", "await"]),
    ("js_fetch", "```javascript\nfetch('https://api.example.com/data')\n  .then(response => response.json())\n  .then(data => console.log(data))\n  .catch(error => console.error('Erreur:', error));\n```", ["javascript", "fetch", "api", "http", "ajax"]),
    ("js_async_await", "```javascript\nasync function getData() {\n  try {\n    const response = await fetch('https://api.example.com/data');\n    const data = await response.json();\n    return data;\n  } catch (error) {\n    console.error('Erreur:', error);\n  }\n}\n```", ["javascript", "async", "await", "promise"]),
    ("js_dom", "```javascript\nconst el = document.querySelector('#monId');\nel.textContent = 'Nouveau texte';\nel.style.color = 'red';\n```", ["javascript", "dom", "querySelector", "html"]),
    ("js_event", "```javascript\nconst bouton = document.getElementById('monBouton');\nbouton.addEventListener('click', (event) => {\n  event.preventDefault();\n  console.log('Clique !');\n});\n```", ["javascript", "event", "listener", "click"]),
    ("js_array", "```javascript\nconst arr = [1, 2, 3, 4, 5];\narr.map(x => x * 2);\narr.filter(x => x > 2);\narr.reduce((a,b) => a+b);\n```", ["javascript", "array", "map", "filter", "reduce"]),
    ("js_localStorage", "```javascript\nlocalStorage.setItem('cle', JSON.stringify({nom: 'KA'}));\nconst data = JSON.parse(localStorage.getItem('cle'));\n```", ["javascript", "localStorage", "stockage", "cache"]),
    ("js_node_fs", "```javascript\nconst fs = require('fs');\nconst contenu = fs.readFileSync('fichier.txt', 'utf8');\nfs.writeFileSync('sortie.txt', 'Hello world');\n```", ["javascript", "node.js", "fs", "fichier"]),
    ("html_structure", "```html\n<!DOCTYPE html>\n<html lang=\"fr\">\n<head>\n  <meta charset=\"UTF-8\">\n  <title>Mon site</title>\n  <link rel=\"stylesheet\" href=\"style.css\">\n</head>\n<body>\n  <h1>Bonjour</h1>\n  <script src=\"script.js\"></script>\n</body>\n</html>\n```", ["html", "structure", "doctype", "template"]),
    ("css_center_div", "```css\n.container {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n  min-height: 100vh;\n}\n```", ["css", "center", "centrer", "div", "flex"]),
    ("css_flexbox", "```css\n.container {\n  display: flex;\n  gap: 16px;\n  justify-content: space-between;\n  flex-wrap: wrap;\n}\n```", ["css", "flexbox", "flex", "layout"]),
    ("css_grid", "```css\n.container {\n  display: grid;\n  grid-template-columns: repeat(3, 1fr);\n  gap: 20px;\n}\n```", ["css", "grid", "layout", "columns"]),
    ("sql_select", "```sql\nSELECT nom, age FROM utilisateurs WHERE age > 18 ORDER BY nom ASC LIMIT 10;\n```", ["sql", "select", "where", "order by"]),
    ("sql_join", "```sql\nSELECT u.nom, c.produit\nFROM utilisateurs u\nLEFT JOIN commandes c ON u.id = c.utilisateur_id;\n```", ["sql", "join", "left join", "inner join"]),
    ("sql_create_table", "```sql\nCREATE TABLE utilisateurs (\n  id INTEGER PRIMARY KEY AUTOINCREMENT,\n  nom TEXT NOT NULL,\n  email TEXT UNIQUE,\n  age INTEGER DEFAULT 0\n);\n```", ["sql", "create", "table", "schema"]),
    ("sql_insert_update", "```sql\nINSERT INTO utilisateurs (nom, email, age) VALUES ('Alice', 'alice@mail.com', 25);\nUPDATE utilisateurs SET age = 26 WHERE nom = 'Alice';\nDELETE FROM utilisateurs WHERE id = 1;\n```", ["sql", "insert", "update", "delete", "crud"]),
    ("sql_group_by", "```sql\nSELECT categorie, COUNT(*) as total, AVG(prix) as prix_moyen\nFROM produits GROUP BY categorie HAVING COUNT(*) > 5;\n```", ["sql", "group by", "having", "aggregate"]),
    ("bash_loop", "```bash\nfor fichier in *.txt; do\n  echo \"Traitement de $fichier\"\ndone\n```", ["bash", "for", "loop", "shell"]),
    ("bash_find", "```bash\nfind . -name '*.py' -mtime -7\nfind . -name '*.pyc' -delete\n```", ["bash", "find", "recherche", "shell"]),
    ("bash_grep", "```bash\ngrep -r 'TODO' *.py\ngrep -rn 'function' .\n```", ["bash", "grep", "recherche", "texte", "shell"]),
    ("bash_variables", "```bash\nNOM=\"KA\"\nDATE=$(date +%Y-%m-%d)\nif [ -f \"config.json\" ]; then\n  echo \"Fichier existe\"\nfi\n```", ["bash", "variable", "if", "condition", "shell"]),
    ("git_workflow", "```bash\ngit add .\ngit commit -m \"Message\"\ngit push origin main\ngit status\n```", ["git", "add", "commit", "push"]),
    ("git_branch", "```bash\ngit branch feature-ka\ngit checkout feature-ka\ngit checkout main\ngit merge feature-ka\ngit branch -d feature-ka\n```", ["git", "branch", "checkout", "merge"]),
    ("git_undo", "```bash\ngit reset HEAD fichier\ngit checkout -- fichier\ngit stash\ngit stash pop\n```", ["git", "reset", "stash", "undo", "annuler"]),
    ("http_codes", "HTTP : 200 OK, 201 Created, 301 Moved, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Internal Server Error.", ["http", "code", "status", "200", "404", "500"]),
    ("rest_api", "API REST : GET /users (liste), GET /users/42 (un), POST /users (creer), PUT /users/42 (modifier), DELETE /users/42 (supprimer).", ["api", "rest", "design", "endpoint"]),
]