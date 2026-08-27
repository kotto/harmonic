import { useState } from 'react';
import { specialize } from '../services/api';

export function CreateScreen({ onBack }: { onBack: () => void }) {
  const [domain, setDomain] = useState('');
  const [status, setStatus] = useState<'idle' | 'creating' | 'done' | 'error'>('idle');
  const [message, setMessage] = useState('');

  const handleCreate = async () => {
    if (!domain.trim()) return;
    setStatus('creating');
    setMessage("Creation de l'hologramme " + domain + "...");
    try {
      const result = await specialize(domain);
      if (result.success) {
        setStatus('done');
        setMessage("Hologramme " + domain + " cree avec " + (result.facts_created || 0) + " faits !");
      } else {
        setStatus('error');
        setMessage('Erreur: ' + (result.error || result.message));
      }
    } catch (e: any) {
      setStatus('error');
      setMessage('Erreur: ' + e.message);
    }
  };

  return (
    <>
      <div className="header">
        <button className="header__back" onClick={onBack}>← Retour</button>
        <span className="header__title">Creer un hologramme</span>
      </div>

      <div className="scroll">
        <div style={{ background: 'var(--g1)', border: '.5px solid var(--b1)', borderRadius: 16, padding: 20 }}>
          <div style={{ fontSize: 13, color: 'var(--t2)', marginBottom: 16, lineHeight: 1.5 }}>
            Creer un expert IA specialise dans le domaine de votre choix.
            Fournissez 5 a 20 exemples, l'assistant apprend le vocabulaire en 30-60 secondes.
          </div>

          <div className="label">Domaine de specialisation</div>
          <input
            value={domain}
            onChange={e => setDomain(e.target.value)}
            placeholder="ex: Droit des contrats, Medecine, Finance..."
            style={{
              width: '100%', padding: '12px 16px', marginBottom: 16,
              background: 'var(--g2)', border: '.5px solid var(--b2)',
              borderRadius: 12, color: 'var(--t1)', fontSize: 14, outline: 'none',
            }}
          />

          {message && (
            <div style={{
              padding: 12, marginBottom: 16, borderRadius: 10, fontSize: 12, lineHeight: 1.4,
              background: status === 'done' ? 'var(--life-d)' : status === 'error' ? 'rgba(255,100,100,.12)' : 'var(--g2)',
              border: '.5px solid ' + (status === 'done' ? 'var(--life-g)' : status === 'error' ? 'rgba(255,100,100,.3)' : 'var(--b1)'),
              color: status === 'done' ? 'var(--life)' : status === 'error' ? '#ff6464' : 'var(--t2)',
            }}>
              {message}
            </div>
          )}

          <button
            className="btn btn-life"
            onClick={handleCreate}
            disabled={status === 'creating' || !domain.trim()}
          >
            {status === 'creating' ? 'Creation en cours...' : "Creer l'hologramme"}
          </button>

          {status === 'done' && (
            <button className="btn btn-soul" style={{ marginTop: 8 }} onClick={onBack}>
              Tester l'hologramme →
            </button>
          )}
        </div>
      </div>
    </>
  );
}
