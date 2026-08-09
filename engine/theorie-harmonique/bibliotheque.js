/* ─────────────────────────────────────────────────────────────
   THÉORIE HARMONIQUE UNIVERSELLE — bibliotheque.js
   Sommaire des documents, chargement et rendu du contenu.
   ───────────────────────────────────────────────────────────── */
(function () {
  "use strict";

  var D = window.THU_DATA;
  var CATS = {
    fondamentaux: "Fondamentaux",
    derivations: "Dérivations",
    applications: "Applications",
    ouverts: "Problèmes ouverts"
  };

  var content = document.getElementById("libContent");
  var toc = document.getElementById("libToc");
  var countEl = document.getElementById("libCount");

  /* ── Sommaire ─────────────────────────────────────────────── */
  function buildToc() {
    if (countEl) {
      countEl.textContent = D.documents.length + " documents";
    }
    if (!toc) return;
    toc.innerHTML = Object.keys(CATS).map(function (cat) {
      var docs = D.documents.filter(function (d) { return d.category === cat; });
      var items = docs.map(function (d) {
        return (
          '<li>' +
            '<a href="bibliotheque.html?doc=' + encodeURIComponent(d.file) + '" data-file="' + d.file + '">' +
              '<span class="lib__doc-title">' + d.title + '</span>' +
            '</a>' +
          '</li>'
        );
      }).join("");
      return (
        '<div class="lib__cat">' +
          '<h3 class="lib__cat-name">' + CATS[cat] + ' <span class="lib__cat-count">' + docs.length + '</span></h3>' +
          '<ul class="lib__docs">' + items + '</ul>' +
        '</div>'
      );
    }).join("");
  }

  /* ── Chargement d'un document ─────────────────────────────── */
  function loadDoc(file) {
    var doc = D.documents.filter(function (d) { return d.file === file; })[0];
    if (!doc) { openEmpty(); return; }

    /* état actif dans le sommaire */
    Array.prototype.forEach.call(toc.querySelectorAll("a[data-file]"), function (a) {
      a.classList.toggle("is-active", a.dataset.file === file);
    });

    content.innerHTML =
      '<div class="lib__loading"><span class="lib__spinner"></span><p>Lecture de « ' +
      doc.title + ' »…</p></div>';

    fetch("docs/" + file)
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.text();
      })
      .then(function (md) {
        var rendered = window.MarkdownRenderer.render(md);
        content.innerHTML =
          '<div class="md">' +
            '<header class="md__header">' +
              '<p class="section-kicker">' + (CATS[doc.category] || doc.category) + '</p>' +
              '<h1>' + escapeHtmlText(doc.title) + '</h1>' +
              '<p class="md__meta">' + doc.file + '</p>' +
            '</header>' +
            rendered +
          '</div>';
        window.scrollTo({ top: 0, behavior: "auto" });
      })
      .catch(function (err) {
        content.innerHTML =
          '<div class="lib__error"><p>Impossible de charger « ' + doc.file + ' ».</p>' +
          '<p class="md__meta">' + err.message + '</p></div>';
      });
  }

  function openEmpty() {
    content.innerHTML =
      '<div class="lib__empty">' +
        '<span class="lib__empty-sigil" aria-hidden="true">∿</span>' +
        '<p>Choisissez un document dans la bibliothèque.<br />La théorie écrite, dans son intégralité.</p>' +
      '</div>';
  }

  function escapeHtmlText(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  /* ── Délégation de clics sur le sommaire (sans rechargement) ─ */
  function bindToc() {
    if (!toc) return;
    toc.addEventListener("click", function (e) {
      var a = e.target.closest("a[data-file]");
      if (a) {
        e.preventDefault();
        loadDoc(a.dataset.file);
      }
    });
  }

  /* ── Init ─────────────────────────────────────────────────── */
  function init() {
    buildToc();
    bindToc();
    var params = new URLSearchParams(window.location.search);
    var file = params.get("doc");
    if (file) {
      loadDoc(file);
    } else {
      openEmpty();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
