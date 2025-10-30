'use client'

import React from 'react'

interface InstitutionalGaugeProps {
  value: number // 0-100
  signal: 'BUY' | 'WAIT' | 'MONITOR'
  confidence: number
  size?: 'sm' | 'md' | 'lg'
}

export const InstitutionalGauge: React.FC<InstitutionalGaugeProps> = ({ 
  value, 
  signal, 
  confidence, 
  size = 'md' 
}) => {
  const radius = size === 'lg' ? 80 : size === 'md' ? 60 : 40
  const strokeWidth = size === 'lg' ? 4 : size === 'md' ? 3 : 2
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (value / 100) * circumference

  const getColors = (signal: 'BUY' | 'WAIT' | 'MONITOR') => {
    switch (signal) {
      case 'BUY': return {
        gradientStart: '#0055FF', // Electric cobalt
        gradientEnd: '#00C8FF',   // Electric azure
        glow: '#0055FF',
        text: 'text-buy-primary'
      }
      case 'WAIT': return {
        gradientStart: '#FF5D00', // Fiery orange
        gradientEnd: '#E50000',   // Intense scarlet
        glow: '#FF5D00',
        text: 'text-sell-caution'
      }
      case 'MONITOR': return {
        gradientStart: '#0055FF', // Electric cobalt - BLUE for high confidence
        gradientEnd: '#00C8FF',   // Electric azure
        glow: '#0055FF',
        text: 'text-buy-primary'
      }
      default: return {
        gradientStart: '#9099a6',
        gradientEnd: '#6b7280',
        glow: 'transparent',
        text: 'text-text-secondary'
      }
    }
  }

  const colors = getColors(signal)

  return (
    <div className="relative flex items-center justify-center" style={{ width: radius * 2.5, height: radius * 2.5 }}>
      <svg 
        className="transform -rotate-90 filter drop-shadow-lg" 
        width={radius * 2.5} 
        height={radius * 2.5}
        style={{
          filter: `drop-shadow(0 0 12px ${colors.glow}40)`
        }}
      >
        {/* Background circle */}
        <circle
          className="text-background-tertiary"
          strokeWidth={strokeWidth}
          stroke="currentColor"
          fill="transparent"
          r={radius}
          cx={radius * 1.25}
          cy={radius * 1.25}
          opacity={0.2}
        />
        
        {/* Progress circle with gradient */}
        <circle
          strokeWidth={strokeWidth}
          fill="transparent"
          r={radius}
          cx={radius * 1.25}
          cy={radius * 1.25}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          stroke={`url(#${signal}-gradient)`}
          style={{
            transition: 'stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        />
        
        {/* Gradient definitions */}
        <defs>
          <linearGradient id={`${signal}-gradient`} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={colors.gradientStart} />
            <stop offset="100%" stopColor={colors.gradientEnd} />
          </linearGradient>
          
          {/* Glowing effect */}
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
            <feMerge> 
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
      </svg>
      
      {/* Center content */}
      <div className="absolute text-center">
        <div className={`text-3xl font-light ${colors.text} tracking-wider`}>
          {value.toFixed(0)}%
        </div>
        <div className="text-xs text-text-tertiary uppercase tracking-widest font-mono">
          Confidence
        </div>
        <div className={`text-sm font-semibold ${colors.text} mt-1 tracking-wide`}>
          {signal}
        </div>
      </div>
    </div>
  )
}