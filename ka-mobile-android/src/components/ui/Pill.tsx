import type { ColorAccent } from '@/types'

interface PillProps {
  children: React.ReactNode
  color?: ColorAccent
  size?: 'sm' | 'xs'
  className?: string
}

const PILL_STYLES: Record<ColorAccent, string> = {
  soul: 'bg-[var(--soul-d)] border-[var(--soul-g)] text-[var(--soul-l)]',
  life: 'bg-[var(--life-d)] border-[var(--life-g)] text-[var(--life)]',
  wisdom: 'bg-[var(--wisdom-d)] border-[var(--wisdom-g)] text-[var(--wisdom)]',
  rose: 'bg-[var(--rose-d)] border-[var(--rose-g)] text-[var(--rose)]',
  sky: 'bg-[var(--sky-d)] border-[var(--sky-g)] text-[var(--sky)]',
  coral: 'bg-[var(--coral)] border-[var(--coral)] text-white',
}

const PILL_SIZES: Record<string, string> = {
  sm: 'text-[10.5px] px-[10px] py-[4px]',
  xs: 'text-[8.5px] px-[6px] py-[2px]',
}

export default function Pill({ children, color = 'soul', size = 'sm', className = '' }: PillProps) {
  return (
    <span
      className={`inline-flex items-center font-medium border-[--bw,0.5px] ${PILL_STYLES[color]} ${PILL_SIZES[size]} ${className}`}
      style={{
        borderRadius: 'var(--r-pill, 20px)',
        borderWidth: 'var(--bw, 0.5px)',
      }}
    >
      {children}
    </span>
  )
}