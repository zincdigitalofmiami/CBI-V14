import { clsx } from 'clsx'
import { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'secondary' | 'outline' | 'destructive'
  size?: 'sm' | 'default'
  className?: string
}

export function Badge({ children, variant = 'default', size = 'default', className }: BadgeProps) {
  const baseStyles = 'inline-flex items-center rounded-full font-medium'
  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    default: 'px-2.5 py-0.5 text-xs',
  }
  
  const variantStyles = {
    default: 'bg-background-tertiary text-text-primary border border-border-primary',
    success: 'bg-green-500/20 text-green-400 border border-green-500/30',
    warning: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
    danger: 'bg-red-500/20 text-red-400 border border-red-500/30',
    info: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
    secondary: 'bg-background-tertiary text-text-secondary border border-border-secondary',
    outline: 'bg-transparent text-text-primary border border-border-primary',
    destructive: 'bg-red-500/20 text-red-400 border border-red-500/30',
  }

  return (
    <span className={clsx(baseStyles, sizeStyles[size], variantStyles[variant], className)}>
      {children}
    </span>
  )
}

