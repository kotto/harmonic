"""
HCV PRO - Legacy OpenClaw Integration (DEPRECATED)
====================================================

⚠️  CE FICHIER EST OBSOLÈTE ⚠️

Ce fichier a été remplacé par Hermes Integration.
Veuillez utiliser 'hermes_integration.py' à la place.

Migration vers Hermes:
- Hermes est le successeur officiel d'OpenClaw
- Support multi-plateformes (Linux, macOS, WSL2, Android/Termux)
- Migration automatique des configurations OpenClaw
- Documentation: https://hermes-agent.nousresearch.com/docs/

Pour migrer:
1. Installez Hermes: curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
2. Migrez vos données: hermes claw migrate
3. Mettez à jour vos imports: from hermes_integration import HermesService

Ce fichier est conservé pour compatibilité rétrograde temporaire.
"""

# Redirection vers Hermes pour compatibilité
import warnings
warnings.warn(
    "OpenClaw est déprécié. Utilisez Hermes à la place. "
    "Importez depuis 'hermes_integration' au lieu de 'openclaw_integration'.",
    DeprecationWarning,
    stacklevel=2
)

from hermes_integration import HermesService

# Alias pour compatibilité rétrograde
OpenClawService = HermesService

print("⚠️  OpenClaw Integration est déprécié. Utilisez Hermes Integration à la place.")