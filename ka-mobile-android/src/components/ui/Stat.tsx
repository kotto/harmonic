import type { Stat as StatType } from '@/types'

interface StatProps {
  stat: StatType
}

export default function Stat({ stat }: StatProps) {
  const valClass = stat.color === 'green'
    ? 'text-[var(--life)]'
    : stat.color === 'red'
    ? 'text-[var(--coral)]'
    : stat.color === 'accent'
    ? 'text-[var(--soul-l)]'
    : 'text-[var(--t1)]'

  return (
    <div
      className="bg-[var(--g1)] px-[6px] py-[10px] text-center"
      style={{
        borderRadius: 'var(--r-card, 12px)',
        border: 'var(--bw, 0.5px) solid var(--b2)',
      }}
    >
      <div className={`text-[16px] font-medium leading-none ${valClass}`}>
        {stat.value}{stat.suffix || ''}
      </div>
      <div className="mt-[3px] text-[9.5px] text-[var(--t4)]">{stat.label}</div>
    </div>
  )
}