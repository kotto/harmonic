#!/usr/bin/env python3
"""
VÃ©rifie les modÃ¨les dÃ©ployÃ©s sur l'instance AWS et leurs capacitÃ©s.
Interroge l'API pour identifier le modÃ¨le backend exact.
"""
import requests
import json
import time

API_BASE = "http://__EC2_IP__:8000"

def check_health():
    """VÃ©rifie les features de l'API"""
    r = requests.get(f"{API_BASE}/health", timeout=10)
    data = r.json()
    print("=" * 70)
    print("INFORMATIONS API")
    print("=" * 70)
    print(f"Version: {data.get('version', 'N/A')}")
    print(f"Features: {json.dumps(data.get('features', {}), indent=2)}")
    return data

def ask_model_identity():
    """Demande au modÃ¨le de s'identifier"""
    prompts = [
        "Quel est le nom exact du modÃ¨le que tu utilises ? RÃ©ponds en une phrase.",
        "Quelles sont tes capacitÃ©s ? As-tu des capacitÃ©s audio, video, ou multimodales ?",
        "Es-tu Qwen 3.4, DeepSeek V4, ou un autre modÃ¨le ? RÃ©ponds prÃ©cisÃ©ment.",
        "Peux-tu analyser des images, de l'audio, ou de la vidÃ©o ?",
    ]
    
    for prompt in prompts:
        print(f"\n{'=' * 70}")
        print(f"QUESTION: {prompt}")
        print(f"{'=' * 70}")
        try:
            payload = {"prompt": prompt, "max_tokens": 200, "temperature": 0.0}
            r = requests.post(f"{API_BASE}/generate", json=payload, timeout=30)
            data = r.json()
            text = data.get("content") or data.get("response") or data.get("text", "")
            if not text and isinstance(data.get("response_data"), dict):
                text = data["response_data"].get("content", "")
            print(f"REPONSE: {text[:500]}")
        except Exception as e:
            print(f"ERREUR: {e}")
        time.sleep(1)

def test_audio_capability():
    """Teste si le modÃ¨le peut traiter de l'audio"""
    print(f"\n{'=' * 70}")
    print("TEST CAPACITE AUDIO")
    print(f"{'=' * 70}")
    prompts = [
        "Analyse ce fichier audio: dÃ©cris ce que tu entends.",
        "Peux-tu traiter des fichiers audio ? Si oui, quels formats ?",
    ]
    for prompt in prompts:
        try:
            payload = {"prompt": prompt, "max_tokens": 200, "temperature": 0.0}
            r = requests.post(f"{API_BASE}/generate", json=payload, timeout=30)
            data = r.json()
            text = data.get("content") or data.get("response") or data.get("text", "")
            if not text and isinstance(data.get("response_data"), dict):
                text = data["response_data"].get("content", "")
            print(f"\nQ: {prompt}")
            print(f"R: {text[:300]}")
        except Exception as e:
            print(f"ERREUR: {e}")
        time.sleep(1)

def test_video_capability():
    """Teste si le modÃ¨le peut traiter de la vidÃ©o"""
    print(f"\n{'=' * 70}")
    print("TEST CAPACITE VIDEO")
    print(f"{'=' * 70}")
    prompts = [
        "Peux-tu analyser des images ou des vidÃ©os ?",
        "DÃ©cris ce que tu vois dans cette image: un coucher de soleil sur la mer.",
    ]
    for prompt in prompts:
        try:
            payload = {"prompt": prompt, "max_tokens": 200, "temperature": 0.0}
            r = requests.post(f"{API_BASE}/generate", json=payload, timeout=30)
            data = r.json()
            text = data.get("content") or data.get("response") or data.get("text", "")
            if not text and isinstance(data.get("response_data"), dict):
                text = data["response_data"].get("content", "")
            print(f"\nQ: {prompt}")
            print(f"R: {text[:300]}")
        except Exception as e:
            print(f"ERREUR: {e}")
        time.sleep(1)

def check_s3_models():
    """VÃ©rifie les modÃ¨les dans S3 via l'API"""
    print(f"\n{'=' * 70}")
    print("VERIFICATION MODELE BACKEND")
    print(f"{'=' * 70}")
    prompts = [
        "Quel modÃ¨le est dÃ©ployÃ© sur l'instance AWS derriÃ¨re toi ? Qwen, DeepSeek, ou autre ?",
        "Es-tu connectÃ© Ã  Qwen 3.4 ou DeepSeek V4 ? Ou utilises-tu les deux ?",
    ]
    for prompt in prompts:
        try:
            payload = {"prompt": prompt, "max_tokens": 200, "temperature": 0.0}
            r = requests.post(f"{API_BASE}/generate", json=payload, timeout=30)
            data = r.json()
            text = data.get("content") or data.get("response") or data.get("text", "")
            if not text and isinstance(data.get("response_data"), dict):
                text = data["response_data"].get("content", "")
            print(f"\nQ: {prompt}")
            print(f"R: {text[:500]}")
        except Exception as e:
            print(f"ERREUR: {e}")
        time.sleep(1)

if __name__ == "__main__":
    print("""
â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
â•‘     VERIFICATION DES MODELES ET CAPACITES AWS              â•‘
â•‘     Instance: http://__EC2_IP__:8000                     â•‘
â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    """)
    
    check_health()
    ask_model_identity()
    check_s3_models()
    test_audio_capability()
    test_video_capability()
    
    print(f"\n{'=' * 70}")
    print("VERIFICATION TERMINEE")
    print(f"{'=' * 70}")
