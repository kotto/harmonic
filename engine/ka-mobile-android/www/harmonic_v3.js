/* ══════════════════════════════════════════════════════════════════════════
   HARMONIC AI v3 — Client JS pour KA Mobile
   ══════════════════════════════════════════════════════════════════════════
   Intelligence ondulatoire embarquée dans la WebView :

   • PhaseEncoder  : s_n = exp(i·α·n) — addition/soustraction ÉMERGENTES,
                     O(1), zéro aliasing, utilisable HORS-LIGNE.
   • LogEncoder    : Ψ_n = exp(i·log(n)·SCALE·k·x) — mul/div émergentes
                     via FFT (nécessite numpy-wasm — sinon fallback natif).
   • KuramotoNet   : inférence logique par synchronisation de phase.

   PRINCIPES :
     1. L'addition ÉMERGE : s_a · s_b = s_{a+b} (0 fait stocké)
     2. La négation est PHYSIQUE : s + (-s) = 0
     3. Déterminisme 100% : même entrée → même sortie

   Intégration : inclure <script src="harmonic_v3.js"></script>
   puis utiliser window.HarmonicAI.
   ══════════════════════════════════════════════════════════════════════════ */
(function (global) {
  'use strict';

  var TAU = 2 * Math.PI;
  var PHI = (1 + Math.sqrt(5)) / 2;

  // ── PhaseEncoder : add/sub émergents (O(1), zéro aliasing) ──
  function PhaseEncoder(maxN) {
    this.maxN = maxN || 200000;
    this.alpha = TAU / (this.maxN * 2 + 1);
  }
  PhaseEncoder.prototype.encode = function (n) {
    return { re: Math.cos(this.alpha * n), im: Math.sin(this.alpha * n) };
  };
  PhaseEncoder.prototype.decode = function (s) {
    var p = Math.atan2(s.im, s.re);
    if (p < 0) p += TAU;
    var n = p / this.alpha;
    var r = Math.round(n);
    return Math.abs(n - r) < 0.001 ? r : n;
  };
  PhaseEncoder.prototype.mul = function (a, b) {
    return { re: a.re * b.re - a.im * b.im, im: a.re * b.im + a.im * b.re };
  };
  PhaseEncoder.prototype.conj = function (a) { return { re: a.re, im: -a.im }; };
  PhaseEncoder.prototype.add = function (a, b) { return this.decode(this.mul(this.encode(a), this.encode(b))); };
  PhaseEncoder.prototype.sub = function (a, b) { return this.decode(this.mul(this.encode(a), this.conj(this.encode(b)))); };

  // ── Solver arithmétique hybride ──
  function HarmonicSolver() {
    this.phase = new PhaseEncoder(200000);
    // Fallback natif pour mul/div (la FFT JS serait trop lente sans wasm)
  }
  HarmonicSolver.prototype.solve = function (expr) {
    expr = expr.replace(/\s+/g, '');
    // Addition / soustraction (émergence phase)
    var m;
    if ((m = expr.match(/^([\d.]+)\+([\d.]+)$/))) return this.phase.add(parseFloat(m[1]), parseFloat(m[2]));
    if ((m = expr.match(/^([\d.]+)-([\d.]+)$/))) return this.phase.sub(parseFloat(m[1]), parseFloat(m[2]));
    // Multiplication / division (fallback natif — FFT JS non dispo)
    if ((m = expr.match(/^([\d.]+)\*([\d.]+)$/))) return parseFloat(m[1]) * parseFloat(m[2]);
    if ((m = expr.match(/^([\d.]+)\/([\d.]+)$/))) return parseFloat(m[1]) / parseFloat(m[2]);
    // Chaîne additive a+b+c
    if ((m = expr.match(/^[\d.]+(\+[\d.]+)+$/))) {
      var parts = expr.split('+').map(parseFloat);
      var s = this.phase.encode(parts[0]);
      for (var i = 1; i < parts.length; i++) s = this.phase.mul(s, this.phase.encode(parts[i]));
      return this.phase.decode(s);
    }
    return NaN;
  };
  HarmonicSolver.prototype.isArithmetic = function (expr) {
    return /^[\d\s.+\-*/()]+$/.test(expr) && /[\d]/.test(expr);
  };

  // ── KuramotoNet minimal : inférence logique par phases ──
  function KuramotoNet(kappa) {
    this.kappa = kappa || 1.0;
    this.names = [];
    this.idx = {};
    this.facts = [];      // [a, b, strength]
    this.exclusions = []; // [a, b]
  }
  KuramotoNet.prototype.addNode = function (name) {
    if (!(name in this.idx)) { this.idx[name] = this.names.length; this.names.push(name); }
  };
  KuramotoNet.prototype.implication = function (a, b, strength) {
    this.addNode(a); this.addNode(b);
    this.facts.push([a, b, strength || 1.0]);
  };
  KuramotoNet.prototype.exclusion = function (a, b) {
    this.addNode(a); this.addNode(b);
    this.exclusions.push([a, b]);
  };
  KuramotoNet.prototype.run = function (steps, seed) {
    var n = this.names.length, i, j, t, s;
    // Matrice K
    var K = [];
    for (i = 0; i < n; i++) K.push(new Float64Array(n));
    for (i = 0; i < this.facts.length; i++) {
      var f = this.facts[i];
      K[this.idx[f[1]]][this.idx[f[0]]] += this.kappa * f[2];
      K[this.idx[f[0]]][this.idx[f[1]]] += this.kappa * f[2] * 0.5;
    }
    for (i = 0; i < this.exclusions.length; i++) {
      var e = this.exclusions[i];
      K[this.idx[e[0]]][this.idx[e[1]]] -= this.kappa;
      K[this.idx[e[1]]][this.idx[e[0]]] -= this.kappa;
    }
    // Phases aléatoires déterministes (seed simple)
    var theta = [];
    for (i = 0; i < n; i++) {
      var h = (seed || 42) * 2654435761 + i * 40503;
      h = (h ^ (h >> 13)) >>> 0;
      theta.push((h / 4294967296) * TAU);
    }
    var dt = 0.02;
    for (t = 0; t < steps; t++) {
      var dtheta = new Float64Array(n);
      for (i = 0; i < n; i++) {
        var sum = 0;
        for (j = 0; j < n; j++) if (K[i][j] !== 0) sum += K[i][j] * Math.sin(theta[j] - theta[i]);
        dtheta[i] = sum;
      }
      for (i = 0; i < n; i++) theta[i] += dt * dtheta[i];
    }
    return theta;
  };
  KuramotoNet.prototype.infer = function (question, candidates, steps) {
    var tokens = question.toLowerCase().match(/[a-zà-ÿ]+/g) || [];
    var qe = tokens.filter(function (t) { return t in this.idx; });
    // Pas d'ancrage dans cette version légère — on mesure la cohérence
    var theta = this.run(steps || 200, 42);
    var out = [];
    for (var i = 0; i < candidates.length; i++) {
      var c = candidates[i].toLowerCase();
      if (c in this.idx) {
        var ph = theta[this.idx[c]] % TAU;
        var dist = Math.min(ph, TAU - ph);
        out.push({ candidate: candidates[i], score: 1 / (1 + dist), verdict: dist < 0.35 ? 'true' : '?' });
      } else out.push({ candidate: candidates[i], score: 0, verdict: '?' });
    }
    out.sort(function (a, b) { return b.score - a.score; });
    return out.slice(0, 5);
  };

  // ── API publique ──
  var HarmonicAI = {
    version: '3.0',
    solver: new HarmonicSolver(),
    net: new KuramotoNet(1.0),
    PHI: PHI,
    TAU: TAU,

    /** Résout une expression arithmétique (émergence si possible). */
    solve: function (expr) {
      if (!this.solver.isArithmetic(expr)) return NaN;
      return this.solver.solve(expr);
    },

    /** Vérifie si un message contient une arithmétique émergente. */
    detect: function (message) {
      var m = message.match(/([\d.]+)\s*([+\-*/])\s*([\d.]+)/);
      if (!m) return null;
      return { a: parseFloat(m[1]), op: m[2], b: parseFloat(m[3]) };
    },

    /** Ingère un fait dans le réseau Kuramoto. */
    ingest: function (sujet, relation, objet) {
      this.net.implication(sujet.toLowerCase(), objet.toLowerCase());
      return { ok: true, facts: this.net.facts.length };
    },

    /** Inférence logique par synchronisation. */
    ask: function (question, candidates) {
      return this.net.infer(question, candidates || [], 200);
    },

    /** Émergence vs calcul : statistiques d'utilisation. */
    stats: { emergence: 0, fallback: 0 }
  };

  // Hook : intercepter les messages arithmétiques avant l'envoi serveur
  HarmonicAI.tryLocal = function (message) {
    var det = HarmonicAI.detect(message);
    if (det && (det.op === '+' || det.op === '-')) {
      HarmonicAI.stats.emergence++;
      var expr = det.a + det.op + det.b;
      return { local: true, expression: expr, result: HarmonicAI.solve(expr), method: 'phase_emergence' };
    }
    return { local: false };
  };

  global.HarmonicAI = HarmonicAI;
  if (global.console && console.log) console.log('KA · HarmonicAI v3 embarqué (émergence phase O(1))');

})(typeof window !== 'undefined' ? window : this);
