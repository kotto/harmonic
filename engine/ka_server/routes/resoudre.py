"""
KA Server — Route /api/resoudre
================================
Bridge vers solveur_structure.py (pipeline transvertical + codec psi).
Permet au frontend KA Hologramme de resoudre des questions arithmetiques.
"""

import logging
import sys
import os
from pathlib import Path
from flask import request, jsonify

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ENGINE_DIR))


def register_resoudre_routes(app, services):
    """Enregistre la route /api/resoudre."""

    # Import paresseux du solveur
    _solveur = None

    def get_solveur():
        nonlocal _solveur
        if _solveur is not None:
            return _solveur
        try:
            from solveur_structure import resoudre as _resoudre
            from enrichisseur import reponse_redigee
            _solveur = (_resoudre, reponse_redigee)
            log.info("  Solveur structure charge avec succes")
        except Exception as e:
            log.warning("Solveur structure non disponible: %s", e)
            _solveur = False
        return _solveur

    @app.route('/api/resoudre', methods=['POST', 'OPTIONS'])
    def api_resoudre():
        """Resout une question arithmetique via le pipeline transvertical.

        Body JSON:
            question (str): La question a resoudre
            style (str): Style de reponse (conversationnel, vocal, bref, pedagogique)

        Returns JSON:
            success: bool
            question: str
            resultat: float
            resultat_formate: str
            operations: str
            etapes: str
            style: str
        """
        if request.method == 'OPTIONS':
            return '', 200

        data = request.get_json(silent=True) or {}
        question = (data.get('question') or '').strip()
        style = (data.get('style') or 'conversationnel').strip()

        if not question:
            return jsonify({
                'success': False,
                'error': 'Question requise',
                'code': 'MISSING_QUESTION'
            }), 400

        # Resoudre via solveur_structure.py
        solveur = get_solveur()
        if solveur and solveur is not False:
            try:
                resolver_fn, rediger_fn = solveur
                resultat = resolver_fn(question)
                if resultat is not None:
                    # Generer la reponse redigee
                    # Le codec psi donne le resultat, on reconstruit les operations
                    reponse = rediger_fn(
                        question,
                        f"INIT({resultat})",
                        resultat,
                        style
                    )
                    return jsonify({
                        'success': True,
                        'question': question,
                        'resultat': resultat,
                        'resultat_formate': reponse.get('resultat_formate', str(resultat)),
                        'operations': reponse.get('trajectoire_psi', ''),
                        'etapes': reponse.get('explication', ''),
                        'conclusion': reponse.get('conclusion', ''),
                        'style': style,
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Impossible de resoudre la question',
                        'code': 'RESOLUTION_FAILED'
                    }), 422
            except Exception as e:
                log.error("Erreur solveur: %s", e, exc_info=True)
                return jsonify({
                    'success': False,
                    'error': f"Erreur: {e}",
                    'code': 'SOLVER_ERROR'
                }), 500

        # Fallback : extraction regex simple
        import re
        nums = re.findall(r'\d+(?:\.\d+)?', question)
        if nums:
            vals = [float(n) for n in nums]
            resultat = vals[0] * (vals[1] / 100 if len(vals) > 1 else 1)
            rs = str(resultat) if resultat == int(resultat) else f"{resultat:.2f}"
            return jsonify({
                'success': True,
                'question': question,
                'resultat': resultat,
                'resultat_formate': rs,
                'operations': f"INIT({vals[0]}) MUL({vals[1] / 100 if len(vals) > 1 else 1})",
                'etapes': f"valeur initiale: {vals[0]} x {vals[1] / 100 if len(vals) > 1 else 1} = {rs}",
                'conclusion': f"Le resultat est {rs}.",
                'style': style,
                'fallback': True,
            })

        return jsonify({
            'success': False,
            'error': 'Aucun nombre detecte',
            'code': 'NO_NUMBERS'
        }), 422
