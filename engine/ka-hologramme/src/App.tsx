import { useState, useEffect } from 'react';
import { Capacitor } from '@capacitor/core';
import { Splash } from './screens/Splash';
import { HomeScreen } from './screens/HomeScreen';
import { ChatScreen } from './screens/ChatScreen';
import { ProfileScreen } from './screens/ProfileScreen';
import { CreateScreen } from './screens/CreateScreen';
import { ErrorBoundary } from './components/ErrorBoundary';
import type { Screen, Hologramme } from './types';

export default function App() {
  const [splash, setSplash] = useState(true);
  const [screen, setScreen] = useState<Screen>('home');
  const [hologrammeActif, setHologrammeActif] = useState<Hologramme | null>(null);
  const [kaVoice, setKaVoice] = useState(true);

  // Detection app native (Capacitor) : vrai telephone / emulateur.
  // En natif, la vraie barre Android s'affiche — on masque la fausse.
  const isNative = Capacitor.isNativePlatform();

  useEffect(() => {
    const t = setTimeout(() => setSplash(false), 4000);
    return () => clearTimeout(t);
  }, []);

  // Gestion du bouton back Android
  useEffect(() => {
    if (!isNative) return;
    let backCount = 0;

    const handleBack = (e: PopStateEvent) => {
      e.preventDefault();
      if (screen === 'home') {
        backCount++;
        if (backCount >= 2) {
          // Quitter l'app (comportement natif)
          (window as any).Capacitor?.Plugins?.App?.exitApp?.();
        } else {
          // Premier back -> message
          setTimeout(() => { backCount = 0; }, 2000);
        }
      } else {
        setScreen('home');
      }
    };

    window.addEventListener('popstate', handleBack);
    return () => window.removeEventListener('popstate', handleBack);
  }, [isNative, screen]);

  if (splash) return <Splash />;

  return (
    <ErrorBoundary>
      <div className={`phone${isNative ? ' native' : ''}`}>
        {/* Orbs */}
        <div className="orb o1" /><div className="orb o2" /><div className="orb o3" />

        {/* Status */}
        <div className="sb">
          <span className="sb__t">9:41</span>
          <span className="sb__r">{kaVoice ? '🎤 KA' : 'KA'}</span>
        </div>

        {/* Screen */}
        <div className="screen">
          {screen === 'home' && <HomeScreen onNavigate={setScreen} onSelectH={setHologrammeActif} />}
          {screen === 'create' && <CreateScreen onBack={() => setScreen('home')} />}
          {screen === 'chat' && hologrammeActif && (
            <ChatScreen hologramme={hologrammeActif} onBack={() => setScreen('home')} kaVoice={kaVoice} />
          )}
          {screen === 'profile' && (
            <ProfileScreen
              onNavigate={setScreen}
              kaVoice={kaVoice}
              onToggleVoice={() => setKaVoice((v) => !v)}
            />
          )}
        </div>

        {/* KA presence */}
        <div className={`ka-indicator ${kaVoice ? '' : 'mute'}`}>
          <span className="ka-dot" />
          KA present{kaVoice ? ' · Mode vocal' : ' · Silencieux'}
        </div>

        {/* Nav */}
        <nav className="nav">
          {(['home', 'chat', 'profile'] as const).map((s) => (
            <button
              key={s}
              className={`nav__item ${screen === s ? 'on' : ''}`}
              onClick={() => setScreen(s)}
            >
              {s === 'home' && (
                <svg viewBox="0 0 24 24"><path d="M3 13h1v7c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-7h1a1 1 0 0 0 .7-1.7l-9-8.5a1 1 0 0 0-1.4 0l-9 8.5A1 1 0 0 0 3 13z" /></svg>
              )}
              {s === 'chat' && (
                <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z" /></svg>
              )}
              {s === 'profile' && (
                <svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" /></svg>
              )}
              <span>{s === 'home' ? 'Accueil' : s === 'chat' ? 'Chat' : 'Profil'}</span>
            </button>
          ))}
        </nav>
      </div>
    </ErrorBoundary>
  );
}