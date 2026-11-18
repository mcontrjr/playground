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

/** Distribution's donut/list goes to 12 categorical slots instead of
 * the shared 8 (`MAX_CATEGORICAL_SLOTS`) — it's the one chart with
 * room (a legend row per slice with swatch + name + percent + amount,
 * same secondary encoding every other chart has) to carry more series
 * before folding into "Other". Pulls from its own --series-dist-N
 * vars (12 hues picked and *ordered* — see tokens.css — so adjacent
 * slices never land two similar hues next to each other; it does not
 * reuse --series-1..8 since those were optimized as an 8-hue set, not
 * a prefix of a 12-hue one). */
const DISTRIBUTION_SERIES_VARS = [
  '--series-dist-1',
  '--series-dist-2',
  '--series-dist-3',
  '--series-dist-4',
  '--series-dist-5',
  '--series-dist-6',
  '--series-dist-7',
  '--series-dist-8',
  '--series-dist-9',
  '--series-dist-10',
  '--series-dist-11',
  '--series-dist-12',
] as const

export const MAX_DISTRIBUTION_SLOTS = DISTRIBUTION_SERIES_VARS.length

export function assignDistributionColors(count: number): string[] {
  const colors: string[] = []
  for (let i = 0; i < count; i += 1) {
    colors.push(
      i < MAX_DISTRIBUTION_SLOTS ? resolveCssVar(DISTRIBUTION_SERIES_VARS[i]!) : resolveCssVar(OTHER_VAR),
    )
  }
  return colors
}
