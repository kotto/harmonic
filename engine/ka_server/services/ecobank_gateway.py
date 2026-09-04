"""
ecobank_gateway.py — Rétro-compatibilité
=========================================
Ce fichier a été remplacé par `banking_gateway.py` (interface générique).
Tous les symboles sont ré-exportés depuis le nouveau module.

⚠️  Les nouveaux imports doivent utiliser `banking_gateway` à la place.
    Ce fichier sera supprimé dans une version future.

Migration :
    from ka_server.services.ecobank_gateway import get_ecobank_client
    → from ka_server.services.banking_gateway import get_payment_processor

    from ka_server.services.ecobank_gateway import EcobankClient
    → from ka_server.services.banking_gateway import PaymentProcessor
"""

from .banking_gateway import *  # noqa: F401, F403

import warnings
warnings.warn(
    "ecobank_gateway est déprécié. Utilisez banking_gateway à la place.",
    DeprecationWarning, stacklevel=2,
)