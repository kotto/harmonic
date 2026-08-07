#!/usr/bin/env node
/* ══════════════════════════════════════════════════════════════════════════
   VITAL KA ANDROID — Synchronisation des assets web → www/
   ══════════════════════════════════════════════════════════════════════════
   Copie les fichiers de l'app web (vital-ka/) vers www/ pour Capacitor.
   - Remplace les liens Google Fonts CDN par les fonts locales (offline)
   - Génère index.html (point d'entrée Capacitor) → redirige vers vital_ka.html

   Usage : node scripts/sync-assets.mjs
   ══════════════════════════════════════════════════════════════════════════ */
import { copyFileSync, mkdirSync, readdirSync, readFileSync, writeFileSync, existsSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');   // vital-ka-android/
const VITAL_KA_ROOT = join(ROOT, '..');                             // vital-ka/
const WWW  = join(ROOT, 'www');

// ── Fichiers à embarquer (source de vérité = vital-ka/) ──
const HTML_SOURCES = [
  { src: join('apps', 'web', 'vital_ka.html'), dest: 'vital_ka.html' },
  { src: join('apps', 'patient', 'ka_patient.html'), dest: 'ka_patient.html' },
  { src: join('apps', 'medecins', 'ka_medecins.html'), dest: 'ka_medecins.html' },
  { src: join('apps', 'pharmacien', 'ka_pharmacien.html'), dest: 'ka_pharmacien.html' },
  { src: join('apps', 'solidarite', 'ka_solidarite.html'), dest: 'ka_solidarite.html' },
  { src: join('apps', 'launcher', 'ka_launcher.html'), dest: 'ka_launcher.html' },
  { src: join('apps', 'labo', 'ka_laboratoire.html'), dest: 'ka_laboratoire.html' },
  { src: join('apps', 'diaspora', 'ka_diaspora_shop.html'), dest: 'ka_diaspora_shop.html' },
  { src: join('apps', 'admin', 'ka_admin.html'), dest: 'ka_admin.html' },
  { src: join('apps', 'sphere', 'ka_sphere.html'), dest: 'ka_sphere.html' },
];

const JS_SOURCES = [
  { src: join('core', 'js', 'vital_ka_config.js'), dest: 'vital_ka_config.js' },
  { src: join('core', 'js', 'vital_ka_native.js'), dest: 'vital_ka_native.js' },
  { src: join('core', 'js', 'ka_core.js'), dest: 'ka_core.js' },
  { src: join('core', 'js', 'ka_secure.js'), dest: 'ka_secure.js' },
  { src: join('core', 'js', 'ka_bridge.js'), dest: 'ka_bridge.js' },
  { src: join('core', 'js', 'ka_hcv.js'), dest: 'ka_hcv.js' },
  { src: join('core', 'js', 'ka_network.js'), dest: 'ka_network.js' },
  { src: join('core', 'js', 'vital_ka_hologram.js'), dest: 'vital_ka_hologram.js' },
  { src: join('core', 'js', 'vital_ka_knowledge.js'), dest: 'vital_ka_knowledge.js' },
  { src: join('core', 'js', 'vital_ka_voice.js'), dest: 'vital_ka_voice.js' },
  { src: join('core', 'js', 'vital_ka_stt.js'), dest: 'vital_ka_stt.js' },
  { src: join('core', 'js', 'vital_ka_dialogue.js'), dest: 'vital_ka_dialogue.js' },
  { src: join('core', 'js', 'vital_ka_conversation.js'), dest: 'vital_ka_conversation.js' },
  { src: join('core', 'js', 'vital_ka_ble.js'), dest: 'vital_ka_ble.js' },
  { src: join('core', 'js', 'ka_telemedecine.js'), dest: 'ka_telemedecine.js' },
  { src: join('core', 'js', 'vital_ka_ai.js'), dest: 'vital_ka_ai.js' },
  { src: join('core', 'js', 'vital_ka_app.js'), dest: 'vital_ka_app.js' },
  { src: join('core', 'js', 'ka_care_voice.js'), dest: 'ka_care_voice.js' },
  { src: join('core', 'js', 'seed_doctors_demo.js'), dest: 'seed_doctors_demo.js' },
  { src: join('core', 'js', 'ka_wallet.js'), dest: 'ka_wallet.js' },
  { src: join('core', 'js', 'ka_platform.js'), dest: 'ka_platform.js' },
  { src: join('core', 'js', 'ka_hologram_router.js'), dest: 'ka_hologram_router.js' },
];

const CSS_SOURCES = [
  { src: join('apps', 'web', 'vital_ka.css'), dest: 'vital_ka.css' },
  { src: join('apps', 'web', 'vital_ka_ai.css'), dest: 'vital_ka_ai.css' },
  { src: join('apps', 'web', 'ka_telemedecine.css'), dest: 'ka_telemedecine.css' },
];

const ASSETS_SOURCES = [
  { src: join('apps', 'web', 'logo2.jpg'), dest: 'logo2.jpg' },
  { src: join('apps', 'web', 'manifest.json'), dest: 'manifest.json' },
];

const DATA_SOURCES = [
  { src: join('data', 'vital_ka_diseases.json'), dest: join('data', 'vital_ka_diseases.json') },
  { src: join('data', 'vital_ka_malaria.json'), dest: join('data', 'vital_ka_malaria.json') },
  { src: join('data', 'vital_ka_tropical.json'), dest: join('data', 'vital_ka_tropical.json') },
  { src: join('data', 'vital_ka_ntd.json'), dest: join('data', 'vital_ka_ntd.json') },
  { src: join('data', 'vital_ka_vih_tb.json'), dest: join('data', 'vital_ka_vih_tb.json') },
  { src: join('data', 'vital_ka_pediatrie.json'), dest: join('data', 'vital_ka_pediatrie.json') },
  { src: join('data', 'vital_ka_urgences.json'), dest: join('data', 'vital_ka_urgences.json') },
  { src: join('data', 'vital_ka_sante_mentale.json'), dest: join('data', 'vital_ka_sante_mentale.json') },
  { src: join('data', 'vital_ka_chroniques.json'), dest: join('data', 'vital_ka_chroniques.json') },
  { src: join('data', 'vital_ka_mere_enfant.json'), dest: join('data', 'vital_ka_mere_enfant.json') },
  { src: join('data', 'vital_ka_malnutrition.json'), dest: join('data', 'vital_ka_malnutrition.json') },
  { src: join('data', 'vital_ka_pharmacie.json'), dest: join('data', 'vital_ka_pharmacie.json') },
  { src: join('data', 'vital_ka_vaccination.json'), dest: join('data', 'vital_ka_vaccination.json') },
  { src: join('data', 'vital_ka_phytotherapie.json'), dest: join('data', 'vital_ka_phytotherapie.json') },
];

let copied = 0, missing = 0, bytes = 0;

function ensureDir(p) { mkdirSync(p, { recursive: true }); }

function copy(srcRel, destRel) {
  const s = join(VITAL_KA_ROOT, srcRel), d = join(WWW, destRel);
  if (!existsSync(s)) { console.warn('  ⚠ ABSENT :', srcRel); missing++; return; }
  ensureDir(dirname(d));
  copyFileSync(s, d);
  copied++; bytes += statSync(s).size;
}

// ── HTML : remplacer les liens Google Fonts par la font locale ──
function patchHtml(srcRel, destRel) {
  const s = join(VITAL_KA_ROOT, srcRel), d = join(WWW, destRel);
  if (!existsSync(s)) { console.warn('  ⚠ ABSENT :', srcRel); missing++; return; }
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

HTML_SOURCES.forEach(({src, dest}) => patchHtml(src, dest));
JS_SOURCES.forEach(({src, dest}) => copy(src, dest));
CSS_SOURCES.forEach(({src, dest}) => copy(src, dest));
ASSETS_SOURCES.forEach(({src, dest}) => copy(src, dest));
DATA_SOURCES.forEach(({src, dest}) => copy(src, dest));
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