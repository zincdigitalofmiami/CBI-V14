import { BrowserRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import SentimentPage from './pages/SentimentPage'
import StrategyPage from './pages/StrategyPage'
import LegislationPage from './pages/LegislationPage'
import './App.css'

function Navigation() {
  const links = [
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/sentiment', label: 'Sentiment' },
    { to: '/strategy', label: 'Strategy' },
    { to: '/legislation', label: 'Legislation' },
  ]

  return (
    <header className="cbi-header">
      <div className="cbi-header__brand">CBI‑V14</div>
      <nav className="cbi-header__nav">
        {links.map(link => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `cbi-header__nav-link${isActive ? ' cbi-header__nav-link--active' : ''}`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="cbi-app">
        <Navigation />
        <main className="cbi-app__main">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/sentiment" element={<SentimentPage />} />
            <Route path="/strategy" element={<StrategyPage />} />
            <Route path="/legislation" element={<LegislationPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

