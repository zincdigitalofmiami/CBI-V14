'use client'

import { useState } from 'react'
import RiskRadar from './RiskRadar'
import SubstitutionEconomics from './SubstitutionEconomics'
import CurrencyWaterfall from './CurrencyWaterfall'
import BiofuelMandates from './BiofuelMandates'

const analytics = [
  {
    id: 'risk-radar',
    name: 'Risk Radar',
    description: '6-factor risk analysis with feature importance',
    component: RiskRadar,
    icon: '🎯'
  },
  {
    id: 'substitution',
    name: 'Substitution Economics',
    description: 'Soy vs Palm vs Canola cost analysis',
    component: SubstitutionEconomics,
    icon: '⚖️'
  },
  {
    id: 'currency',
    name: 'Currency Waterfall',
    description: 'FX impact breakdown (USD/BRL/CNY/ARS)',
    component: CurrencyWaterfall,
    icon: '💱'
  },
  {
    id: 'biofuel',
    name: 'Biofuel Mandates',
    description: 'Policy impact on vegetable oil demand',
    component: BiofuelMandates,
    icon: '🛢️'
  }
]

export default function AdvancedAnalyticsCarousel() {
  const [activeTab, setActiveTab] = useState(0)
  
  const ActiveComponent = analytics[activeTab].component

  return (
    <div className="bg-background-secondary rounded-lg border border-gray-800">
      {/* Tab Navigation */}
      <div className="flex border-b border-gray-700">
        {analytics.map((analytic, index) => (
          <button
            key={analytic.id}
            onClick={() => setActiveTab(index)}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === index
                ? 'bg-background-tertiary text-text-primary border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-gray-300 hover:bg-background-tertiary/50'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <span>{analytic.icon}</span>
              <span className="hidden sm:inline">{analytic.name}</span>
            </div>
            <div className="text-xs text-gray-500 mt-1 hidden lg:block">
              {analytic.description}
            </div>
          </button>
        ))}
      </div>

      {/* Active Component */}
      <div className="p-0">
        <ActiveComponent />
      </div>

      {/* Tab Indicators (Mobile) */}
      <div className="flex justify-center gap-2 p-4 sm:hidden">
        {analytics.map((_, index) => (
          <button
            key={index}
            onClick={() => setActiveTab(index)}
            className={`w-2 h-2 rounded-full transition-colors ${
              activeTab === index ? 'bg-blue-400' : 'bg-gray-600'
            }`}
          />
        ))}
      </div>
    </div>
  )
}
