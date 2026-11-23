/**
 * Holds the active workspace for the whole app.
 *
 * `workspace` in this context is the single source of truth — every data
 * hook reaches the backend through `api`, which stamps the slug onto the
 * `X-Workspace` header, and that slug is set here. Entering or leaving a
 * workspace therefore means exactly one thing: changing this value (and
 * clearing React Query, so no other workspace's rows survive in cache).
 *
 * The value is mirrored into `sessionStorage` purely so a page refresh
 * doesn't bounce you back to the splash screen mid-session. It is a
 * convenience, not the source of truth: closing the tab ends the
 * session, and `clearWorkspace()` wipes it.
 */
import { useQueryClient } from '@tanstack/react-query'
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { setActiveWorkspaceSlug } from '../api/client'
import type { Workspace } from '../api/workspaces'

const STORAGE_KEY = 'tp.workspace'

interface WorkspaceContextValue {
  /** Null until a workspace is entered or created. */
  workspace: Workspace | null
  enterWorkspace: (workspace: Workspace) => void
  clearWorkspace: () => void
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null)

function readStored(): Workspace | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<Workspace>
    if (
      typeof parsed?.id === 'number' &&
      typeof parsed?.slug === 'string' &&
      typeof parsed?.name === 'string'
    ) {
      return { id: parsed.id, slug: parsed.slug, name: parsed.name }
    }
    return null
  } catch {
    // Private-mode / disabled storage, or a corrupt value: fall back to
    // the splash screen rather than failing to boot.
    return null
  }
}

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [workspace, setWorkspace] = useState<Workspace | null>(readStored)

  // Keep the fetch layer in step with the state, including on first
  // render when the workspace was restored from storage — otherwise the
  // first request of a refreshed session would go out unscoped.
  useEffect(() => {
    setActiveWorkspaceSlug(workspace?.slug ?? null)
  }, [workspace])

  const enterWorkspace = useCallback(
    (next: Workspace) => {
      // Set the header before any component can react to the state
      // change and fire a query.
      setActiveWorkspaceSlug(next.slug)
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      } catch {
        // Non-fatal: the workspace still works for this page load.
      }
      queryClient.clear()
      setWorkspace(next)
    },
    [queryClient],
  )

  const clearWorkspace = useCallback(() => {
    setActiveWorkspaceSlug(null)
    try {
      sessionStorage.removeItem(STORAGE_KEY)
    } catch {
      // Ignore — the in-memory state below is what gates the UI.
    }
    queryClient.clear()
    setWorkspace(null)
  }, [queryClient])

  const value = useMemo(
    () => ({ workspace, enterWorkspace, clearWorkspace }),
    [workspace, enterWorkspace, clearWorkspace],
  )

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>
}

export function useWorkspace(): WorkspaceContextValue {
  const context = useContext(WorkspaceContext)
  if (context === null) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider')
  }
  return context
}
