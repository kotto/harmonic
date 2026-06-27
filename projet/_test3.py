import sys, os
sys.path.insert(0, r'f:\SAAS - Copie')
import torch
from harmonic_training.model.harmonic_model import HarmonicForCausalLM, HARMONIC_CONFIGS
from harmonic_weight_initializer import init_harmonic_model
config = HARMONIC_CONFIGS['harmonic-tiny']
model = HarmonicForCausalLM(config)
print(f'Modele cree: {sum(p.numel() for p in model.parameters()):,} params')
model = init_harmonic_model(model)
print('Init harmonique OK')
batch, seq_len = 1, 16
input_ids = torch.randint(1, config['vocab_size'] - 1, (batch, seq_len))
logits, loss, signatures = model(input_ids, labels=input_ids)
print(f'Forward: logits={logits.shape}, loss={loss.item():.4f}')
print('OK')
