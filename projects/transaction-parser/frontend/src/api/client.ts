/**
 * Thin typed fetch wrapper. Every request goes through `/api/v1`, which
 * Vite proxies to the backend in dev and the frontend's own server
 * forwards in docker-compose. Errors are normalized into `ApiError` so
 * callers can branch on structured `code` values (e.g. the 409
 * AMBIGUOUS_INSTITUTION upload flow) without re-parsing the response.
 *
 * Workspace scoping lives here too: the backend reads the active
 * workspace from an `X-Workspace` header, and injecting it at this one
 * choke point is what let every existing query hook stay untouched.
 * The value is set from React (see `WorkspaceProvider`) via
 * `setActiveWorkspaceSlug`, because `api` is a plain module, not a hook.
 */

const API_BASE = '/api/v1'

export const WORKSPACE_HEADER = 'X-Workspace'

let activeWorkspaceSlug: string | null = null

/** Point every subsequent request at this workspace (null clears it). */
export function setActiveWorkspaceSlug(slug: string | null): void {
  activeWorkspaceSlug = slug
}

export function getActiveWorkspaceSlug(): string | null {
  return activeWorkspaceSlug
}

export class ApiError extends Error {
  readonly status: number
  /** Raw `detail` payload from FastAPI — may be a string, an object with
   * `code`/`message`, or a validation-error array. */
  readonly detail: unknown
  /** Present when `detail.code` exists (our structured error shape). */
  readonly code: string | undefined

  constructor(status: number, detail: unknown) {
    const message = extractMessage(detail)
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.code = extractCode(detail)
  }
}

function extractMessage(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const first = detail[0] as { msg?: string } | undefined
    if (first?.msg) return first.msg
    return 'Request validation failed.'
  }
  if (detail && typeof detail === 'object' && 'message' in detail) {
    const message = (detail as { message?: unknown }).message
    if (typeof message === 'string') return message
  }
  return 'Request failed.'
}

function extractCode(detail: unknown): string | undefined {
  if (detail && typeof detail === 'object' && 'code' in detail) {
    const code = (detail as { code?: unknown }).code
    if (typeof code === 'string') return code
  }
  return undefined
}

async function parseErrorBody(response: Response): Promise<unknown> {
  try {
    const body = await response.json()
    return body?.detail ?? body
  } catch {
    return response.statusText
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body && !(init.body instanceof FormData)
        ? { 'Content-Type': 'application/json' }
        : {}),
      // Listed before `init.headers` so a caller can still override it —
      // the workspace endpoints take the slug in the path instead.
      ...(activeWorkspaceSlug ? { [WORKSPACE_HEADER]: activeWorkspaceSlug } : {}),
      ...init?.headers,
    },
  })

  if (!response.ok) {
    const detail = await parseErrorBody(response)
    throw new ApiError(response.status, detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export function buildQuery(
  params: Record<string, string | number | boolean | number[] | string[] | undefined>,
): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue
    if (Array.isArray(value)) {
      for (const item of value) search.append(key, String(item))
    } else {
      search.append(key, String(value))
    }
  }
  const qs = search.toString()
  return qs ? `?${qs}` : ''
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),

  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),

  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),

  postForm: <T>(path: string, form: FormData) =>
    request<T>(path, { method: 'POST', body: form }),
}
