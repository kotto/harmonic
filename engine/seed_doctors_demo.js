/**
 * Seed — 3 médecins africains fictifs pour démonstration
 * =========================================================
 * Exécuté au chargement de l'app si l'annuaire est vide.
 * Génère des avatars SVG data-URI (photos stylisées).
 */

(function seedDemoDoctors() {
  'use strict';
  if (typeof localStorage === 'undefined') return;
  if (localStorage.getItem('ka_doctors_directory')) return; // déjà peuplé

  // ── Générateur d'avatar SVG (cercle dégradé + initiales) ──
  function makeAvatar(initials, hue1, hue2) {
    const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
      + '<defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">'
      + '<stop offset="0%" style="stop-color:hsl(' + hue1 + ',70%,45%)"/>'
      + '<stop offset="100%" style="stop-color:hsl(' + hue2 + ',60%,25%)"/>'
      + '</linearGradient></defs>'
      + '<circle cx="50" cy="50" r="48" fill="url(#g)" stroke="rgba(212,168,83,0.3)" stroke-width="2"/>'
      + '<text x="50" y="66" text-anchor="middle" fill="white" font-family="Inter,sans-serif" font-weight="700" font-size="36">' + initials + '</text>'
      + '</svg>';
    return 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)));
  }

  const doctors = [
    {
      id: 'doc_demo_001',
      name: 'Amadou Diallo',
      specialty: 'Médecine générale — Infectiologie',
      license: 'MED-2021-ABJ',
      phone: '+225 07 12 34 56 78',
      email: 'dr.diallo@vitalka.africa',
      address: 'CHU de Treichville, Abidjan, Côte d\'Ivoire',
      bio: '15 ans d\'expérience en médecine tropicale. Formé à la Faculté de Médecine d\'Abidjan. Spécialiste du paludisme et des maladies infectieuses émergentes. Parle français, dioula, baoulé et anglais.',
      status: 'online',
      accepting: true,
      videoEnabled: true,
      audioEnabled: true,
      chatEnabled: true,
      hoursStart: '07:30',
      hoursEnd: '17:00',
      avatar: makeAvatar('AD', 35, 10),
      publishedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: 'doc_demo_002',
      name: 'Fatoumata Keita',
      specialty: 'Pédiatrie — Nutrition',
      license: 'MED-2019-BKO',
      phone: '+223 76 98 76 54 32',
      email: 'dr.keita@vitalka.africa',
      address: 'Hôpital Gabriel Touré, Bamako, Mali',
      bio: 'Pédiatre diplômée de l\'Université de Bamako. Spécialisée en malnutrition infantile et suivi néonatal en zone rurale. Coordinatrice du programme "Un enfant, un repas". Parle français, bambara, soninké et anglais.',
      status: 'online',
      accepting: true,
      videoEnabled: true,
      audioEnabled: true,
      chatEnabled: true,
      hoursStart: '08:00',
      hoursEnd: '16:30',
      avatar: makeAvatar('FK', 330, 300),
      publishedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: 'doc_demo_003',
      name: 'Jean-Pierre Ndayishimiye',
      specialty: 'Cardiologie — Médecine interne',
      license: 'MED-2020-BJM',
      phone: '+257 61 23 45 67 89',
      email: 'dr.ndayishimiye@vitalka.africa',
      address: 'Hôpital Prince Régent Charles, Bujumbura, Burundi',
      bio: 'Cardiologue formé à l\'Université de Dakar (Sénégal) et spécialisé à Paris VI. Expert en hypertension artérielle et insuffisance cardiaque en contexte tropical. Membre de la Société Africaine de Cardiologie. Parle français, kirundi, swahili et anglais.',
      status: 'busy',
      accepting: true,
      videoEnabled: true,
      audioEnabled: true,
      chatEnabled: false,
      hoursStart: '09:00',
      hoursEnd: '19:00',
      avatar: makeAvatar('JN', 200, 170),
      publishedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
  ];

  localStorage.setItem('ka_doctors_directory', JSON.stringify(doctors));
  console.log('[Seed] 🌍 3 médecins africains ajoutés à l\'annuaire');
})();
