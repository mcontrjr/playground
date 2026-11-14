import type { ReactNode } from 'react'
import { useEffect } from 'react'
import styles from './Modal.module.css'

interface ModalProps {
  title: string
  children: ReactNode
  onClose: () => void
  wide?: boolean
  ariaLabel?: string
}

/** Shared dialog shell — same overlay/card treatment as the upload
 * flow's InstitutionPickerDialog, generalized so Categories' several
 * dialogs (impact preview, delete confirm, add category) don't each
 * reimplement the overlay. */
export function Modal({ title, children, onClose, wide, ariaLabel }: ModalProps) {
  useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [onClose])

  return (
    <div
      className={styles.overlay}
      role="dialog"
      aria-modal="true"
      aria-label={ariaLabel ?? title}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div className={wide ? `${styles.dialog} ${styles.dialogWide}` : styles.dialog}>
        <h2 className={styles.title}>{title}</h2>
        {children}
      </div>
    </div>
  )
}
