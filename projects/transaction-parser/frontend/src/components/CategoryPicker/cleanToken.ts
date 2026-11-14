const NOISE_WORDS = new Set([
  'THE',
  'AND',
  'FOR',
  'INC',
  'LLC',
  'CO',
  'LTD',
  'PURCHASE',
  'DEBIT',
  'CREDIT',
  'CARD',
  'PAYMENT',
  'POS',
  'ONLINE',
])

/**
 * Derives a short, keyword-worthy token from a raw transaction
 * description, for prefilling the "also add a keyword" follow-up.
 *
 * Keyword matching on the backend is a plain substring match against
 * `normalized_description` (uppercased, whitespace-collapsed — but
 * otherwise verbatim, punctuation included). So this must return a
 * *contiguous slice of the original text*, not a cleaned/rejoined
 * token — stripping internal punctuation (".", "*", "#") and splicing
 * words back together would silently produce a keyword that can never
 * substring-match the real description again.
 */
export function cleanToken(description: string): string {
  const upper = description.toUpperCase().replace(/\s+/g, ' ').trim()

  // Drop a trailing run that's store numbers / city / state noise:
  // sequences of digits, or 2+ consecutive all-caps "location" words
  // preceded by heavy whitespace (bank exports often pad description
  // with spaces before city/state). Keep it conservative — only trim
  // from the right, never touch the leading merchant token.
  const withoutTrailingDigits = upper.replace(/\s*[\d#]{2,}.*$/, '')
  const base = withoutTrailingDigits.length >= 3 ? withoutTrailingDigits : upper

  const words = base.split(' ').filter((w) => w.length > 0)
  const meaningful = words.filter((w) => w.length > 1 && !NOISE_WORDS.has(w.replace(/[^A-Z]/g, '')))
  const candidates = meaningful.length > 0 ? meaningful : words

  if (candidates.length === 0) return upper.slice(0, 20)

  // Prefer the word with the most *letters* (not raw character count,
  // so a short word padded with punctuation like "*TRIP" doesn't beat
  // "UBER") as the most merchant-specific contiguous token — returned
  // verbatim, punctuation intact, so it stays a real substring of the
  // original description (e.g. "AXS.COM*FESTIVAL" or "PEET'S").
  const letterCount = (word: string) => (word.match(/[A-Z]/g) ?? []).length
  let best = candidates[0]!
  for (const word of candidates) {
    if (letterCount(word) > letterCount(best)) best = word
  }
  return best.slice(0, 32)
}
