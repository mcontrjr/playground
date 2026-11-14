import { THEME_LABELS, THEMES, useTheme } from '../../theme/useTheme'
import styles from './ThemeSwitcher.module.css'

/** Three swatches, one per supported dark theme. Each swatch previews
 * its own palette's ink/paper/accent so switching is a visual choice,
 * not a label-reading exercise. */
export function ThemeSwitcher() {
  const [theme, setTheme] = useTheme()

  return (
    <div className={styles.wrap} role="group" aria-label="Theme">
      {THEMES.map((name) => (
        <button
          key={name}
          type="button"
          className={name === theme ? `${styles.swatch} ${styles.swatchActive}` : styles.swatch}
          data-theme-preview={name}
          onClick={() => setTheme(name)}
          aria-pressed={name === theme}
          title={THEME_LABELS[name]}
        >
          <span className={styles.swatchDot} />
          <span className={styles.swatchLabel}>{THEME_LABELS[name]}</span>
        </button>
      ))}
    </div>
  )
}
