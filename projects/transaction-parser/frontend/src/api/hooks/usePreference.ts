import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { api } from '../client'
import { queryKeys } from '../queryKeys'
import type { Preference } from '../types'

/** Debounced write-through cache for one server-persisted preference
 * key. Reads resolve instantly from localStorage (so theme/filters
 * paint on the very first frame, before the network round-trip
 * lands) and reconcile with the server's value once it arrives;
 * writes update localStorage immediately and flush to the server
 * after a short debounce so rapid filter changes (typing in a search
 * box, toggling several chips) don't fire one PUT per keystroke.
 *
 * `T` is any plain object shape the caller defines (filter state,
 * `{ name: ThemeName }`, etc.) — it's serialized to JSON verbatim, so
 * the only real constraint is "JSON-serializable object," which
 * `object` captures well enough without forcing every caller to add
 * an index signature just to satisfy a generic bound. */
export function usePreference<T extends object>(
  key: string,
  fallback: T,
): [T, (next: T) => void, { isReady: boolean }] {
  const queryClient = useQueryClient()
  const storageKey = `pref:${key}`

  const [value, setValue] = useState<T>(() => readLocal(storageKey, fallback))
  const [isReady, setIsReady] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const { data } = useQuery({
    queryKey: queryKeys.preference(key),
    queryFn: () => api.get<Preference | null>(`/preferences/${key}`),
    staleTime: Infinity,
  })

  useEffect(() => {
    if (data === undefined) return
    if (data) {
      setValue(data.value as T)
      writeLocal(storageKey, data.value)
    }
    setIsReady(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data])

  const mutation = useMutation({
    mutationFn: (next: T) => api.put<Preference>(`/preferences/${key}`, { value: next }),
    onSuccess: (result) => {
      queryClient.setQueryData(queryKeys.preference(key), result)
    },
  })

  const update = (next: T) => {
    setValue(next)
    writeLocal(storageKey, next)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      mutation.mutate(next)
    }, 400)
  }

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [])

  return [value, update, { isReady }]
}

function readLocal<T extends object>(storageKey: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback
  try {
    const raw = window.localStorage.getItem(storageKey)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

function writeLocal(storageKey: string, value: unknown): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(storageKey, JSON.stringify(value))
  } catch {
    // Storage full/disabled — the server round-trip is still the
    // source of truth on next load, so this is safe to swallow.
  }
}
