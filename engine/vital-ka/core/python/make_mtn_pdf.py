# -*- coding: utf-8 -*-
"""Assemble le dossier MTN : markdown → HTML (couverture + corps) → PDF."""
import json, re, html as html_lib
from pathlib import Path

import markdown

ENGINE = Path(__file__).resolve().parent
MTN = ENGINE / "dossier_mtn"
OUT_HTML = MTN / "DOSSIER_MTN.html"

# ── 1. Palette (générée par palette.cascade) ──
PALETTE = """
:root {
  --page-bg: #f2f3f4;
  --section-bg: #eff0f1;
  --card-bg: #edeff1;
  --table-stripe: #e9ebec;
  --header-fill: #516a77;
  --cover-block: #587989;
  --border: #bdced7;
  --icon: #426a7e;
  --accent: #c42f48;
  --accent-secondary: #8532c1;
  --text-primary: #1e2021;
  --text-muted: #848b8e;
  --semantic-success: #519367;
  --semantic-warning: #a28346;
  --semantic-error: #ad4e45;
  --semantic-info: #597795;
}
"""

# ── 2. Nettoyage du contenu ──
EMOJI_MAP = {
    '✅': '[OK] ', '❌': '[KO] ', '⚠️': '[ATTENTION] ', '⚠': '[ATTENTION] ',
    '📡': '', '🏥': '', '🌊': '', '🔐': '', '🎯': '', '💡': '', '🚀': '',
    '📊': '', '📄': '', '📦': '', '📚': '', '📋': '', '🧠': '', '📎': '',
    '👁️': '', '⏱️': '', '🔢': '', '💰': '', '🔒': '', '🟢': '[EN COURS] ',
    '🔴': '[BLOQUE] ', '🟡': '[EN ATTENTE] ', '⚪': '', '▶': '', '←': '&larr; ',
    '→': '&rarr; ', '×': '&times; ', '≈': '&asymp; ',
}
EMOJI_RE = re.compile(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F]')


def clean_emoji(text: str) -> str:
    return EMOJI_RE.sub('', text)


def md_to_html(md_text: str) -> str:
    """Markdown → HTML (extensions tables, fenced_code)."""
    return markdown.markdown(
        md_text,
        extensions=['tables', 'fenced_code', 'nl2br'],
        output_format='html5',
    )


# ── Conversion LaTeX → texte simple (les formules exotiques cassent le rendu) ──
LATEX_REPLACEMENTS = [
    # Texte spécial fréquent
    (r'\text{softmax}_i', 'softmax'),
    (r'\text{softmax}', 'softmax'),
    (r'\cdot', '·'),
    (r'\times', 'x'),
    (r'\sqrt', 'sqrt'),
    (r'\sum', '∑'),
    (r'\int', '∫'),
    (r'\frac', 'frac'),
    (r'\varphi', 'φ'),
    (r'\psi', 'ψ'),
    (r'\alpha', 'α'),
    (r'\phi', 'φ'),
    (r'\omega', 'ω'),
    (r'\Gamma', 'Γ'),
    (r'\left', ''),
    (r'\right', ''),
    (r'\,', ' '),
    (r'\{', '{'),
    (r'\}', '}'),
    (r'\langle', '<'),
    (r'\rangle', '>'),
    (r'\|', '|'),
    (r'\_', '_'),
    (r'\{', '{'),
]
LATEX_RE = re.compile(r'\$\$?(.+?)\$\$?')


def convert_latex(text: str) -> str:
    """Remplace les formules LaTeX inline par leur version texte simple."""
    def repl(m):
        inner = m.group(1)
        for pat, rep in LATEX_REPLACEMENTS:
            inner = inner.replace(pat, rep)
        # Retirer les accolades de groupement
        inner = re.sub(r'\{([^}]*)\}', r'\1', inner)
        inner = re.sub(r'_{?(\w+)}?', r'_\1', inner)   # indices
        inner = re.sub(r'\^{?(\w+)}?', r'^\1', inner)  # exposants
        inner = re.sub(r'\s+', ' ', inner).strip()
        return inner
    return LATEX_RE.sub(repl, text)


def convert_latex_in_md(md_text: str) -> str:
    """Convertit le LaTeX dans le markdown (en préservant les blocs code)."""
    out_lines = []
    in_code = False
    for line in md_text.split('\n'):
        if line.strip().startswith('```'):
            in_code = not in_code
        if not in_code:
            line = convert_latex(line)
        out_lines.append(line)
    return '\n'.join(out_lines)


def wrap_html(body: str, title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>{html_lib.escape(title)}</title>
<style>
{PALETTE}
@page {{ size: A4; margin: 18mm 16mm 18mm 16mm; }}
html, body {{ margin: 0; padding: 0; background: var(--page-bg);
  color: var(--text-primary);
  font-family: 'Segoe UI', 'DejaVu Sans', Arial, sans-serif;
  font-size: 10.5pt; line-height: 1.55; }}
.page {{ max-width: 180mm; margin: 0 auto; padding: 12mm 4mm;
  background: var(--page-bg); }}

/* ── Couverture ── */
.cover {{ background: linear-gradient(160deg, #1e2a35 0%, var(--header-fill) 55%, var(--cover-block) 100%);
  color: #fff; padding: 0; }}
.cover-inner {{ padding: 28mm 18mm; }}
.cover-kicker {{ font-size: 12pt; letter-spacing: 4px; text-transform: uppercase;
  opacity: .75; margin-bottom: 10mm; }}
.cover-title {{ font-size: 30pt; font-weight: 800; line-height: 1.15;
  margin: 0 0 8mm 0; }}
.cover-sub {{ font-size: 14pt; opacity: .9; margin-bottom: 18mm; }}
.cover-metrics {{ display: flex; gap: 6mm; margin: 14mm 0; }}
.cover-metric {{ flex: 1; background: rgba(255,255,255,.10);
  border-radius: 3mm; padding: 6mm 5mm; text-align: center; }}
.cover-metric b {{ display: block; font-size: 22pt; color: #fff; }}
.cover-metric span {{ font-size: 8.5pt; opacity: .8; }}
.cover-footer {{ margin-top: 16mm; font-size: 9.5pt; opacity: .75;
  border-top: 1px solid rgba(255,255,255,.3); padding-top: 5mm; }}

/* ── Typographie ── */
h1 {{ font-size: 17pt; color: var(--header-fill); border-bottom: 2px solid var(--border);
  padding-bottom: 3mm; margin: 14mm 0 6mm; page-break-after: avoid; }}
h2 {{ font-size: 13.5pt; color: var(--icon); margin: 10mm 0 4mm; page-break-after: avoid; }}
h3 {{ font-size: 11.5pt; color: var(--text-primary); margin: 7mm 0 3mm; page-break-after: avoid; }}
p {{ margin: 2.5mm 0; text-align: justify; }}
ul, ol {{ margin: 2.5mm 0 2.5mm 7mm; }}
li {{ margin: 1.2mm 0; }}
strong {{ color: var(--text-primary); }}
hr {{ border: none; border-top: 1px solid var(--border); margin: 8mm 0; }}

/* ── Tableaux ── */
table {{ width: 100%; border-collapse: collapse; margin: 4mm auto;
  font-size: 9pt; page-break-inside: avoid; }}
thead th {{ background: var(--header-fill); color: #fff; text-align: left;
  padding: 2.2mm 3mm; font-weight: 600; }}
tbody td {{ padding: 2mm 3mm; border-bottom: 1px solid var(--border);
  vertical-align: top; }}
tbody tr:nth-child(even) {{ background: var(--table-stripe); }}

/* ── Code ── */
code {{ background: var(--section-bg); border: 1px solid var(--border);
  border-radius: 1.5mm; padding: 0.5mm 1.5mm; font-size: 8.5pt;
  font-family: Consolas, 'DejaVu Sans Mono', monospace; }}
pre {{ background: var(--section-bg); border: 1px solid var(--border);
  border-radius: 2mm; padding: 4mm; overflow-wrap: break-word;
  white-space: pre-wrap; page-break-inside: avoid; }}
pre code {{ background: none; border: none; padding: 0; }}

/* ── Divers ── */
blockquote {{ border-left: 3px solid var(--accent); background: var(--card-bg);
  margin: 4mm 0; padding: 3mm 5mm; color: var(--text-primary); }}
.meta {{ color: var(--text-muted); font-size: 9pt; }}
.confidential {{ display: inline-block; background: var(--accent); color: #fff;
  font-size: 8.5pt; padding: 1.5mm 4mm; border-radius: 1.5mm;
  letter-spacing: 2px; text-transform: uppercase; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


def build_cover() -> str:
    return """
<section class="page cover">
  <div class="cover-inner">
    <div class="cover-kicker">Partenariat strategique · MTN Group × Vital Ka</div>
    <h1 class="cover-title">Compression massive harmonique<br>
      L'IA qui tient dans un smartphone</h1>
    <div class="cover-sub">Dossier technique · Proposition de partenariat technologique
      · Confidentiel</div>
    <div class="cover-metrics">
      <div class="cover-metric"><b>57x</b><span>compression<br>hologrammes</span></div>
      <div class="cover-metric"><b>0.5%</b><span>hallucinations<br>(vs 4.5% LLM)</span></div>
      <div class="cover-metric"><b>2.6 min</b><span>15 experts<br>sur CPU</span></div>
    </div>
    <div class="cover-footer">
      Vital Ka — Ecosysteme de sante panafricain<br>
      Technologie : Harmonic Wavelet Attention Transformer (HWAT) v1.0<br>
      1er aout 2026 · Dossier v1.0
    </div>
  </div>
</section>"""


def main():
    # Ordre des documents
    docs = [
        ("DOSSIER_TECHNIQUE_MTN_COMPRESSION_HARMONIQUE.md", "Dossier principal"),
        ("ANNEXE_A_FONDEMENTS_MATHEMATIQUES.md", "Annexe A — Fondements mathematiques"),
        ("ANNEXE_B_BENCHMARKS.md", "Annexe B — Benchmarks"),
        ("ANNEXE_C_ARCHITECTURE.md", "Annexe C — Architecture"),
        ("ANNEXE_D_BUDGET.md", "Annexe D — Budget & modele economique"),
    ]

    sections = [build_cover()]
    for fname, label in docs:
        fpath = MTN / fname
        if not fpath.exists():
            print(f"⚠️  {fname} absent")
            continue
        md_text = fpath.read_text(encoding='utf-8')
        # Nettoyer les emojis
        md_text = clean_emoji(md_text)
        # Convertir le LaTeX en texte simple
        md_text = convert_latex_in_md(md_text)
        # Retirer la ligne de titre h1 du fichier (la couverture la porte)
        lines = md_text.split('\n')
        while lines and lines[0].startswith('# '):
            lines.pop(0)
        md_text = '\n'.join(lines)
        body = md_to_html(md_text)
        sections.append(f'<section class="page">\n{body}\n</section>')

    html_doc = wrap_html('\n'.join(sections), "Dossier technique MTN — Compression massive harmonique")
    OUT_HTML.write_text(html_doc, encoding='utf-8')
    print(f"✅ HTML généré : {OUT_HTML} ({OUT_HTML.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
