/* ─────────────────────────────────────────────────────────────
   HARMONIC AI FINANCE — app.js
   Console : saisie → moteur harmonique → réponse/refus,
   historique localStorage, export, bouton évaluation.
   ───────────────────────────────────────────────────────────── */
(function () {
  "use strict";

  var Engine = window.HarmonicEngine;
  var chat = document.getElementById("chat");
  var empty = document.getElementById("emptyState");
  var form = document.getElementById("form");
  var input = document.getElementById("input");
  var send = document.getElementById("send");
  var historyEl = document.getElementById("history");
  var STORE_KEY = "haf_sessions";

  var sessions = loadSessions();

  /* ── Persistance ──────────────────────────────────────────── */
  function loadSessions() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY)) || []; }
    catch (e) { return []; }
  }
  function saveSessions() {
    localStorage.setItem(STORE_KEY, JSON.stringify(sessions));
  }

  /* ── Rendu de la réponse ──────────────────────────────────── */
  function confidenceClass(conf) {
    if (conf >= 95) return "conf--high";
    if (conf >= 90) return "conf--mid";
    return "conf--low";
  }

  function renderPoint(fact, score, index) {
    var c = fact.confidence;
    var rows = fact.points.map(function (p) {
      return '<div class="point__label">' + p.label + '</div>' +
             '<div class="point__value">' + p.value + '</div>';
    }).join("");

    var html = '<div class="point">' +
      '<h4 class="point__title"><span class="point__n">' + String(index + 1).padStart(2, "0") + '</span>' +
      fact.title + ' <span class="conf-badge ' + confidenceClass(c) + '">' + c + ' % ±' + fact.margin + ' %</span></h4>' +
      '<div class="point__rows">' + rows + '</div>';

    if (fact.formula) {
      html += '<div class="block block--formula"><span class="block__label">Formule</span>' + fact.formula + '</div>';
    }
    if (fact.calculation) {
      html += '<div class="block block--calc"><span class="block__label">Calcul</span>' + fact.calculation + '</div>';
    }
    if (fact.assumptions && fact.assumptions.length) {
      html += '<div class="block"><span class="block__label">Hypothèses</span><ul>' +
        fact.assumptions.map(function (a) { return "<li>" + a + "</li>"; }).join("") + "</ul></div>";
    }
    if (fact.limitations && fact.limitations.length) {
      html += '<div class="block"><span class="block__label">Limitations</span><ul>' +
        fact.limitations.map(function (a) { return "<li>" + a + "</li>"; }).join("") + "</ul></div>";
    }
    if (fact.verification) {
      html += '<div class="answer__verif">' + fact.verification + '</div>';
    }
    // Source & tags
    if (fact.source) {
      html += '<div class="block"><span class="block__label">Source</span>' + fact.source;
      if (fact.source_url) {
        html += ' <a href="' + fact.source_url + '" target="_blank" rel="noopener" style="color:var(--wave);margin-left:8px">⧉</a>';
      }
      html += '</div>';
    }
    if (fact.tags && fact.tags.length) {
      html += '<div class="block"><span class="block__label">Tags</span>' +
        fact.tags.map(function (t) { return '<span style="display:inline-block;background:var(--gold-line);color:var(--gold);padding:2px 8px;border-radius:999px;font-size:10px;font-family:var(--font-mono);margin-right:4px">#' + t + '</span>'; }).join("") +
        '</div>';
    }
    html += "</div>";
    return html;
  }

  function renderAnswer(result) {
    var points = result.matches.map(function (m, i) {
      return renderPoint(m.fact, m.score, i);
    }).join("");
    var caveat = result.matches.map(function (m) { return m.fact.caveat; })
      .filter(Boolean).filter(function (v, i, a) { return a.indexOf(v) === i; });

    var html = '<div class="answer__head">' +
      '<h3 class="answer__title">Réponse sourcée — ' + result.matches.length + ' fait' +
      (result.matches.length > 1 ? "s" : "") + '</h3>' +
      '<div class="answer__meta">score <span>' + result.score.toFixed(3) + '</span> · seuil <span>' + result.threshold.toFixed(2) + '</span> · domaine <span>' + result.domain + '</span></div>' +
      '</div>' +
      points;

    if (caveat.length) {
      html += caveat.map(function (c) {
        return '<div class="answer__caveat"><strong>⚠ Avertissement :</strong> ' + c + "</div>";
      }).join("");
    }
    html += '<div class="answer__rid">🎯 <strong>Response ID</strong> : ' + result.id + "</div>";
    return html;
  }

  function renderRefusal(result) {
    return '<div class="refusal">' +
      '<div class="refusal__title">⛔ Refus anti-hallucination — par construction</div>' +
      '<p class="refusal__text">' + result.disclaimer + "</p>" +
      '<p class="refusal__score">Score de résonance : ' + result.score.toFixed(3) +
      ' · seuil : ' + result.threshold.toFixed(2) + ' [' + result.domain + ']</p>' +
      '<div class="refusal__rid">🎯 <strong>Response ID</strong> : ' + result.id + "</div>" +
      "</div>";
  }

  function pushMessage(kind, html, rid) {
    var wrap = document.createElement("div");
    wrap.className = "msg msg--" + kind;
    wrap.innerHTML = '<div class="msg__bubble">' + html + "</div>";
    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
    return wrap;
  }

  /* ── Résolution ───────────────────────────────────────────── */
  function solve(prompt) {
    if (empty) empty.style.display = "none";
    pushMessage("q", prompt);
    var think = pushMessage("a", '<div class="thinking"><div class="thinking__bars">' +
      '<span></span><span></span><span></span><span></span><span></span></div>Résonance…</div>');

    setTimeout(function () {
      var result = Engine.solve(prompt);
      var html = result.status === "answered" ? renderAnswer(result) : renderRefusal(result);
      think.querySelector(".msg__bubble").innerHTML = html;
      think.scrollIntoView({ block: "nearest" });
      record(prompt, result);
    }, 420);
  }

  function record(prompt, result) {
    sessions.unshift({
      id: result.id,
      ts: new Date().toISOString(),
      q: prompt.slice(0, 120) + (prompt.length > 120 ? "…" : ""),
      status: result.status,
      score: result.score,
      rid: result.id
    });
    sessions = sessions.slice(0, 40);
    saveSessions();
    renderHistory();
  }

  /* ── Historique ───────────────────────────────────────────── */
  function renderHistory() {
    historyEl.innerHTML = sessions.map(function (s, i) {
      var badge = s.status === "answered"
        ? '<span style="color:var(--ok)">✓</span>'
        : '<span style="color:var(--danger)">⛔</span>';
      return '<button class="history__item" data-i="' + i + '">' +
        '<span>' + badge + ' ' + s.q + "</span>" +
        '<span class="history__del" data-del="' + i + '" title="Supprimer">×</span>' +
        "</button>";
    }).join("");
  }

  function restoreSession(i) {
    var s = sessions[i];
    if (!s) return;
    var result = Engine.solve(s.q);
    pushMessage("q", s.q);
    pushMessage("a", result.status === "answered" ? renderAnswer(result) : renderRefusal(result));
  }

  function exportSessions() {
    if (!sessions.length) { alert("Aucune session à exporter."); return; }
    var lines = sessions.map(function (s) {
      return "[" + s.ts + "] " + s.status.toUpperCase() + " · score " + s.score.toFixed(3) +
        "\n  Q : " + s.q + "\n  ID : " + s.rid;
    });
    var blob = new Blob(["HARMONIC AI FINANCE — journal des sessions\n\n" + lines.join("\n\n")],
      { type: "text/plain;charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "harmonic-finance-journal.txt";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  /* ── Événements ───────────────────────────────────────────── */
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var q = input.value.trim();
    if (!q) return;
    input.value = "";
    solve(q);
  });

  document.querySelectorAll(".sug").forEach(function (btn) {
    btn.addEventListener("click", function () {
      solve(btn.dataset.q);
    });
  });

  historyEl.addEventListener("click", function (e) {
    var del = e.target.closest("[data-del]");
    if (del) {
      e.stopPropagation();
      sessions.splice(parseInt(del.dataset.del, 10), 1);
      saveSessions();
      renderHistory();
      return;
    }
    var item = e.target.closest("[data-i]");
    if (item) restoreSession(parseInt(item.dataset.i, 10));
  });

  document.getElementById("btnExport").addEventListener("click", exportSessions);
  document.getElementById("btnClear").addEventListener("click", function () {
    if (!sessions.length) return;
    if (confirm("Effacer tout l'historique ?")) {
      sessions = [];
      saveSessions();
      renderHistory();
    }
  });

  // Bouton évaluation (Ctrl+Shift+E ou clic caché)
  document.addEventListener("keydown", function (e) {
    if (e.ctrlKey && e.shiftKey && e.key === "E") {
      e.preventDefault();
      runEval();
    }
  });

  function runEval() {
    if (!window.HAF_Eval) { alert("Module d'évaluation non chargé"); return; }
    pushMessage("q", "[ÉVALUATION] Lancement benchmark complet…");
    var think = pushMessage("a", '<div class="thinking"><div class="thinking__bars"><span></span><span></span><span></span><span></span><span></span></div>Évaluation en cours…</div>');
    setTimeout(function () {
      var metrics = window.HAF_Eval.run();
      var html = '<div class="eval-report">' +
        '<h4>📊 Rapport d\'évaluation</h4>' +
        '<div class="eval__overall">Global: P=' + (metrics.overall.precision * 100).toFixed(1) + '% R=' + (metrics.overall.recall * 100).toFixed(1) + '% F1=' + (metrics.overall.f1 * 100).toFixed(1) + '%</div>' +
        '<div class="eval__domains">' +
        Object.keys(metrics.byDomain).map(function (d) {
          var m = metrics.byDomain[d];
          return '<div class="eval__domain">[' + d + '] P=' + (m.precision * 100).toFixed(1) + '% R=' + (m.recall * 100).toFixed(1) + '% F1=' + (m.f1 * 100).toFixed(1) + '% (n=' + m.support + ')</div>';
        }).join("") +
        '</div>' +
        '<p style="margin-top:12px;font-family:var(--font-mono);font-size:11px;color:var(--muted)">Voir console développeur (F12) pour le détail complet.</p>' +
        '</div>';
      think.querySelector(".msg__bubble").innerHTML = html;
    }, 600);
  }

  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  renderHistory();
})();
