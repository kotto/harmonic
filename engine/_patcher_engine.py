# -*- coding: utf-8 -*-
"""Applique à engine/ka_index.html (source de vérité) :
1. script ka_hybrid.js chargé après harmonic_v3.js
2. askKA branché sur le noyau hybride (refus final) — RP supprimé
"""
import io

p = 'ka_index.html'
s = io.open(p, encoding='utf-8').read()

# ── 1. Charger le noyau hybride (après harmonic_v3.js) ──
TAG_OLD = "\t<script src=\"harmonic_v3.js\"></script>\n"
TAG_NEW = ("\t<script src=\"harmonic_v3.js\"></script>\n"
           "\t<script src=\"ka_hybrid.js\"></script>  <!-- 🧠 noyau hybride : calcul exact, corpus médical, refus calibré -->\n")
assert s.count(TAG_OLD) == 1, f"script harmonic_v3 introuvable ({s.count(TAG_OLD)})"
s = s.replace(TAG_OLD, TAG_NEW)

# ── 2. Remplacer les phrases aléatoires par le refus honnête ──
RP_OLD = ("\tconst RP=['Je suis KA, votre assistant personnel intelligent. "
          "Posez-moi une question !','Que voulez-vous savoir ? Je suis là pour vous aider.',"
          "'Bonjour ! Je suis KA. Que puis-je faire pour vous ?'];\n")
RP_NEW = ("\t// ═══ PONT D'AUDIT HYBRIDE — noyau local (garanti) + cerveau de connaissances ═══\n"
          "\t// Plus de phrases aléatoires : hors-ligne, KA répond par le noyau\n"
          "\t// (calcul exact, corpus médical, conduites, refus calibré) ou se tait.\n")
assert s.count(RP_OLD) == 1, f"RP introuvable ({s.count(RP_OLD)})"
s = s.replace(RP_OLD, RP_NEW)

# ── 3. askKA → noyau hybride, refus FINAL (preuve : le cerveau hallucine) ──
ASK_OLD = """\t\tasync function askKA(message) {
\t\t  if (!API_ONLINE) return RP[Math.floor(Math.random() * RP.length)];
\t\t  try {
\t\t    // Récupérer/générer un user_id persistant
\t\t    let uid = localStorage.getItem('ka_user_id');
\t\t    if (!uid) { uid = 'user_' + Date.now().toString(36) + Math.random().toString(36).slice(2,6); localStorage.setItem('ka_user_id', uid); }
\t\t    
\t\t    // 📜 Historique conversationnel (multi-tours) — localStorage
\t\t    let hist = [];
\t\t    try { hist = JSON.parse(localStorage.getItem('ka_chat_hist') || '[]'); } catch(e) {}
\t\t    hist = hist.slice(-6); // garder les 6 derniers échanges
\t\t    const res = await fetch(API_URL + '/api/chat', {
\t\t      method: 'POST',
\t\t      headers: {'Content-Type': 'application/json'},
\t\t      body: JSON.stringify({message: message, user_id: uid, history: hist})
\t\t    });
\t\t    if (!res.ok) throw new Error('API error');
\t\t    const data = await res.json();
\t\t    // Sauvegarder l'échange
\t\t    hist.push({role:'user', content:message});
\t\t    hist.push({role:'assistant', content:(data.response||'').slice(0,500)});
\t\t    try { localStorage.setItem('ka_chat_hist', JSON.stringify(hist.slice(-6))); } catch(e) {}
\t\t    
\t\t    // Afficher les infos de spécialisation si présentes
\t\t    if (data.specialization) {
\t\t      const spec = data.specialization;
\t\t      setTimeout(() => {
\t\t        const el = document.getElementById('spec-info');
\t\t        if (el && spec.success) {
\t\t          el.innerHTML = '🎯 '+spec.domain+' · '+spec.triplets_count.toLocaleString()+' faits';
\t\t          el.style.display = 'block';
\t\t        }
\t\t      }, 500);
\t\t    }
\t\t    
\t\t    return data.response || RP[Math.floor(Math.random() * RP.length)];
\t\t  } catch(e) {
\t\t    API_ONLINE = false;
\t\t    return RP[Math.floor(Math.random() * RP.length)];
\t\t  }
\t\t}
"""
ASK_NEW = """\t\tasync function askKA(message) {
\t\t  // ═══ LE NOYAU HYBRIDE — réponse immédiate, garantie, hors-ligne ═══
\t\t  // Calcul exact par les ondes · corpus médical · conduites d'urgence ·
\t\t  // identité · concepts appris · refus calibré (« je préfère me taire »).
\t\t  // ⚠️ Le refus du noyau est FINAL : l'escalade vers /api/chat a été testée
\t\t  // et retirée — le cerveau répond parfois hors-sujet (« météo à Paris » →
\t\t  // « Art nouveau… ») ; on refuse plutôt que d'inventer.
\t\t  if (window.KAHybrid) {
\t\t    const core = KAHybrid.repondre(message);
\t\t    return KAHybrid.phraseModele(core);
\t\t  }
\t\t  // Secours (noyau absent) : ancien chemin cerveau, refus honnête si hors-ligne
\t\t  if (!API_ONLINE) return 'Je ne peux pas répondre à ça — ce n\\'est pas dans ce que je connais.';
\t\t  const rep = await repondreCerveau(message);
\t\t  return rep || 'Je ne peux pas répondre à ça — ce n\\'est pas dans ce que je connais.';
\t\t}

\t\tasync function repondreCerveau(message) {
\t\t  try {
\t\t    // Récupérer/générer un user_id persistant
\t\t    let uid = localStorage.getItem('ka_user_id');
\t\t    if (!uid) { uid = 'user_' + Date.now().toString(36) + Math.random().toString(36).slice(2,6); localStorage.setItem('ka_user_id', uid); }
\t\t    
\t\t    // 📜 Historique conversationnel (multi-tours) — localStorage
\t\t    let hist = [];
\t\t    try { hist = JSON.parse(localStorage.getItem('ka_chat_hist') || '[]'); } catch(e) {}
\t\t    hist = hist.slice(-6); // garder les 6 derniers échanges
\t\t    const res = await fetch(API_URL + '/api/chat', {
\t\t      method: 'POST',
\t\t      headers: {'Content-Type': 'application/json'},
\t\t      body: JSON.stringify({message: message, user_id: uid, history: hist})
\t\t    });
\t\t    if (!res.ok) throw new Error('API error');
\t\t    const data = await res.json();
\t\t    // Sauvegarder l'échange
\t\t    hist.push({role:'user', content:message});
\t\t    hist.push({role:'assistant', content:(data.response||'').slice(0,500)});
\t\t    try { localStorage.setItem('ka_chat_hist', JSON.stringify(hist.slice(-6))); } catch(e) {}
\t\t    
\t\t    // Afficher les infos de spécialisation si présentes
\t\t    if (data.specialization) {
\t\t      const spec = data.specialization;
\t\t      setTimeout(() => {
\t\t        const el = document.getElementById('spec-info');
\t\t        if (el && spec.success) {
\t\t          el.innerHTML = '🎯 '+spec.domain+' · '+spec.triplets_count.toLocaleString()+' faits';
\t\t          el.style.display = 'block';
\t\t        }
\t\t      }, 500);
\t\t    }
\t\t    return data.response || '';
\t\t  } catch(e) {
\t\t    API_ONLINE = false;
\t\t    return '';
\t\t  }
\t\t}
"""
assert s.count(ASK_OLD) == 1, f"askKA introuvable ({s.count(ASK_OLD)})"
s = s.replace(ASK_OLD, ASK_NEW)

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print("✅ engine/ka_index.html : noyau hybride chargé + askKA branché + RP supprimé")
