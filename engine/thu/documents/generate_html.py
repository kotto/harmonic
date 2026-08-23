import markdown
import re

# Read the markdown
with open("E:/SAAS - Copie/engine/thu/documents/MODELE_STANDARD_HARMONIQUE.md", "r", encoding="utf-8") as f:
    md_content = f.read()

# Convert markdown to HTML (with extensions for tables, code blocks, etc.)
html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code', 'codehilite', 'nl2br'])

# Wrap in a complete HTML document with MathJax for LaTeX rendering
html_template = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Modèle Standard Harmonique</title>
<script>
MathJax = {{
  tex: {{
    inlineMath: [['$','$'], ['\\\\(','\\\\)']],
    displayMath: [['$$','$$'], ['\\[','\\]']],
    processEscapes: true
  }}
}};
</script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<style>
  @page {{
    size: A4;
    margin: 25mm 20mm 25mm 20mm;
  }}
  html, body {{
    margin: 0;
    padding: 0;
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1a1a1a;
  }}
  body {{
    max-width: 170mm;
    margin: 0 auto;
    padding: 20px;
  }}
  h1 {{
    font-size: 24pt;
    text-align: center;
    margin-top: 0;
    border-bottom: 3px solid #1a1a1a;
    padding-bottom: 12px;
  }}
  h2 {{
    font-size: 18pt;
    margin-top: 32px;
    border-bottom: 1px solid #ccc;
    padding-bottom: 6px;
  }}
  h3 {{
    font-size: 14pt;
    margin-top: 24px;
  }}
  h4 {{
    font-size: 12pt;
    margin-top: 20px;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
    font-size: 9pt;
  }}
  th, td {{
    border: 1px solid #999;
    padding: 5px 8px;
    text-align: left;
  }}
  th {{
    background: #f0f0f0;
    font-weight: bold;
  }}
  code {{
    background: #f5f5f5;
    padding: 1px 4px;
    border-radius: 3px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9pt;
  }}
  pre {{
    background: #f5f5f5;
    padding: 12px;
    border-radius: 5px;
    overflow-x: auto;
    font-size: 9pt;
  }}
  blockquote {{
    border-left: 4px solid #ccc;
    margin: 16px 0;
    padding: 8px 16px;
    background: #fafafa;
    font-style: italic;
  }}
  hr {{
    border: none;
    border-top: 1px solid #ddd;
    margin: 32px 0;
  }}
  .mjx-chtml {{
    font-size: 100% !important;
  }}
</style>
</head>
<body>
{body}
</body>
</html>
"""

html_content = html_template.format(body=html_body)

# Write the HTML file
output_path = "E:/SAAS - Copie/engine/thu/documents/MODELE_STANDARD_HARMONIQUE.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML generated: {output_path}")
print(f"HTML size: {len(html_content)} chars")