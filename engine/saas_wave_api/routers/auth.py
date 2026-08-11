"""routers.auth — enregistrement et clés API."""

from fastapi import APIRouter, Body, HTTPException

from ..core.keys import PLANS, create_key

router = APIRouter(prefix='/v1/auth', tags=['auth'])


@router.post('/register')
def register(body: dict = Body(...)):
    """Enregistrement public — plan free. Pro/Enterprise : gérés côté admin (CLI)."""
    email = (body.get('email') or '').strip().lower()
    if not email or '@' not in email:
        raise HTTPException(status_code=400, detail={
            'error': 'Email invalide', 'code': 'BAD_EMAIL'})
    key = create_key(email, plan='free')
    return {
        'api_key': key,
        'plan': 'free',
        'daily_limit': PLANS['free']['daily_limit'],
        'usage': 'curl -H "X-API-Key: <clé>" http://localhost:8000/v1/meta/status',
        'note': 'La clé est personnelle — ne la partagez pas. Quota réinitialisé chaque jour.',
    }
