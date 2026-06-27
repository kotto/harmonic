"""
Configuration d'entrainement du modele harmonique
===================================================
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TrainingConfig:
    """Configuration complete pour l'entrainement."""
    
    # Modele
    model_name: str = 'harmonic-tiny'
    
    # Donnees
    dataset_name: str = 'HuggingFaceFW/fineweb-edu'
    dataset_config: str = 'sample-10BT'
    dataset_split: str = 'train'
    max_samples: Optional[int] = None  # None = tout
    sequence_length: int = 2048
    vocab_size: int = 50304  # Taille du vocabulaire pour le tokenizer
    
    # Optimisation
    learning_rate: float = 3e-4
    weight_decay: float = 0.1
    beta1: float = 0.9
    beta2: float = 0.95
    epsilon: float = 1e-8
    
    # Scheduler
    scheduler: str = 'cosine'  # cosine, linear, constant
    warmup_steps: int = 1000
    min_lr_ratio: float = 0.1
    
    # Entrainement
    batch_size: int = 8
    gradient_accumulation_steps: int = 4
    max_steps: int = 100000
    save_steps: int = 5000
    eval_steps: int = 500
    logging_steps: int = 10
    
    # Regularisation
    dropout: float = 0.1
    attention_dropout: float = 0.1
    gradient_clip_val: float = 1.0
    
    # Precision mixte
    mixed_precision: str = 'bf16'  # 'fp16', 'bf16', 'no'
    
    # Checkpoint
    output_dir: str = './checkpoints'
    resume_from_checkpoint: Optional[str] = None
    
    # Distributed
    distributed: bool = False
    world_size: int = 1
    
    # Evaluation
    eval_batch_size: int = 16
    eval_sequence_length: int = 2048
    
    def __post_init__(self):
        """Validation de la configuration."""
        assert self.model_name in ['harmonic-tiny', 'harmonic-small', 'harmonic-base',
                                    'harmonic-large', 'harmonic-xl'], \
            f"Modele inconnu: {self.model_name}"
        assert self.scheduler in ['cosine', 'linear', 'constant']
        assert self.mixed_precision in ['fp16', 'bf16', 'no']
