import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { useFailures } from '../../api/hooks/useFailures'
import logo from '../../assets/parser-logo.svg'
import { ThemeSwitcher } from '../ThemeSwitcher/ThemeSwitcher'
import styles from './Layout.module.css'

interface NavItem {
  to: string
  label: string
  badge?: number
}

export function Layout({ children }: { children: ReactNode }) {
  const { data: failures } = useFailures(false)
  const unresolvedCount = failures?.length ?? 0

  const navItems: NavItem[] = [
    { to: '/', label: 'Upload', badge: unresolvedCount },
    { to: '/overview', label: 'Overview' },
    { to: '/time-series', label: 'Time Series' },
    { to: '/distribution', label: 'Distribution' },
    { to: '/records', label: 'Records' },
    { to: '/budget', label: 'Budget' },
    { to: '/categories', label: 'Categories' },
    { to: '/accounts', label: 'Accounts' },
    { to: '/history', label: 'History' },
  ]

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <img src={logo} alt="" className={styles.brandMark} width={28} height={28} />
          <span className={styles.brandName}>Parser</span>
        </div>

        <nav className={styles.nav} aria-label="Primary">
          {navItems.map((item) => (
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
