/**
 * The parser logo, in its two states.
 *
 * At rest it is just the mark — the splash screen's identity, sitting
 * still. It spins only while something is actually in flight: a
 * workspace loading, or the first import running. Keeping the spin tied
 * to real work means motion on screen always means "the app is busy",
 * and never just "the app is open".
 */
import logo from '../../assets/parser-logo.svg'
import styles from './LogoSpinner.module.css'

interface LogoMarkProps {
  size?: number
  /** Rotate the mark, and announce it to assistive tech as busy. */
  spinning?: boolean
  /** Describes what is loading; only used while spinning. */
  label?: string
  className?: string
}

/**
 * The logo. Static by default; pass `spinning` while work is in flight.
 *
 * Only the spinning form is a live region — a resting logo is decoration
 * and shouldn't announce itself.
 */
export function LogoMark({
  size = 48,
  spinning = false,
  label = 'Loading',
  className = '',
}: LogoMarkProps) {
  return (
    <span
      className={`${styles.mark} ${spinning ? styles.markSpinning : ''} ${className}`}
      {...(spinning
        ? { role: 'status', 'aria-live': 'polite', 'aria-label': label }
        : { 'aria-hidden': true })}
    >
      <img src={logo} alt="" className={styles.image} width={size} height={size} />
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

/** Centered spinning logo plus caption, for whole-page loading states. */
export function LoadingOverlay({
  message = 'Loading',
  size = 56,
  fullScreen = false,
}: LoadingOverlayProps) {
  return (
    <div className={`${styles.overlay} ${fullScreen ? styles.overlayFull : ''}`}>
      <LogoMark size={size} spinning label={message} />
      <p className={styles.label}>{message}</p>
    </div>
  )
}
