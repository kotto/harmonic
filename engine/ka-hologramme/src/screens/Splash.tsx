import { useEffect, useState } from 'react';

export function Splash() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setShow(true), 100);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="phone" style={{ alignItems: 'center', justifyContent: 'center', background: 'radial-gradient(ellipse at 48% 16%, #2a2048 0%, #18163a 42%, #0e0e1a 100%)' }}>
      <div style={{
        position: 'absolute', width: 400, height: 400, top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
        borderRadius: '50%', background: 'radial-gradient(circle,rgba(155,148,255,.15) 0%,transparent 68%)',
        animation: 'pulse 3s ease-in-out infinite',
      }} />
      <div style={{
        opacity: show ? 1 : 0, transform: show ? 'scale(1)' : 'scale(.8)',
        filter: show ? 'blur(0)' : 'blur(8px)', transition: 'all 2s ease-out',
        display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 2,
      }}>
        <img src="/logo.jpg" alt="KA" style={{ width: 80, height: 80, borderRadius: 20, objectFit: 'contain' }} />
        <div style={{ fontSize: 11, letterSpacing: 6, textTransform: 'uppercase', color: 'var(--t3)', marginTop: 16 }}>
          Votre spécialiste harmonique
        </div>
      </div>
      <div style={{
        position: 'absolute', bottom: 50, display: 'flex', alignItems: 'center', gap: 8,
        fontSize: 11, color: 'var(--t4)', opacity: show ? 1 : 0, transition: 'opacity 1s 2s',
      }}>
        <span>Initialisation</span>
        {[0,1,2].map(i => (
          <div key={i} style={{
            width: 4, height: 4, borderRadius: '50%', background: 'var(--soul-g)',
            animation: 'pulse 1.2s ease-in-out infinite',
            animationDelay: `${i * 0.2}s`,
          }} />
        ))}
      </div>
    </div>
  );
}