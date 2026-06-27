# MANUAL CONFIGURATION INSTRUCTIONS - CONNECTIVE AI MULTI-MODAL

## CONNEXION SSH
```bash
ssh -i ~/.ssh/deep ec2-user@35.171.182.151
```

## CONFIGURATION CLES API
```bash
cd /home/ec2-user/connective-ai-multimodal
nano connective_ai_multimodal.py
```

## REMPLACER LES CLES:
- YOUR_DEEPSEEK_KEY → "sk-votre_clé_deepseek"
- YOUR_OPENAI_KEY → "sk-votre_clé_openai"
- YOUR_ANTHROPIC_KEY → "sk-ant-votre_clé_anthropic"
- YOUR_PERPLEXITY_KEY → "pplx-votre_clé_perplexity"
- YOUR_HUGGINGFACE_KEY → "hf_votre_clé_huggingface"

## REDEMARRAGE SERVICE:
```bash
sudo systemctl restart connective-ai-multimodal
```

## VALIDATION:
```bash
curl http://35.171.182.151:8000/health
curl http://35.171.182.151:8000/modalities
```

## TESTS LM ARENA:
```bash
python test_multimodal_lm_arena.py
```

## ENDPOINTS DISPONIBLES:
- API: http://35.171.182.151:8000
- Documentation: http://35.171.182.151:8000/docs
- Health: http://35.171.182.151:8000/health
- Modalities: http://35.171.182.151:8000/modalities
- LM Arena Score: http://35.171.182.151:8000/lm_arena_score

## COUTS ESTIMES:
- Infrastructure: $286/semaine
- API Deepseek: $1,000
- API GPT-4: $2,000
- API Claude: $1,500
- API Perplexity: $500
- API Hugging Face: $500
- Total: $5,786/semaine