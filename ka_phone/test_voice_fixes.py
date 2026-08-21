#!/usr/bin/env python3
"""
Tests headless du module vocal KA PHONE — valide les correctifs sans réseau
ni modèles lourds (XTTS/Whisper/Piper désactivés ou mockés).
"""
import os, sys, io, wave, json, types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

RESULTS = []

def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print(f"  {'✅' if cond else '❌'} {name}" + (f" — {detail}" if detail else ""))

print("=" * 64)
print("TEST MODULE VOCAL KA PHONE — correctifs")
print("=" * 64)

# ─────────────────────────────────────────────────────────────
# 1. Orchestrateur : init paresseuse (pas de chargement XTTS 1,8 Go)
# ─────────────────────────────────────────────────────────────
print("\n[1] Orchestrateur — init paresseuse")
import harmonic_speech_orchestrator as hso_mod
HarmonicSpeechOrchestrator = hso_mod.HarmonicSpeechOrchestrator

import time
t0 = time.time()
orch = HarmonicSpeechOrchestrator(voice_profile="kemet_sage", enrich_text=False)
init_ms = (time.time() - t0) * 1000
check("init < 2000 ms (XTTS non chargé au démarrage)", init_ms < 2000, f"{init_ms:.0f} ms")
check("modèle XTTS non importé en mémoire", "TTS.api" not in sys.modules)
check("moteur détecté", orch.tts_engine["type"] in ("speech_service", "none"),
      f"type={orch.tts_engine['type']} available={orch.tts_engine['available']} xtts_lazy={orch.tts_engine.get('xtts_lazy')}")

# ─────────────────────────────────────────────────────────────
# 2. Profils de voix : chaque profil a une voix réelle distincte
# ─────────────────────────────────────────────────────────────
print("\n[2] Profils vocaux → voix Edge réelles")
vp = hso_mod.VOICE_PROFILES
voices = {k: v.get("edge_voice") for k, v in vp.items()}
check("5 profils ont une edge_voice", all(voices.values()), json.dumps(voices))
check("au moins 4 voix distinctes", len(set(voices.values())) >= 4,
      f"{len(set(voices.values()))} distinctes")

# ─────────────────────────────────────────────────────────────
# 3. Mode déterministe (médical) : aucun enrichissement aléatoire
# ─────────────────────────────────────────────────────────────
print("\n[3] Enrichissement prosodique déterministe")
prosody = {"template_name": "factuel", **hso_mod.PROSODIC_TEMPLATES["factuel"]}
txt = "Le paludisme est une urgence."
ok = all(orch._enrich_text(txt, prosody) == txt for _ in range(50))
check("enrich_text=False → texte inchangé (50 essais)", ok)
orch_riche = HarmonicSpeechOrchestrator(enrich_text=True)
variants = {orch_riche._enrich_text(txt, prosody) for _ in range(80)}
check("enrich_text=True → variation possible", len(variants) > 1, f"{len(variants)} variantes")

# ─────────────────────────────────────────────────────────────
# 4. Détection prosodique
# ─────────────────────────────────────────────────────────────
print("\n[4] Détection prosodique")
p1 = orch._detect_prosody("Raconte-moi une histoire de Kemet", {})
p2 = orch._detect_prosody("Quelle est la capitale du Sénégal ?", {})
p3 = orch._detect_prosody("Calcule la dérivée de x au carré", {})
check("conte détecté", p1["template_name"] == "conte", p1["template_name"])
check("factuel détecté", p2["template_name"] == "factuel", p2["template_name"])
check("mathematique détecté", p3["template_name"] == "mathematique", p3["template_name"])

# ─────────────────────────────────────────────────────────────
# 5. TTSStreamingService : instance unique dans l'orchestrateur
# ─────────────────────────────────────────────────────────────
print("\n[5] Streaming TTS — singleton orchestrateur")
import tts_streaming as ts_mod
a = orch._get_streaming_tts()
b = orch._get_streaming_tts()
check("même instance réutilisée", a is b)
check("cache disque paresseux (RAM vide au départ)", len(a.cache.cache) == 0,
      f"{len(a.cache.cache)} entrées RAM")

# ─────────────────────────────────────────────────────────────
# 6. Cache TTS : format MP3/WAV respecté
# ─────────────────────────────────────────────────────────────
print("\n[6] Cache TTS — format réel (mp3/wav)")
cache = ts_mod.TTSCache(max_size=5)
fake_mp3 = b"\xff\xfb" + b"\x00" * 500   # en-tête MP3 factice
fake_wav_hdr = b"RIFF" + b"\x00" * 500
cache.put("bonjour mp3", fake_mp3, voice="denise", fmt="mp3")
cache.put("bonjour wav", fake_wav_hdr, voice="denise", fmt="wav")
r1 = cache.get_ex("bonjour mp3", voice="denise")
r2 = cache.get_ex("bonjour wav", voice="denise")
check("get_ex mp3 → (bytes, 'mp3')", r1 and r1[1] == "mp3" and r1[0] == fake_mp3)
check("get_ex wav → (bytes, 'wav')", r2 and r2[1] == "wav")
check("get() rétro-compatible (bytes seuls)", cache.get("bonjour mp3", voice="denise") == fake_mp3)
# Vérifier l'extension disque
files = os.listdir(cache.cache_dir)
check("fichier .mp3 sur disque", any(f.endswith(".mp3") for f in files))
# LRU : borné à max_size
for i in range(10):
    cache.put(f"phrase {i}", b"x" * 100, voice="v")
check("LRU borné à max_size=5", len(cache.cache) <= 5, f"{len(cache.cache)} entrées")

# ─────────────────────────────────────────────────────────────
# 7. Mapping voix : noms complets Edge passent tels quels
# ─────────────────────────────────────────────────────────────
print("\n[7] Mapping voix Edge")
svc_stream = ts_mod.TTSStreamingService()
check("'henri' → fr-FR-HenriNeural", svc_stream._map_voice_to_edge("henri") == "fr-FR-HenriNeural")
check("'fr-FR-JeromeNeural' passé tel quel",
      svc_stream._map_voice_to_edge("fr-FR-JeromeNeural") == "fr-FR-JeromeNeural")
check("inconnu → Denise par défaut", svc_stream._map_voice_to_edge("xyz") == "fr-FR-DeniseNeural")

# ─────────────────────────────────────────────────────────────
# 8. Découpage en phrases (français)
# ─────────────────────────────────────────────────────────────
print("\n[8] Découpage en phrases")
s = svc_stream._split_sentences(
    "Le patient a de la fièvre. La température est de 39,5 degrés ! "
    "Que faire ? Il faut consulter rapidement.")
check("4 phrases détectées", len(s) == 4, f"{len(s)} phrases: {s}")

# ─────────────────────────────────────────────────────────────
# 9. speak() dégradé : fallback sinusoïdal WAV valide
# ─────────────────────────────────────────────────────────────
print("\n[9] speak() en mode dégradé (sans TTS réseau/local)")
# Forcer l'échec du streaming TTS pour tester le chemin de secours
orch.tts_engine = {"type": "none", "available": False, "xtts_lazy": False}
orch._streaming_tts.speak_cached_ex = lambda *a, **k: None  # simule panne Edge+Piper
out_path = os.path.join(HERE, "..", "data", "speech", "test_fallback.wav")
res = orch.speak("Test de synthèse de secours.", output_path=out_path)
wav_ok = False
try:
    with wave.open(out_path, 'r') as wf:
        wav_ok = wf.getnframes() > 1000 and wf.getframerate() == 22050
except Exception as e:
    print("    wave error:", e)
check("WAV sinusoïdal valide généré", wav_ok and os.path.getsize(out_path) > 2000,
      f"{os.path.getsize(out_path)} octets, durée={res['duration_s']}s")
check("métadonnées speak() complètes",
      all(k in res for k in ("audio_path", "duration_s", "voice", "prosody_template", "speed")))
check("profil kemet_sage utilisé", res["voice"] == "Le Sage de Kemet", res["voice"])

# ─────────────────────────────────────────────────────────────
# 10. Durée audio : WAV exact + estimation MP3
# ─────────────────────────────────────────────────────────────
print("\n[10] Durée audio (WAV / MP3)")
d_wav = orch._get_audio_duration(out_path)
check("durée WAV > 0.5 s", d_wav > 0.5, f"{d_wav}s")
mp3_path = os.path.join(HERE, "..", "data", "speech", "test_fake.mp3")
with open(mp3_path, "wb") as f:
    f.write(b"\xff\xfb" + b"\x11" * 48000)  # ~8 s à 48 kbit/s
d_mp3 = orch._get_audio_duration(mp3_path)
check("durée MP3 estimée par bitrate (~8 s)", 6.0 < d_mp3 < 10.0, f"{d_mp3}s")
os.remove(mp3_path)

# ─────────────────────────────────────────────────────────────
# 11. SpeechService : pas de chargement whisper dans is_stt_available
# ─────────────────────────────────────────────────────────────
print("\n[11] SpeechService — sondes non bloquantes")
from speech_service import SpeechService
svc = SpeechService()
_ = svc.is_stt_available()
check("whisper non chargé par is_stt_available()", svc.whisper_loaded is False)
check("synthesize() refuse proprement sans Piper",
      svc.synthesize("test", os.path.join(HERE, "..", "data", "speech", "should_not_exist.wav")) is False
      if not svc.piper_available else True)

# ─────────────────────────────────────────────────────────────
# 12. Voice engine unifié : Piper via SpeechService + enhance_audio
# ─────────────────────────────────────────────────────────────
print("\n[12] HarmonicVoiceEngine")
import harmonic_voice_engine as hve
ve = hve.HarmonicVoiceEngine()
check("plus d'import phi_piper_engine", "phi_piper_engine" not in sys.modules)
check("engines stats accessibles", isinstance(ve.stats["engines"], dict),
      json.dumps(ve.stats["engines"]))
# enhance_audio sur le WAV généré plus haut
with open(out_path, "rb") as f:
    wav_bytes = f.read()
enhanced = ve.enhance_audio(wav_bytes, boost_phi=True)
enh_ok = False
try:
    with wave.open(io.BytesIO(enhanced), 'rb') as wf:
        enh_ok = wf.getnframes() > 1000
except Exception:
    pass
check("enhance_audio → WAV valide (post-processeur φ)", enh_ok, f"{len(enhanced)} octets")

# ─────────────────────────────────────────────────────────────
# 13. Barge-in streaming
# ─────────────────────────────────────────────────────────────
print("\n[13] Barge-in")
svc_stream.start_playback()
svc_stream.request_barge_in()
check("barge-in détecté", svc_stream.check_barge_in() is True)
check("is_playing remis à False", svc_stream.is_playing is False)

# ─────────────────────────────────────────────────────────────
# BILAN
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 64)
ok_count = sum(1 for _, c, _ in RESULTS if c)
print(f"BILAN : {ok_count}/{len(RESULTS)} tests réussis")
if ok_count == len(RESULTS):
    print("✅ MODULE VOCAL CORRIGÉ ET FONCTIONNEL")
else:
    print("❌ Des tests ont échoué :")
    for name, c, d in RESULTS:
        if not c:
            print(f"   - {name} {d}")
sys.exit(0 if ok_count == len(RESULTS) else 1)
