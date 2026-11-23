/**
 * The spinning parser logo, used as the app's one loading indicator:
 * on the splash screen while a workspace loads, and over the Upload page
 * while the first import runs.
 */
import logo from '../../assets/parser-logo.svg'
import styles from './LogoSpinner.module.css'

interface LogoSpinnerProps {
  size?: number
  /** Accessible description of what is loading. */
  label?: string
}

export function LogoSpinner({ size = 48, label = 'Loading' }: LogoSpinnerProps) {
  return (
    <span className={styles.spinner} role="status" aria-live="polite" aria-label={label}>
      <img src={logo} alt="" className={styles.mark} width={size} height={size} />
    </span>
  )
}

interface LoadingOverlayProps {
  /** Shown beneath the logo; also the spinner's accessible label. */
  message?: string
  size?: number
  /** Fill the viewport rather than the content area. */
  fullScreen?: boolean
}

/** Centered spinner plus caption, for whole-page loading states. */
export function LoadingOverlay({
  message = 'Loading',
  size = 56,
  fullScreen = false,
}: LoadingOverlayProps) {
  return (
    <div className={`${styles.overlay} ${fullScreen ? styles.overlayFull : ''}`}>
      <LogoSpinner size={size} label={message} />
      <p className={styles.label}>{message}</p>
    </div>
  )
}
