import { Hologramme } from '../App';

const TEMPLATES = [
  { id: 'sante', nom: 'Santé', icone: '🏥', description: 'Votre santé', exemples: 5, precision: 100 },
  { id: 'finance', nom: 'Finance', icone: '💰', description: 'Votre budget', exemples: 5, precision: 100 },
  { id: 'relations', nom: 'Relations', icone: '💜', description: 'Vos proches', exemples: 5, precision: 100 },
  { id: 'memoire', nom: 'Mémoire', icone: '🧠', description: 'Souvenirs', exemples: 5, precision: 100 },
];

export function HomeScreen({ onNavigate, onSelectH }: {
  onNavigate: (s: 'home' | 'create' | 'chat' | 'profile') => void;
  onSelectH: (h: Hologramme) => void;
}) {
  return (
    <>
      {/* Status bar spacer */}
      <div style={{ flexShrink: 0 }} />

      <div className="scroll">
        {/* ═══ HCV COMPRESSION — ENTRY POINT ═══ */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(155,148,255,.12), rgba(77,232,174,.06))',
          border: '1px solid var(--soul-g)', borderRadius: 20, padding: 20, marginBottom: 16,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 11, letterSpacing: '.12em', color: 'var(--soul)', textTransform: 'uppercase' }}>⚡ Compression HCV</span>
            <span style={{ fontSize: 10, color: 'var(--t4)' }}>v3.2 · breveté</span>
          </div>
          
          <div style={{ fontSize: 28, fontWeight: 300, color: 'var(--t1)', marginBottom: 4 }}>
            Compressez ×213
          </div>
          <div style={{ fontSize: 13, color: 'var(--t3)', marginBottom: 16, lineHeight: 1.5 }}>
            Images, vidéos, fichiers — sans perte, bit-exact, directement sur votre appareil.
          </div>

          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <button className="btn" style={{
              flex: 1, padding: 12, background: 'var(--soul-d)', border: '.5px solid var(--soul-g)',
              borderRadius: 14, color: 'var(--soul)', fontSize: 13, fontWeight: 500, cursor: 'pointer',
            }} onClick={() => alert('Sélectionnez une image à compresser')}>
              📸 Compresser
            </button>
            <button className="btn" style={{
              flex: 1, padding: 12, background: 'var(--life-d)', border: '.5px solid var(--life-g)',
              borderRadius: 14, color: 'var(--life)', fontSize: 13, fontWeight: 500, cursor: 'pointer',
            }} onClick={() => alert('Sélectionnez une vidéo à améliorer')}>
              🎬 Améliorer
            </button>
          </div>

          <details>
            <summary style={{ fontSize: 11, color: 'var(--t4)', cursor: 'pointer', letterSpacing: '.05em' }}>
              Comment ça marche ?
            </summary>
            <div style={{ marginTop: 8, fontSize: 12, color: 'var(--t3)', lineHeight: 1.6 }}>
              La compression harmonique HCV décompose l'image en ondes (THU), 
              ne stocke que les coefficients essentiels, et reconstruit bit-exact.
              Résultat : 213× de compression, qualité identique.
            </div>
          </details>
        </div>

        {/* ═══ IMAGE ENHANCEMENT ═══ */}
        <div style={{
          background: 'var(--g1)', border: '.5px solid var(--b1)', borderRadius: 16, padding: 16, marginBottom: 16,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span style={{ fontSize: 11, letterSpacing: '.12em', color: 'var(--t3)', textTransform: 'uppercase' }}>✨ Amélioration</span>
          </div>
          <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--t1)', marginBottom: 4 }}>
            Photos et vidéos
          </div>
          <div style={{ fontSize: 12, color: 'var(--t4)', lineHeight: 1.5, marginBottom: 12 }}>
            Réduction de bruit, sur-échantillonnage, correction couleur — le tout en local.
          </div>
          <button className="btn" style={{
            width: '100%', padding: 10, background: 'var(--g2)', border: '.5px solid var(--b2)',
            borderRadius: 12, color: 'var(--t2)', fontSize: 13, cursor: 'pointer',
          }} onClick={() => alert('Ouvrir la galerie')}>
            📁 Choisir un fichier
          </button>
        </div>

        {/* ═══ HOLOGRAMMES KA ═══ */}
        <div style={{ marginBottom: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: 11, letterSpacing: '.12em', color: 'var(--t4)', textTransform: 'uppercase' }}>
              🤖 Découvrir KA
            </span>
            <button style={{
              fontSize: 11, color: 'var(--soul)', background: 'none', border: 'none', cursor: 'pointer',
            }} onClick={() => onNavigate('create')}>+ Créer</button>
          </div>

          <div className="h-grid">
            {TEMPLATES.map(t => (
              <div key={t.id} className="h-card" onClick={() => {
                onSelectH({ id: t.id, nom: t.nom, icone: t.icone, exemples: t.exemples, precision: t.precision, temps: '0s', actif: true });
                onNavigate('chat');
              }}>
                <div style={{ fontSize: 24, marginBottom: 6 }}>{t.icone}</div>
                <div className="h-card__name">{t.nom}</div>
                <div className="h-card__meta">{t.description}</div>
                <span className="tag tag-life" style={{ marginTop: 6, display: 'inline-block' }}>Prêt</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}