import type { Screen, Hologramme } from '../types';

const HOLOS: Hologramme[] = [
  { id: '1', nom: 'Finance', icone: '💰', exemples: 12, precision: 95, temps: '3 min', actif: true },
  { id: '2', nom: 'Droit contrats', icone: '⚖️', exemples: 8, precision: 88, temps: '2 min', actif: true },
  { id: '3', nom: 'Diagnostic', icone: '🏥', exemples: 5, precision: 72, temps: '1 min', actif: false },
  { id: '4', nom: 'Couverture', icone: '🏠', exemples: 4, precision: 100, temps: '2 min', actif: true },
];

export function ProfileScreen({ onNavigate, kaVoice, onToggleVoice }: {
  onNavigate: (s: Screen) => void;
  kaVoice: boolean;
  onToggleVoice: () => void;
}) {
  return (
    <>
      <div style={{ textAlign: 'center', padding: '16px 0 8px' }}>
        <h2 style={{ fontSize: 20, fontWeight: 300, color: 'var(--t1)' }}>KA</h2>
        <p style={{ fontSize: 12, color: 'var(--t4)', marginTop: 2 }}>Compression · IA · Privacy</p>
      </div>

      {/* Stats compression en premier */}
      <div className="stat-grid" style={{ marginBottom: 12 }}>
        <div className="stat">
          <div className="stat__n" style={{ color: 'var(--soul)' }}>213×</div>
          <div className="stat__l">COMPRESSION</div>
        </div>
        <div className="stat">
          <div className="stat__n" style={{ color: 'var(--life)' }}>0</div>
          <div className="stat__l">PERTE (%)</div>
        </div>
        <div className="stat">
          <div className="stat__n" style={{ color: 'var(--t1)' }}>4</div>
          <div className="stat__l">HOLOGRAMMES</div>
        </div>
      </div>

      <div className="scroll">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {HOLOS.map(h => (
            <div key={h.id} className="h-item anim-fade">
              <div>
                <div className="h-item__n">{h.icone} {h.nom}</div>
                <div className="h-item__m">{h.exemples} exemples · {h.precision}% · {h.temps}</div>
              </div>
              <span className="h-item__s">{h.actif ? 'ACTIF' : 'EN COURS'}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Manifestation KA */}
      <div className="card" style={{ margin: '8px 0', flexShrink: 0 }}>
        <div style={{ fontSize: 11, color: 'var(--t3)', letterSpacing: '.08em', marginBottom: 8 }}>MANIFESTATION KA</div>
        <div style={{ display: 'flex', gap: 8 }}>
          <div
            style={{
              flex: 1, padding: 10, textAlign: 'center', borderRadius: 10, cursor: 'pointer',
              background: kaVoice ? 'var(--soul-d)' : 'var(--g1)',
              border: `.5px solid ${kaVoice ? 'var(--soul-g)' : 'var(--b1)'}`,
            }}
            onClick={() => !kaVoice && onToggleVoice()}
          >
            <span style={{ fontSize: 16 }}>🎤</span>
            <div style={{ fontSize: 10, color: kaVoice ? 'var(--soul)' : 'var(--t4)', marginTop: 4 }}>Vocal</div>
          </div>
          <div
            style={{
              flex: 1, padding: 10, textAlign: 'center', borderRadius: 10, cursor: 'pointer',
              background: !kaVoice ? 'var(--soul-d)' : 'var(--g1)',
              border: `.5px solid ${!kaVoice ? 'var(--soul-g)' : 'var(--b1)'}`,
            }}
            onClick={() => kaVoice && onToggleVoice()}
          >
            <span style={{ fontSize: 16 }}>🔇</span>
            <div style={{ fontSize: 10, color: !kaVoice ? 'var(--soul)' : 'var(--t4)', marginTop: 4 }}>Silencieux</div>
          </div>
        </div>
      </div>

      {/* Compression discrète */}
      <details style={{ flexShrink: 0 }}>
        <summary style={{ fontSize: 10, color: 'var(--t4)', letterSpacing: '.08em', cursor: 'pointer', padding: 4 }}>
          ⚡ Compression HCV
        </summary>
        <div style={{ padding: '8px 0', fontSize: 11, color: 'var(--t3)', lineHeight: 1.5 }}>
          Compression harmonique ×213, bit-exact. Technologie brevetée THU V2.
          <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
            <div className="stat" style={{ flex: 1, padding: 8 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--t1)' }}>213×</div>
              <div style={{ fontSize: 9, color: 'var(--t4)', marginTop: 2, letterSpacing: '.08em' }}>RATIO</div>
            </div>
            <div className="stat" style={{ flex: 1, padding: 8 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--t1)' }}>49s</div>
              <div style={{ fontSize: 9, color: 'var(--t4)', marginTop: 2, letterSpacing: '.08em' }}>4K/FRAME</div>
            </div>
          </div>
          {/* Enhancement */}
          <div style={{ marginTop: 8, padding: 8, background: 'var(--g1)', borderRadius: 8, border: '.5px solid var(--b1)' }}>
            <div style={{ fontWeight: 500, color: 'var(--t2)', marginBottom: 4 }}>Amélioration image/vidéo</div>
            <div style={{ fontSize: 10, color: 'var(--t4)' }}>
              Réduction de bruit · Sur-échantillonnage · Correction couleur · Compression ×213
            </div>
          </div>
        </div>
      </details>
    </>
  );
}