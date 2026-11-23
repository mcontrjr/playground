import { useState } from 'react'
import {
  useClashDismissals,
  useClashes,
  useDismissClash,
  useResolveClash,
  useUndismissClash,
} from '../../api/hooks/useClashes'
import type { ClashClaim, TransactionClash } from '../../api/types'
import styles from './ClashReview.module.css'

const MONEY_FORMATTER = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

function formatAmount(amount: string): string {
  const value = Number.parseFloat(amount)
  const formatted = MONEY_FORMATTER.format(Math.abs(value))
  return value < 0 ? `−${formatted}` : formatted
}

/** One clashing row: the competing categories, which one priority picked,
 * and the two ways to settle it.
 *
 * Resolving writes category_source='manual', which is permanently sticky
 * — so "all like it" is offered alongside "just this row" to avoid
 * opting a recurring merchant out of auto-categorization one row at a
 * time. */
function ClashRow({ clash }: { clash: TransactionClash }) {
  const resolve = useResolveClash()
  const dismiss = useDismissClash()
  const [choice, setChoice] = useState<number | null>(null)

  const winner = clash.claims.find((c) => c.is_winner) ?? null
  const chosen = choice ?? winner?.category_id ?? null
  const chosenClaim = clash.claims.find((c) => c.category_id === chosen) ?? null
  // Changing nothing isn't worth a manual pin — the actions switch to
  // "dismiss" when the current winner is already what the user wants.
  const isOverride = chosen !== null && chosen !== clash.current_category_id

  const loserIds = winner
    ? clash.claims.filter((c) => c.category_id !== winner.category_id).map((c) => c.category_id)
    : []
  const loserNames = clash.claims
    .filter((c) => winner && c.category_id !== winner.category_id)
    .map((c) => c.category_name)
    .join(', ')

  const submit = (scope: 'row' | 'all_matching') => {
    if (chosen === null) return
    resolve.mutate({
      transaction_ids: [clash.transaction_id],
      category_id: chosen,
      scope,
      keyword: scope === 'all_matching' ? (chosenClaim?.keyword ?? null) : null,
    })
  }

  /** Dismiss the winner against every competing claim. A row contested
   * by three categories needs each pairing dismissed, otherwise the
   * clash stays listed via the one that wasn't covered. */
  const submitDismiss = (rowOnly: boolean) => {
    if (!winner) return
    for (const loserId of loserIds) {
      dismiss.mutate({
        winner_category_id: winner.category_id,
        loser_category_id: loserId,
        transaction_id: rowOnly ? clash.transaction_id : null,
      })
    }
  }

  return (
    <li className={styles.row} data-testid="clash-row">
      <div className={styles.rowHeader}>
        <span className={styles.description} title={clash.description}>
          {clash.description}
        </span>
        <span className={styles.amount}>{formatAmount(clash.amount)}</span>
      </div>

      {clash.transfer_decided && (
        <p className={styles.transferNote} data-testid="transfer-note">
          Decided as a transfer, which is matched before priority is
          considered — reordering categories cannot change this one.
        </p>
      )}

      <div className={styles.claims}>
        {clash.claims.map((claim: ClashClaim) => {
          const selected = claim.category_id === chosen
          return (
            <button
              key={claim.category_id}
              type="button"
              className={selected ? `${styles.claim} ${styles.claimSelected}` : styles.claim}
              onClick={() => setChoice(claim.category_id)}
              data-testid="clash-claim"
              data-selected={selected}
            >
              <span className={styles.claimName}>{claim.category_name}</span>
              <span className={styles.claimMeta}>
                {claim.is_winner ? 'current · ' : ''}
                {claim.stage === 'transfer' ? 'transfer' : `priority ${claim.priority}`} · matched{' '}
                <code>{claim.keyword}</code>
              </span>
            </button>
          )
        })}
      </div>

      <div className={styles.actions}>
        {isOverride ? (
          <>
            <button
              type="button"
              className={styles.primaryAction}
              disabled={resolve.isPending}
              onClick={() => submit('row')}
              data-testid="resolve-row"
            >
              Use for this record
            </button>
            <button
              type="button"
              className={styles.secondaryAction}
              disabled={resolve.isPending || !chosenClaim}
              onClick={() => submit('all_matching')}
              title={
                chosenClaim
                  ? `Also pin every unsettled record matching "${chosenClaim.keyword}"`
                  : undefined
              }
              data-testid="resolve-all-matching"
            >
              Use for all like it
            </button>
          </>
        ) : (
          /* Nothing to change — the categorizer already picked what the
             user would pick. Dismissing records that judgment so the row
             stops being listed, without pinning it 'manual' (which would
             opt it out of future rule fixes). */
          <>
            <button
              type="button"
              className={styles.primaryAction}
              disabled={dismiss.isPending || !loserIds.length}
              onClick={() => submitDismiss(false)}
              title={
                winner
                  ? `Stop flagging ${winner.category_name} over ${loserNames} everywhere`
                  : undefined
              }
              data-testid="dismiss-rule"
            >
              This is correct — stop flagging
            </button>
            <button
              type="button"
              className={styles.secondaryAction}
              disabled={dismiss.isPending || !loserIds.length}
              onClick={() => submitDismiss(true)}
              title="Dismiss only this record, leaving the pairing flagged"
              data-testid="dismiss-row"
            >
              Just this record
            </button>
          </>
        )}
        {resolve.isError && <span className={styles.error}>Could not save.</span>}
        {dismiss.isError && <span className={styles.error}>Could not dismiss.</span>}
      </div>
    </li>
  )
}

/** The dismissed pairings, revealed on demand. Kept visible (as a count
 * with a toggle) rather than fully hidden: a rule-level dismissal
 * suppresses future rows too, so it needs to stay findable and
 * reversible. */
function DismissedPanel({ onClose }: { onClose: () => void }) {
  const { data, isLoading } = useClashDismissals()
  const undismiss = useUndismissClash()

  if (isLoading) return <p className={styles.muted}>Loading…</p>

  const items = data?.items ?? []

  return (
    <div className={styles.dismissedPanel} data-testid="dismissed-panel">
      <div className={styles.dismissedHeader}>
        <span className={styles.dismissedTitle}>Dismissed as correct</span>
        <button type="button" className={styles.linkButton} onClick={onClose}>
          Hide
        </button>
      </div>
      {items.length === 0 ? (
        <p className={styles.muted}>Nothing dismissed yet.</p>
      ) : (
        <ul className={styles.dismissedList}>
          {items.map((d) => (
            <li key={d.id} className={styles.dismissedRow} data-testid="dismissed-row">
              <span>
                <strong>{d.winner_category_name}</strong> over {d.loser_category_name}
                {d.transaction_id !== null && (
                  <span className={styles.scopeTag}>one record</span>
                )}
              </span>
              <span className={styles.dismissedMeta}>
                hides {d.hidden_count}
                <button
                  type="button"
                  className={styles.linkButton}
                  onClick={() => undismiss.mutate(d.id)}
                  disabled={undismiss.isPending}
                  data-testid="undismiss"
                >
                  Restore
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

/** The clash backlog: every row where two or more categories compete and
 * the categorizer silently picked a winner.
 *
 * Two different outcomes, deliberately distinct:
 * - **Resolve** (you disagree) writes category_source='manual', pinning
 *   the row permanently against future rule changes.
 * - **Dismiss** (you agree) records a judgment about the rules and
 *   leaves the row alone, so a later keyword fix still reaches it. */
export function ClashReview() {
  const { data, isLoading, isError } = useClashes(false)
  const [showDismissed, setShowDismissed] = useState(false)

  if (isLoading) return <p className={styles.muted}>Checking for conflicts…</p>
  if (isError) return <p className={styles.error}>Could not load conflicts.</p>

  const items = data?.items ?? []
  const dismissedCount = data?.dismissed_count ?? 0

  const dismissedLine = dismissedCount > 0 && (
    <p className={styles.muted}>
      {dismissedCount} record{dismissedCount === 1 ? '' : 's'} dismissed as correct.{' '}
      <button
        type="button"
        className={styles.linkButton}
        onClick={() => setShowDismissed((v) => !v)}
        data-testid="toggle-dismissed"
      >
        {showDismissed ? 'Hide' : 'Review'}
      </button>
    </p>
  )

  if (items.length === 0) {
    return (
      <div className={styles.empty} data-testid="clash-empty">
        <p>No unresolved conflicts.</p>
        {(data?.settled_count ?? 0) > 0 && (
          <p className={styles.muted}>
            {data?.settled_count} already settled by hand and left untouched.
          </p>
        )}
        {dismissedLine}
        {showDismissed && <DismissedPanel onClose={() => setShowDismissed(false)} />}
      </div>
    )
  }

  return (
    <section className={styles.wrap}>
      <header className={styles.header}>
        <h3 className={styles.heading}>
          {data?.total} conflict{data?.total === 1 ? '' : 's'} to review
        </h3>
        <p className={styles.sub}>
          These records match more than one category. Priority picked the
          current one for you — confirm it or choose another.
          {(data?.settled_count ?? 0) > 0 &&
            ` ${data?.settled_count} record${data?.settled_count === 1 ? '' : 's'} you already set by hand are excluded.`}
        </p>
        {dismissedLine}
      </header>
      {showDismissed && <DismissedPanel onClose={() => setShowDismissed(false)} />}
      <ul className={styles.list}>
        {items.map((clash) => (
          <ClashRow key={clash.transaction_id} clash={clash} />
        ))}
      </ul>
    </section>
  )
}
