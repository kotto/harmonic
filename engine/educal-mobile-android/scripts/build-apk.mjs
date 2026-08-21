// 🎓 EDU-KA — build-apk (jumeau de ka-mobile-android/scripts/build-apk.mjs)
// Pipeline : sync-assets → cap add android (si absent) → cap sync → gradlew assembleDebug
import { execSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const run = cmd => { console.log('▶', cmd); execSync(cmd, { cwd: ROOT, stdio: 'inherit' }); };

run('node scripts/sync-assets.mjs');
if (!existsSync(join(ROOT, 'android'))) run('npx cap add android');
run('npx cap sync android');
run('cd android && gradlew assembleDebug');
console.log('✅ APK : android/app/build/outputs/apk/debug/app-debug.apk');
