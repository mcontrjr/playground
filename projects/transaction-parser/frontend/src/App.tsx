import { Navigate, Route, Routes } from 'react-router-dom'
import { useHasTransactions } from './api/hooks/useWorkspaceBootstrap'
import { Layout } from './components/Layout/Layout'
import { AccountsPage } from './pages/AccountsPage'
import { BudgetPage } from './pages/BudgetPage'
import { CategoriesPage } from './pages/CategoriesPage'
import { DistributionPage } from './pages/DistributionPage'
import { HistoryPage } from './pages/HistoryPage'
import { OverviewPage } from './pages/OverviewPage'
import { RecordsPage } from './pages/RecordsPage'
import { SplashPage } from './pages/SplashPage'
import { TimeSeriesPage } from './pages/TimeSeriesPage'
import { UploadPage } from './pages/UploadPage'
import { useWorkspace } from './workspace/WorkspaceContext'

function App() {
  const { workspace } = useWorkspace()
  const hasTransactions = useHasTransactions()

  // No workspace chosen yet: the splash screen is the whole app. Rendered
  // outside <Layout> so there is no sidebar to navigate with.
  if (workspace === null) {
    return <SplashPage />
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        {/* Categories stays available from the start: it is configuration,
            not a report, and editing it before the first import is a
            reasonable thing to want. */}
        <Route path="/categories" element={<CategoriesPage />} />
        {/* The rest have nothing to say without records — Accounts
            included, since accounts are discovered during ingest. Until
            the first upload they are hidden from the sidebar; guarding
            the routes too means a bookmarked or stale URL redirects to
            Upload instead of rendering an empty dashboard. */}
        {hasTransactions ? (
          <>
            <Route path="/overview" element={<OverviewPage />} />
            <Route path="/time-series" element={<TimeSeriesPage />} />
            <Route path="/distribution" element={<DistributionPage />} />
            <Route path="/records" element={<RecordsPage />} />
            <Route path="/budget" element={<BudgetPage />} />
            <Route path="/accounts" element={<AccountsPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </>
        ) : null}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}

export default App
