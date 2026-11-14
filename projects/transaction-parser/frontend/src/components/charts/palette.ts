/**
 * Categorical color assignment for charts. Hues are assigned by stable
 * sort position (largest categories by magnitude get the earlier, more
 * saturated slots) but — per the dataviz skill's "color follows the
 * entity" rule — a given category keeps the same color across renders
 * of the *same* page as long as its relative rank doesn't change. We
 * don't key colors by category id globally (there are ~20 categories,
 * more than the 8 safe categorical slots), so the 9th+ by magnitude
 * always folds into the shared "Other" gray rather than generating a
 * new hue.
 */

const SERIES_VARS = [
  '--series-1',
  '--series-2',
  '--series-3',
  '--series-4',
  '--series-5',
  '--series-6',
  '--series-7',
  '--series-8',
] as const

export const MAX_CATEGORICAL_SLOTS = SERIES_VARS.length
export const OTHER_VAR = '--series-other'
export const OTHER_LABEL = 'Other'

/** Resolves a CSS custom property to its computed hex/rgb value so
 * Recharts (which wants a literal color string, not `var(...)`) can
 * use it directly. Falls back to the raw var() reference if the
 * document isn't available (e.g. in tests). */
export function resolveCssVar(name: string): string {
  if (typeof window === 'undefined') return `var(${name})`
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value || `var(${name})`
}

/** Assigns colors to a list of category names/ids already sorted by
 * descending magnitude (as the API returns them). Items past the 8th
 * slot share the "Other" color. Returns a lookup by index. */
export function assignSeriesColors(count: number): string[] {
  const colors: string[] = []
  for (let i = 0; i < count; i += 1) {
    colors.push(i < MAX_CATEGORICAL_SLOTS ? resolveCssVar(SERIES_VARS[i]!) : resolveCssVar(OTHER_VAR))
  }
  return colors
}
