import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './app.css'
import Finance from './Finance.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Finance />
  </StrictMode>,
)
