#!/usr/bin/env node
/* ══════════════════════════════════════════════════════════════════════════
   KA CARE ANDROID — Synchronisation des assets web → www/
   ══════════════════════════════════════════════════════════════════════════
   Copie les fichiers de l'app web (engine/ka_care/) vers www/ pour Capacitor.
   ══════════════════════════════════════════════════════════════════════════ */
import { copyFileSync, mkdirSync, readdirSync, readFileSync, writeFileSync, existsSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');   // ka-care-android/
const SRC  = join(ROOT, '..', 'ka_care');                            // engine/ka_care/
const WWW  = join(ROOT, 'www');

// ── Fichiers à embarquer ──
const HTML  = ['index.html', 'website.html', 'dossier_presentation.html'];
const JS    = ['ble_manager.js', 'sw.js'];
const ASSETS = ['manifest.json'];
const ICONS = ['icon.svg'];

let copied = 0, missing = 0, bytes = 0;

function ensureDir(p) { mkdirSync(p, { recursive: true }); }

function copy(srcRel, destRel) {
  const s = join(SRC, srcRel), d = join(WWW, destRel ?? srcRel);
  if (!existsSync(s)) { console.warn('  ⚠ ABSENT :', srcRel); missing++; return; }
  ensureDir(dirname(d));
  copyFileSync(s, d);
  copied++; bytes += statSync(s).size;
}

function copyDir(dirRel) {
  const dirSrc = join(SRC, dirRel);
  if (!existsSync(dirSrc)) { console.warn('  ⚠ DOSSIER ABSENT :', dirRel); missing++; return; }
  const files = readdirSync(dirSrc);
  for (const f of files) {
    const s = join(dirSrc, f);
    if (statSync(s).isFile()) {
      copy(join(dirRel, f));
    }
  }
}

// ── HTML : supprimer les liens Google Fonts CDN (offline) ──
function patchHtml(name) {
  const s = join(SRC, name), d = join(WWW, name);
  if (!existsSync(s)) { console.warn('  ⚠ ABSENT :', name); missing++; return; }
  let html = readFileSync(s, 'utf8');
  html = html.replace(/<link[^>]*fonts\.googleapis\.com[^>]*>/g, '');
  html = html.replace(/<link[^>]*fonts\.gstatic\.com[^>]*>/g, '');
  ensureDir(dirname(d));
  writeFileSync(d, html, 'utf8');
  copied++; bytes += Buffer.byteLength(html);
}

console.log('═══ KA CARE — sync assets → www/ ═══');
ensureDir(WWW);

HTML.forEach(patchHtml);
JS.forEach(f => copy(f));
ASSETS.forEach(f => copy(f));
ICONS.forEach(f => copy(join('icons', f)));

// Capacitor lit index.html directement — pas besoin de redirect supplémentaire
console.log(`═══ ${copied} fichiers copiés (${(bytes / 1024).toFixed(0)} Ko) — ${missing} manquant(s) ═══`);
process.exit(missing ? 1 : 0);