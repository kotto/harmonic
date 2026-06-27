// api/auth.js — Authentification JWT sécurisée
// Les credentials sont stockés en variables d'environnement Vercel, jamais en clair

const jwt = require('jsonwebtoken');

const RATE_LIMIT = new Map(); // IP → { count, resetAt }
const MAX_ATTEMPTS = 5;
const WINDOW_MS = 15 * 60 * 1000; // 15 min

function rateLimit(ip) {
  const now = Date.now();
  const entry = RATE_LIMIT.get(ip) || { count: 0, resetAt: now + WINDOW_MS };
  if (now > entry.resetAt) { entry.count = 0; entry.resetAt = now + WINDOW_MS; }
  entry.count++;
  RATE_LIMIT.set(ip, entry);
  return entry.count > MAX_ATTEMPTS;
}

module.exports = async function handler(req, res) {
  // CORS strict — uniquement le domaine Vercel autorisé
  const origin = req.headers.origin || '';
  const allowed = process.env.ALLOWED_ORIGIN || '';
  if (allowed && origin !== allowed) {
    return res.status(403).json({ error: 'Origin non autorisée' });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Méthode non autorisée' });
  }

  const ip = req.headers['x-forwarded-for']?.split(',')[0] || req.socket?.remoteAddress || 'unknown';
  if (rateLimit(ip)) {
    return res.status(429).json({ error: 'Trop de tentatives. Réessayez dans 15 minutes.' });
  }

  const { username, password } = req.body || {};
  if (!username || !password) {
    return res.status(400).json({ error: 'Identifiants manquants' });
  }

  // Validation contre les variables d'environnement (jamais hardcodé)
  const validUser = process.env.HCV_ADMIN_USER;
  const validPass = process.env.HCV_ADMIN_PASS;

  if (!validUser || !validPass) {
    return res.status(500).json({ error: 'Configuration serveur manquante' });
  }

  // Comparaison en temps constant pour éviter timing attacks
  const crypto = require('crypto');
  const userBuf = Buffer.from(username);
  const validUserBuf = Buffer.from(validUser);
  const passBuf = Buffer.from(password);
  const validPassBuf = Buffer.from(validPass);

  // Vérifier les longueurs d'abord pour éviter les erreurs
  const userMatch = userBuf.length === validUserBuf.length && 
                    crypto.timingSafeEqual(userBuf, validUserBuf);
  const passMatch = passBuf.length === validPassBuf.length && 
                    crypto.timingSafeEqual(passBuf, validPassBuf);

  if (!userMatch || !passMatch) {
    return res.status(401).json({ error: 'Identifiants invalides' });
  }

  const secret = process.env.JWT_SECRET;
  if (!secret) return res.status(500).json({ error: 'JWT_SECRET manquant' });

  const token = jwt.sign(
    { sub: username, role: 'operator', iat: Math.floor(Date.now() / 1000) },
    secret,
    { expiresIn: '8h', algorithm: 'HS256' }
  );

  // Cookie HttpOnly + Secure + SameSite=Strict
  res.setHeader('Set-Cookie', [
    `hcv_token=${token}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=28800`
  ]);

  return res.status(200).json({ ok: true, expiresIn: 28800 });
};
