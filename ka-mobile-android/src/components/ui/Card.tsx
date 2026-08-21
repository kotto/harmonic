interface CardProps {
  children: React.ReactNode
  raised?: boolean
  onClick?: () => void
  className?: string
  style?: React.CSSProperties
}

export default function Card({ children, raised, onClick, className = '', style }: CardProps) {
  return (
    <div
      onClick={onClick}
      className={`p-3 mb-2 ${raised ? 'bg-[var(--g2)]' : 'bg-[var(--g1)]'} ${onClick ? 'cursor-pointer' : ''} ${className}`}
      style={{
        borderRadius: 'var(--r-card, 14px)',
        border: 'var(--bw, 0.5px) solid var(--b2)',
        borderColor: raised ? 'var(--b3)' : 'var(--b2)',
        ...style,
      }}
    >
      {children}
    </div>
  )
}