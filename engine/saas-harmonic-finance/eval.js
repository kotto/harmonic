/* ─────────────────────────────────────────────────────────────
   HARMONIC AI FINANCE — eval.js
   Harnais d'évaluation : precision/recall/F1 par domaine,
   calibration seuils, matrice de confusion, rapport.
   ───────────────────────────────────────────────────────────── */
(function () {
  "use strict";

  var Engine = window.HarmonicEngine;
  var KNOWLEDGE = window.HAF_KNOWLEDGE;

  /* Dataset d'évaluation étendu (questions → fait attendu + domaine) */
  var EVAL_DATASET = [
    // Compliance - MiFID Reporting
    { q: "Quelles sont les exigences de reporting MiFID II pour les produits dérivés sur actions européennes ? Citez les articles spécifiques.", expect: "mifid_art26", domain: "compliance" },
    { q: "Reporting transactions MiFIR article 26 champs requis", expect: "mifid_art26", domain: "compliance" },
    { q: "Quels sont les 65 champs du reporting transactionnel ?", expect: "mifid_art26", domain: "compliance" },
    { q: "Délai reporting T+1 MiFID dérivés", expect: "mifid_art26", domain: "compliance" },

    // Compliance - Transparence pré-trade
    { q: "Article 20 MiFID transparence pré-trade quotes liquides", expect: "mifid_art20", domain: "compliance" },
    { q: "Seuils liquidité small caps MiFID II", expect: "mifid_art20", domain: "compliance" },
    { q: "Exigences transparence pre-trade instruments liquides", expect: "mifid_art20", domain: "compliance" },

    // Compliance - RTS
    { q: "RTS 22 normes techniques reporting formats validation", expect: "rts22", domain: "compliance" },
    { q: "Format ISO 20022 reporting transactions MiFIR", expect: "rts22", domain: "compliance" },
    { q: "RTS 27 RTS 28 meilleure execution reporting", expect: "rts27_28", domain: "compliance" },
    { q: "Top 5 venues execution quality reporting", expect: "rts27_28", domain: "compliance" },

    // Risk - VaR
    { q: "Calculez la Value at Risk 95% pour un portefeuille 10M volatilité 18%", expect: "var95", domain: "risk" },
    { q: "VaR 95% formule paramétrique RiskMetrics z-score", expect: "var95", domain: "risk" },
    { q: "Value at Risk 1 jour 95% calcul exemple", expect: "var95", domain: "risk" },
    { q: "Limites VaR normalité tail risk", expect: "var95", domain: "risk" },

    // Risk - Expected Shortfall
    { q: "Expected Shortfall Bâle III.5 mesure cohérente tail risk", expect: "es_basel", domain: "risk" },
    { q: "ES 97.5% quantile FRTB difference VaR", expect: "es_basel", domain: "risk" },
    { q: "Expected shortfall coherent risk measure subadditive", expect: "es_basel", domain: "risk" },

    // Risk - Bâle Crédit / Liquidité
    { q: "RWA risque credit approche standardisee Bâle III", expect: "basel_credit_rwa", domain: "risk" },
    { q: "Risk weighted assets credit risk standardised approach", expect: "basel_credit_rwa", domain: "risk" },
    { q: "LCR NSFR ratios liquidité Bâle III HQLA", expect: "liquidity_lcr_nsfr", domain: "risk" },
    { q: "Liquidity Coverage Ratio 30 jours stress HQLA niveau 1", expect: "liquidity_lcr_nsfr", domain: "risk" },

    // Négatifs (doivent être refusés)
    { q: "Quelle est la meilleure recette de tarte aux pommes ?", expect: null, domain: "general" },
    { q: "Comment faire du pain maison ?", expect: null, domain: "general" },
    { q: "Météo à Paris demain", expect: null, domain: "general" },
    { q: "Cours de l'action Apple en temps réel", expect: null, domain: "general" },
    { q: "Bitcoin price prediction 2025", expect: null, domain: "general" },
    { q: "Comment investir en bourse pour debutant", expect: null, domain: "general" },
  ];

  function computeMetrics(results) {
    var byDomain = {};
    var all = { tp: 0, fp: 0, fn: 0, tn: 0 };

    results.forEach(function (r) {
      var dom = r.domain;
      if (!byDomain[dom]) byDomain[dom] = { tp: 0, fp: 0, fn: 0, tn: 0 };

      if (r.expected && r.predicted === r.expected) {
        byDomain[dom].tp++; all.tp++;
      } else if (r.expected && r.predicted !== r.expected) {
        byDomain[dom].fn++; all.fn++;
      } else if (!r.expected && r.predicted) {
        byDomain[dom].fp++; all.fp++;
      } else {
        byDomain[dom].tn++; all.tn++;
      }
    });

    function prf(tp, fp, fn) {
      var p = tp / (tp + fp) || 0;
      var rec = tp / (tp + fn) || 0;
      var f1 = (2 * p * rec) / (p + rec) || 0;
      return { precision: p, recall: rec, f1: f1 };
    }

    var report = { byDomain: {}, overall: prf(all.tp, all.fp, all.fn) };
    Object.keys(byDomain).forEach(function (d) {
      report.byDomain[d] = prf(byDomain[d].tp, byDomain[d].fp, byDomain[d].fn);
      report.byDomain[d].support = byDomain[d].tp + byDomain[d].fn;
    });
    report.overall.support = all.tp + all.fn;
    return report;
  }

  function runEvaluation() {
    var results = [];
    EVAL_DATASET.forEach(function (item) {
      var res = Engine.solve(item.q);
      var predicted = res.matches.length > 0 ? res.matches[0].fact.id : null;
      results.push({
        q: item.q,
        expected: item.expect,
        predicted: predicted,
        score: res.score,
        threshold: res.threshold,
        domain: item.domain,
        status: res.status
      });
    });
    return computeMetrics(results);
  }

  function printReport(metrics) {
    console.log("\n═══════════════════════════════════════════");
    console.log("  HARMONIC AI FINANCE — ÉVALUATION");
    console.log("═══════════════════════════════════════════\n");

    console.log("PAR DOMAINE :");
    Object.keys(metrics.byDomain).forEach(function (d) {
      var m = metrics.byDomain[d];
      console.log("  " + d.toUpperCase() + " (n=" + m.support + ")");
      console.log("    Precision : " + (m.precision * 100).toFixed(1) + "%");
      console.log("    Recall    : " + (m.recall * 100).toFixed(1) + "%");
      console.log("    F1        : " + (m.f1 * 100).toFixed(1) + "%");
    });

    console.log("\nGLOBAL :");
    console.log("  Precision : " + (metrics.overall.precision * 100).toFixed(1) + "%");
    console.log("  Recall    : " + (metrics.overall.recall * 100).toFixed(1) + "%");
    console.log("  F1        : " + (metrics.overall.f1 * 100).toFixed(1) + "%");
    console.log("  Support   : " + metrics.overall.support);

    console.log("\nDÉTAIL PAR QUESTION :");
    EVAL_DATASET.forEach(function (item, i) {
      var r = results[i];
      var ok = (r.expected === r.predicted) ? "✓" : "✗";
      console.log("  " + ok + " [" + r.domain + "] score=" + r.score.toFixed(3) + " thr=" + r.threshold.toFixed(2) + " → " + (r.predicted || "REFUSED"));
      console.log("      Q: " + item.q.slice(0, 70) + "…");
      if (r.expected !== r.predicted) {
        console.log("      EXPECTED: " + (r.expected || "REFUSED") + " | GOT: " + (r.predicted || "REFUSED"));
      }
    });
    console.log("");
  }

  // Exposer pour console navigateur
  window.HAF_Eval = {
    run: function () {
      var metrics = runEvaluation();
      printReport(metrics);
      return metrics;
    },
    dataset: EVAL_DATASET,
    computeMetrics: computeMetrics
  };

  // Auto-run si ouvert directement dans console
  if (typeof window !== "undefined" && window.console) {
    // window.HAF_Eval.run(); // décommenter pour auto-run
  }
})();

// Variable `results` capturée pour printReport
var results = [];