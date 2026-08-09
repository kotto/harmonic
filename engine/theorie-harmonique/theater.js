/* ─────────────────────────────────────────────────────────────
   THÉORIE HARMONIQUE UNIVERSELLE — theater.js
   Contrôle de la scène : sélection, lecture, vitesse, masse.
   ───────────────────────────────────────────────────────────── */
(function () {
  "use strict";

  var ANIMS = window.THU_ANIMS;
  var canvas = document.getElementById("stage");
  var ctx = canvas.getContext("2d");

  var state = {
    id: null,
    t: 0,
    playing: true,
    speed: 10,
    mass: 0.3
  };

  var W, H;

  function resize() {
    var stage = canvas.parentElement;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = stage.clientWidth;
    H = stage.clientHeight;
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    canvas.style.width = W + "px";
    canvas.style.height = H + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  var els = {
    list: document.getElementById("animList"),
    title: document.getElementById("stageTitle"),
    tag: document.getElementById("stageTag"),
    sub: document.getElementById("stageSub"),
    level: document.getElementById("stageLevel"),
    overlay: document.getElementById("stageOverlay"),
    progress: document.getElementById("progressFill"),
    play: document.getElementById("btnPlay"),
    pause: document.getElementById("btnPause"),
    reset: document.getElementById("btnReset"),
    speed: document.getElementById("speed"),
    speedVal: document.getElementById("speedVal"),
    massCtrl: document.getElementById("massCtrl"),
    mass: document.getElementById("mass"),
    massVal: document.getElementById("massVal")
  };

  /* ── Liste des animations ─────────────────────────────────── */
  function buildList() {
    els.list.innerHTML = Object.keys(ANIMS).map(function (id) {
      var a = ANIMS[id];
      return (
        '<button class="theater__item" data-id="' + id + '">' +
          '<span class="theater__item-icon">' + a.icon + '</span>' +
          '<span class="theater__item-body">' +
            '<span class="theater__item-title">' + a.title + '</span>' +
            '<span class="theater__item-tag">' + a.tag + '</span>' +
          '</span>' +
        '</button>'
      );
    }).join("");

    els.list.addEventListener("click", function (e) {
      var btn = e.target.closest(".theater__item");
      if (btn) select(btn.dataset.id);
    });
  }

  /* ── Sélection ────────────────────────────────────────────── */
  function select(id) {
    var a = ANIMS[id];
    if (!a) return;
    state.id = id;
    state.t = 0;
    state.playing = true;
    state.speed = a.defaultSpeed || 10;
    els.speed.value = state.speed;
    els.speedVal.textContent = state.speed + "×";
    els.massCtrl.hidden = a.id !== "gravite";

    Array.prototype.forEach.call(els.list.querySelectorAll(".theater__item"), function (b) {
      b.classList.toggle("is-active", b.dataset.id === id);
    });

    els.title.textContent = a.title;
    els.tag.textContent = a.tag;
    els.level.textContent = "";
    els.sub.textContent = "";
    els.overlay.innerHTML = "";
    document.title = "Animations — " + a.title + " · Théorie Harmonique Universelle";
  }

  /* ── Boucle de rendu ──────────────────────────────────────── */
  function meta() {
    return { level: "", sub: "", overlay: null, progress: null, extra: { mass: state.mass } };
  }

  function loop() {
    var a = ANIMS[state.id];
    if (!a) { requestAnimationFrame(loop); return; }

    if (state.playing) {
      state.t += 0.05 * (state.speed / 10);
    }

    var m = meta();
    a.draw(ctx, W, H, state.t, m);

    els.level.textContent = m.level || "";
    els.sub.textContent = m.sub || "";
    els.sub.style.opacity = m.sub ? 1 : 0;

    if (m.overlay && m.overlay.length) {
      els.overlay.innerHTML = m.overlay.map(function (o) {
        return '<div class="ov"><span>' + o.k + '</span>' + o.v + '</div>';
      }).join("");
    } else {
      els.overlay.innerHTML = "";
    }

    /* barre de progression */
    if (a.duration > 0) {
      var p = (state.t % a.duration) / a.duration;
      els.progress.style.width = Math.round(p * 100) + "%";
    } else if (m.progress != null) {
      els.progress.style.width = Math.round(ease01(m.progress) * 100) + "%";
    } else {
      els.progress.style.width = "0%";
    }

    requestAnimationFrame(loop);
  }

  function ease01(x) { return Math.min(1, Math.max(0, x)); }

  /* ── Contrôles ────────────────────────────────────────────── */
  function bindControls() {
    els.play.addEventListener("click", function () { state.playing = true; });
    els.pause.addEventListener("click", function () { state.playing = false; });
    els.reset.addEventListener("click", function () {
      state.t = 0;
      state.playing = true;
    });
    els.speed.addEventListener("input", function () {
      state.speed = parseInt(els.speed.value, 10) || 10;
      els.speedVal.textContent = state.speed + "×";
    });
    els.mass.addEventListener("input", function () {
      state.mass = (parseInt(els.mass.value, 10) || 0) / 100;
      els.massVal.textContent = Math.round(state.mass * 100) + "%";
    });
  }

  /* ── Init ─────────────────────────────────────────────────── */
  function init() {
    buildList();
    bindControls();
    resize();
    window.addEventListener("resize", resize);
    var params = new URLSearchParams(window.location.search);
    var requested = params.get("anim");
    select(ANIMS[requested] ? requested : "onde");
    loop();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
