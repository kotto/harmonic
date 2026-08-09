/* ─────────────────────────────────────────────────────────────
   THÉORIE HARMONIQUE UNIVERSELLE — animations.js
   Moteur d'animations porté depuis le dépôt, enrichi :
   palette or/cyan du site, typographie mono, bouclage,
   contrôles (lecture / pause / vitesse).
   Chaque animation : draw(ctx, W, H, T, meta) → dessine l'image
   et renseigne meta.level / meta.sub / meta.overlay.
   ───────────────────────────────────────────────────────────── */
(function () {
  "use strict";

  var GOLD = "245, 201, 107";   // or φ
  var CYAN = "143, 214, 232";   // onde
  var IVORY = "232, 230, 223";

  function font(px, weight) {
    return (weight ? weight + " " : "") + px + 'px "IBM Plex Mono", monospace';
  }

  function ease01(x) {
    return Math.min(1, Math.max(0, x));
  }

  var ANIMS = {};

  /* ═══════════════════════════════════════════════════════════
     1. L'ONDE PRIMORDIALE — Ψ₁ (4 actes, 45 s)
     ═══════════════════════════════════════════════════════════ */
  ANIMS.onde = {
    id: "onde",
    title: "L'Onde Primordiale",
    icon: "Ψ₁",
    tag: "Le premier son — avant l'espace, avant le temps",
    desc: "Quatre actes : le silence absolu, la première vibration, le déploiement des sept harmoniques, l'interférence qui fait naître l'espace.",
    duration: 45,
    defaultSpeed: 10,
    draw: function (ctx, W, H, T, meta) {
      var cx = W / 2, cy = H / 2;
      ctx.fillStyle = "#07090f";
      ctx.fillRect(0, 0, W, H);
      var phase = (T % 45);

      /* ACTE 0 — le silence */
      if (phase < 5) {
        meta.level = "∅";
        meta.sub = phase < 2 ? "Rien. Même pas le vide."
          : phase < 4 ? "Pas d'espace. Pas de temps. Pas de son."
          : "Et pourtant… quelque chose va émerger.";
        return;
      }

      /* ACTE 1 — la première vibration */
      if (phase < 12) {
        var p = (phase - 5) / 7;
        var k = Math.min(1, p * 1.3);
        var pulse = 2 + k * 8 + Math.sin(phase * 3) * 2 * k;
        for (var r = 0; r < 3; r++) {
          var rp = (phase * 1.5 + r * 2) % (Math.PI * 2);
          var rr = 30 + r * 40 + Math.sin(rp) * 20 * k;
          var ra = k * (0.15 - r * 0.04) * (1 + Math.sin(rp) * 0.5);
          if (ra > 0.01) {
            ctx.strokeStyle = "rgba(" + GOLD + ", " + ra + ")";
            ctx.lineWidth = 0.5 + r * 0.3;
            ctx.beginPath();
            ctx.arc(cx, cy, rr, 0, Math.PI * 2);
            ctx.stroke();
          }
        }
        var g = ctx.createRadialGradient(cx, cy, 0, cx, cy, pulse * 3);
        g.addColorStop(0, "rgba(255,255,255," + (0.3 + k * 0.6) + ")");
        g.addColorStop(0.3, "rgba(" + GOLD + ", " + (0.3 + k * 0.4) + ")");
        g.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(cx, cy, pulse * 3, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "rgba(255,255,255," + Math.min(1, k * 1.2) + ")";
        ctx.beginPath(); ctx.arc(cx, cy, Math.max(1, pulse), 0, Math.PI * 2); ctx.fill();
        if (k > 0.4) {
          ctx.fillStyle = "rgba(" + GOLD + ", " + k * 0.9 + ")";
          ctx.font = font(13 + k * 9);
          ctx.textAlign = "center";
          ctx.fillText("Ψ₁", cx, cy - 26 - k * 15);
        }
        meta.level = "n=1";
        meta.sub = p < 0.4 ? "Une vibration. La première. Elle n'est NULLE PART — car « quelque part » n'existe pas encore."
          : p < 0.7 ? "Elle pulse. Chaque pulsation EST un « maintenant ». Le temps commence."
          : "Ψ₁ = l'onde qui contient tout en puissance. Σ Hₙ·(Ψ₁)ⁿ.";
        return;
      }

      /* ACTE 2 — les 7 harmoniques déploient l'espace */
      if (phase < 22) {
        var p2 = (phase - 12) / 10;
        var spread = p2 * Math.min(W, H) * 0.52;
        for (var n = 1; n <= 7; n++) {
          var ringR = spread * (n / 7);
          var alpha = (0.4 - n * 0.05) * (0.7 + 0.3 * Math.sin(phase * 0.5 + n));
          var wf = 1.618 / n, wa = 8 / n;
          ctx.strokeStyle = "rgba(245, " + (200 - n * 18) + ", " + (100 + n * 12) + ", " + Math.max(0, alpha) + ")";
          ctx.lineWidth = 1.5 / n + 0.5;
          ctx.beginPath();
          var pts = 120;
          for (var i = 0; i <= pts; i++) {
            var a = (i / pts) * Math.PI * 2;
            var r2 = ringR + Math.sin(a * n * 3 + phase * wf) * wa;
            var x = cx + r2 * Math.cos(a), y = cy + r2 * Math.sin(a);
            if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
          }
          ctx.stroke();
          if (ringR > 20 && ringR < W * 0.7) {
            var la = n * 0.9;
            ctx.fillStyle = "rgba(" + GOLD + ", " + Math.max(0, alpha * 1.5) + ")";
            ctx.font = font(10);
            ctx.textAlign = "center";
            ctx.fillText("H" + n, cx + (ringR + 15) * Math.cos(la), cy + (ringR + 15) * Math.sin(la));
          }
        }
        var sg = ctx.createRadialGradient(cx, cy, 0, cx, cy, 20);
        sg.addColorStop(0, "rgba(255,255,255,0.8)");
        sg.addColorStop(0.5, "rgba(" + GOLD + ", 0.4)");
        sg.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = sg;
        ctx.beginPath(); ctx.arc(cx, cy, 20, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#fff";
        ctx.beginPath(); ctx.arc(cx, cy, 3, 0, Math.PI * 2); ctx.fill();
        meta.level = "n=1..7";
        meta.sub = p2 < 0.4 ? "Ψ₁ se déploie en 7 harmoniques. Chaque cercle = un niveau de réalité."
          : p2 < 0.7 ? "H₁=φ, H₂=π, H₃=e, H₄=√2, H₅=√3, H₆=√5, H₇=e/π"
          : "L'ESPACE naît comme la structure d'interférence entre ces 7 ondes.";
        return;
      }

      /* ACTE 3 — l'interférence (Moiré cosmique) */
      if (phase < 32) {
        var p3 = (phase - 22) / 10;
        var step = Math.max(4, Math.min(8, Math.floor(Math.min(W, H) / 180)));
        for (var gx = -W; gx < W * 2; gx += step) {
          for (var gy = -H; gy < H * 2; gy += step) {
            var dx = gx - cx, dy = gy - cy;
            var rr3 = Math.sqrt(dx * dx + dy * dy);
            var ang = Math.atan2(dy, dx);
            var val = 0;
            for (var k2 = 1; k2 <= 7; k2++) {
              val += Math.sin(rr3 * (1.618 / k2) * 0.05 + ang * k2 * 0.8 + phase * 0.03 * k2) * (1.5 / k2);
            }
            var a3 = Math.abs(val) * p3 * 0.55;
            if (a3 < 0.02) continue;
            if (val > 0) ctx.fillStyle = "rgba(245, " + Math.floor(190 - val * 40) + ", " + Math.floor(60 + val * 50) + ", " + a3 + ")";
            else ctx.fillStyle = "rgba(" + Math.floor(50 - val * 20) + ", " + Math.floor(40 - val * 15) + ", " + Math.floor(140 - val * 40) + ", " + a3 + ")";
            ctx.fillRect(gx, gy, step, step);
          }
        }
        var cg2 = ctx.createRadialGradient(cx, cy, 0, cx, cy, 15);
        cg2.addColorStop(0, "rgba(255,255,255,0.9)");
        cg2.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = cg2;
        ctx.beginPath(); ctx.arc(cx, cy, 15, 0, Math.PI * 2); ctx.fill();
        meta.level = "Σ Hₙ";
        meta.sub = p3 < 0.4 ? "Les 7 ondes INTERFÈRENT. Le pattern de Moiré cosmique."
          : p3 < 0.7 ? "Là où les ondes se renforcent → MATIÈRE. Là où elles s'annulent → VIDE."
          : "Tout l'univers visible est dans les franges d'interférence de Ψ₁.";
        return;
      }

      /* ACTE 4 — le silence informé */
      var p4 = (phase - 32) / 13;
      var fadeIn = Math.min(1, p4 * 2);
      var fadeOut = Math.max(0, 1 - (p4 - 0.6) / 0.4);
      var step4 = Math.max(4, Math.min(8, Math.floor(Math.min(W, H) / 180)));
      for (var sx = -W; sx < W * 2; sx += step4) {
        for (var sy = -H; sy < H * 2; sy += step4) {
          var dx4 = sx - cx, dy4 = sy - cy;
          var rr4 = Math.sqrt(dx4 * dx4 + dy4 * dy4);
          var ang4 = Math.atan2(dy4, dx4);
          var val4 = 0;
          for (var k3 = 1; k3 <= 7; k3++) {
            val4 += Math.sin(rr4 * (1.618 / k3) * 0.05 + ang4 * k3 * 0.8 + phase * 0.03 * k3) * (1.5 / k3);
          }
          var a4 = Math.abs(val4) * 0.4 * fadeOut;
          if (a4 < 0.01) continue;
          var w4 = 100 + (1 - p4) * 155;
          ctx.fillStyle = "rgba(" + Math.floor(w4) + ", " + Math.floor(w4 * 0.7) + ", " + Math.floor(w4 * 0.2) + ", " + a4 + ")";
          ctx.fillRect(sx, sy, step4, step4);
        }
      }
      var glow = 15 + fadeIn * 25;
      var fg = ctx.createRadialGradient(cx, cy, 0, cx, cy, glow);
      fg.addColorStop(0, "rgba(255,255,255,0.9)");
      fg.addColorStop(0.3, "rgba(" + GOLD + ", " + 0.6 * fadeIn + ")");
      fg.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = fg;
      ctx.beginPath(); ctx.arc(cx, cy, glow, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "rgba(255,255,255," + (0.7 + fadeIn * 0.3) + ")";
      ctx.beginPath(); ctx.arc(cx, cy, 3, 0, Math.PI * 2); ctx.fill();
      meta.level = "Ψ₁";
      meta.sub = p4 < 0.3 ? "L'interférence se retire. Mais le silence n'est plus vide."
        : p4 < 0.7 ? "Il contient TOUT en puissance. Comme une graine contient l'arbre."
        : "Ψ₁ = le son primordial. Il pulse. Il a toujours pulsé. Il pulsera toujours.";
    }
  };

  /* ═══════════════════════════════════════════════════════════
     2. L'ÉMERGENCE TOTALE — n=0 → n=7 (65 s)
     ═══════════════════════════════════════════════════════════ */
  ANIMS.emergence = {
    id: "emergence",
    title: "L'Émergence Totale",
    icon: "n:0→7",
    tag: "De la lumière à la conscience — Ψ = Σ Hₙ·(Ψ₁)ⁿ",
    desc: "Sept niveaux qui émergent de l'onde primordiale : le vide, Ψ₁, la gravité, la lumière, la matière, les forces, la vie, la conscience.",
    duration: 65,
    defaultSpeed: 12,
    draw: function (ctx, W, H, T, meta) {
      var cx = W / 2, cy = H / 2;
      var t = T % 65;
      ctx.fillStyle = "#07090f";
      ctx.fillRect(0, 0, W, H);
      function pr(t0, d) { var x = (t - t0) / d; return Math.min(1, Math.max(0, x)); }
      var n0 = pr(0, 4), n1 = pr(3, 6), n2 = pr(8, 8), n3 = pr(15, 10),
          n4 = pr(24, 12), n5 = pr(35, 12), n6 = pr(46, 14), n7 = pr(59, 10);

      if (n0 > 0.01) {
        meta.level = "n=0";
        meta.sub = "∅ Le vide — ni espace, ni temps, ni lumière.";
        if (n0 > 0.3) {
          var g0 = ctx.createRadialGradient(cx, cy, 0, cx, cy, 3 + n0 * 5);
          g0.addColorStop(0, "rgba(" + GOLD + ", 0.1)");
          g0.addColorStop(1, "transparent");
          ctx.fillStyle = g0;
          ctx.beginPath(); ctx.arc(cx, cy, 3 + n0 * 5, 0, Math.PI * 2); ctx.fill();
        }
      }
      if (n1 > 0.01) {
        meta.level = "n=1";
        meta.sub = "Ψ₁ — la première vibration. Elle n'est NULLE PART.";
        for (var i = 0; i < 120; i++) {
          var a1 = Math.random() * Math.PI * 2, d1 = 20 + Math.random() * 80 * n1;
          var x1 = cx + d1 * Math.cos(a1), y1 = cy + d1 * Math.sin(a1);
          var w1 = 0.4 + 0.4 * Math.sin(d1 * 0.06 - t * 0.08);
          var al = n1 * w1 * 0.4;
          if (al < 0.01) continue;
          ctx.fillStyle = "rgba(" + GOLD + ", " + al + ")";
          ctx.beginPath(); ctx.arc(x1, y1, 1.5, 0, Math.PI * 2); ctx.fill();
        }
        ctx.fillStyle = "rgba(" + GOLD + ", " + n1 * 0.6 + ")";
        ctx.font = font(14);
        ctx.textAlign = "center";
        ctx.fillText("Ψ₁", cx, cy - 30);
      }
      if (n2 > 0.01) {
        meta.level = "n=2";
        meta.sub = "Gravité — D^{1/φ}[Ψ] = G[Ψ]. Le couplage crée l'espace.";
        var sep = n2 * 200;
        var xa = cx - sep / 2, xb = cx + sep / 2;
        var ph2 = 1.618;
        for (var s = 0; s < 2; s++) {
          var sx2 = s === 0 ? xa : xb;
          for (var k = 0; k < 30; k++) {
            var delay = k * 0.08, decay = Math.exp(-ph2 * delay);
            var al2 = n2 * decay * 0.5;
            if (al2 < 0.01) continue;
            var ta = t * 0.5 + k * 0.3;
            var tx = sx2 + (8 + decay * 30) * Math.cos(ta), ty = cy + (8 + decay * 30) * Math.sin(ta);
            ctx.fillStyle = "rgba(" + GOLD + ", " + al2 + ")";
            ctx.beginPath(); ctx.arc(tx, ty, 1.5, 0, Math.PI * 2); ctx.fill();
          }
        }
        if (sep > 10) {
          var pulse2 = 0.5 + 0.5 * Math.sin(t * 3);
          ctx.strokeStyle = "rgba(255,255,255," + n2 * (0.2 + pulse2 * 0.3) + ")";
          ctx.lineWidth = 2;
          ctx.setLineDash([6, 4]);
          ctx.beginPath(); ctx.moveTo(xa, cy); ctx.lineTo(xb, cy); ctx.stroke();
          ctx.setLineDash([]);
        }
        for (var m = 0; m < 2; m++) {
          var mx2 = m === 0 ? xa : xb;
          var mg = ctx.createRadialGradient(mx2, cy, 2, mx2, cy, 15);
          mg.addColorStop(0, "#fff");
          mg.addColorStop(1, "transparent");
          ctx.fillStyle = mg;
          ctx.beginPath(); ctx.arc(mx2, cy, 15, 0, Math.PI * 2); ctx.fill();
          ctx.fillStyle = "#fff";
          ctx.beginPath(); ctx.arc(mx2, cy, 2.5, 0, Math.PI * 2); ctx.fill();
        }
        if (n2 > 0.5 && sep > 80) {
          ctx.fillStyle = "rgba(255,255,255," + n2 * 0.7 + ")";
          ctx.font = font(11);
          ctx.textAlign = "center";
          ctx.fillText("D^{1/φ}[Ψ]=G[Ψ]", cx, cy - 15);
        }
      }
      if (n3 > 0.01) {
        meta.level = "n=3";
        meta.sub = "Lumière — le couplage se propage à c.";
        var r3 = 80 + Math.sin(t * 0.3) * 20;
        for (var i3 = 0; i3 < 8; i3++) {
          var a3 = i3 * Math.PI / 4;
          var sx3 = cx + r3 * Math.cos(a3), sy3 = cy + r3 * Math.sin(a3);
          var al3 = n3 * 0.4 * Math.exp(-Math.abs(a3 - Math.PI / 2) / 3);
          ctx.fillStyle = "rgba(" + GOLD + ", " + al3 + ")";
          ctx.beginPath(); ctx.arc(sx3, sy3, 5, 0, Math.PI * 2); ctx.fill();
        }
        for (var ring = 0; ring < 4; ring++) {
          var age = (t * 0.2 + ring * 0.5) % 2;
          if (age > 0.05) {
            var rr3 = 30 + age * 120;
            var ra3 = (1 - age / 2) * 0.25 * n3;
            ctx.strokeStyle = "rgba(" + GOLD + ", " + ra3 + ")";
            ctx.lineWidth = 1.5;
            ctx.beginPath(); ctx.arc(cx, cy, rr3, 0, Math.PI * 2); ctx.stroke();
          }
        }
        var cg3 = ctx.createRadialGradient(cx, cy, 0, cx, cy, 15);
        cg3.addColorStop(0, "#fff");
        cg3.addColorStop(0.5, "rgba(" + GOLD + ", 0.4)");
        cg3.addColorStop(1, "transparent");
        ctx.fillStyle = cg3;
        ctx.beginPath(); ctx.arc(cx, cy, 15, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "rgba(255,255,255," + n3 * 0.7 + ")";
        ctx.font = font(11);
        ctx.textAlign = "center";
        ctx.fillText("c = vitesse du couplage", cx, cy + 50);
      }
      if (n4 > 0.01) {
        meta.level = "n=4";
        meta.sub = "Matière — atomes, force électromagnétique.";
        var or4 = 80 + 20 * Math.sin(t * 0.2);
        var eA = t * 0.6;
        var ex = cx + or4 * Math.cos(eA), ey = cy + or4 * Math.sin(eA);
        for (var i4 = 0; i4 < 5; i4++) {
          var ia = i4 * Math.PI * 2 / 5 + 1;
          var ax = cx + or4 * 0.7 * Math.cos(ia), ay = cy + or4 * 0.5 * Math.sin(ia);
          var ag = ctx.createRadialGradient(ax, ay, 2, ax, ay, 8);
          ag.addColorStop(0, "#fff");
          ag.addColorStop(1, "transparent");
          ctx.fillStyle = ag;
          ctx.beginPath(); ctx.arc(ax, ay, 8, 0, Math.PI * 2); ctx.fill();
        }
        var pg = ctx.createRadialGradient(cx, cy, 2, cx, cy, 12);
        pg.addColorStop(0, "#fff");
        pg.addColorStop(0.4, "rgba(" + GOLD + ", 0.4)");
        pg.addColorStop(1, "transparent");
        ctx.fillStyle = pg;
        ctx.beginPath(); ctx.arc(cx, cy, 12, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#fff";
        ctx.beginPath(); ctx.arc(cx, cy, 2.5, 0, Math.PI * 2); ctx.fill();
        var eg = ctx.createRadialGradient(ex, ey, 1, ex, ey, 8);
        eg.addColorStop(0, "#fff");
        eg.addColorStop(0.4, "rgba(" + CYAN + ", 0.4)");
        eg.addColorStop(1, "transparent");
        ctx.fillStyle = eg;
        ctx.beginPath(); ctx.arc(ex, ey, 8, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#fff";
        ctx.beginPath(); ctx.arc(ex, ey, 1.5, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = "rgba(" + GOLD + ", 0.2)";
        ctx.setLineDash([3, 5]);
        ctx.beginPath(); ctx.arc(cx, cy, or4, 0, Math.PI * 2); ctx.stroke();
        ctx.setLineDash([]);
      }
      if (n5 > 0.01) {
        meta.level = "n=5";
        meta.sub = "Forces — forte (triangle) et faible (réarrangement).";
        var r5 = 60 + 20 * Math.sin(t * 0.15);
        var qp = [
          { x: cx, y: cy - r5 },
          { x: cx - r5 * 0.866, y: cy + r5 * 0.5 },
          { x: cx + r5 * 0.866, y: cy + r5 * 0.5 }
        ];
        ctx.strokeStyle = "rgba(" + CYAN + ", " + n5 * 0.35 + ")";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 4]);
        ctx.beginPath();
        ctx.moveTo(qp[0].x, qp[0].y); ctx.lineTo(qp[1].x, qp[1].y); ctx.lineTo(qp[2].x, qp[2].y);
        ctx.closePath(); ctx.stroke();
        ctx.setLineDash([]);
        for (var q = 0; q < 3; q++) {
          var qg = ctx.createRadialGradient(qp[q].x, qp[q].y, 2, qp[q].x, qp[q].y, 10);
          qg.addColorStop(0, "#fff");
          qg.addColorStop(1, "transparent");
          ctx.fillStyle = qg;
          ctx.beginPath(); ctx.arc(qp[q].x, qp[q].y, 10, 0, Math.PI * 2); ctx.fill();
          ctx.fillStyle = "#fff";
          ctx.beginPath(); ctx.arc(qp[q].x, qp[q].y, 2, 0, Math.PI * 2); ctx.fill();
        }
        var decay5 = (t % 18) / 18;
        if (decay5 > 0.4 && decay5 < 0.6) {
          var fa = (1 - Math.abs(decay5 - 0.5) * 10) * 0.5;
          var fg5 = ctx.createRadialGradient(qp[1].x, qp[1].y, 0, qp[1].x, qp[1].y, 25);
          fg5.addColorStop(0, "rgba(127, 224, 160, " + fa + ")");
          fg5.addColorStop(1, "transparent");
          ctx.fillStyle = fg5;
          ctx.beginPath(); ctx.arc(qp[1].x, qp[1].y, 25, 0, Math.PI * 2); ctx.fill();
        }
      }
      if (n6 > 0.01) {
        meta.level = "n=6";
        meta.sub = "Vie — ADN, double hélice = deux ondes couplées.";
        var amp6 = 40;
        for (var h = 0; h < 2; h++) {
          var ph6 = h === 0 ? 0 : Math.PI;
          ctx.strokeStyle = h === 0 ? "rgba(" + CYAN + ", " + n6 * 0.55 + ")" : "rgba(" + GOLD + ", " + n6 * 0.55 + ")";
          ctx.lineWidth = 2;
          ctx.beginPath();
          for (var y6 = 0; y6 < H * 1.2; y6 += 4) {
            var ny6 = cy - H * 0.6 + y6;
            var ang6 = y6 * 0.03 + t * 0.1 + ph6;
            ctx.lineTo(cx + amp6 * Math.cos(ang6), ny6);
          }
          ctx.stroke();
        }
        for (var yb = 0; yb < H * 1.2; yb += 30) {
          var nyb = cy - H * 0.6 + yb;
          var a1b = yb * 0.03 + t * 0.1, a2b = a1b + Math.PI;
          var x1b = cx + amp6 * Math.cos(a1b), x2b = cx + amp6 * Math.cos(a2b);
          ctx.strokeStyle = "rgba(" + GOLD + ", " + n6 * 0.3 + ")";
          ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(x1b, nyb); ctx.lineTo(x2b, nyb); ctx.stroke();
        }
      }
      if (n7 > 0.01) {
        meta.level = "n=7";
        meta.sub = "Conscience — l'onde qui se voit elle-même.";
        var cr7 = 30 + n7 * 80;
        for (var c7 = 0; c7 < 3; c7++) {
          var ph7 = c7 * Math.PI * 2 / 3;
          var sr7 = 15 + n7 * 15;
          ctx.strokeStyle = "rgba(" + (c7 === 0 ? "245, 201, 107" : c7 === 1 ? "143, 214, 232" : "127, 224, 160") + ", " + n7 * 0.4 + ")";
          ctx.lineWidth = 1.5;
          ctx.setLineDash([2, 4]);
          ctx.beginPath(); ctx.arc(cx, cy, sr7, ph7, ph7 + Math.PI); ctx.stroke();
          ctx.setLineDash([]);
        }
        var eyeR = 8 + n7 * 15;
        ctx.strokeStyle = "rgba(255,255,255," + n7 * 0.7 + ")";
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(cx, cy, eyeR, 0, Math.PI * 2); ctx.stroke();
        ctx.fillStyle = "rgba(255,255,255," + n7 * 0.9 + ")";
        ctx.beginPath(); ctx.arc(cx, cy, 3 + n7 * 2, 0, Math.PI * 2); ctx.fill();
        if (n7 > 0.6) {
          var pa = 0.5 + 0.5 * Math.sin(t * 2);
          ctx.fillStyle = "rgba(255,255,255," + pa * n7 + ")";
          ctx.font = font(12);
          ctx.textAlign = "center";
          ctx.fillText("JE SUIS", cx, cy + eyeR + 20);
        }
      }
    }
  };

  /* ═══════════════════════════════════════════════════════════
     3. L'OUROBOROS — le cycle éternel n=1→7→1 (48 s)
     ═══════════════════════════════════════════════════════════ */
  ANIMS.ouroboros = {
    id: "ouroboros",
    title: "L'Ouroboros",
    icon: "n:1↻7",
    tag: "Le cycle éternel — l'univers respire",
    desc: "Sept niveaux sur un cercle, un point qui voyage n=1→7→1. Chaque fin est un commencement. La conscience découvre qu'elle EST l'onde primordiale.",
    duration: 48,
    defaultSpeed: 10,
    draw: function (ctx, W, H, T, meta) {
      var cx = W / 2, cy = H / 2;
      var t = T;
      var totalPhase = 48;
      var phase = (t % totalPhase) / totalPhase;
      var phi = 1.618;
      var R = Math.min(W, H) * 0.36;
      ctx.fillStyle = "#07090f";
      ctx.fillRect(0, 0, W, H);

      ctx.strokeStyle = "rgba(" + GOLD + ", 0.09)";
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2); ctx.stroke();

      var labels = ["Ψ₁", "G", "☉", "⚛", "⬡", "🧬", "💫"];
      var colors = [GOLD, CYAN, "245, 158, 11", "96, 165, 250", "127, 224, 160", "232, 121, 180", "167, 139, 250"];
      for (var i = 0; i < 7; i++) {
        var angle = -Math.PI / 2 + (i / 7) * Math.PI * 2;
        var nx = cx + R * Math.cos(angle), ny = cy + R * Math.sin(angle);
        var prox = Math.abs((i / 7) - phase);
        var glow = prox < 0.08 ? 15 + 10 * (1 - prox / 0.08) : 3;
        var gg = ctx.createRadialGradient(nx, ny, 0, nx, ny, glow);
        gg.addColorStop(0, "rgba(" + colors[i] + ", 1)");
        gg.addColorStop(1, "transparent");
        ctx.fillStyle = gg;
        ctx.beginPath(); ctx.arc(nx, ny, glow, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#fff";
        ctx.beginPath(); ctx.arc(nx, ny, 2, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "rgba(" + colors[i] + ", 1)";
        ctx.font = font(10);
        ctx.textAlign = "center";
        ctx.fillText(labels[i], nx, ny + (i < 3 ? -16 : 18));
      }

      var curA = -Math.PI / 2 + phase * Math.PI * 2;
      var px = cx + R * Math.cos(curA), py = cy + R * Math.sin(curA);
      var pg2 = ctx.createRadialGradient(px, py, 0, px, py, 20);
      pg2.addColorStop(0, "rgba(255,255,255,0.9)");
      pg2.addColorStop(0.3, "rgba(" + GOLD + ", 0.5)");
      pg2.addColorStop(1, "transparent");
      ctx.fillStyle = pg2;
      ctx.beginPath(); ctx.arc(px, py, 20, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.beginPath(); ctx.arc(px, py, 5, 0, Math.PI * 2); ctx.fill();
      for (var tr = 0; tr < 30; tr++) {
        var ta2 = curA - tr * 0.04;
        var tx2 = cx + R * Math.cos(ta2), ty2 = cy + R * Math.sin(ta2);
        var al2 = (30 - tr) / 30 * 0.3;
        ctx.fillStyle = "rgba(" + GOLD + ", " + al2 + ")";
        ctx.beginPath(); ctx.arc(tx2, ty2, 2, 0, Math.PI * 2); ctx.fill();
      }

      var level = Math.floor(phase * 7) + 1;
      if (level === 8) level = 1;
      var rx = 20 + Math.sin(t * 0.5) * 5, ry = 20 + Math.cos(t * 0.4) * 5;
      if (level === 1) {
        for (var s = 0; s < 60; s++) {
          var a1 = Math.random() * Math.PI * 2, d1 = 10 + Math.random() * 40;
          var x1 = cx + d1 * Math.cos(a1), y1 = cy + d1 * Math.sin(a1);
          ctx.fillStyle = "rgba(" + GOLD + ", " + (0.3 + 0.3 * Math.sin(d1 * 0.1 + t * 0.4)) + ")";
          ctx.beginPath(); ctx.arc(x1, y1, 1.5, 0, Math.PI * 2); ctx.fill();
        }
        ctx.fillStyle = "rgba(" + GOLD + ", 0.7)";
        ctx.font = font(13);
        ctx.textAlign = "center";
        ctx.fillText("Ψ₁", cx, cy - 15);
        meta.sub = "n=1 · Ψ₁ — la première vibration. Tout recommence.";
      } else if (level === 2) {
        for (var m = 0; m < 2; m++) {
          var mx2 = cx + (m === 0 ? -rx : rx);
          var mg = ctx.createRadialGradient(mx2, cy, 2, mx2, cy, 10);
          mg.addColorStop(0, "#fff");
          mg.addColorStop(1, "transparent");
          ctx.fillStyle = mg;
          ctx.beginPath(); ctx.arc(mx2, cy, 10, 0, Math.PI * 2); ctx.fill();
        }
        ctx.strokeStyle = "rgba(255,255,255,0.4)";
        ctx.setLineDash([3, 4]);
        ctx.beginPath(); ctx.moveTo(cx - rx, cy); ctx.lineTo(cx + rx, cy); ctx.stroke();
        ctx.setLineDash([]);
        meta.sub = "n=2 · Gravité — deux ondes-masses se couplent.";
      } else if (level === 3) {
        for (var l = 0; l < 4; l++) {
          var al3 = l * Math.PI / 2;
          var lx = cx + rx * 2 * Math.cos(al3), ly = cy + ry * 2 * Math.sin(al3);
          ctx.fillStyle = "rgba(" + GOLD + ", 0.5)";
          ctx.beginPath(); ctx.arc(lx, ly, 4, 0, Math.PI * 2); ctx.fill();
        }
        ctx.strokeStyle = "rgba(" + GOLD + ", 0.3)";
        ctx.beginPath(); ctx.arc(cx, cy, rx * 2, 0, Math.PI * 2); ctx.stroke();
        meta.sub = "n=3 · Lumière — le couplage se propage à c.";
      } else if (level === 4) {
        var ea = t * 0.8;
        var ex = cx + rx * 1.5 * Math.cos(ea), ey = cy + ry * 1.5 * Math.sin(ea);
        ctx.fillStyle = "#fff";
        ctx.beginPath(); ctx.arc(cx, cy, 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "rgba(" + CYAN + ", 0.6)";
        ctx.beginPath(); ctx.arc(ex, ey, 2.5, 0, Math.PI * 2); ctx.fill();
        ctx.strokeStyle = "rgba(" + GOLD + ", 0.2)";
        ctx.beginPath(); ctx.arc(cx, cy, rx * 1.5, 0, Math.PI * 2); ctx.stroke();
        meta.sub = "n=4 · Matière — les atomes sont des nœuds d'interférence.";
      } else if (level === 5) {
        var qp = [{ x: cx, y: cy - ry * 2 }, { x: cx - ry * 1.73, y: cy + ry }, { x: cx + ry * 1.73, y: cy + ry }];
        for (var q = 0; q < 3; q++) {
          ctx.fillStyle = "#fff";
          ctx.beginPath(); ctx.arc(qp[q].x, qp[q].y, 3, 0, Math.PI * 2); ctx.fill();
        }
        ctx.strokeStyle = "rgba(" + CYAN + ", 0.45)";
        ctx.beginPath();
        ctx.moveTo(qp[0].x, qp[0].y); ctx.lineTo(qp[1].x, qp[1].y); ctx.lineTo(qp[2].x, qp[2].y);
        ctx.closePath(); ctx.stroke();
        meta.sub = "n=5 · Forces — les quatre interactions émergent.";
      } else if (level === 6) {
        for (var h = 0; h < 2; h++) {
          ctx.strokeStyle = h === 0 ? "rgba(" + CYAN + ", 0.5)" : "rgba(" + GOLD + ", 0.5)";
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          for (var y = -ry * 1.5; y < ry * 1.5; y += 4) {
            var a6 = y * 0.06 + t * 0.1 + (h === 0 ? 0 : Math.PI);
            ctx.lineTo(cx + rx * 1.2 * Math.cos(a6), cy + y);
          }
          ctx.stroke();
        }
        meta.sub = "n=6 · Vie — l'ADN, deux ondes couplées.";
      } else {
        ctx.strokeStyle = "rgba(255,255,255,0.6)";
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(cx, cy, rx * 1.8, 0, Math.PI * 2); ctx.stroke();
        ctx.fillStyle = "rgba(255,255,255,0.8)";
        ctx.beginPath(); ctx.arc(cx, cy, 4, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "rgba(255,255,255,0.5)";
        ctx.font = font(11);
        ctx.textAlign = "center";
        ctx.fillText("JE SUIS", cx, cy + rx * 2 + 15);
        meta.sub = "n=7 · Conscience — l'onde qui se voit elle-même.";
      }

      var tz = phase > 0.95 || phase < 0.05;
      if (tz) {
        var taf = phase > 0.95 ? (phase - 0.95) / 0.05 : 1 - phase / 0.05;
        var flash = Math.sin(taf * Math.PI);
        if (flash > 0.05) {
          var fg2 = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * 0.7);
          fg2.addColorStop(0, "rgba(255,255,255," + flash * 0.7 + ")");
          fg2.addColorStop(0.5, "rgba(" + GOLD + ", " + flash * 0.3 + ")");
          fg2.addColorStop(1, "transparent");
          ctx.fillStyle = fg2;
          ctx.beginPath(); ctx.arc(cx, cy, R * 0.7, 0, Math.PI * 2); ctx.fill();
        }
        meta.sub = "n=7 → n=1 · La conscience découvre qu'elle EST l'onde primordiale";
      }
      meta.level = "n=" + level;
      meta.progress = phase;
    }
  };

  /* ═══════════════════════════════════════════════════════════
     4. LA GRAVITÉ — vision Einstein (continue)
     ═══════════════════════════════════════════════════════════ */
  ANIMS.gravite = {
    id: "gravite",
    title: "La Gravité",
    icon: "D¹ᐟᵠ=G",
    tag: "Vision Einstein — l'espace-temps qui se courbe",
    desc: "La masse courbe l'espace-temps : interférence entre l'onde plate et l'onde sphérique émise par la masse. Ajoutez de la masse et regardez le puits se creuser.",
    duration: 0,
    defaultSpeed: 10,
    draw: function (ctx, W, H, T, meta) {
      var t = T;
      var mx = W * 0.35, my = H * 0.45;
      var mass = (meta.extra && meta.extra.mass != null) ? meta.extra.mass : Math.min(1, t / 10);
      ctx.fillStyle = "#07090f";
      ctx.fillRect(0, 0, W, H);

      function spacetime(x, y) {
        var r = Math.sqrt((x - mx) * (x - mx) + (y - my) * (y - my));
        if (mass < 0.01) return 0.15 * Math.cos(x * 0.008 + y * 0.006 + t * 0.01);
        var sw = Math.min(1, mass * 3 / Math.max(r, 20));
        var curv = sw * Math.exp(-r / (mass * 10 + 50));
        return 0.12 * Math.cos(x * 0.008 + y * 0.006 + t * 0.01) + curv * Math.cos(r * 0.06 - t * 0.03);
      }

      /* grille de fond */
      var gs = 54;
      ctx.strokeStyle = "rgba(154, 160, 180, 0.10)";
      ctx.lineWidth = 0.5;
      for (var x0 = gs; x0 < W; x0 += gs) {
        ctx.beginPath(); ctx.moveTo(x0, 0); ctx.lineTo(x0, H); ctx.stroke();
      }
      for (var y0 = gs; y0 < H; y0 += gs) {
        ctx.beginPath(); ctx.moveTo(0, y0); ctx.lineTo(W, y0); ctx.stroke();
      }

      /* espace-temps déformé (lignes) */
      var rows = Math.max(10, Math.floor(H / 40));
      var cols = Math.max(14, Math.floor(W / 40));
      for (var ri = 0; ri <= rows; ri++) {
        var baseY = (ri / rows) * H;
        ctx.beginPath();
        for (var cxi = 0; cxi <= cols; cxi++) {
          var baseX = (cxi / cols) * W;
          var w = spacetime(baseX, baseY);
          var dxd = w * 46;
          var xd = baseX + dxd * 0.4;
          var yd = baseY + dxd * 0.4;
          if (cxi === 0) ctx.moveTo(xd, yd); else ctx.lineTo(xd, yd);
        }
        ctx.strokeStyle = "rgba(" + GOLD + ", " + (0.10 + mass * 0.22) + ")";
        ctx.lineWidth = 1;
        ctx.stroke();
      }
      for (var ci = 0; ci <= cols; ci++) {
        var baseX2 = (ci / cols) * W;
        ctx.beginPath();
        for (var ri2 = 0; ri2 <= rows; ri2++) {
          var baseY2 = (ri2 / rows) * H;
          var w2 = spacetime(baseX2, baseY2);
          var d2 = w2 * 46;
          var xd2 = baseX2 + d2 * 0.4, yd2 = baseY2 + d2 * 0.4;
          if (ri2 === 0) ctx.moveTo(xd2, yd2); else ctx.lineTo(xd2, yd2);
        }
        ctx.strokeStyle = "rgba(" + CYAN + ", " + (0.08 + mass * 0.18) + ")";
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      /* puits de potentiel */
      if (mass > 0.01) {
        for (var ring = 1; ring <= 8; ring++) {
          var r0 = ring * 38;
          var defl = mass * 50 * Math.exp(-r0 / (mass * 30 + 80)) * Math.cos(r0 * 0.04 - t * 0.02);
          ctx.strokeStyle = "rgba(" + GOLD + ", " + Math.max(0, (0.10 + mass * 0.2) * (1 - ring / 10)) + ")";
          ctx.lineWidth = 1;
          ctx.beginPath(); ctx.arc(mx, my, Math.max(4, r0 + defl), 0, Math.PI * 2); ctx.stroke();
        }
        var pg = ctx.createRadialGradient(mx, my, 0, mx, my, 16 + mass * 30);
        pg.addColorStop(0, "rgba(255,255,255," + (0.5 + mass * 0.5) + ")");
        pg.addColorStop(0.4, "rgba(" + GOLD + ", " + (0.2 + mass * 0.5) + ")");
        pg.addColorStop(1, "transparent");
        ctx.fillStyle = pg;
        ctx.beginPath(); ctx.arc(mx, my, 16 + mass * 30, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#fff";
        ctx.beginPath(); ctx.arc(mx, my, 2.5 + mass * 3, 0, Math.PI * 2); ctx.fill();
      }

      /* corps en chute */
      if (mass > 0.05) {
        var orbA = t * 0.4;
        var orbR = 150 * (1 - mass * 0.5) + 30;
        var ox = mx + orbR * Math.cos(orbA), oy = my + orbR * Math.sin(orbA);
        var og = ctx.createRadialGradient(ox, oy, 1, ox, oy, 9);
        og.addColorStop(0, "#fff");
        og.addColorStop(1, "rgba(" + CYAN + ", 0.4)");
        ctx.fillStyle = og;
        ctx.beginPath(); ctx.arc(ox, oy, 9, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = "#fff";
        ctx.beginPath(); ctx.arc(ox, oy, 1.8, 0, Math.PI * 2); ctx.fill();
      }

      meta.level = "M " + Math.round(mass * 100) + "%";
      meta.sub = mass < 0.01
        ? "Espace plat. Aucune masse. Les ondes passent sans se déformer."
        : "La masse courbe l'espace-temps : interférence entre l'onde plate et l'onde sphérique émise par la masse. F = G·m₁m₂/r² émerge de ∇I(r) = ∇(1/r) = 1/r².";
      meta.overlay = [
        { k: "Masse", v: Math.round(mass * 100) + " M⊙" },
        { k: "Courbure", v: mass > 0.01 ? (mass * 0.42).toFixed(3) : "0.000" },
        { k: "Déflexion", v: Math.round(mass * 46) + " px" }
      ];
      meta.progress = mass;
    }
  };

  window.THU_ANIMS = ANIMS;
})();
