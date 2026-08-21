import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useChat } from '@/hooks/useChat'
import type { ChatMessage } from '@/hooks/useChat'
import { isNative, ensureNativeLoaded } from '@/services/native'

/** Reconnaissance d'ID dans un texte (ex: ABC-2026-00042, PATIENT-MB-3847) */
const ID_PATTERN = /\b[A-Z][A-Z0-9]+-[0-9]{4,}\b/
const API_HOST = window.location.origin

/** Joue l'empreinte sonore d'un identifiant via l'API */
function playSonicId(id: string, variant = 'mobile') {
  const url = `${API_HOST}/api/sonic-id/${encodeURIComponent(id)}?variant=${variant}`
  fetch(url)
    .then(r => r.blob())
    .then(blob => {
      const audio = new Audio(URL.createObjectURL(blob))
      audio.play().catch(() => {})
    })
    .catch(() => {})  // silencieux en cas d'erreur
}

const KEY_ROWS = [
  [['1','~'],['2','@'],['3','#'],['4','$'],['5','%'],['6','^'],['7','&'],['8','*'],['9','('],['0',')']],
  [['a','à'],['z','æ'],['e','€'],['r','®'],['t','™'],['y','¥'],['u','ù'],['i','ï'],['o','œ'],['p','°']],
  [['q',''],['s','ß'],['d',''],['f',''],['g',''],['h',''],['j',''],['k',''],['l',''],['m','µ']],
  [['w',''],['x',''],['c','ç'],['v',''],['b',''],['n','ñ']],
]

const EMOJIS = ['😊','😂','❤️','🔥','✨','🙏','👍','🎉','😄','😍','🤔','😎','🥰','💪','🙌','👋','🎶','🌟','💡','🚀','🌍','🍕','☕','🎯','💬','✅','😘','🫶','🤩','😅','🫠','🤝','🌸','⭐','🎵']

const SUGGESTIONS: Record<string, string[]> = {
  '': ['Qui es-tu ?', 'C\'est quoi le paludisme ?', 'Que faire en cas d\'AVC ?', '15 + 27'],
  qu: ['Qui es-tu ?', 'Qu\'est-ce que le diabète ?', 'Qu\'est-ce que la liberté ?', 'Quel est le plus haut sommet ?'],
  ce: ['C\'est quoi le paludisme ?', 'C\'est quoi le VIH ?', 'C\'est quoi la vitesse de la lumière ?'],
  q: ['Que faire en cas d\'AVC ?', 'Que faire en cas de brûlure ?', 'Que faire en cas de serpent ?'],
  co: ['Comment traiter le paludisme ?', 'Comment définir le nombre d\'or ?'],
  so: ['Sophie', 'Soirée'],
  ap: ['Appeler'],
  de: ['Définir l\'hypertension', 'Définir la drépanocytose'],
}

export default function MessagesScreen() {
  const navigate = useNavigate()
  const { messages, isProcessing, send } = useChat()
  const [text, setText] = useState('')
  const [shift, setShift] = useState(false)
  const [lock, setLock] = useState(false)
  const [altMode, setAltMode] = useState(false)
  const [voice, setVoice] = useState(false)
  const [emoji, setEmoji] = useState(false)
  const [showKbd, setShowKbd] = useState(true)
  const lastShift = useRef(0)
  const msgListRef = useRef<HTMLDivElement>(null)
  const voiceTimer = useRef<ReturnType<typeof setInterval>>()

  useEffect(() => {
    if (msgListRef.current) {
      msgListRef.current.scrollTop = msgListRef.current.scrollHeight
    }
  }, [messages])

  const getSuggestions = (t: string) => {
    const lastWord = (t.trim().split(' ').pop() || '').toLowerCase()
    for (const [k, v] of Object.entries(SUGGESTIONS)) {
      if (k && lastWord.startsWith(k)) return v.slice(0, 6)
    }
    return SUGGESTIONS[''].slice(0, 6)
  }

  const sendMsg = () => {
    const val = text.trim()
    if (!val || isProcessing) return
    send(val)
    setText('')
  }

  const handleKeyPress = (c: string) => {
    setText(prev => prev + c)
    if (shift && !lock) {
      setShift(false)
    }
  }

  const handleShift = () => {
    const n = Date.now()
    if (n - lastShift.current < 280) {
      setLock(!lock)
      setShift(!lock)
    } else {
      setShift(!shift)
      setLock(false)
    }
    lastShift.current = n
  }

  const toggleVoice = async () => {
    if (voice) {
      setVoice(false)
      clearInterval(voiceTimer.current)
      // Arrêter la reconnaissance vocale si en cours
      const vr = (window as any).voiceRecognition
      if (vr && typeof vr.stop === 'function') {
        try { vr.stop() } catch (e) {}
      }
      return
    }

    // Détection native ou Web Speech API
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SR) {
      // Web Speech API (Android WebView ou navigateur)
      try {
        const recognition = new SR()
        ;(window as any).voiceRecognition = recognition
        recognition.lang = 'fr-FR'
        recognition.continuous = false
        recognition.interimResults = true

        recognition.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript
          setText(transcript)
          if (event.results[0].isFinal) {
            setVoice(false)
            send(transcript)
          }
        }
        recognition.onerror = () => {
          setVoice(false)
        }
        recognition.start()
        setVoice(true)
        return
      } catch (e) {
        console.warn('[KA] Web Speech API error:', e)
      }
    }

    // Fallback : simulation simplifiée
    setVoice(true)
    setText('')
    const phrases = ['Rendez-vous demain à 19h ?','Appelle Sophie','Prépare ma réunion','Qui es-tu ?','C\'est quoi le diabète ?','Que faire en cas d\'AVC ?']
    const phrase = phrases[Math.floor(Math.random() * phrases.length)]
    let i = 0
    voiceTimer.current = setInterval(() => {
      if (i >= phrase.length) {
        clearInterval(voiceTimer.current)
        setVoice(false)
        return
      }
      setText(prev => prev + phrase[i])
      i++
    }, 72)
  }

  useEffect(() => {
    return () => clearInterval(voiceTimer.current)
  }, [])

  /** Affichage d'un message selon son type */
  const renderMessage = (m: ChatMessage) => {
    if (m.sender === 'user') {
      return <div key={m.id} className="msg msg--m">{m.text}</div>
    }
    if (m.sender === 'ka') {
      const match = m.text.match(ID_PATTERN)
      return (
        <div key={m.id} className="msg msg--ka">
          <div className="msg__ka__dot" />
          {m.text}
          {match && (
            <span
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 4,
                marginLeft: 6, padding: '2px 8px 2px 6px',
                borderRadius: 20, fontSize: 10, fontWeight: 600,
                background: 'rgba(108,99,255,.15)',
                border: '0.5px solid rgba(108,99,255,.25)',
                color: '#8b83ff', cursor: 'pointer',
                whiteSpace: 'nowrap', verticalAlign: 'middle',
                transition: 'background .2s',
              }}
              onClick={() => playSonicId(match[0])}
              title={`Identifiant détecté : ${match[0]} — cliquer pour écouter sa signature sonore`}
              role="button"
            >
              🎵
            </span>
          )}
        </div>
      )
    }
    // contact
    return <div key={m.id} className="msg msg--t">{m.text}</div>
  }

  const renderKey = (label: string, alt: string, w: number, cls = '', fn: () => void) => (
    <div
      key={label + alt}
      className="key"
      style={{ width: w + 'px' }}
      onClick={(e) => { e.preventDefault(); fn() }}
      role="button"
    >
      <span className="key__c">{label}</span>
      {alt && <span className="key__a">{alt}</span>}
    </div>
  )

  return (
    <>
      <div className="flex shrink-0 items-center justify-between px-[22px] pt-[14px]">
        <div
          className="cursor-pointer rounded-xl px-2 py-1 text-[13px] text-[var(--t3)] transition-colors active:bg-[var(--g2)]"
          onClick={() => navigate('/')}
          role="button"
        >
          ‹ KA
        </div>
        <div className="text-[11px] tracking-[.08em] text-[var(--sky)] opacity-65">ASSISTANT</div>
        <div style={{ width: '48px' }} />
      </div>

      {/* Messages */}
      <div ref={msgListRef} className="flex-1 flex flex-col justify-end gap-2 px-[18px] py-[8px] overflow-y-auto hide-scrollbar min-h-0">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full px-6">
            <div className="text-4xl mb-2 opacity-40">🌐</div>
            <div className="text-[14px] text-[var(--t3)] mb-3">Assistant KA — Que voulez-vous savoir ?</div>

            {/* Cartes de suggestions cliquables */}
            <div className="grid grid-cols-2 gap-2 w-full mb-3">
              {[
                { emoji: '🤖', text: 'Qui es-tu ?', hint: 'Identité' },
                { emoji: '🩺', text: 'C\'est quoi le diabète ?', hint: 'Santé' },
                { emoji: '⚠️', text: 'Que faire en cas d\'AVC ?', hint: 'Urgence' },
                { emoji: '🔢', text: '15 + 27', hint: 'Calcul' },
                { emoji: '🌍', text: 'Capitale de la France', hint: 'Géo' },
                { emoji: '💡', text: 'Parle-moi de la lumière', hint: 'Science' },
              ].map((card, i) => (
                <div
                  key={i}
                  className="p-3 cursor-pointer transition-all active:scale-95 hover:bg-[var(--g2)]"
                  style={{
                    background: 'var(--g1)',
                    border: 'var(--bw, 0.5px) solid var(--b2)',
                    borderRadius: 'var(--r-card, 14px)',
                  }}
                  onClick={() => { setText(''); send(card.text) }}
                  role="button"
                >
                  <div className="text-[18px] mb-1">{card.emoji}</div>
                  <div className="text-[11px] text-[var(--t2)] leading-tight">{card.text}</div>
                  <div className="text-[8px] text-[var(--t4)] mt-1">{card.hint}</div>
                </div>
              ))}
            </div>

            <div className="text-[10px] text-[var(--t4)]">
              ou tapez votre question ci-dessous
            </div>
          </div>
        )}
        {messages.map(renderMessage)}

        {/* Indicateur de frappe */}
        {isProcessing && (
          <div className="msg msg--ka msg--typing">
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
        )}
      </div>

      {/* Intent bar */}
      <div className="mx-4 mb-2 flex shrink-0 cursor-text items-center gap-[10px] px-[14px] py-[11px]"
        style={{
          background: 'rgba(45,212,191,0.06)',
          border: 'var(--bw, 0.5px) solid var(--b2)',
          borderRadius: 'var(--r-pill, 26px)',
        }}
        onClick={() => setShowKbd(true)}
      >
        <div className="h-8 w-8 shrink-0 rounded-full bg-[var(--soul-d)] flex items-center justify-center"
          style={{ border: '0.5px solid var(--soul-g)', animation: 'breathe 4s ease-in-out infinite' }}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <circle cx="8" cy="8" r="7" fill="rgba(45,212,191,0.85)"/>
            <ellipse cx="6" cy="5.5" rx="3" ry="2.2" fill="rgba(255,255,255,0.28)"/>
          </svg>
        </div>
        <div className="flex-1 text-[15px] text-[var(--t1)] min-h-[20px] flex items-center break-all">
          {text}
          <span className="inline-block w-[1.5px] h-[18px] bg-[var(--soul)] ml-[1px] shrink-0"
            style={{ animation: 'blink 1.1s ease-in-out infinite' }} />
        </div>
        <div
          className={`h-8 w-8 shrink-0 rounded-full flex items-center justify-center cursor-pointer transition-all active:scale-[.88] ${text.length > 0 ? 'opacity-100' : 'opacity-0'}`}
          style={{ background: 'var(--soul-d)', border: '0.5px solid var(--soul-g)' }}
          onClick={sendMsg}
          role="button"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
            <path d="M1.5 7h11M8 2.5l5 4.5-5 4.5" stroke="rgba(175,169,236,0.9)" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>

      {/* Suggestions */}
      <div className="flex gap-[7px] px-4 pb-[7px] overflow-x-auto hide-scrollbar shrink-0">
        {getSuggestions(text).map((w, i) => (
          <div
            key={w}
            className={`shrink-0 px-3 py-[5px] text-[12.5px] cursor-pointer whitespace-nowrap transition-all active:scale-[.93] ${
              i === 0
                ? 'bg-[var(--soul-d)] text-[var(--soul-l)]'
                : 'bg-[var(--g1)] text-[var(--t2)]'
            }`}
            style={{
              borderRadius: 'var(--r-pill, 18px)',
              border: i === 0 ? 'var(--bw, 0.5px) solid var(--soul-g)' : 'var(--bw, 0.5px) solid var(--b2)',
            }}
            onClick={() => {
              const words = text.trim().split(' ')
              words[words.length - 1] = w
              setText(words.join(' ') + ' ')
            }}
          >
            {w}
          </div>
        ))}
      </div>

      {/* Keyboard */}
      {showKbd && !emoji && (
        <div className="kbd shrink-0">
          {/* Toolbar */}
          <div className="flex gap-[5px] px-[3px] pb-2">
            <div className={`tbn ${voice ? 'tbn--on' : ''}`} onClick={toggleVoice} role="button">
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <rect x="4" y="1" width="6" height="8" rx="3" stroke="currentColor" strokeWidth="1.2" fill="none"/>
                <path d="M2 7c0 2.8 2.2 5 5 5s5-2.2 5-5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" fill="none"/>
                <line x1="7" y1="12" x2="7" y2="14" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
              </svg>
              <span>{voice ? '● Écoute…' : 'Voix'}</span>
            </div>
            <div className="tbn" onClick={() => setEmoji(!emoji)} role="button">
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.2" fill="none"/>
                <circle cx="4.8" cy="5.8" r=".85" fill="currentColor"/>
                <circle cx="9.2" cy="5.8" r=".85" fill="currentColor"/>
                <path d="M4.2 9c.7 1 1.8 1.6 2.8 1.6s2.1-.6 2.8-1.6" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" fill="none"/>
              </svg>
              <span>Emoji</span>
            </div>
            <div className="tbn" onClick={() => {
              const pastes = ['Qui es-tu ?','C\'est quoi le diabète ?','Que faire en cas d\'AVC ?','Qui a découvert la pénicilline ?']
              setText(prev => prev + pastes[Math.floor(Math.random() * pastes.length)])
            }} role="button">
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <rect x="2" y="4" width="10" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.2" fill="none"/>
                <path d="M5 4V3a2 2 0 014 0v1" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" fill="none"/>
              </svg>
              <span>Coller</span>
            </div>
            <div className="tbn tbn--xs" onClick={() => setText('')} role="button">
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M2 7h10M8 3.5l4 3.5-4 3.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
              </svg>
            </div>
          </div>

          {/* Key rows */}
          <div className="row row--n" id="rn">
            {KEY_ROWS[0].map(([c, a]) => {
              const d = altMode ? (a || c) : c
              return renderKey(d, altMode ? c : a, 32, '', () => handleKeyPress(d))
            })}
          </div>
          {[1, 2].map((ri) => (
            <div className="row" key={ri}>
              {KEY_ROWS[ri].map(([c, a]) => {
                const d = (shift || lock) ? c.toUpperCase() : c
                return renderKey(d, a, 33, '', () => {
                  handleKeyPress(d)
                  if (shift && !lock) { setShift(false) }
                })
              })}
            </div>
          ))}
          <div className="row">
            <div
              className={`key key--sp ${(shift || lock) ? 'key--sft' : ''}`}
              style={{ width: '43px' }}
              onClick={handleShift}
              role="button"
            >
              <span className="key__c">{lock ? '⇪' : '⇧'}</span>
            </div>
            {KEY_ROWS[3].map(([c, a]) => {
              const d = (shift || lock) ? c.toUpperCase() : c
              return renderKey(d, a, 35, '', () => {
                handleKeyPress(d)
                if (shift && !lock) { setShift(false) }
              })
            })}
            <div className="key key--sp key--del" style={{ width: '43px' }}
              onClick={() => setText(prev => prev.slice(0, -1))} role="button">
              <span className="key__c">⌫</span>
            </div>
          </div>
          <div className="row">
            <div className="key key--sp" style={{ width: '49px' }}
              onClick={() => setAltMode(!altMode)} role="button">
              <span className="key__c">{altMode ? 'ABC' : '123'}</span>
            </div>
            <div className="key key--spc" onClick={() => handleKeyPress(' ')} role="button">
              <span className="key__c">espace</span>
            </div>
            <div className="key key--life" style={{ width: '82px' }} onClick={sendMsg} role="button">
              <span className="key__c">{isProcessing ? '…' : 'Envoyer'}</span>
            </div>
          </div>
        </div>
      )}

      {/* Emoji panel */}
      <div className={`ep ${emoji ? 'ep--on' : ''}`}>
        {EMOJIS.map(e => (
          <div key={e} className="eb" onClick={() => { handleKeyPress(e) }} role="button">
            {e}
          </div>
        ))}
      </div>

      <style>{`
        .msg {
          border-radius: 18px; padding: 10px 14px;
          font-size: 14.5px; line-height: 1.42;
          max-width: 252px;
          animation: fu 0.25s ease-out;
        }
        .msg--t {
          background: var(--g2); border: 0.5px solid var(--b2);
          color: var(--t1);
          border-bottom-left-radius: 4px;
          align-self: flex-start;
        }
        .msg--m {
          background: var(--soul-d); border: 0.5px solid var(--soul-g);
          color: var(--t1);
          border-bottom-right-radius: 4px;
          align-self: flex-end;
        }
        .msg--ka {
          align-self: flex-start;
          background: var(--g1); border: 0.5px solid var(--b1);
          color: var(--t2);
          border-radius: 18px;
          max-width: 280px;
          display: flex;
          align-items: flex-start;
          gap: 8px;
        }
        .msg--typing {
          gap: 4px;
          padding: 14px 18px;
        }
        .msg__ka__dot {
          width: 6px; height: 6px;
          background: var(--teal);
          border-radius: 50%;
          margin-top: 6px;
          flex-shrink: 0;
        }
        .typing-dot {
          width: 6px; height: 6px;
          background: var(--t3);
          border-radius: 50%;
          animation: typing-bounce 1.2s ease-in-out infinite;
        }
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typing-bounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40% { transform: scale(1); opacity: 0.9; }
        }
        .kbd {
          background: linear-gradient(to bottom, rgba(22,20,38,0.98), rgba(16,14,30,1));
          border-top: 0.5px solid rgba(45,212,191,0.12);
          padding: 8px 5px calc(7px + var(--sb));
        }
        .tbn {
          flex: 1; height: 33px; border-radius: 9px;
          background: var(--g1); border: 0.5px solid var(--b1);
          display: flex; align-items: center; justify-content: center; gap: 4px;
          cursor: pointer; color: var(--t3); font-size: 12px;
          transition: all 0.1s;
        }
        .tbn:active { background: var(--g2); transform: scale(0.95); }
        .tbn--on { background: var(--soul-d); border-color: var(--soul-g); color: var(--soul-l); }
        .tbn--xs { flex: 0.5; }
        .row { display: flex; justify-content: center; gap: 4.5px; margin-bottom: 7px; }
        .row--n .key { height: 40px; border-radius: 9px; }
        .row--n .key__c { font-size: 14.5px; }
        .key {
          height: 46px; min-width: 30px; border-radius: 11px;
          background: var(--g2); border: 0.5px solid var(--b2);
          display: flex; flex-direction: column; align-items: center; justify-content: center;
          cursor: pointer; position: relative; overflow: hidden;
          flex-shrink: 0; touch-action: manipulation;
        }
        .key:active, .key--p { background: rgba(45,212,191,0.28) !important; transform: scale(0.91) !important; }
        .key__c { font-size: 17px; color: var(--t1); line-height: 1; font-weight: 400; }
        .key__a { font-size: 8.5px; color: rgba(230,255,250,0.22); line-height: 1; margin-top: 2px; }
        .key--sp { background: var(--g1); border-color: var(--b1); }
        .key--sp .key__c { font-size: 12.5px; color: var(--t3); }
        .key--life { background: var(--life-d); border-color: var(--life-g); }
        .key--life .key__c { color: var(--life); font-size: 12.5px; font-weight: 500; }
        .key--sft { background: rgba(45,212,191,0.16) !important; border-color: var(--soul) !important; }
        .key--sft .key__c { color: var(--soul-l); }
        .key--del .key__c { font-size: 13px; color: var(--t3); }
        .key--spc {
          height: 44px; border-radius: 22px;
          background: rgba(45,212,191,0.10); border-color: rgba(45,212,191,0.09);
        }
        .key--spc .key__c { font-size: 12.5px; color: var(--t4); letter-spacing: 0.06em; }
        .ep {
          display: none; flex-wrap: wrap; gap: 3px; padding: 9px 7px;
          max-height: 148px; overflow-y: auto;
          background: linear-gradient(to bottom, rgba(22,20,38,0.98), rgba(16,14,30,1));
          border-top: 0.5px solid rgba(45,212,191,0.12);
        }
        .ep--on { display: flex; }
        .eb { font-size: 25px; cursor: pointer; padding: 4px; border-radius: 8px; transition: background 0.08s; }
        .eb:active { background: var(--g2); }
        @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0; } }
        @keyframes fu { from { opacity: 0; transform: translateY(7px); } to { opacity: 1; transform: translateY(0); } }

        /* ── Thème V2 : coins angulaires, bordures 1px ── */
        [data-theme="v2"] .key { border-radius: 0 !important; border-width: 1px !important; }
        [data-theme="v2"] .key--spc { border-radius: 0 !important; }
        [data-theme="v2"] .tbn { border-radius: 1px !important; }
        [data-theme="v2"] .msg { border-radius: 0 !important; border-width: 1px !important; }
        [data-theme="v2"] .msg--t { border-bottom-left-radius: 0 !important; }
        [data-theme="v2"] .msg--m { border-bottom-right-radius: 0 !important; }
        [data-theme="v2"] .msg--ka { border-radius: 0 !important; }
        [data-theme="v2"] .msg__ka__dot { border-radius: 0 !important; }
        [data-theme="v2"] .typing-dot { border-radius: 0 !important; }
        [data-theme="v2"] .kbd { border-top-width: 1px !important; }
        [data-theme="v2"] .ep { border-top-width: 1px !important; }
        [data-theme="v2"] .eb { border-radius: 0 !important; }
        [data-theme="v2"] .key--life { border-width: 1px !important; }
      `}</style>
    </>
  )
}