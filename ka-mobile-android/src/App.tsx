import { useState, useEffect } from 'react'
import { useNavigate, useLocation, Routes, Route } from 'react-router-dom'
import DeviceFrame from './components/layout/DeviceFrame'
import MorePanel from './components/layout/MorePanel'
import HomeScreen from './screens/HomeScreen'
import MessagesScreen from './screens/MessagesScreen'
import CallScreen from './screens/CallScreen'
import MemoryScreen from './screens/MemoryScreen'
import PrepareScreen from './screens/PrepareScreen'
import JourneyScreen from './screens/JourneyScreen'
import RelationScreen from './screens/RelationScreen'
import CaptureScreen from './screens/CaptureScreen'
import DecideScreen from './screens/DecideScreen'
import HealthScreen from './screens/HealthScreen'
import StorageScreen from './screens/StorageScreen'
import HologramScreen from './screens/HologramScreen'
import CodeScreen from './screens/CodeScreen'
import CameraScreen from './screens/CameraScreen'
import VitalKaScreen from './screens/VitalKaScreen'
import OnboardingScreen from './screens/OnboardingScreen'
import DemoScreen from './screens/DemoScreen'

const NAV_ITEMS = [
  { path: '/', label: 'Accueil', icon: 'home' },
  { path: '/messages', label: 'Messages', icon: 'messages' },
  { path: '/memory', label: 'Mémoire', icon: 'memory' },
] as const

const CALL_PATH = '/call'
const FULLSCREEN_PATHS = new Set([CALL_PATH, '/camera', '/demo', '/onboarding'])
const HIDE_NAV_PATHS = new Set([CALL_PATH])

function NavIcon({ icon, active }: { icon: string; active: boolean }) {
  const c = active ? 'rgba(45,212,191,0.9)' : 'rgba(230,255,250,0.45)'
  const sw = '1.5'

  switch (icon) {
    case 'home':
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M3 12L12 4l9 8M5 10v9a1 1 0 001 1h4v-5h4v5h4a1 1 0 001-1v-9" stroke={c} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" fill="none"/>
        </svg>
      )
    case 'messages':
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 4h16a1 1 0 011 1v11a1 1 0 01-1 1H7l-4 4V5a1 1 0 011-1z" stroke={c} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round" fill="none"/>
        </svg>
      )
    case 'memory':
      return (
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="9" stroke={c} strokeWidth={sw} fill="none"/>
          <path d="M12 8v4l3 3" stroke={c} strokeWidth={sw} strokeLinecap="round" fill="none"/>
        </svg>
      )
    default:
      return null
  }
}

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()
  const [showMore, setShowMore] = useState(false)

  // Rediriger vers l'onboarding si l'utilisateur ne s'est jamais présenté
  useEffect(() => {
    const onboarded = localStorage.getItem('ka_user')
    if (!onboarded && location.pathname !== '/demo' && location.pathname !== '/onboarding') {
      navigate('/onboarding', { replace: true })
    }
  }, [])

  const showNav = !HIDE_NAV_PATHS.has(location.pathname)
  const inFullscreen = FULLSCREEN_PATHS.has(location.pathname)

  if (inFullscreen) {
    return (
      <DeviceFrame>
        <Routes>
          <Route path="/call" element={<CallScreen />} />
          <Route path="/camera" element={<CameraScreen />} />
          <Route path="/demo" element={<DemoScreen />} />
          <Route path="/onboarding" element={<OnboardingScreen />} />
        </Routes>
      </DeviceFrame>
    )
  }

  return (
    <DeviceFrame>
      <Routes>
        <Route path="/" element={<HomeScreen />} />
        <Route path="/messages" element={<MessagesScreen />} />
        <Route path="/memory" element={<MemoryScreen />} />
        <Route path="/prepare" element={<PrepareScreen />} />
        <Route path="/journey" element={<JourneyScreen />} />
        <Route path="/relation" element={<RelationScreen />} />
        <Route path="/capture" element={<CaptureScreen />} />
        <Route path="/decide" element={<DecideScreen />} />
        <Route path="/health" element={<HealthScreen />} />
        <Route path="/storage" element={<StorageScreen />} />
        <Route path="/hologram" element={<HologramScreen />} />
        <Route path="/code" element={<CodeScreen />} />
        <Route path="/vitalka" element={<VitalKaScreen />} />
        <Route path="*" element={<HomeScreen />} />
      </Routes>

      {showMore && <MorePanel onClose={() => setShowMore(false)} />}

      {showNav && (
        <nav className="flex shrink-0 items-center justify-around px-[22px] pb-[calc(10px+var(--sb))] pt-2"
          style={{ background: 'rgba(45,212,191,0.03)', borderTop: '0.5px solid var(--b1)' }}
          aria-label="Navigation principale"
        >
          {NAV_ITEMS.map((item) => {
            const active = location.pathname === item.path
            return (
              <button
                key={item.path}
                onClick={() => { setShowMore(false); navigate(item.path) }}
                className="flex flex-col items-center gap-1 cursor-pointer border-none bg-transparent px-2 py-1"
                aria-label={item.label}
              >
                <NavIcon icon={item.icon} active={active} />
                <span className="text-[10px] tracking-[.04em] transition-colors duration-150"
                  style={{ color: active ? 'var(--soul-l)' : 'var(--t4)' }}>
                  {item.label}
                </span>
              </button>
            )
          })}

          <button
            onClick={() => setShowMore(!showMore)}
            className="flex flex-col items-center gap-1 cursor-pointer border-none bg-transparent px-2 py-1"
            aria-label="Plus"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="5" cy="12" r="1.5" fill={showMore ? 'rgba(45,212,191,0.9)' : 'rgba(230,255,250,0.45)'}/>
              <circle cx="12" cy="12" r="1.5" fill={showMore ? 'rgba(45,212,191,0.9)' : 'rgba(230,255,250,0.45)'}/>
              <circle cx="19" cy="12" r="1.5" fill={showMore ? 'rgba(45,212,191,0.9)' : 'rgba(230,255,250,0.45)'}/>
            </svg>
            <span className="text-[10px] tracking-[.04em]"
              style={{ color: showMore ? 'var(--soul-l)' : 'var(--t4)' }}>
              Plus
            </span>
          </button>
        </nav>
      )}
    </DeviceFrame>
  )
}