import { useState } from 'react';
import { Hologramme } from '../App';
import { reponseRedigee, type ReponseKA, type StyleKA } from '../services/ka';

export function ChatScreen({ hologramme, onBack, kaVoice }: {
  hologramme: Hologramme;
  onBack: () => void;
  kaVoice: boolean;
}) {
  const [msgs, setMsgs] = useState<ReponseKA[]>([
    reponseRedigee(
      'Combien de tuiles pour un toit de 130m²?',
      'INIT(130) MUL(12)',
      1560,
      'conversationnel'
    ),
  ]);
  const [input, setInput] = useState('');
  const [styleKA, setStyleKA] = useState<StyleKA>('conversationnel');

  const send = () => {
    if (!input.trim()) return;
    const q = input;
    setInput('');
    const rep = reponseRedigee(
      q,
      'INIT(130) MUL(12) MUL(1.15)',
      1794,
      styleKA
    );
    setMsgs(prev => [...prev, rep]);
  };

  return (
    <>
      <div className="header">
        <button className="header__back" onClick={onBack}>← Accueil</button>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--life)', display: 'inline-block', animation: 'pulse 2s ease-in-out infinite' }} />
          <span style={{ fontSize: 12, color: 'var(--soul)' }}>KA présent</span>
        </span>
      </div>
      <div style={{ fontSize: 11, color: 'var(--t3)', marginBottom: 4 }}>
        {hologramme.icone} {hologramme.nom} · {hologramme.precision}%
      </div>

      <div className="scroll" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {msgs.map((m, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div className="bubble bubble-q anim-slide">{m.explication ? '' : m.conclusion}</div>
            <div className="bubble bubble-r anim-slide">
              <div className="value value-life" style={{ fontSize: 28 }}>{m.resultat_formate}</div>
              <div className="traj">{m.conclusion}</div>
              <div className="traj">{m.explication}</div>
              <div className="psi">ψ {m.trajectoire_psi} · {m.style}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Style selector */}
      <div style={{ display: 'flex', gap: 6, padding: '4px 0', flexShrink: 0 }}>
        {(['conversationnel', 'vocal', 'bref', 'pédagogique'] as StyleKA[]).map(s => {
          const isActive = styleKA === s;
          return (
          <button key={s} onClick={() => setStyleKA(s)}
            style={{
              flex: 1, padding: '6px 8px', borderRadius: 10, fontSize: 10, cursor: 'pointer',
              background: isActive ? 'var(--soul-d)' : 'var(--g1)',
              color: isActive ? 'var(--soul)' : 'var(--t4)',
              border: '.5px solid ' + (isActive ? 'var(--soul-g)' : 'var(--b1)'),
            }}>{s}</button>
          );
        })}
      </div>

      <div className="chat-input">
        <input value={input} onChange={e => setInput(e.target.value)}
          placeholder="Posez votre question..."
          onKeyDown={e => e.key === 'Enter' && send()} />
        <button onClick={send}>→</button>
        {kaVoice && (
          <button style={{ width: 44, height: 44, borderRadius: '50%', background: 'var(--life-d)', border: '.5px solid var(--life-g)', color: 'var(--life)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', fontSize: 18 }}>
            🎤
          </button>
        )}
      </div>

      {/* Image enhancement discrète */}
      <div className="enhance-badge" onClick={() => alert('Compression HCV: image/video optimisée')}>
        <span>⚡</span> Amélioration image/vidéo disponible
      </div>
    </>
  );
}