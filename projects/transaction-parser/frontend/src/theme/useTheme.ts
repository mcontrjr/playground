import { useEffect } from 'react'
import { usePreference } from '../api/hooks/usePreference'

export const THEMES = ['gruvbox', 'tokyo-night', 'nord', 'pennant'] as const
export type ThemeName = (typeof THEMES)[number]

export const THEME_LABELS: Record<ThemeName, string> = {
  gruvbox: 'Gruvbox',
  'tokyo-night': 'Tokyo Night',
  nord: 'Nord',
  pennant: 'Pennant',
}

interface ThemePreference {
  name: ThemeName
}

const DEFAULT_THEME: ThemePreference = { name: 'gruvbox' }

/** The active theme, persisted server-side (via the preferences cache)
 * so it survives across devices/reloads, with an instant localStorage
 * read on first paint so the page never flashes the default theme
 * before the network resolves. Writes `data-theme` on <html>, which is
 * the only thing `tokens.css` keys its three palettes off of. */
export function useTheme(): [ThemeName, (name: ThemeName) => void] {
  const [pref, setPref] = usePreference<ThemePreference>('theme', DEFAULT_THEME)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', pref.name)
  }, [pref.name])

  const setTheme = (name: ThemeName) => setPref({ name })

  return [pref.name, setTheme]
}
