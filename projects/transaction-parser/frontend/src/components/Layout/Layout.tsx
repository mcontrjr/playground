import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useFailures } from '../../api/hooks/useFailures'
import { useHasTransactions } from '../../api/hooks/useWorkspaceBootstrap'
import logo from '../../assets/parser-logo.svg'
import { useWorkspace } from '../../workspace/WorkspaceContext'
import { ThemeSwitcher } from '../ThemeSwitcher/ThemeSwitcher'
import styles from './Layout.module.css'

interface NavItem {
  to: string
  label: string
  badge?: number
  /** Needs at least one record to be meaningful. */
  requiresRecords?: boolean
}

export function Layout({ children }: { children: ReactNode }) {
  const { data: failures } = useFailures(false)
  const { workspace, clearWorkspace } = useWorkspace()
  const hasTransactions = useHasTransactions()
  const unresolvedCount = failures?.length ?? 0

  const navItems: NavItem[] = [
    { to: '/', label: 'Upload', badge: unresolvedCount },
    { to: '/categories', label: 'Categories' },
    { to: '/overview', label: 'Overview', requiresRecords: true },
    { to: '/time-series', label: 'Time Series', requiresRecords: true },
    { to: '/distribution', label: 'Distribution', requiresRecords: true },
    { to: '/records', label: 'Records', requiresRecords: true },
    { to: '/budget', label: 'Budget', requiresRecords: true },
    { to: '/accounts', label: 'Accounts', requiresRecords: true },
    { to: '/history', label: 'History', requiresRecords: true },
  ]

  const visibleItems = navItems.filter(
    (item) => !item.requiresRecords || hasTransactions,
  )

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <img src={logo} alt="" className={styles.brandMark} width={28} height={28} />
          <span className={styles.brandName}>Parser</span>
        </div>

        {workspace && (
          <div className={styles.workspace}>
            <span className={styles.workspaceLabel}>Workspace</span>
            <span className={styles.workspaceName} title={workspace.slug}>
              {workspace.name}
            </span>
            <button
              type="button"
              className={styles.workspaceSwitch}
              onClick={clearWorkspace}
            >
              Switch
            </button>
          </div>
        )}

        <nav className={styles.nav} aria-label="Primary">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
              }
            >
              {item.label}
              {!!item.badge && item.badge > 0 && (
                <span className={styles.badge} aria-label={`${item.badge} unresolved failures`}>
                  {item.badge}
                </span>
              )}
            </NavLink>
          ))}
          {!hasTransactions && (
            <p className={styles.navHint}>
              Import a statement to unlock records, analytics and budget.
            </p>
          )}
        </nav>

        <div className={styles.sidebarFooter}>
          <span className={styles.footerLabel}>Theme</span>
          <ThemeSwitcher />
        </div>
      </aside>
      <main className={styles.main}>{children}</main>
    </div>
  )
}
