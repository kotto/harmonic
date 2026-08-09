/* ─────────────────────────────────────────────────────────────
   THÉORIE HARMONIQUE UNIVERSELLE — renderer.js
   Mini-rendu Markdown (blocs + inline), sans dépendance.
   Gère : titres, code, tables, citations, listes, règles, gras,
   italique, code inline, liens.
   ───────────────────────────────────────────────────────────── */
(function () {
  "use strict";

  function escapeHtml(s) {
    return s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* Rendu inline : code, gras, italique, liens */
  function inline(s) {
    s = escapeHtml(s);
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (_, t, u) {
      return '<a href="' + u + '" target="_blank" rel="noopener">' + t + "</a>";
    });
    return s;
  }

  /* Cellules d'une ligne de tableau */
  function cells(row) {
    var c = row.split("|");
    if (row.trim().charAt(0) === "|") c.shift();
    if (row.trim().charAt(row.trim().length - 1) === "|") c.pop();
    return c.map(function (s) { return s.trim(); });
  }

  function isSep(row) {
    return /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(row);
  }

  function renderTable(rows) {
    var thead = "", tbody = "";
    for (var i = 0; i < rows.length; i++) {
      if (isSep(rows[i])) continue;
      var tr = "";
      cells(rows[i]).forEach(function (c, j) {
        var tag = i === 0 ? "th" : "td";
        tr += "<" + tag + ">" + inline(c) + "</" + tag + ">";
      });
      if (i === 0) thead = "<tr>" + tr + "</tr>";
      else tbody += "<tr>" + tr + "</tr>";
    }
    return "<div class='md-table'><table><thead>" + thead + "</thead><tbody>" + tbody + "</tbody></table></div>\n";
  }

  var BLOCK_START = /^(#{1,6}\s|```|>\s?|\s*[-*+]\s+|\s*\d+\.\s+|\s*\|)/;

  function renderMarkdown(md) {
    var lines = (md || "").replace(/\r\n/g, "\n").split("\n");
    var html = "";
    var i = 0;

    while (i < lines.length) {
      var line = lines[i];

      /* Bloc de code délimité */
      if (/^```/.test(line.trim())) {
        var buf = [];
        i++;
        while (i < lines.length && !/^```/.test(lines[i].trim())) {
          buf.push(lines[i]);
          i++;
        }
        i++; /* clôture */
        html += "<pre><code>" + escapeHtml(buf.join("\n")) + "</code></pre>\n";
        continue;
      }

      /* Tableau */
      if (/^\s*\|/.test(line) && i + 1 < lines.length && isSep(lines[i + 1])) {
        var rows = [];
        while (i < lines.length && /^\s*\|/.test(lines[i])) {
          rows.push(lines[i]);
          i++;
        }
        html += renderTable(rows);
        continue;
      }

      /* Titre */
      var h = line.match(/^(#{1,6})\s+(.*)$/);
      if (h) {
        html += "<h" + h[1].length + ">" + inline(h[2]) + "</h" + h[1].length + ">\n";
        i++;
        continue;
      }

      /* Règle horizontale */
      if (/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(line)) {
        html += "<hr />\n";
        i++;
        continue;
      }

      /* Citation */
      if (/^\s*>/.test(line)) {
        var bq = [];
        while (i < lines.length && /^\s*>/.test(lines[i])) {
          bq.push(lines[i].replace(/^\s*>\s?/, ""));
          i++;
        }
        html += "<blockquote>" + inline(bq.join("\n")) + "</blockquote>\n";
        continue;
      }

      /* Liste non ordonnée */
      if (/^\s*[-*+]\s+/.test(line)) {
        html += "<ul>\n";
        while (i < lines.length && /^\s*[-*+]\s+/.test(lines[i])) {
          html += "<li>" + inline(lines[i].replace(/^\s*[-*+]\s+/, "")) + "</li>\n";
          i++;
        }
        html += "</ul>\n";
        continue;
      }

      /* Liste ordonnée */
      if (/^\s*\d+\.\s+/.test(line)) {
        html += "<ol>\n";
        while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
          html += "<li>" + inline(lines[i].replace(/^\s*\d+\.\s+/, "")) + "</li>\n";
          i++;
        }
        html += "</ol>\n";
        continue;
      }

      /* Ligne vide */
      if (line.trim() === "") {
        i++;
        continue;
      }

      /* Paragraphe */
      var para = [];
      while (
        i < lines.length &&
        lines[i].trim() !== "" &&
        !BLOCK_START.test(lines[i])
      ) {
        para.push(lines[i]);
        i++;
      }
      html += "<p>" + inline(para.join(" ")) + "</p>\n";
    }
    return html;
  }

  window.MarkdownRenderer = { render: renderMarkdown };
})();
