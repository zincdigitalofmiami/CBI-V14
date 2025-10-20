import './index.css'
import App from './App'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

const rootElement = document.getElementById('root')
if (!rootElement) throw new Error('Failed to find the root element')

const root = createRoot(rootElement)

root.render(
  <StrictMode>
    <App />
  </StrictMode>,
)
