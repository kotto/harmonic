import { useNavigate } from 'react-router-dom'
import type { ColorAccent } from '@/types'

interface SpaceHeaderProps {
  title: string
  badge?: string
  badgeColor?: ColorAccent
  backPath?: string
  rightAction?: React.ReactNode
}

const ACCENT_COLORS: Record<ColorAccent, string> = {
  soul: 'var(--soul-l)',
  life: 'var(--life)',
  wisdom: 'var(--wisdom)',
  rose: 'var(--rose)',
  sky: 'var(--sky)',
  coral: 'var(--coral)',
}

export default function SpaceHeader({
  title,
  badge,
  badgeColor = 'soul',
  backPath = '/',
  rightAction,
}: SpaceHeaderProps) {
  const navigate = useNavigate()

  return (
    <div className="flex shrink-0 items-center justify-between px-[22px] pt-[14px]">
      <div
        className="cursor-pointer rounded-xl px-2 py-1 text-[13px] text-[var(--t3)] transition-colors active:bg-[var(--g2)]"
        onClick={() => navigate(backPath)}
        role="button"
      >
        ‹ <span className="hud-title">{title}</span>
      </div>
      {badge && (
        <div
          className="text-[11px] tracking-[.08em] hud-title"
          style={{ color: ACCENT_COLORS[badgeColor], opacity: 0.65 }}
        >
          {badge}
        </div>
      )}
      <div style={{ width: rightAction ? 'auto' : '48px' }}>
        {rightAction}
      </div>
    </div>
  )
}