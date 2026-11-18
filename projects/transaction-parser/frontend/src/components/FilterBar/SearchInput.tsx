import { useEffect, useState } from 'react'
import styles from './FilterBar.module.css'
import { useDebouncedValue } from './useDebouncedValue'

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  id?: string
  placeholder?: string
}

/** The debounced description search, extracted out of FilterBar so
 * RecordsPage can render it directly above the table instead of
 * inside the chip bar — same 350ms debounce behavior as before. */
export function SearchInput({ value, onChange, id = 'records-search', placeholder = 'Description contains…' }: SearchInputProps) {
  const [draft, setDraft] = useState(value)
  const debounced = useDebouncedValue(draft, 350)

  useEffect(() => {
    if (debounced !== value) onChange(debounced)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced])

  useEffect(() => {
    setDraft(value)
    // Only resync from external changes (e.g. preference load) —
    // not from our own debounced writes, which would otherwise fight
    // the user's typing.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  return (
    <div className={styles.field}>
      <label className={styles.fieldLabel} htmlFor={id}>
        Search
      </label>
      <input
        id={id}
        className={styles.search}
        type="search"
        placeholder={placeholder}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
      />
    </div>
  )
}
