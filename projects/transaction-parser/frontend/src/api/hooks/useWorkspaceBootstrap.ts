import { useQuery } from '@tanstack/react-query'
import { queryKeys } from '../queryKeys'
import { workspacesApi, type WorkspaceBootstrap } from '../workspaces'
import { useWorkspace } from '../../workspace/WorkspaceContext'

/**
 * The active workspace's bootstrap payload.
 *
 * Seeded by the splash screen when entering, so this normally resolves
 * from cache on first render. Its `has_transactions` flag is what gates
 * the data pages in the sidebar, so it is refetched after an upload.
 */
export function useWorkspaceBootstrap() {
  const { workspace } = useWorkspace()

  return useQuery<WorkspaceBootstrap>({
    queryKey: queryKeys.workspaceBootstrap(workspace?.slug ?? ''),
    queryFn: () => workspacesApi.bootstrap(workspace!.slug),
    enabled: workspace !== null,
  })
}

/**
 * Whether the active workspace has any records yet.
 *
 * Defaults to false while the answer is still unknown, so a brand-new
 * workspace never flashes the full nav before settling into the gated
 * one. The splash screen seeds this cache on entry, so an established
 * workspace resolves to true without a visible transition.
 */
export function useHasTransactions(): boolean {
  const { data } = useWorkspaceBootstrap()
  return data?.has_transactions ?? false
}
