"""
routes/sonic_id.py — API d'empreinte sonore pseudo-aléatoire.

Endpoints
---------
GET /api/sonic-id/<identifier>
    Retourne un fichier WAV unique pour l'identifiant.
    Query params :
      - variant : "mobile" | "care" | "default" (par défaut "default")
      - download : "1" pour forcer le téléchargement

HEAD /api/sonic-id/<identifier>
    Métadonnées (durée, longueur) sans le corps.

POST /api/sonic-id
    JSON : {"identifier": "ABC-123", "variant": "mobile"}
    Retourne le WAV en body.
"""

from flask import request, Response, abort

from ka_server.services.sonic_id import sonic_id_wav, sonic_id_duration


def register_sonic_id_routes(app, services):
    """Enregistre les routes d'empreinte sonore."""

    @app.route('/api/sonic-id/<path:identifier>', methods=['GET', 'HEAD'])
    def api_sonic_id_get(identifier: str):
        if not identifier or len(identifier) > 256:
            abort(400, "Identifier trop long ou vide")

        variant = request.args.get("variant", "default")
        if variant not in ("default", "mobile", "care"):
            abort(400, "Variant invalide. Choisir: default, mobile, care")

        wav_data = sonic_id_wav(identifier, variant=variant)
        duration = sonic_id_duration(identifier, variant=variant)

        headers = {
            "X-Sonic-Duration": f"{duration:.2f}",
            "X-Sonic-Identifier": identifier,
            "X-Sonic-Variant": variant,
            "Cache-Control": "public, max-age=86400, immutable",
            "Content-Type": "audio/wav",
            "Content-Length": str(len(wav_data)),
        }

        if request.method == "HEAD":
            return Response(status=200, headers=headers)

        if request.args.get("download") == "1":
            safe_name = identifier.replace("/", "-").replace("\\", "-")[:30]
            headers["Content-Disposition"] = f'attachment; filename="sonic-{safe_name}.wav"'

        return Response(wav_data, mimetype="audio/wav", headers=headers)

    @app.route('/api/sonic-id', methods=['POST'])
    def api_sonic_id_post():
        """Alternative POST pour les clients qui ne peuvent pas encoder
        d'identifiants spéciaux dans l'URL."""
        body = request.get_json(silent=True)
        if not body or "identifier" not in body:
            abort(400, "JSON with 'identifier' required")

        identifier = str(body["identifier"])
        if len(identifier) > 256:
            abort(400, "Identifier trop long")

        variant = body.get("variant", "default")
        if variant not in ("default", "mobile", "care"):
            abort(400, "Variant invalide. Choisir: default, mobile, care")

        wav_data = sonic_id_wav(identifier, variant=variant)
        duration = sonic_id_duration(identifier, variant=variant)

        return Response(
            wav_data,
            mimetype="audio/wav",
            headers={
                "X-Sonic-Duration": f"{duration:.2f}",
                "X-Sonic-Identifier": identifier,
                "X-Sonic-Variant": variant,
                "Cache-Control": "public, max-age=86400, immutable",
            },
        )