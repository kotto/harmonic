/* ══════════════════════════════════════════════════════════════════════════
   TEST HEADLESS — vital_ka_voice.js (node, sans navigateur)
   Stub window / speechSynthesis / document, puis évalue le module et vérifie :
   profils, buildDiagnosisSpeech (déterministe), speak/stop, voix FR,
   fallback sans diagnostic, chemin non supporté, glue UI.
   ══════════════════════════════════════════════════════════════════════════ */
'use strict';

const fs = require('fs');
const path = require('path');

let passed = 0, failed = 0;
function ok(cond, label) {
  if (cond) { passed++; console.log('  ✅ ' + label); }
  else { failed++; console.log('  ❌ ' + label); }
}
function section(t) { console.log('\n══ ' + t + ' ══'); }

// ── Stubs navigateur ──
const spoken = [];
let cancelCount = 0;
let voicesList = [];

class FakeUtterance {
  constructor(text) { this.text = text; this.lang = ''; this.rate = 1; this.pitch = 1; this.volume = 1; this.voice = null; this.onend = null; this.onerror = null; }
}

const synthStub = {
  getVoices: () => voicesList,
  speak: (u) => { spoken.push(u); },
  cancel: () => { cancelCount++; },
  onvoiceschanged: null,
};

const removedClasses = [];
const fakeBtn = { classList: { remove: (c) => removedClasses.push(c), add: () => {} } };

globalThis.window = { speechSynthesis: synthStub };
globalThis.speechSynthesis = synthStub;
globalThis.SpeechSynthesisUtterance = FakeUtterance;
globalThis.document = { querySelectorAll: () => [fakeBtn], addEventListener: () => {}, body: { appendChild: () => {} } };

// ── Chargement du module (astuce eval indirect pour capter le const top-level) ──
const code = fs.readFileSync(path.join(__dirname, 'vital_ka_voice.js'), 'utf8');
(0, eval)(code + ';globalThis.KA_VOICE = KA_VOICE;globalThis.aiSpeakLast = aiSpeakLast;'
  + 'globalThis.speakDiagnosisResult = speakDiagnosisResult;globalThis.voiceStop = voiceStop;');

const V = globalThis.KA_VOICE;

(async () => {

/* ═══ 1. Profils vocaux ═══ */
section('Profils vocaux');
ok(V.PROFILES.conseiller.rate === 1.0 && V.PROFILES.conseiller.pitch === 1.0,
  'conseiller : rate 1.0 / pitch 1.0 (factuel)');
ok(V.PROFILES.compagnon.rate === 0.88 && V.PROFILES.compagnon.pitch === 1.05,
  'compagnon : rate 0.88 / pitch 1.05 (ralenti, chaleureux)');
ok(typeof V.PROFILES.conseiller.label === 'string' && typeof V.PROFILES.compagnon.label === 'string',
  'labels présents');

/* ═══ 2. buildDiagnosisSpeech — strictement déterministe ═══ */
section('buildDiagnosisSpeech');
const diag = {
  top: { name: 'Paludisme', score: 0.87, g: 'ELEVEE', u: true, c: 'TDR + ACT', d: '24h' },
  scores: {}, symptoms: [], date: '2026-07-30', patientId: 'p1',
};
const s1 = V.buildDiagnosisSpeech(diag);
ok(s1.includes('Diagnostic probable : Paludisme'), 'nom de la pathologie lu tel quel');
ok(s1.includes('confiance 87 pour cent'), 'score 0.87 → "confiance 87 pour cent"');
ok(s1.includes('Gravité : ELEVEE.'), 'gravité lue');
ok(s1.includes('situation urgente'), 'alerte urgence prononcée (u=true)');
ok(s1.includes('Conduite à tenir : TDR + ACT'), 'conduite à tenir lue sans reformulation');
ok(s1.includes('Délai de consultation : 24h.'), 'délai de consultation lu');
ok(s1.includes('aide au diagnostic'), 'rappel "aide au diagnostic" systématique');
ok(V.buildDiagnosisSpeech(diag) === s1, 'sortie strictement identique au 2e appel (déterminisme)');
ok(V.buildDiagnosisSpeech({ top: { name: 'X', score: 87 } }).includes('confiance 87 pour cent'),
  'score déjà en pourcentage (87) non doublé');
ok(V.buildDiagnosisSpeech(null) === '' && V.buildDiagnosisSpeech({}) === '',
  'diag null/sans top → chaîne vide');

/* ═══ 3. Sélection de voix française ═══ */
section('Sélection de voix FR');
voicesList = [
  { lang: 'en-US', name: 'Microsoft David' },
  { lang: 'fr-FR', name: 'Microsoft Hortense' },
  { lang: 'fr-FR', name: 'Google français' },
];
if (typeof synthStub.onvoiceschanged === 'function') synthStub.onvoiceschanged();
V.speakSync('test voix', 'conseiller');
ok(spoken[spoken.length - 1].voice && spoken[spoken.length - 1].voice.name === 'Microsoft Hortense',
  'Tier 1 : voix Edge Natural (Hortense) prioritaire sur Google');
voicesList = [{ lang: 'fr-FR', name: 'Microsoft Zira' }, { lang: 'fr-FR', name: 'AurelieNeural' }];
synthStub.onvoiceschanged();
V.speakSync('test voix 3', 'conseiller');
ok(spoken[spoken.length - 1].voice.name === 'AurelieNeural',
  'Tier 2 : voix Neural/Online (AurelieNeural) sans Edge Natural');
voicesList = [{ lang: 'fr-FR', name: 'Microsoft Hortense' }];
synthStub.onvoiceschanged();
V.speakSync('test voix 2', 'conseiller');
ok(spoken[spoken.length - 1].voice.name === 'Microsoft Hortense',
  'onvoiceschanged invalide le cache → repli sur 1re voix FR');

/* ═══ 4. speak / stop / état ═══ */
section('speak / stop');
spoken.length = 0; cancelCount = 0;
const r1 = V.speakSync('Bonjour le monde', 'compagnon');
ok(r1 === true, 'speak() retourne true quand supporté');
ok(spoken.length === 1, 'une utterance émise');
ok(spoken[0].lang === 'fr-FR', 'langue fr-FR forcée');
ok(spoken[0].rate === 0.88 && spoken[0].pitch === 1.05, 'profil compagnon appliqué');
ok(V.isSpeaking() === true, 'isSpeaking() true pendant la lecture');
V.speakSync('Deuxième phrase', 'conseiller');
ok(cancelCount >= 1, 'speak() annule la lecture précédente (cancel)');
ok(spoken[1].rate === 1.0, 'profil conseiller appliqué');
spoken[1].onend();
ok(V.isSpeaking() === false, 'onend → isSpeaking() false');
ok(removedClasses.includes('ka-voice-speaking'), 'onend nettoie la classe .ka-voice-speaking');
const before = cancelCount;
V.stop();
ok(cancelCount === before + 1, 'stop() appelle speechSynthesis.cancel()');
ok(V.speakSync('') === false && V.speakSync('   ') === false, 'texte vide → false, rien lu');

/* ═══ 5. speakLastDiagnosis ═══ */
section('speakLastDiagnosis');
spoken.length = 0;
globalThis.getLastDiagnosis = () => diag;
await V.speakLastDiagnosis('conseiller');
ok(spoken.length === 1 && spoken[0].text.includes(s1.substring(0, 80)),
  'lit le texte deterministe du dernier diagnostic');
globalThis.getLastDiagnosis = () => null;
V.speakLastDiagnosis('conseiller');
ok(spoken[spoken.length - 1].text.includes('Aucun diagnostic disponible'),
  'fallback "Aucun diagnostic disponible" sans diagnostic');
delete globalThis.getLastDiagnosis;

/* ═══ 6. setEnabled / chemin non supporté ═══ */
section('Activation / support');
V.setEnabled(false);
ok(V.isEnabled() === false, 'setEnabled(false) → isEnabled() false');
V.setEnabled(true);
ok(V.isEnabled() === true, 'setEnabled(true) → isEnabled() true');
const winBackup = globalThis.window;
delete globalThis.window;
ok(V.isSupported() === false, 'sans window.speechSynthesis → non supporté');
ok(V.speakSync('test') === false, 'speak() → false quand non supporté');
ok(V.isEnabled() === false, 'isEnabled() false quand non supporté');
globalThis.window = winBackup;

/* ═══ 7. Glue UI ═══ */
section('Glue UI');
spoken.length = 0;
let aiMsg = null;
globalThis.aiAddMessage = (t, kind) => { aiMsg = { t, kind }; };
globalThis.getLastDiagnosis = () => diag;
await globalThis.aiSpeakLast();
ok(spoken.length === 1, 'aiSpeakLast() déclenche la lecture');
ok(aiMsg && aiMsg.kind === 'system' && aiMsg.t.includes('🔊'), 'aiSpeakLast() trace un message système');
spoken[0].onend(); // la lecture précédente se termine (sinon toggle stop)
// toggle du bouton résultat : 1er appel lit, 2e arrête
const added = [];
const btn = { classList: { add: (c) => added.push(c), remove: () => {} } };
spoken.length = 0;
globalThis.speakDiagnosisResult(btn);
ok(spoken.length === 1 && added.includes('ka-voice-speaking'),
  'speakDiagnosisResult() lit + marque le bouton');
const cancels = cancelCount;
globalThis.speakDiagnosisResult(btn); // déjà en lecture → stop
ok(cancelCount === cancels + 1, 'speakDiagnosisResult() en lecture → toggle stop');
globalThis.voiceStop();
ok(V.isSpeaking() === false, 'voiceStop() arrête tout');

})().catch(e => { console.error(e); process.exit(1); });

/* ═══ Bilan ═══ */
console.log('\n════════════════════════════════════════');
console.log('BILAN : ' + passed + ' ✅ / ' + failed + ' ❌ (' + (passed + failed) + ' assertions)');
process.exit(failed ? 1 : 0);
