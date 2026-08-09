/* ─────────────────────────────────────────────────────────────
   THÉORIE HARMONIQUE UNIVERSELLE — app.js
   Rendu des données, ondes animées, révélations, compteurs, nav.
   ───────────────────────────────────────────────────────────── */
(function () {
  "use strict";

  var D = window.THU_DATA;

  /* ── Révélations au scroll ─────────────────────────────────── */
  function initReveals() {
    var els = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("is-visible"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ── Canvas : interférence d'ondes (hero) ──────────────────── */
  function initWaves() {
    var canvas = document.getElementById("waves");
    if (!canvas) return;
    var ctx = canvas.getContext("2d");
    var W, H, dpr;
    var t = 0;
    var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = canvas.clientWidth;
      H = canvas.clientHeight;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    /* Plusieurs ondes (fréquences liées à φ) dont la somme crée l'interférence */
    function draw() {
      ctx.clearRect(0, 0, W, H);
      var n = 6;
      var baseAmp = H * 0.035;
      for (var k = 0; k < n; k++) {
        var phi = Math.pow(1.618033988749895, -(k + 1));       // fréquences φ-spacées
        var speed = 0.00055 + k * 0.00009;
        var amp = baseAmp * (1.35 - k * 0.13);
        var color = k % 2 === 0
          ? "rgba(245, 201, 107, " + (0.16 - k * 0.018) + ")"
          : "rgba(143, 214, 232, " + (0.13 - k * 0.015) + ")";
        ctx.beginPath();
        for (var x = 0; x <= W; x += 4) {
          var y = H * (0.42 + 0.16 * Math.sin(x * 0.0032 * phi + t * speed * 10))   // grande enveloppe
                 + amp * Math.sin(x * 0.011 * phi + t * speed * 40)                  // onde fine
                 + amp * 0.45 * Math.sin(x * 0.0052 + t * speed * 17);               // 2e harmonique
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.stroke();
      }
      // Ligne de résonance centrale (l'égalité D[Ψ]=G[Ψ])
      ctx.beginPath();
      var yr = H * 0.42;
      ctx.moveTo(0, yr);
      ctx.lineTo(W, yr);
      ctx.strokeStyle = "rgba(245, 201, 107, 0.08)";
      ctx.setLineDash([2, 10]);
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.setLineDash([]);
    }

    function loop() {
      t += 1;
      draw();
      requestAnimationFrame(loop);
    }

    resize();
    window.addEventListener("resize", resize);
    if (reduced) { draw(); } else { loop(); }
  }

  /* ── Rendu : constantes ────────────────────────────────────── */
  function renderConstants() {
    var grid = document.getElementById("constantsGrid");
    if (!grid || !D.constants) return;
    grid.innerHTML = D.constants.map(function (c) {
      return (
        '<article class="const-card reveal" data-delay="' + ((c.n - 1) % 4) + '">' +
          '<span class="const-card__num">H' + c.n + '</span>' +
          '<div class="const-card__symbol">' + c.symbol + '</div>' +
          '<div class="const-card__name">' + c.name + '</div>' +
          '<div class="const-card__value">' + c.value + '</div>' +
          '<p class="const-card__role">' + c.role + '</p>' +
          '<p class="const-card__geo">' + c.geo + '</p>' +
        '</article>'
      );
    }).join("");
  }

  /* ── Rendu : axiomes ───────────────────────────────────────── */
  function renderAxioms() {
    var list = document.getElementById("axiomsList");
    if (!list || !D.axioms) return;
    list.innerHTML = D.axioms.map(function (a) {
      return (
        '<li class="reveal">' +
          '<span class="axiom__n">' + String(a.n).padStart(2, "0") + '</span>' +
          '<div>' +
            '<h4 class="axiom__title">' + a.title + '</h4>' +
            '<p class="axiom__text">' + a.text + '</p>' +
          '</div>' +
        '</li>'
      );
    }).join("");
  }

  /* ── Rendu : table des dérivations ─────────────────────────── */
  function renderDerivations() {
    var body = document.getElementById("derivBody");
    if (!body || !D.derivations) return;
    body.innerHTML = D.derivations.map(function (d) {
      return (
        '<tr>' +
          '<td>' + d.domaine + '</td>' +
          '<td>' + d.equation + '</td>' +
          '<td>' + d.derivee + '</td>' +
          '<td>' + d.constantes + '</td>' +
        '</tr>'
      );
    }).join("");
  }

  /* ── Badge « Innovation majeure » dans chaque section ──────── */
  function injectBadges() {
    /* héro, équation fondatrice, manifeste */
    var hero = document.querySelector(".hero__content");
    if (hero && !hero.querySelector(".badge")) {
      var hb = document.createElement("span");
      hb.className = "badge";
      hb.textContent = "Innovation majeure — un formalisme unique pour tous les domaines";
      hero.insertBefore(hb, hero.firstChild);
    }
    var fond = document.querySelector(".fondatrice__inner");
    if (fond && !fond.querySelector(".badge")) {
      var fb = document.createElement("span");
      fb.className = "badge";
      fb.textContent = "Innovation majeure — l'équation qui dit tout";
      fond.insertBefore(fb, fond.firstChild);
    }
    var man = document.querySelector(".manifeste__inner");
    if (man && !man.querySelector(".badge")) {
      var mb = document.createElement("span");
      mb.className = "badge";
      mb.textContent = "Innovation majeure — la stratégie : les résultats d'abord";
      man.insertBefore(mb, man.firstChild);
    }
    /* chaque section du site */
    document.querySelectorAll("main .section").forEach(function (sec) {
      var head = sec.querySelector(".section__head");
      if (!head || head.querySelector(".badge")) return;
      var b = document.createElement("span");
      b.className = "badge";
      b.textContent = "Innovation majeure";
      head.insertBefore(b, head.firstChild);
    });
  }

  /* ── Rendu : applications ──────────────────────────────────── */
  function renderApps() {
    var grid = document.getElementById("appsGrid");
    if (!grid || !D.applications) return;
    grid.innerHTML = D.applications.map(function (a) {
      var stats = a.stats.map(function (s) {
        return (
          '<div class="app-card__stat">' +
            '<span class="app-card__stat-k">' + s.k + '</span>' +
            '<span class="app-card__stat-v">' + s.v + '</span>' +
          '</div>'
        );
      }).join("");
      return (
        '<article class="app-card reveal">' +
          '<div class="app-card__head">' +
            '<span class="app-card__id">' + a.id + '</span>' +
            '<div class="app-card__icon" aria-hidden="true">' + a.icon + '</div>' +
          '</div>' +
          '<div class="app-card__titleblock">' +
            '<h3 class="app-card__title">' + a.name + '</h3>' +
            '<p class="app-card__claim">' + a.claim + '</p>' +
            '<span class="badge badge--sm">Innovation majeure</span>' +
          '</div>' +
          '<div class="app-card__body">' +
            '<div class="app-card__stats">' + stats + '</div>' +
            '<p class="app-card__detail">' + a.detail + '</p>' +
            '<p class="app-card__modules">' + a.modules + '</p>' +
          '</div>' +
        '</article>'
      );
    }).join("");
  }

  /* ── Rendu : compteurs animés ──────────────────────────────── */
  function renderStats() {
    var grid = document.getElementById("statsGrid");
    if (!grid || !D.stats) return;
    grid.innerHTML = D.stats.map(function (s, i) {
      return (
        '<div class="stat reveal" data-delay="' + (i % 4) + '">' +
          '<div class="stat__value" data-count="' + s.value + '" data-suffix="' + s.suffix + '">0</div>' +
          '<div class="stat__label">' + s.label + '</div>' +
        '</div>'
      );
    }).join("");
    animateCounters();
  }

  function animateCounters() {
    var counters = document.querySelectorAll(".stat__value[data-count]");
    if (!("IntersectionObserver" in window)) {
      counters.forEach(function (el) {
        el.textContent = el.dataset.count + el.dataset.suffix;
      });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        io.unobserve(el);
        var target = parseInt(el.dataset.count, 10);
        var suffix = el.dataset.suffix || "";
        var start = null;
        var dur = 1300;
        function step(ts) {
          if (!start) start = ts;
          var p = Math.min((ts - start) / dur, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * eased) + suffix;
          if (p < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
      });
    }, { threshold: 0.4 });
    counters.forEach(function (el) { io.observe(el); });
  }

  /* ── Rendu : benchmarks ────────────────────────────────────── */
  function renderBenchmarks() {
    var body = document.getElementById("benchBody");
    if (!body || !D.benchmarks) return;
    body.innerHTML = D.benchmarks.map(function (b) {
      return (
        '<tr>' +
          '<td>' + b.name + '</td>' +
          '<td><span class="bench-result">' + b.result + '</span></td>' +
          '<td>' + b.preuve + '</td>' +
        '</tr>'
      );
    }).join("");
  }

  /* ── Rendu : preuves ───────────────────────────────────────── */
  function renderProofs() {
    var grid = document.getElementById("proofsGrid");
    if (!grid || !D.proofs) return;
    grid.innerHTML = D.proofs.map(function (p) {
      return (
        '<article class="proof reveal">' +
          '<h3 class="proof__domaine">' + p.domaine + '</h3>' +
          '<span class="proof__eq">' + p.equivalence + '</span>' +
          '<span class="proof__precision">' + p.precision + '</span>' +
          '<span class="proof__niveau">' + p.niveau + '</span>' +
        '</article>'
      );
    }).join("");
  }

  /* ── Navigation : état au scroll + menu mobile ─────────────── */
  function initNav() {
    var nav = document.getElementById("nav");
    var links = Array.prototype.slice
      .call(document.querySelectorAll(".nav__links a"))
      .filter(function (a) { return (a.getAttribute("href") || "")[0] === "#"; });
    var toggle = document.getElementById("navToggle");
    var menu = document.querySelector(".nav__links");

    function onScroll() {
      nav.classList.toggle("nav--scrolled", window.scrollY > 30);
      var pos = window.scrollY + window.innerHeight * 0.35;
      var current = "hero";
      links.forEach(function (a) {
        var sec = document.querySelector(a.getAttribute("href"));
        if (sec && sec.offsetTop <= pos) current = a.getAttribute("href");
      });
      links.forEach(function (a) {
        a.classList.toggle("is-active", a.getAttribute("href") === current);
      });
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    if (toggle && menu) {
      toggle.addEventListener("click", function () {
        var open = menu.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      menu.querySelectorAll("a").forEach(function (a) {
        a.addEventListener("click", function () {
          menu.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
        });
      });
    }
  }

  /* ── Rendu : puces du langage ondulatoire ─────────────────── */
  function renderLangChips() {
    var chips = document.getElementById("langChips");
    if (!chips || !D.waveLanguage) return;
    chips.innerHTML = D.waveLanguage.primitives.map(function (p) {
      return '<a class="lang-chip" href="langage.html">' + p.name + '</a>';
    }).join("");
  }

  /* ── Rendu : aperçu des équivalences LLM ──────────────────── */
  function renderEqTeaser() {
    var body = document.getElementById("eqTeaser");
    if (!body || !D.equivalences) return;
    body.innerHTML = D.equivalences.slice(0, 6).map(function (e) {
      return (
        "<tr>" +
          "<td>" + e.n + "</td>" +
          "<td class='eq-llm'>" + e.llm + "</td>" +
          "<td class='eq-wave'>" + e.wave + "</td>" +
          "<td class='eq-file'>" + e.file + "</td>" +
        "</tr>"
      );
    }).join("");
  }

  /* ── Rendu : animations ───────────────────────────────────── */
  function renderAnims() {
    var grid = document.getElementById("animsGrid");
    if (!grid || !D.animations) return;
    grid.innerHTML = D.animations.map(function (a, i) {
      return (
        '<a class="anim reveal" data-delay="' + (i % 4) + '" href="animations.html?anim=' + a.id + '">' +
          '<div class="anim__icon" aria-hidden="true">' + a.icon + '</div>' +
          '<div class="anim__meta">' +
            '<span class="anim__tag">' + a.tag + '</span>' +
            '<span class="anim__duration">' + a.duration + '</span>' +
          '</div>' +
          '<h3 class="anim__title">' + a.title + '</h3>' +
          '<p class="anim__desc">' + a.desc + '</p>' +
          '<span class="anim__go">Lancer la scène →</span>' +
        '</a>'
      );
    }).join("");
  }

  /* ── Rendu : bibliothèque (aperçu par catégorie) ──────────── */
  var CATS = {
    fondamentaux: "Fondamentaux",
    derivations: "Dérivations",
    applications: "Applications",
    ouverts: "Problèmes ouverts"
  };

  function renderLibCats() {
    var grid = document.getElementById("libCats");
    if (!grid || !D.documents) return;
    grid.innerHTML = Object.keys(CATS).map(function (cat, ci) {
      var docs = D.documents.filter(function (d) { return d.category === cat; });
      var items = docs.slice(0, 5).map(function (d) {
        return (
          '<li><a href="bibliotheque.html?doc=' + encodeURIComponent(d.file) + '">' + d.title + '</a></li>'
        );
      }).join("");
      return (
        '<article class="libcat reveal" data-delay="' + (ci % 4) + '">' +
          '<div class="libcat__head">' +
            '<h3 class="libcat__name">' + CATS[cat] + '</h3>' +
            '<span class="libcat__count">' + docs.length + '</span>' +
          '</div>' +
          '<ul class="libcat__list">' + items + '</ul>' +
          '<a class="libcat__more" href="bibliotheque.html?cat=' + cat + '">Tout lire →</a>' +
        '</article>'
      );
    }).join("");
  }

  /* ── Init ──────────────────────────────────────────────────── */
  function init() {
    renderConstants();
    renderAxioms();
    renderDerivations();
    renderApps();
    renderStats();
    renderBenchmarks();
    renderProofs();
    renderLangChips();
    renderEqTeaser();
    renderAnims();
    renderLibCats();
    injectBadges();
    initNav();
    initWaves();
    initReveals();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
