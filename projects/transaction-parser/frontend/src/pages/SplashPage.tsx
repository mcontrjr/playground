/**
 * The app's entry screen: the logo over two choices — enter an existing
 * workspace, or create a new one.
 *
 * On load the screen plays one short arrival: the mark settles in, then
 * the wordmark, tagline and card rise behind it. The logo is static
 * there and spins only while a workspace is actually loading, so motion
 * on this screen always means the app is busy.
 *
 * Loading a workspace is one request (`/workspaces/{slug}/bootstrap`),
 * and this screen stays on the spinning logo for exactly that round
 * trip. The bootstrap payload is seeded into React Query before entering,
 * so the first page paints without re-fetching what was just fetched.
 */
import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { ApiError } from '../api/client'
import { queryKeys } from '../api/queryKeys'
import {
  SLUG_RULES,
  normalizeSlug,
  workspacesApi,
  type WorkspaceBootstrap,
} from '../api/workspaces'
import { LogoMark } from '../components/LogoSpinner/LogoSpinner'
import { useWorkspace } from '../workspace/WorkspaceContext'
import styles from './SplashPage.module.css'

type Mode = 'choose' | 'create'

/** Debounce for the create form's availability check. */
const AVAILABILITY_DELAY_MS = 350

export function SplashPage() {
  const { enterWorkspace } = useWorkspace()
  const queryClient = useQueryClient()

  const [mode, setMode] = useState<Mode>('choose')
  const [slug, setSlug] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Availability state for the create form only.
  const [availability, setAvailability] = useState<{
    checking: boolean
    available: boolean | null
    reason: string | null
  }>({ checking: false, available: null, reason: null })

  const latestCheck = useRef(0)

  useEffect(() => {
    if (mode !== 'create') return
    const candidate = normalizeSlug(slug)
    if (!candidate) {
      setAvailability({ checking: false, available: null, reason: null })
      return
    }

    setAvailability((prev) => ({ ...prev, checking: true }))
    const checkId = ++latestCheck.current
    const timer = setTimeout(() => {
      workspacesApi
        .availability(candidate)
        .then((result) => {
          // Ignore a response that a later keystroke has superseded.
          if (checkId !== latestCheck.current) return
          setAvailability({
            checking: false,
            available: result.available,
            reason: result.reason,
          })
        })
        .catch(() => {
          if (checkId !== latestCheck.current) return
          setAvailability({ checking: false, available: null, reason: null })
        })
    }, AVAILABILITY_DELAY_MS)

    return () => clearTimeout(timer)
  }, [slug, mode])

  /** Load a workspace and hand it to the provider. */
  async function loadAndEnter(targetSlug: string) {
    const bootstrap: WorkspaceBootstrap = await workspacesApi.bootstrap(targetSlug)

    // Seed the caches the first screens read, so entering doesn't
    // immediately re-request what bootstrap already returned.
    queryClient.setQueryData(
      queryKeys.workspaceBootstrap(bootstrap.workspace.slug),
      bootstrap,
    )
    queryClient.setQueryData(queryKeys.categories, bootstrap.categories)
    queryClient.setQueryData(queryKeys.buckets, bootstrap.buckets)
    queryClient.setQueryData(queryKeys.accounts, bootstrap.accounts)

    enterWorkspace(bootstrap.workspace)
  }

  function describeError(err: unknown, fallback: string): string {
    if (err instanceof ApiError) {
      if (err.code === 'WORKSPACE_NOT_FOUND') {
        return `No workspace named "${normalizeSlug(slug)}". Check the name, or create a new one.`
      }
      if (err.code === 'WORKSPACE_TAKEN') {
        return 'That workspace name is already taken.'
      }
      return err.message
    }
    return fallback
  }

  async function handleEnter(event: React.FormEvent) {
    event.preventDefault()
    const candidate = normalizeSlug(slug)
    if (!candidate || busy) return

    setBusy(true)
    setError(null)
    try {
      await loadAndEnter(candidate)
    } catch (err) {
      setError(describeError(err, 'Could not load that workspace.'))
      setBusy(false)
    }
  }

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault()
    const candidate = normalizeSlug(slug)
    if (!candidate || busy) return

    setBusy(true)
    setError(null)
    try {
      const created = await workspacesApi.create(candidate, displayName)
      await loadAndEnter(created.slug)
    } catch (err) {
      setError(describeError(err, 'Could not create that workspace.'))
      setBusy(false)
    }
  }

  function switchMode(next: Mode) {
    setMode(next)
    setError(null)
    setAvailability({ checking: false, available: null, reason: null })
  }

  // While loading, the logo is the only thing on screen, and this is the
  // one place it spins — the same indicator the first import uses, so
  // "the app is working" always looks the same.
  if (busy) {
    return (
      <div className={`${styles.screen} ${styles.screenLoading}`}>
        <div className={styles.hero}>
          <LogoMark
            size={96}
            spinning
            label={mode === 'create' ? 'Creating workspace' : 'Loading workspace'}
          />
          <p className={styles.loadingNote}>
            {mode === 'create' ? 'Setting up your workspace…' : 'Loading your workspace…'}
          </p>
        </div>
      </div>
    )
  }

  const createDisabled =
    !normalizeSlug(slug) || availability.checking || availability.available === false

  return (
    <div className={styles.screen}>
      <div className={styles.hero}>
        <LogoMark size={96} className={styles.markArrival} />
        <h1 className={`${styles.wordmark} ${styles.riseOne}`}>Parser</h1>
        <p className={`${styles.tagline} ${styles.riseTwo}`}>
          Your accounts, categories, budget and records live in a workspace.
        </p>
      </div>

      <div className={`${styles.options} ${styles.riseThree}`}>
        {mode === 'choose' ? (
          <>
            <section className={styles.card}>
              <div className={styles.cardHeader}>
                <h2 className={styles.cardTitle}>Enter a workspace</h2>
                <p className={styles.cardHint}>
                  Loads your accounts, categories, buckets, keywords, budget and
                  records.
                </p>
              </div>
              <form className={styles.form} onSubmit={handleEnter}>
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="workspace-slug">
                    Workspace name
                  </label>
                  <input
                    id="workspace-slug"
                    className={styles.input}
                    value={slug}
                    onChange={(e) => {
                      setSlug(e.target.value)
                      setError(null)
                    }}
                    placeholder="e.g. init"
                    autoComplete="off"
                    autoCapitalize="none"
                    spellCheck={false}
                    autoFocus
                  />
                </div>
                {error && (
                  <p className={styles.error} role="alert">
                    {error}
                  </p>
                )}
                <button
                  type="submit"
                  className={styles.primary}
                  disabled={!normalizeSlug(slug)}
                >
                  Enter
                </button>
              </form>
            </section>

            <div className={styles.switcher}>
              <button
                type="button"
                className={styles.switchLink}
                onClick={() => switchMode('create')}
              >
                Or create a new workspace
              </button>
            </div>
          </>
        ) : (
          <>
            <section className={styles.card}>
              <div className={styles.cardHeader}>
                <h2 className={styles.cardTitle}>Create a workspace</h2>
                <p className={styles.cardHint}>
                  Starts with a standard set of categories and buckets. You set
                  your own budget once you have records.
                </p>
              </div>
              <form className={styles.form} onSubmit={handleCreate}>
                <div className={styles.field}>
                  <label className={styles.label} htmlFor="new-workspace-slug">
                    Workspace name
                  </label>
                  <input
                    id="new-workspace-slug"
                    className={styles.input}
                    value={slug}
                    onChange={(e) => {
                      setSlug(e.target.value)
                      setError(null)
                    }}
                    placeholder="pick something unique"
                    autoComplete="off"
                    autoCapitalize="none"
                    spellCheck={false}
                    autoFocus
                  />
                  <p className={styles.rules}>{SLUG_RULES}</p>
                  {availability.checking && (
                    <p className={styles.checking}>Checking availability…</p>
                  )}
                  {!availability.checking && availability.available === true && (
                    <p className={styles.available}>
                      “{normalizeSlug(slug)}” is available.
                    </p>
                  )}
                  {!availability.checking && availability.available === false && (
                    <p className={styles.error}>{availability.reason}</p>
                  )}
                </div>

                <div className={styles.field}>
                  <label className={styles.label} htmlFor="new-workspace-name">
                    Display name (optional)
                  </label>
                  <input
                    id="new-workspace-name"
                    className={styles.input}
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="defaults to the workspace name"
                    autoComplete="off"
                  />
                </div>

                {error && (
                  <p className={styles.error} role="alert">
                    {error}
                  </p>
                )}
                <button type="submit" className={styles.primary} disabled={createDisabled}>
                  Create workspace
                </button>
              </form>
            </section>

            <div className={styles.switcher}>
              <button
                type="button"
                className={styles.switchLink}
                onClick={() => switchMode('choose')}
              >
                Back to entering a workspace
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
