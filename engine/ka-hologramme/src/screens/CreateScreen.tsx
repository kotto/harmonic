import { useState } from 'react';

export function CreateScreen({ onBack }: { onBack: () => void }) {
  const [exemples] = useState([
    { q: '"100m² de toiture → combien de tuiles ?"', r: 'INIT(100) MUL(12) = 1200' },
    { q: '"150m² avec pente 30° → tuiles ?"', r: 'INIT(150) MUL(12) MUL(1.15) = 2070' },
    { q: '"Budget 5000€, marge 15% → coût ?"', r: 'INIT(5000) MUL(0.85) = 4250' },
    { q: '"Surface 200m², tuiles 12/m² → total ?"', r: 'INIT(200) MUL(12) = 2400' },
    { q: '"Toit 75m², 10% perte → tuiles ?"', r: 'INIT(75) MUL(12) MUL(1.1) = 990' },
  ]);
  const [training] = useState(true);

  return (
    <>
      <div className="header">
        <button className="header__back" onClick={onBack}>← Retour</button>
        <span className="header__title">Expert Couverture</span>
        <span style={{ fontSize: 11, color: 'var(--t4)' }}>{exemples.length}/5</span>
      </div>

      <div className="scroll">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '4px 0' }}>
          {exemples.map((ex, i) => (
            <div key={i} className="ex ex-input anim-fade" style={{ animationDelay: `${i * 0.1}s` }}>
              <div className="ex__q">{ex.q}</div>
              <div className="ex__r">→ {ex.r}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="progress" style={{ margin: '8px 0' }}>
        <div className="progress__fill" style={{ width: training ? '100%' : '60%' }} />
      </div>
      <div style={{ textAlign: 'center', fontSize: 11, color: 'var(--t4)', marginBottom: 8 }}>
        {training ? '✓ Hologramme prêt · 5 exemples · 2 min 03s' : '4/5 exemples · Encore 1 exemple'}
      </div>

      <button className="btn btn-life" style={{ marginBottom: 8 }} onClick={onBack}>
        Tester l'hologramme →
      </button>
    </>
  );
}