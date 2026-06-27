// api/_middleware.js — Vérification JWT partagée
const jwt = require('jsonwebtoken');

/**
 * Vérifie le token JWT depuis le cookie ou le header Authorization.
 * Retourne le payload décodé ou null.
 */
function verifyToken(req) {
  const secret = process.env.JWT_SECRET;
  if (!secret) return null;

  // Priorité : cookie HttpOnly, sinon header Bearer
  let token = null;
  const cookieHeader = req.headers.cookie || '';
  const match = cookieHeader.match(/hcv_token=([^;]+)/);
  if (match) {
    token = match[1];
  } else {
    const auth = req.headers.authorization || '';
    if (auth.startsWith('Bearer ')) token = auth.slice(7);
  }

  if (!token) return null;

  try {
    return jwt.verify(token, secret, { algorithms: ['HS256'] });
  } catch {
    return null;
  }
}

module.exports = { verifyToken };
