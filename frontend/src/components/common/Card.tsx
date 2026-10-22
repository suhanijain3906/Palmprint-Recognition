import type { ReactNode } from 'react'

interface CardProps {
  title?: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
  className?: string
}

export function Card({ title, subtitle, actions, children, className = '' }: CardProps) {
  return (
    <section className={`card p-5 ${className}`}>
      {(title || actions) && (
        <header className="mb-4 flex items-start justify-between gap-3">
          <div>
            {title && <h2 className="text-base font-semibold text-navy-900">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {actions}
        </header>
      )}
      {children}
    </section>
  )
}

export default Card
