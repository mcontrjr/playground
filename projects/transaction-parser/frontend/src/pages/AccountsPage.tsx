import { useEffect, useRef, useState } from 'react'
import { ApiError } from '../api/client'
import { useAccounts } from '../api/hooks/useAccounts'
import { usePatchAccount } from '../api/hooks/useAccountMutations'
import type { Account } from '../api/types'
import styles from './AccountsPage.module.css'

function AccountRow({ account, onToast }: { account: Account; onToast: (message: string) => void }) {
  const [nameDraft, setNameDraft] = useState(account.display_name)
  const patchAccount = usePatchAccount()

  useEffect(() => setNameDraft(account.display_name), [account.display_name])

  const commitRename = () => {
    const trimmed = nameDraft.trim()
    if (!trimmed || trimmed === account.display_name) {
      setNameDraft(account.display_name)
      return
    }
    patchAccount.mutate(
      { id: account.id, patch: { display_name: trimmed } },
      {
        onSuccess: (updated) => onToast(`Renamed to "${updated.display_name}".`),
        onError: (err) => {
          setNameDraft(account.display_name)
          onToast(err instanceof ApiError ? err.message : 'Rename failed.')
        },
      },
    )
  }

  return (
    <div className={styles.row} data-testid="account-row" data-account-name={account.display_name}>
      <div className={styles.nameCol}>
        <input
          className={styles.nameInput}
          value={nameDraft}
          onChange={(e) => setNameDraft(e.target.value)}
          onBlur={commitRename}
          onKeyDown={(e) => {
            if (e.key === 'Enter') commitRename()
            if (e.key === 'Escape') setNameDraft(account.display_name)
          }}
          aria-label={`Rename ${account.display_name}`}
          data-testid="account-name-input"
        />
        <span className={styles.meta}>
          {account.institution_name} · {account.kind === 'card' ? 'Card' : 'Checking'}
          {account.account_hint && account.kind === 'card' ? ` ···${account.account_hint}` : ''}
        </span>
      </div>
      <span className={styles.txnCount}>
        {account.transaction_count} transaction{account.transaction_count === 1 ? '' : 's'}
      </span>
    </div>
  )
}

export function AccountsPage() {
  const { data: accounts, isLoading, isError, error } = useAccounts()
  const [toast, setToast] = useState<string | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showToast = (message: string) => {
    setToast(message)
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 4000)
  }

  useEffect(() => () => {
    if (toastTimer.current) clearTimeout(toastTimer.current)
  }, [])

  const sorted = [...(accounts ?? [])].sort(
    (a, b) => a.institution_name.localeCompare(b.institution_name) || a.display_name.localeCompare(b.display_name),
  )

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Accounts</h1>
        <p className={styles.subtitle}>
          Rename an account to whatever you'll recognize — the name you set here is what shows up
          everywhere accounts are listed or filtered.
        </p>
      </header>

      {isError && (
        <p className={styles.errorBanner}>
          {error instanceof ApiError ? error.message : 'Could not load accounts.'}
        </p>
      )}

      {isLoading ? (
        <p className={styles.meta}>Loading…</p>
      ) : sorted.length === 0 ? (
        <p className={styles.meta}>No accounts yet — upload a statement to get started.</p>
      ) : (
        <div className={styles.list}>
          {sorted.map((account) => (
            <AccountRow key={account.id} account={account} onToast={showToast} />
          ))}
        </div>
      )}

      {toast && (
        <div className={styles.toast} data-testid="accounts-toast">
          {toast}
        </div>
      )}
    </div>
  )
}
