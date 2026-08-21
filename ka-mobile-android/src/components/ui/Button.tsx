import type { ColorAccent } from '@/types'

interface ButtonProps {
  children: React.ReactNode
  color?: ColorAccent | 'ghost'
  onClick?: () => void
  className?: string
}

const BTN_STYLES: Record<string, string> = {
  soul: 'bg-[var(--soul-d)] border-[var(--soul-g)] text-[var(--soul-l)]',
  life: 'bg-[var(--life-d)] border-[var(--life-g)] text-[var(--life)]',
  wisdom: 'bg-[var(--wisdom-d)] border-[var(--wisdom-g)] text-[var(--wisdom)]',
  rose: 'bg-[var(--rose-d)] border-[var(--rose-g)] text-[var(--rose)]',
  sky: 'bg-[var(--sky-d)] border-[var(--sky-g)] text-[var(--sky)]',
  ghost: 'bg-none border-none text-[var(--t3)] text-xs',
}

export default function Button({ children, color = 'soul', onClick, className = '' }: ButtonProps) {
  const isGhost = color === 'ghost'
  return (
    <div
      onClick={onClick}
      className={`${isGhost ? '' : 'border-[--bw,0.5px]'} px-[13px] py-[13px] text-center text-[13px] font-normal tracking-[.02em] cursor-pointer transition-all active:scale-[.97] ${isGhost ? BTN_STYLES[color] : BTN_STYLES[color]} ${className}`}
      style={{
        borderRadius: 'var(--r-button, 26px)',
        borderWidth: isGhost ? 0 : 'var(--bw, 0.5px)',
      }}
      role="button"
    >
      {children}
    </div>
  )
}