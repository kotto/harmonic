#!/usr/bin/env node
/* ══════════════════════════════════════════════════════════════════════════
   KA MOBILE ANDROID — Build APK complet (source → APK)
   ══════════════════════════════════════════════════════════════════════════
   Enchaîne les 3 étapes du pipeline officiel :
     1. scripts/sync-assets.mjs   — patch la source engine/ka_index.html → www/
     2. npx cap sync android      — www/ → android/app/src/main/assets/public/
     3. gradlew assembleDebug     — APK final (ou assembleRelease)

   Usage : node scripts/build-apk.mjs [--release] [--install] [--device SERIAL]
     --release     : assembleRelease (nécessite keystore configuré)
     --install     : installe l'APK sur le device/émulateur connecté (adb)
     --device X    : serial adb cible pour --install
   ══════════════════════════════════════════════════════════════════════════ */
import { existsSync, readFileSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');   // ka-mobile-android/
const ANDROID = join(ROOT, 'android');

// ── Arguments ───────────────────────────────────────────────────────────────
const ARGS = process.argv.slice(2);
const RELEASE = ARGS.includes('--release');
const INSTALL = ARGS.includes('--install');
const DEVICE = ARGS.includes('--device') ? ARGS[ARGS.indexOf('--device') + 1] : null;
const VARIANT = RELEASE ? 'release' : 'debug';

function fail(msg) { console.error('❌ ' + msg); process.exit(1); }
function step(msg) { console.log('\n━━━ ' + msg + ' ━━━'); }

// ── Résoudre le SDK Android (local.properties > ANDROID_HOME) ──────────────
function resolveSdk() {
  const lp = join(ANDROID, 'local.properties');
  if (existsSync(lp)) {
    const m = readFileSync(lp, 'utf8').match(/^sdk\.dir=(.+)$/m);
    if (m) {
      try { return JSON.parse('"' + m[1].replace(/\\/g, '\\\\') + '"'); } catch (e) { return m[1]; }
    }
  }
  return process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT || null;
}

// ── Vérifier un prérequis binaire ──────────────────────────────────────────
function have(cmd) {
  const r = spawnSync(cmd, ['--version'], { stdio: 'ignore', shell: true });
  return r.status === 0;
}

// ════════════════════ 0. Prérequis ════════════════════
console.log('═══ KA Mobile — build APK (' + VARIANT + ') ═══');
const sdk = resolveSdk();
if (!sdk) fail('SDK Android introuvable (local.properties / ANDROID_HOME)');
if (!existsSync(sdk)) fail('sdk.dir introuvable : ' + sdk);
if (!have('node')) fail('Node.js requis');
if (!existsSync(join(ANDROID, 'gradlew.bat')) && !existsSync(join(ANDROID, 'gradlew'))) {
  fail('Wrapper Gradle absent dans android/');
}
console.log('  ✓ SDK : ' + sdk);

// ════════════════════ 1. sync-assets (source → www/) ════════════════════
step('1/3 — sync-assets (engine/ka_index.html → www/, patchs idempotents)');
let r = spawnSync('node', [join(ROOT, 'scripts', 'sync-assets.mjs')], { stdio: 'inherit' });
if (r.status !== 0) fail('sync-assets.mjs a échoué (code ' + r.status + ')');

// ════════════════════ 2. cap sync android (www/ → assets/public/) ════════════════════
step('2/3 — cap sync android (www/ → assets APK)');
if (!existsSync(join(ROOT, 'node_modules', '@capacitor', 'cli'))) {
  fail('Capacitor CLI absent — lancer "npm install" dans ka-mobile-android/');
}
r = spawnSync('npx cap sync android', { cwd: ROOT, stdio: 'inherit', shell: true });
if (r.status !== 0) fail('cap sync android a échoué (code ' + r.status + ')');

// Garde-fou : l'asset embarqué doit être la version récente (> 170 Ko, signé)
const embedded = join(ANDROID, 'app', 'src', 'main', 'assets', 'public', 'ka_index.html');
if (!existsSync(embedded)) fail('ka_index.html absent des assets APK');
const embSize = statSync(embedded).size;
if (embSize < 170000) fail('ka_index.html embarqué suspect (' + embSize + ' octets — version obsolète ?)');
console.log('  ✓ assets/public/ka_index.html : ' + embSize + ' octets');

// ════════════════════ 3. gradlew (APK final) ════════════════════
step('3/3 — gradlew assemble' + VARIANT[0].toUpperCase() + VARIANT.slice(1));
const gradleCmd = process.platform === 'win32' ? 'gradlew.bat' : './gradlew';
r = spawnSync(gradleCmd + ' assemble' + VARIANT[0].toUpperCase() + VARIANT.slice(1) + ' --console=plain -q',
  { cwd: ANDROID, stdio: 'inherit', shell: true });
if (r.status !== 0) fail('Gradle a échoué (code ' + r.status + ')');

// ── Vérification finale ────────────────────────────────────────────────────
const apk = join(ANDROID, 'app', 'build', 'outputs', 'apk', VARIANT, 'app-' + VARIANT + '.apk');
if (!existsSync(apk)) fail('APK introuvable : ' + apk);
const apkSize = statSync(apk).size;
console.log('\n═══ ✅ APK construit : ' + apk + ' (' + (apkSize / 1048576).toFixed(1) + ' Mo) ═══');

// ── Option --install ───────────────────────────────────────────────────────
if (INSTALL) {
  const adb = join(sdk, 'platform-tools', 'adb.exe');
  if (!existsSync(adb)) fail('adb introuvable : ' + adb);
  const devArg = DEVICE ? ' -s ' + DEVICE : '';
  console.log('\n━━━ Installation sur le device/émulateur ━━━');
  r = spawnSync('"' + adb + '"' + devArg + ' install -r "' + apk + '"', { stdio: 'inherit', shell: true });
  if (r.status !== 0) fail('adb install a échoué (code ' + r.status + ')');
  console.log('✅ APK installé' + (DEVICE ? ' sur ' + DEVICE : ''));
}

console.log('\nRappel du flux : éditer engine/ka_index.html → node scripts/build-apk.mjs');
process.exit(0);
