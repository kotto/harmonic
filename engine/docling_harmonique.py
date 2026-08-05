"""
KA Enterprise — Pipeline d'ingestion structurée inspiré de Docling (IBM)
========================================================================
Transforme des documents bruts (markdown, HTML, texte) en **Documents
Harmoniques structurés** puis en hologrammes spécialisés à faits
structurels.

Modèle compatible avec DoclingDocument :
  • sections : hiérarchie de sections (niveau, titre, enfants)
  • items    : liste plate (text, table, list_item, code) avec ordre de
               lecture et provenance (source, position, chemin hiérarchique)
  • metadata : titre, langue, date, source

Le gain vs l'ingestion « texte plat » :
  • le RAG devient STRUCTUREL — une question remonte la hiérarchie
    (titre de section = contexte) au lieu de lire des chunks découpés
    au hasard ;
  • les TABLES sont préservées ligne/colonne (pas du texte aplati) ;
  • l'ordre de lecture et la provenance sont conservés.

Usage :
    from docling_harmonique import parse_markdown, holomorphize, recall_structured
    doc = parse_markdown(text)                 # → DocumentHarmonique
    faits = holomorphize(doc, 'rh', 'mon_domaine')  # → [(s, r, o, sec, score)]
    recall_structured(doc, 'quel est le prix ?')    # → sections complètes
"""

import re
import json
import logging
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any

log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# MODÈLE DE DOCUMENT (fidèle à DoclingDocument)
# ══════════════════════════════════════════════════════════════════════════


@dataclass
class Item:
    """Élément de contenu (text, table, list_item, code)."""
    id: str
    label: str                                # text | table | list_item | code | figure
    text: str
    level: int = 1
    children: List['Item'] = field(default_factory=list)  # table → rows → cells
    prov: List[Dict] = field(default_factory=list)        # [{source, pos, path}]
    meta: Dict = field(default_factory=dict)              # ex: table headers

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'label': self.label, 'text': self.text,
            'level': self.level,
            'children': [c.to_dict() for c in self.children],
            'prov': self.prov, 'meta': self.meta,
        }


@dataclass
class Section:
    """Section hiérarchique (SectionItem dans Docling)."""
    id: str
    level: int
    text: str
    children: List['Section'] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'level': self.level, 'text': self.text,
            'children': [c.to_dict() for c in self.children],
            'items': [i.to_dict() for i in self.items],
        }

    def all_items(self) -> List[Item]:
        """Tous les items de la section, y compris ceux des sous-sections."""
        out = list(self.items)
        for c in self.children:
            out.extend(c.all_items())
        return out


@dataclass
class DocumentHarmonique:
    """Document structuré — équivalent KA du DoclingDocument."""
    name: str
    schema_name: str = 'HarmoniqueDocument'
    version: str = '1.0'
    metadata: Dict = field(default_factory=dict)      # title, language, date, source
    sections: List[Section] = field(default_factory=list)
    items: List[Item] = field(default_factory=list)   # liste plate (ordre de lecture)

    def to_dict(self) -> dict:
        return {
            'schema_name': self.schema_name,
            'version': self.version,
            'name': self.name,
            'metadata': self.metadata,
            'sections': [s.to_dict() for s in self.sections],
            'items': [i.to_dict() for i in self.items],
        }

    def export_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def to_markdown(self) -> str:
        """Export markdown (miroir de export_to_markdown de Docling)."""
        lines = []
        if self.metadata.get('title'):
            lines.append('# ' + self.metadata['title'] + '\n')
        for s in self.sections:
            lines.append(_section_to_markdown(s))
        return '\n'.join(lines)


def _section_to_markdown(s: Section) -> str:
    out = ['#' * s.level + ' ' + s.text]
    for i in s.items:
        if i.label == 'table':
            out.append(_table_to_markdown(i))
        elif i.label == 'list_item':
            for c in i.children or [i]:
                out.append('- ' + c.text)
        elif i.label == 'code':
            out.append('```\n' + i.text + '\n```')
        else:
            out.append(i.text)
    for c in s.children:
        out.append(_section_to_markdown(c))
    return '\n'.join(out)


def _table_to_markdown(t: Item) -> str:
    rows = t.children or []
    if not rows:
        return '| |\n|---|'
    lines = []
    headers = [c.text for c in rows[0].children] if rows[0].children else [rows[0].text]
    lines.append('| ' + ' | '.join(headers) + ' |')
    lines.append('|' + '---|' * len(headers))
    for r in rows[1:]:
        cells = [c.text for c in r.children] if r.children else [r.text]
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)


# ══════════════════════════════════════════════════════════════════════════
# PARSEURS STRUCTURÉS (analogues aux backends Docling)
# ══════════════════════════════════════════════════════════════════════════

_TITLE_RE = re.compile(r'^(#{1,6})\s+(.+?)\s*$')
_LIST_RE = re.compile(r'^\s*[-*•]\s+(.+)$')
_CODE_RE = re.compile(r'^```')
_TABLE_RE = re.compile(r'^\s*\|.*\|\s*$')
_HEADING_HEUR_RE = re.compile(r'^([A-ZÀ-Ý0-9][A-ZÀ-Ý0-9 \-]{2,60})$')   # ligne courte en MAJUSCULES (accents inclus)

_FRENCH_STOP = {
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'est',
    'sont', 'dans', 'pour', 'avec', 'sur', 'par', 'que', 'qui', 'au', 'aux',
    'ce', 'cette', 'ces', 'en', 'à', 'a', 'the', 'of', 'and', 'to', 'in',
}


def _detect_language(text: str) -> str:
    """Détection de langue simple (fr/en par mots outils)."""
    low = text.lower()
    fr = sum(1 for w in ('le ', 'les ', 'des ', 'est ', 'dans ', 'pour ') if w in low)
    en = sum(1 for w in ('the ', 'and ', 'with ', 'from ', 'this ') if w in low)
    return 'en' if en > fr else 'fr'


def _parse_table_block(lines: List[str], source: str, pos: int) -> Tuple[Item, int]:
    """Parse un bloc table markdown '| a | b |' → Item table avec rows/cells."""
    rows = []
    headers = []
    for k, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        # Séparateur '|---|---|'
        if all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c):
            continue
        row = Item(id=f'cell_{pos}_{k}', label='table_row', text=' | '.join(cells))
        row.children = [
            Item(id=f'cell_{pos}_{k}_{j}', label='table_cell', text=c,
                 meta={'row': k, 'col': j, 'header': k == 0})
            for j, c in enumerate(cells)
        ]
        rows.append(row)
        if k == 0:
            headers = cells
    table = Item(id=f'table_{pos}', label='table', text=headers[0] if headers else 'table',
                 children=rows, prov=[{'source': source, 'pos': pos}],
                 meta={'headers': headers})
    return table, len(lines)


def parse_markdown(text: str, source: str = 'markdown', name: str = 'document') -> DocumentHarmonique:
    """
    Parse un document markdown → DocumentHarmonique.
    Titres #…###### → sections hiérarchiques ; paragraphes, listes, tables,
    blocs code → items avec ordre de lecture (l'ordre du fichier).
    """
    doc = DocumentHarmonique(name=name)
    lines = text.split('\n')
    stack: List[Section] = []          # pile des sections ouvertes
    root_sections: List[Section] = []
    flat_items: List[Item] = []
    buffer: List[str] = []
    in_code = False
    code_buf: List[str] = []
    title = None
    sid = 0
    iid = 0
    pos = 0
    i = 0

    def flush_buffer():
        nonlocal buffer
        para = ' '.join(buffer).strip()
        buffer = []
        if not para:
            return
        nonlocal iid
        it = Item(id=f'item_{iid}', label='text', text=para,
                  prov=[{'source': source, 'pos': pos}])
        iid += 1
        flat_items.append(it)
        if stack:
            stack[-1].items.append(it)
        else:
            # pas de section ouverte → on crée une section implicite
            _attach_orphan(root_sections, it)

    def _attach_orphan(roots: List[Section], it: Item):
        # item hors section : l'attacher à la racine via une pseudo-section
        for r in roots:
            if not r.text and not r.items and not r.children:
                r.items.append(it)
                return
        sec = Section(id=f'sec_orphan', level=1, text='')
        sec.items.append(it)
        roots.append(sec)

    def attach_item(it: Item):
        flat_items.append(it)
        if stack:
            stack[-1].items.append(it)
        else:
            _attach_orphan(root_sections, it)

    while i < len(lines):
        raw = lines[i].rstrip()
        if in_code:
            if _CODE_RE.match(raw):
                in_code = False
                attach_item(Item(id=f'item_{iid}', label='code',
                                 text='\n'.join(code_buf),
                                 prov=[{'source': source, 'pos': pos}]))
                iid += 1
                code_buf = []
            else:
                code_buf.append(raw)
            i += 1
            pos += 1
            continue
        if _CODE_RE.match(raw):
            flush_buffer()
            in_code = True
            i += 1
            pos += 1
            continue

        m = _TITLE_RE.match(raw)
        if m:
            flush_buffer()
            level = len(m.group(1))
            heading = m.group(2).strip()
            if title is None:
                title = heading
            # Dépiler les sections de niveau >= au nouveau titre
            while stack and stack[-1].level >= level:
                stack.pop()
            sec = Section(id=f'sec_{sid}', level=level, text=heading)
            sid += 1
            if stack:
                stack[-1].children.append(sec)
            else:
                root_sections.append(sec)
            stack.append(sec)
            i += 1
            pos += 1
            continue

        # Table : capturer le bloc de lignes consécutives '| ... |'
        if _TABLE_RE.match(raw):
            flush_buffer()
            block = []
            while i < len(lines) and _TABLE_RE.match(lines[i].rstrip()):
                block.append(lines[i].rstrip())
                i += 1
            table, used = _parse_table_block(block, source, pos)
            attach_item(table)
            pos += used
            continue

        if _LIST_RE.match(raw):
            flush_buffer()
            attach_item(Item(id=f'item_{iid}', label='list_item',
                             text=_LIST_RE.match(raw).group(1).strip(),
                             prov=[{'source': source, 'pos': pos}]))
            iid += 1
            i += 1
            pos += 1
            continue

        if raw.strip():
            buffer.append(raw.strip())
        else:
            flush_buffer()
        i += 1
        pos += 1

    flush_buffer()
    if in_code and code_buf:
        attach_item(Item(id=f'item_{iid}', label='code', text='\n'.join(code_buf),
                         prov=[{'source': source, 'pos': pos}]))

    doc.sections = [s for s in root_sections if s.text or s.items or s.children]
    doc.items = flat_items
    doc.metadata = {
        'title': title or name,
        'language': _detect_language(text),
        'date': datetime.date.today().isoformat(),
        'source': source,
        'format': 'markdown',
    }
    return doc


def parse_text(text: str, source: str = 'text', name: str = 'document') -> DocumentHarmonique:
    """
    Parse un texte brut → DocumentHarmonique.
    Heuristique : lignes courtes en MAJUSCULES → titres de section.
    """
    doc = DocumentHarmonique(name=name)
    lines = text.split('\n')
    stack: List[Section] = []
    root_sections: List[Section] = []
    flat_items: List[Item] = []
    buffer: List[str] = []
    title = None
    sid = 0
    iid = 0

    def flush():
        nonlocal buffer
        para = ' '.join(buffer).strip()
        buffer = []
        if not para:
            return
        nonlocal iid
        it = Item(id=f'item_{iid}', label='text', text=para,
                  prov=[{'source': source}])
        iid += 1
        flat_items.append(it)
        if stack:
            stack[-1].items.append(it)

    for line in lines:
        s = line.strip()
        if not s:
            flush()
            continue
        if _HEADING_HEUR_RE.match(s) and len(s) < 60:
            flush()
            if title is None:
                title = s
            while stack and stack[-1].level >= 2:
                stack.pop()
            sec = Section(id=f'sec_{sid}', level=2, text=s)
            sid += 1
            if stack:
                stack[-1].children.append(sec)
            else:
                root_sections.append(sec)
            stack.append(sec)
            continue
        buffer.append(s)
    flush()

    doc.sections = root_sections
    doc.items = flat_items
    doc.metadata = {
        'title': title or name,
        'language': _detect_language(text),
        'date': datetime.date.today().isoformat(),
        'source': source,
        'format': 'text',
    }
    return doc


def parse_html(text: str, source: str = 'html', name: str = 'document') -> DocumentHarmonique:
    """Parse un HTML simple (h1-h6, p, li, table, pre/code) → DocumentHarmonique."""
    import html as _html
    # Normaliser : retirer scripts/styles
    text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.S)
    doc = DocumentHarmonique(name=name)
    stack: List[Section] = []
    root_sections: List[Section] = []
    flat_items: List[Item] = []
    sid = 0
    iid = 0

    def current():
        return stack[-1] if stack else None

    # Tokeniser par balises (simple)
    tokens = re.findall(r'<(/?)(h[1-6]|p|li|table|tr|td|th|pre|code|ul|ol)\b[^>]*>|([^<]+)', text, re.I)
    open_table = None

    for close, tag, content in tokens:
        if tag:
            tag = tag.lower()
            if close:
                if tag == 'table' and open_table is not None:
                    flat_items.append(open_table)
                    cur = current()
                    if cur:
                        cur.items.append(open_table)
                    open_table = None
                continue
            if tag[0] == 'h':
                level = int(tag[1])
                # Le contenu vient après la balise ouvrante
                continue
            if tag == 'table':
                open_table = Item(id=f'table_{sid}', label='table', text='table',
                                  prov=[{'source': source}], meta={'headers': []})
                continue
            if tag in ('tr', 'td', 'th', 'ul', 'ol'):
                continue
            if tag == 'pre' or tag == 'code':
                continue
        elif content and content.strip():
            c = _html.unescape(content.strip())
            if open_table is not None and not open_table.children:
                row = Item(id=f'cell_{iid}', label='table_row', text=c)
                row.children = [Item(id=f'cell_{iid}_0', label='table_cell', text=c,
                                     meta={'row': 0, 'col': 0, 'header': True})]
                open_table.children.append(row)
                continue
            if c.startswith('|') and c.endswith('|'):
                continue
            it = Item(id=f'item_{iid}', label='text', text=c, prov=[{'source': source}])
            iid += 1
            flat_items.append(it)
            cur = current()
            if cur:
                cur.items.append(it)

    doc.sections = root_sections
    doc.items = flat_items
    doc.metadata = {
        'title': name,
        'language': _detect_language(text),
        'date': datetime.date.today().isoformat(),
        'source': source,
        'format': 'html',
    }
    return doc


PARSE_BY_FORMAT = {
    'markdown': parse_markdown,
    'md': parse_markdown,
    'text': parse_text,
    'txt': parse_text,
    'html': parse_html,
}


def parse_document(content: str, format: str = 'markdown', source: str = 'doc',
                   name: str = 'document') -> DocumentHarmonique:
    """Parse selon le format déclaré (markdown | text | html)."""
    fn = PARSE_BY_FORMAT.get((format or 'markdown').lower(), parse_text)
    return fn(content, source=source, name=name)


# ══════════════════════════════════════════════════════════════════════════
# HOLOGRAMMISATION : DocumentHarmonique → faits structurels + contenu
# ══════════════════════════════════════════════════════════════════════════

def _slug(text: str, max_len: int = 48) -> str:
    """Identifiant lisible : texte normalisé tronqué."""
    t = re.sub(r'\s+', ' ', text).strip().strip('.').strip()
    if len(t) > max_len:
        t = t[:max_len - 1].rstrip() + '…'
    return t or '—'


def holomorphize(doc: DocumentHarmonique, secteur: str = 'enterprise',
                 domain: str = 'enterprise') -> List[Tuple[str, str, str, str, float]]:
    """
    Convertit un DocumentHarmonique en faits (sujet, relation, objet, secteur, score).

    Faits STRUCTURELS (nouveau — inspiré des supernodes Docling) :
      • section_est_sous : hiérarchie des sections
      • section_contient : chaque item → sa section (contexte remontable)
      • item_précède : ordre de lecture
    Faits de TABLE : cellule → en-tête de colonne ; lignes → table
    Faits de CONTENU : triplets sujet-verbe-objet extraits des paragraphes
    """
    facts: List[Tuple[str, str, str, str, float]] = []
    domain_slug = _slug(domain, 32)

    def emit(s: str, r: str, o: str, score: float = 0.9):
        facts.append((_slug(s), r, _slug(o), secteur, score))

    # Hiérarchie des sections
    def walk(sections: List[Section], parent: Optional[str]):
        for sec in sections:
            sec_key = sec.text
            if parent:
                emit(sec_key, 'section_est_sous', parent)
            emit(sec_key, 'appartient_au_domaine', domain_slug)
            items = sec.all_items()
            prev = None
            for it in items:
                # Section contient item (contexte)
                emit(sec_key, 'section_contient', it.text)
                # Ordre de lecture
                if prev is not None:
                    emit(prev, 'item_précède', it.text, 0.85)
                prev = it.text
                # Tables : cellule → colonne ; ligne → table
                if it.label == 'table':
                    emit(it.text if it.meta.get('headers') else 'table', 'est_une_table', sec_key)
                    _table_facts(it, emit)
            walk(sec.children, sec_key)

    walk(doc.sections, None)

    # Items orphelins (hors section) → faits de contenu
    for it in doc.items:
        if it.label == 'table':
            _table_facts(it, emit)
        elif it.label == 'text':
            for s, r, o in _extract_triplets(it.text):
                facts.append((_slug(s), r, _slug(o), secteur, 0.8))

    # Dédupliquer (sujet, relation, objet)
    seen = set()
    dedup = []
    for f in facts:
        key = (f[0].lower(), f[1], f[2].lower())
        if key in seen:
            continue
        seen.add(key)
        dedup.append(f)
    return dedup


def _table_facts(table: Item, emit):
    """Cellules → en-têtes de colonne ; lignes → table ; valeurs liées au titre."""
    headers = table.meta.get('headers') or []
    for row in table.children:
        cells = row.children or []
        for cell in cells:
            if cell.meta.get('header'):
                continue
            col = cell.meta.get('col', 0)
            header = headers[col] if col < len(headers) else f'colonne_{col}'
            if header and cell.text:
                emit(cell.text, 'est_valeur_de', header, 0.9)
                emit(header, 'est_colonne_de', table.text, 0.85)


_TRIPLET_RES = [
    # "X est Y" / "X est un Y"
    re.compile(r'\b([A-Za-zÀ-ÿ][\wÀ-ÿ \-]{1,40}?)\s+(?:est|sont)\s+(?:un |une |des )?([a-zà-ÿ][\wÀ-ÿ \-]{1,40}?)\b(?=[.,;)]|$)', re.I),
    # "X nécessite Y" / "X utilise Y" / "X contient Y"
    re.compile(r'\b([A-Za-zÀ-ÿ][\wÀ-ÿ \-]{1,40}?)\s+(?:nécessite|utilise|contient|requiert|produit|génère|traite|réduit|augmente|permet|déclenche|mesure|stocke)\s+([a-zà-ÿ][\wÀ-ÿ \-]{1,40}?)\b(?=[.,;)]|$)', re.I),
    # "X se fait par Y" / "X se traite par Y"
    re.compile(r'\b([A-Za-zÀ-ÿ][\wÀ-ÿ \-]{1,40}?)\s+se\s+(?:fait|traite|mesure|règle|calcule|compose)\s+(?:par|avec|de)\s+([a-zà-ÿ][\wÀ-ÿ \-]{1,40}?)\b(?=[.,;)]|$)', re.I),
]


def _extract_triplets(text: str) -> List[Tuple[str, str, str]]:
    """Extraction légère de triplets sujet-relation-objet (heuristique)."""
    out = []
    for rx in _TRIPLET_RES:
        for m in rx.finditer(text):
            s, o = m.group(1).strip(), m.group(2).strip()
            if not s or not o or s.lower() in _FRENCH_STOP or o.lower() in _FRENCH_STOP:
                continue
            # relation : le verbe du pattern (reconstruit)
            rel = 'est' if 'est' in rx.pattern else ('se_fait_par' if 'se' in rx.pattern else 'utilise')
            out.append((s, rel, o))
    return out


# ══════════════════════════════════════════════════════════════════════════
# RAPPEL STRUCTUREL : la question remonte la hiérarchie (supernode)
# ══════════════════════════════════════════════════════════════════════════

def _tokens(text: str) -> set:
    """Tokens avec stemming naïf (formule ~ formules) : 6+ chars → 5 premiers."""
    out = set()
    for w in re.findall(r'[a-zà-ÿ0-9]+', text.lower()):
        if w in _FRENCH_STOP or len(w) <= 1:
            continue
        out.add(w[:5] if len(w) >= 6 else w)
    return out


def _score_text(text: str, q: set) -> float:
    t = _tokens(text)
    if not t or not q:
        return 0.0
    inter = len(t & q)
    return inter / (len(q) ** 0.5 + 0.001) if inter else 0.0


def recall_structured(doc: DocumentHarmonique, query: str,
                      top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Rappel STRUCTUREL : score les sections (titre + contenu DIRECT — les
    enfants sont scorés séparément, la racine n'engloutit pas le document),
    retourne les sections complètes (titre, hiérarchie, table entière).
    """
    q = _tokens(query)
    scored = []
    for s in doc.sections:
        body = ' '.join(i.text for i in s.items)     # items directs seulement
        score = _score_text(s.text, q) * 1.5 + _score_text(body, q)
        if score > 0:
            scored.append((score, s))
        # Enfants : score propre (pas absorbé par le parent)
        for c in s.children:
            cbody = ' '.join(i.text for i in c.items)
            cscore = _score_text(c.text, q) * 1.5 + _score_text(cbody, q)
            if cscore > 0:
                scored.append((cscore, c))
    scored.sort(key=lambda x: -x[0])
    out = []
    for score, s in scored[:top_k]:
        out.append({
            'score': round(score, 3),
            'section': s.text,
            'level': s.level,
            'parent': _parent_title(doc, s),
            'content': _section_to_markdown(s),
            'items': [i.to_dict() for i in s.items],
        })
    return out


def _parent_title(doc: DocumentHarmonique, target: Section) -> Optional[str]:
    for s in doc.sections:
        if target in s.children:
            return s.text
        for c in s.children:
            if target in c.children:
                return c.text
    return None


# ══════════════════════════════════════════════════════════════════════════
# INTÉGRATION STORE : créer/mettre à jour un hologramme spécialisé
# ══════════════════════════════════════════════════════════════════════════

def build_hologram(doc: DocumentHarmonique, store, domain: str,
                   category: str = 'enterprise') -> dict:
    """
    Construit (ou met à jour) l'hologramme spécialisé du domaine à partir
    du DocumentHarmonique. `store` : objet avec create_hologram/add_facts/recall.
    """
    holo_id = _slug(domain, 32).replace(' ', '_').lower() or 'enterprise'
    if hasattr(store, 'create_hologram'):
        try:
            store.create_hologram(
                holo_id=holo_id,
                name=domain,
                category=category,
                description=f'Hologramme structuré (ingestion Docling-harmonique) : {doc.metadata.get("title", "")}',
                tags=['enterprise', 'structuré', category],
            )
        except Exception as e:
            log.warning(f"  ⚠ create_hologram: {e}")

    facts = holomorphize(doc, secteur=category, domain=domain)
    if hasattr(store, 'add_facts'):
        try:
            store.add_facts(holo_id, facts)
        except Exception as e:
            log.warning(f"  ⚠ add_facts: {e}")

    return {
        'hologram_id': holo_id,
        'facts': len(facts),
        'structural_facts': sum(1 for f in facts if f[1] in
                                ('section_est_sous', 'section_contient', 'item_précède')),
        'table_facts': sum(1 for f in facts if f[1] in ('est_valeur_de', 'est_colonne_de')),
        'sections': len(doc.sections),
        'items': len(doc.items),
    }
