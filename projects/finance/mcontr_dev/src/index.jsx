import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter as Router, Routes, Route} from 'react-router-dom'
import MainPage from './main.jsx'
import InfoPage from './info.jsx'
import GuessPage from './guess.jsx'
import RandomPage from './random.jsx'
import WeatherPage from './weather.jsx'
import FinancePage from './finance.jsx'


createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Router>
      <Routes>
        <Route path='/' element={<MainPage />}/>
        <Route path='/info' element={<InfoPage />}/>
        <Route path='/guess' element={<GuessPage />}/>
        <Route path='/random' element={<RandomPage />}/>
        <Route path='/weather' element={<WeatherPage />}/>
        <Route path='/finance' element={<FinancePage />}/>
      </Routes>
    </Router>
  </StrictMode>
)
