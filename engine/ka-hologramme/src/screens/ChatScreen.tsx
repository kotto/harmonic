import { useState, useRef, useEffect } from 'react';
import type { Hologramme } from '../types';
import { chat, textToSpeech, playAudioBase64 } from '../services/api';

export function ChatScreen({ hologramme, onBack, kaVoice }: {
  hologramme: Hologramme;
  onBack: () => void;
  kaVoice: boolean;
}) {
  const [msgs, setMsgs] = useState<{ question: string; reponse: string }[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [voiceLoading, setVoiceLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const sessionId = useRef('chat_' + Math.random().toString(36).slice(2, 10));

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [msgs]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const q = input.trim();
    setInput('');
    setMsgs(prev => [...prev, { question: q, reponse: '...' }]);
    setLoading(true);

    try {
      const result = await chat(q, { session_id: sessionId.current });
      const reponse = result.response || 'Pas de reponse.';
      setMsgs(prev => {
        const copy = [...prev];
        copy[copy.length - 1].reponse = reponse;
        return copy;
      });

      if (kaVoice && !voiceLoading) {
        try {
          const tts = await textToSpeech(reponse.slice(0, 1000));
          if (tts.success && tts.audio_base64) {
            playAudioBase64(tts.audio_base64);
          }
        } catch {}
      }
    } catch (e: any) {
      setMsgs(prev => {
        const copy = [...prev];
        copy[copy.length - 1].reponse = 'Erreur: ' + e.message;
        return copy;
      });
    } finally {
      setLoading(false);
    }
  };

  const speakText = async (text: string) => {
    if (voiceLoading) return;
    setVoiceLoading(true);
    try {
      const result = await textToSpeech(text.slice(0, 1000));
      if (result.success && result.audio_base64) {
        playAudioBase64(result.audio_base64);
      }
    } catch {} finally {
      setVoiceLoading(false);
    }
  };

  return (
    <>
      <div className="header">
        <button className="header__back" onClick={onBack}>{'←'} Accueil</button>
        <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{
            width: 6, height: 6, borderRadius: '50%', background: 'var(--life)',
            display: 'inline-block', animation: 'pulse 2s ease-in-out infinite',
          }} />
          <span style={{ fontSize: 12, color: 'var(--soul)' }}>KA present</span>
        </span>
      </div>
      <div style={{ fontSize: 11, color: 'var(--t3)', marginBottom: 4 }}>
        {hologramme.icone} {hologramme.nom} · {hologramme.precision}%
      </div>

      <div className="scroll" ref={scrollRef} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {msgs.length === 0 && (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--t4)', fontSize: 13 }}>
            Posez votre question a {hologramme.nom}
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div className="bubble bubble-q anim-slide">{m.question}</div>
            <div className="bubble bubble-r anim-slide">
              {m.reponse === '...' ? (
                <div style={{ display: 'flex', gap: 4 }}>
                  <span>...</span>
                </div>
              ) : (
                <>
                  <div style={{ fontSize: 14, lineHeight: 1.5 }}>{m.reponse}</div>
                  {kaVoice && (
                    <button
                      onClick={() => speakText(m.reponse)}
                      style={{
                        marginTop: 8, padding: '4px 12px', borderRadius: 10, fontSize: 10,
                        background: 'rgba(155,148,255,.15)', border: '.5px solid rgba(155,148,255,.3)',
                        color: 'var(--soul)', cursor: 'pointer', alignSelf: 'flex-start',
                      }}
                      disabled={voiceLoading}
                    >
                      Ecouter
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ fontSize: 11, color: 'var(--t4)', textAlign: 'center', padding: 4 }}>
            Reflexion en cours...
          </div>
        )}
      </div>

      <div className="chat-input">
        <input value={input} onChange={e => setInput(e.target.value)}
          placeholder="Posez votre question..."
          onKeyDown={e => e.key === 'Enter' && send()} disabled={loading} />
        <button onClick={send} disabled={loading}>
          {loading ? '...' : '→'}
        </button>
        {kaVoice && (
          <button onClick={() => speakText(input)}
            style={{
              width: 44, height: 44, borderRadius: '50%',
              background: 'var(--life-d)', border: '.5px solid var(--life-g)',
              color: 'var(--life)', cursor: 'pointer', fontSize: 18,
            }}
            disabled={voiceLoading || !input.trim()}
          >
            {'🎤'}
          </button>
        )}
      </div>

      <div className="enhance-badge" onClick={() => alert('Voir /api/enhance')}>
        <span>Amelioration image/video disponible</span>
      </div>
    </>
  );
}