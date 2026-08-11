"""
hcv_bridge — Pont vers le moteur « HCV PRO » (module manquant, comblé le 11/08/2026)
=====================================================================================

`harmonic_codec.py` (commit 4e3830d) importe `multimodal.hcv_bridge` depuis
l'origine, mais ce module n'a JAMAIS existé ni dans l'historique git ni sur le
disque — l'import cassait le codec à dictionnaire (échec reproductible :
`python -c "from multimodal.harmonic_codec import HarmonicCodec"` → ModuleNotFoundError).

Vérifié par l'audit HCV (RAPPORT_AUDIT_HCV.md) : le moteur « HCV PRO » n'existe
pas en tant qu'algorithme — HCV-Compression-Engine est OpenCV+JPEG+zstd. Ce pont
est donc HONNÊTE : il ne prétend pas brancher un moteur externe inexistant.

Le codec, lui, est autonome : `_encode_residual_hcv` / `_decode_residual_hcv`
(Delta-H + zstd, `harmonic_codec.py` l.214/328) n'utilisent que le contexte zstd
du codec. Le pont fournit les trois fonctions attendues, et le mode activé est
le Delta-H + zstd natif du codec.

Contrat (tel que consommé par harmonic_codec.py) :
    is_hcv_available() -> bool          (drapeau global)
    get_hcv_codec(bit_depth, zstd_level) -> objet codec (non utilisé)
    get_hcv_functions() -> dict non vide  (active le mode Delta-H + zstd)
"""


def is_hcv_available() -> bool:
    """Le moteur HCV PRO externe n'existe pas (audit) — le codec tourne sur
    son Delta-H + zstd natif, qui ne dépend d'aucun module externe."""
    return False


def get_hcv_codec(bit_depth: int = 8, zstd_level: int = 11):
    """Aucun codec externe — retourne None (le codec gère le fallback)."""
    return None


def get_hcv_functions() -> dict:
    """Active le mode 'residual HCV' du codec = Delta-H + zstd natif
    (implémenté dans harmonic_codec.py, pas dans un moteur externe)."""
    return {
        'mode': 'delta_h_zstd_native',
        'note': 'Pont comblé — le moteur HCV PRO externe n existe pas '
                '(RAPPORT_AUDIT_HCV.md) ; le codec utilise son encodeur '
                'Delta-H + zstd intégré.',
    }
