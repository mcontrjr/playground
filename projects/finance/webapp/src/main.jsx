import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import Finance from './Finance.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Finance />
  </StrictMode>,
)
