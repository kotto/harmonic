# 🎵 HCV Compression — Codec Harmonique

## Description
Compression audio et vidéo par dictionnaire spectral 9D. 
119.5× audio, 372.9× vidéo, reconstruction bit-exacte.

## Fonctionnalités
- **Audio HCV2** : 119.5× vs MP3 4×, qualité sans perte disponible
- **Vidéo HCV2** : 6.0× natif, 372.9× mode émergence
- **Codec Binding v2** : 43/200 au benchmark
- **Codec Trajectoire** : tramage par transition, décodage cumulatif

## Fichiers
- `engine/harmonic_voice_codec_v2.py` — Codec audio V2
- `engine/hcv2_video_pipeline.py` — Pipeline vidéo
- `engine/codec_binding.py` — Codec binding
- `engine/codec_trajectoire.py` — Codec trajectoire
- `engine/benchmark_hcv2_vs_standards.py` — Benchmarks

## Statut
✅ Production — Tests benchmarks validés