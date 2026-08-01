#!/usr/bin/env node
/* ══════════════════════════════════════════════════════════════════════════
   VITAL KA ANDROID — Synchronisation des assets web → www/
   ══════════════════════════════════════════════════════════════════════════
   Copie les fichiers de l'app web (racine engine/) vers www/ pour Capacitor.
   - Remplace les liens Google Fonts CDN par les fonts locales (offline)
   - Génère index.html (point d'entrée Capacitor) → redirige vers vital_ka.html

   Usage : node scripts/sync-assets.mjs
   ══════════════════════════════════════════════════════════════════════════ */
import { copyFileSync, mkdirSync, readdirSync, readFileSync, writeFileSync, existsSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');   // vital-ka-android/
const SRC  = join(ROOT, '..');                                       // engine/
const WWW  = join(ROOT, 'www');

// ── Fichiers à embarquer (source de vérité = sw.js / exploration) ──
const HTML = ['vital_ka.html', 'ka_patient.html', 'ka_medecins.html', 'ka_pharmacien.html', 'ka_solidarite.html', 'ka_launcher.html', 'ka_laboratoire.html', 'ka_admin.html'];

const JS = [
  'vital_ka_config.js', 'vital_ka_native.js',
  'ka_core.js', 'ka_secure.js', 'ka_bridge.js', 'ka_hcv.js', 'ka_network.js',
  'vital_ka_hologram.js', 'vital_ka_knowledge.js',
  'vital_ka_voice.js', 'vital_ka_stt.js', 'vital_ka_dialogue.js',
  'vital_ka_conversation.js', 'vital_ka_ble.js', 'ka_telemedecine.js',
  'vital_ka_ai.js', 'vital_ka_app.js', 'ka_care_voice.js', 'seed_doctors_demo.js',
  'ka_wallet.js', 'ka_platform.js', 'ka_hologram_router.js',
];

const CSS = ['vital_ka.css', 'vital_ka_ai.css', 'ka_telemedecine.css'];

const ASSETS = ['logo2.jpg', 'manifest.json'];

const DATA = [
  'vital_ka_diseases.json', 'vital_ka_malaria.json', 'vital_ka_tropical.json',
  'vital_ka_ntd.json', 'vital_ka_vih_tb.json', 'vital_ka_pediatrie.json',
  'vital_ka_urgences.json', 'vital_ka_sante_mentale.json', 'vital_ka_chroniques.json',
  'vital_ka_mere_enfant.json', 'vital_ka_malnutrition.json',
  'vital_ka_pharmacie.json', 'vital_ka_vaccination.json', 'vital_ka_phytotherapie.json',
];

let copied = 0, missing = 0, bytes = 0;

function ensureDir(p) { mkdirSync(p, { recursive: true }); }

function copy(srcRel, destRel) {
  const s = join(SRC, srcRel), d = join(WWW, destRel ?? srcRel);
  if (!existsSync(s)) { console.warn('  ⚠ ABSENT :', srcRel); missing++; return; }
  ensureDir(dirname(d));
  copyFileSync(s, d);
  copied++; bytes += statSync(s).size;
}

// ── HTML : remplacer les liens Google Fonts par la font locale ──
function patchHtml(name) {
  const s = join(SRC, name), d = join(WWW, name);
  if (!existsSync(s)) { console.warn('  ⚠ ABSENT :', name); missing++; return; }
  let html = readFileSync(s, 'utf8');
  let firstDone = false;
  html = html.replace(/<link[^>]*fonts\.googleapis\.com[^>]*>/g, (m) => {
    if (firstDone) return '';                       // 2e lien (Material Symbols) → supprimé
    firstDone = true;
    return '<link href="fonts/fonts.css" rel="stylesheet"/>';
  });
  // Préconnects gstatic inutiles hors-ligne
  html = html.replace(/<link[^>]*fonts\.gstatic\.com[^>]*>/g, '');
  ensureDir(dirname(d));
  writeFileSync(d, html, 'utf8');
  copied++; bytes += Buffer.byteLength(html);
}

console.log('═══ Vital Ka — sync assets → www/ ═══');
ensureDir(WWW); ensureDir(join(WWW, 'data')); ensureDir(join(WWW, 'fonts'));

HTML.forEach(patchHtml);
JS.forEach(f => copy(f));
CSS.forEach(f => copy(f));
ASSETS.forEach(f => copy(f));
DATA.forEach(f => copy(join('data', f)));
// Bundle hologrammes offline (généré par build_hologram_bundle.py)
copy(join('data', 'hologram_bundle.json'), join('data', 'hologram_bundle.json'));

// Fonts locales (téléchargées une fois dans assets_src/fonts)
const FONT_SRC = join(ROOT, 'assets_src', 'fonts');
if (existsSync(FONT_SRC)) {
  for (const f of readdirSync(FONT_SRC)) {
    const s = join(FONT_SRC, f), d = join(WWW, 'fonts', f);
    copyFileSync(s, d); copied++; bytes += statSync(s).size;
  }
} else {
  console.warn('  ⚠ assets_src/fonts absent — les icônes Material seront en texte brut offline');
}

// index.html — point d'entrée Capacitor → vital_ka.html
writeFileSync(join(WWW, 'index.html'),
  '<!DOCTYPE html><html><head><meta charset="utf-8"/>' +
  '<meta http-equiv="refresh" content="0; url=/vital_ka.html"/>' +
  '<title>Vital Ka</title></head><body style="background:#0d0d0d"></body></html>\n', 'utf8');
copied++;

console.log(`═══ ${copied} fichiers copiés (${(bytes / 1024).toFixed(0)} Ko) — ${missing} manquant(s) ═══`);
process.exit(missing ? 1 : 0);
