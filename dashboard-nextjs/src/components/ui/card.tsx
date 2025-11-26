import { clsx } from 'clsx'
import { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
}

export function Card({ children, className }: CardProps) {
  return (
    <div className={clsx(
      'bg-background-secondary border border-border-primary rounded-lg',
      className
    )}>
      {children}
    </div>
  )
}

