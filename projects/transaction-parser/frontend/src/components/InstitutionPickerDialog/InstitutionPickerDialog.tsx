import { useState } from 'react'
import styles from './InstitutionPickerDialog.module.css'

const INSTITUTION_LABELS: Record<string, string> = {
  amex: 'Amex',
  capital_one: 'Capital One',
  discover: 'Discover',
  citi: 'Citi',
  schwab: 'Schwab',
}

interface InstitutionPickerDialogProps {
  filename: string
  candidates: string[]
  onConfirm: (institution: string) => void
  onCancel: () => void
}

export function InstitutionPickerDialog({
  filename,
  candidates,
  onConfirm,
  onCancel,
}: InstitutionPickerDialogProps) {
  const [selected, setSelected] = useState<string | null>(candidates[0] ?? null)

  return (
    <div
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-label="Choose institution"
      data-testid="institution-picker-dialog"
    >
      <div className={styles.dialog}>
        <h2 className={styles.title}>Which bank is this?</h2>
        <p className={styles.body}>
          <span className={styles.filename}>{filename}</span> matches more than one bank's
          format. Pick the right one to continue.
        </p>
        <div className={styles.options}>
          {candidates.map((code) => (
            <button
              key={code}
              type="button"
              className={selected === code ? `${styles.option} ${styles.optionSelected}` : styles.option}
              onClick={() => setSelected(code)}
              aria-pressed={selected === code}
              data-testid={`institution-option-${code}`}
            >
              {INSTITUTION_LABELS[code] ?? code}
            </button>
          ))}
        </div>
        <div className={styles.actions}>
          <button type="button" className={styles.cancelButton} onClick={onCancel}>
            Cancel
          </button>
          <button
            type="button"
            className={styles.confirmButton}
            disabled={!selected}
            onClick={() => selected && onConfirm(selected)}
            data-testid="institution-picker-confirm"
          >
            Upload
          </button>
        </div>
      </div>
    </div>
  )
}
