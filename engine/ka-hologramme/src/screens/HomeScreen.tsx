import { useState } from 'react';
import type { Hologramme } from '../types';
import { compressImage, enhanceImage, openFilePicker } from '../services/api';

const TEMPLATES = [
  { id: 'sante', nom: 'Sante', icone: '🏥', description: 'Votre sante', exemples: 5, precision: 100 },
  { id: 'finance', nom: 'Finance', icone: '💰', description: 'Votre budget', exemples: 5, precision: 100 },
  { id: 'relations', nom: 'Relations', icone: '💜', description: 'Vos proches', exemples: 5, precision: 100 },
  { id: 'memoire', nom: 'Memoire', icone: '🧠', description: 'Souvenirs', exemples: 5, precision: 100 },
];

export function HomeScreen({ onNavigate, onSelectH }: {
  onNavigate: (s: 'home' | 'create' | 'chat' | 'profile') => void;
  onSelectH: (h: Hologramme) => void;
}) {
  const [compressing, setCompressing] = useState(false);
  const [enhancing, setEnhancing] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const handleCompress = async () => {
    const file = await openFilePicker('image/*');
    if (!file) return;
    setCompressing(true);
    setStatusMsg(null);
    try {
      const result = await compressImage(file);
      if (result.success) {
        setStatusMsg('Compression reussie ! x' + result.ratio + ' (' + result.saved_percent + '% gagnes)');
      } else {
        setStatusMsg('Erreur: ' + (result.error || 'echec'));
      }
    } catch (e: any) {
      setStatusMsg('Erreur: ' + e.message);
    } finally {
      setCompressing(false);
    }
  };

  const handleEnhance = async () => {
    const file = await openFilePicker('image/*,video/*');
    if (!file) return;
    setEnhancing(true);
    setStatusMsg(null);
    try {
      const result = await enhanceImage(file);
      if (result.success) {
        setStatusMsg('Image amelioree !');
      } else {
        setStatusMsg('Erreur: ' + (result.error || 'echec'));
      }
    } catch (e: any) {
      setStatusMsg('Erreur: ' + e.message);
    } finally {
      setEnhancing(false);
    }
  };

  return (
    <>
      <div style={{ flexShrink: 0 }} />
      <div className="scroll">
        {/* HCV COMPRESSION */}
        <div style={{
          background: 'linear-gradient(135deg, rgba(155,148,255,.12), rgba(77,232,174,.06))',
          border: '1px solid var(--soul-g)', borderRadius: 20, padding: 20, marginBottom: 16,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <span style={{ fontSize: 11, letterSpacing: '.12em', color: 'var(--soul)', textTransform: 'uppercase' }}>Compression HCV</span>
            <span style={{ fontSize: 10, color: 'var(--t4)' }}>v3.2 · brevetee</span>
          </div>

          <div style={{ fontSize: 28, fontWeight: 300, color: 'var(--t1)', marginBottom: 4 }}>
            Compressez x213
          </div>
          <div style={{ fontSize: 13, color: 'var(--t3)', marginBottom: 16, lineHeight: 1.5 }}>
            Images, videos, fichiers — sans perte, bit-exact, directement sur votre appareil.
          </div>

          {statusMsg && (
            <div style={{
              padding: 10, marginBottom: 12,
              background: 'rgba(77,232,174,.12)',
              border: '1px solid rgba(77,232,174,.35)',
              borderRadius: 10, fontSize: 12, color: 'var(--life)',
            }}>
              {statusMsg}
            </div>
          )}

          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <button className="btn" style={{
              flex: 1, padding: 12, background: 'var(--soul-d)', border: '.5px solid var(--soul-g)',
              borderRadius: 14, color: 'var(--soul)', fontSize: 13, fontWeight: 500, cursor: 'pointer',
            }} onClick={handleCompress} disabled={compressing}>
              {compressing ? 'Compression...' : 'Compresser'}
            </button>
            <button className="btn" style={{
              flex: 1, padding: 12, background: 'var(--life-d)', border: '.5px solid var(--life-g)',
              borderRadius: 14, color: 'var(--life)', fontSize: 13, fontWeight: 500, cursor: 'pointer',
            }} onClick={handleEnhance} disabled={enhancing}>
              {enhancing ? 'Amelioration...' : 'Ameliorer'}
            </button>
          </div>

          <details>
            <summary style={{ fontSize: 11, color: 'var(--t4)', cursor: 'pointer', letterSpacing: '.05em' }}>
              Comment ca marche ?
            </summary>
            <div style={{ marginTop: 8, fontSize: 12, color: 'var(--t3)', lineHeight: 1.6 }}>
              La compression harmonique HCV decompose l'image en ondes (THU),
              ne stocke que les coefficients essentiels, et reconstruit bit-exact.
              Resultat : 213x de compression, qualite identique.
            </div>
          </details>
        </div>

        {/* HOLOGRAMMES KA */}
        <div style={{ marginBottom: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: 11, letterSpacing: '.12em', color: 'var(--t4)', textTransform: 'uppercase' }}>
              Decouvrir KA
            </span>
            <button style={{
              fontSize: 11, color: 'var(--soul)', background: 'none', border: 'none', cursor: 'pointer',
            }} onClick={() => onNavigate('create')}>+ Creer</button>
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
                <span className="tag tag-life" style={{ marginTop: 6, display: 'inline-block' }}>Pret</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
