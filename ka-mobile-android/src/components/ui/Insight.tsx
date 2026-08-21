import type { ColorAccent } from '@/types'

interface InsightProps {
  children: React.ReactNode
  label: string
  color?: ColorAccent
}

const BORDER_COLORS: Record<ColorAccent, string> = {
  soul: 'var(--soul)',
  life: 'var(--life)',
  wisdom: 'var(--wisdom)',
  rose: 'var(--rose)',
  sky: 'var(--sky)',
  coral: 'var(--coral)',
}

export default function Insight({ children, label, color = 'soul' }: InsightProps) {
  return (
    <div
      className="bg-[var(--g1)] px-[14px] py-[12px] mb-3"
      style={{
        borderRadius: 'var(--r-insight, 14px)',
        border: 'var(--bw, 0.5px) solid var(--b2)',
        borderLeft: `2px solid ${BORDER_COLORS[color]}`,
      }}
    >
      <div className="mb-1 text-[9.5px] tracking-[.1em] text-[var(--t4)] uppercase">{label}</div>
      <div className="text-[13px] leading-[1.5] text-[var(--t2)]">{children}</div>
    </div>
  )
}