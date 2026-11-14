import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout/Layout'
import { AccountsPage } from './pages/AccountsPage'
import { CategoriesPage } from './pages/CategoriesPage'
import { DistributionPage } from './pages/DistributionPage'
import { OverviewPage } from './pages/OverviewPage'
import { RecordsPage } from './pages/RecordsPage'
import { TimeSeriesPage } from './pages/TimeSeriesPage'
import { UploadPage } from './pages/UploadPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/overview" element={<OverviewPage />} />
        <Route path="/time-series" element={<TimeSeriesPage />} />
        <Route path="/distribution" element={<DistributionPage />} />
        <Route path="/records" element={<RecordsPage />} />
        <Route path="/categories" element={<CategoriesPage />} />
        <Route path="/accounts" element={<AccountsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

export default App
