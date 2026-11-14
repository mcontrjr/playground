import { useRef, useState } from 'react'
import styles from './UploadDropzone.module.css'

interface UploadDropzoneProps {
  onFilesSelected: (files: File[]) => void
  disabled?: boolean
}

export function UploadDropzone({ onFilesSelected, disabled }: UploadDropzoneProps) {
  const [isDragActive, setIsDragActive] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragActive(false)
    if (disabled) return
    const files = Array.from(event.dataTransfer.files).filter((file) =>
      file.name.toLowerCase().endsWith('.csv'),
    )
    if (files.length > 0) onFilesSelected(files)
  }

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? [])
    if (files.length > 0) onFilesSelected(files)
    event.target.value = ''
  }

  return (
    <div
      className={isDragActive ? `${styles.zone} ${styles.zoneActive}` : styles.zone}
      onDragOver={(event) => {
        event.preventDefault()
        if (!disabled) setIsDragActive(true)
      }}
      onDragLeave={() => setIsDragActive(false)}
      onDrop={handleDrop}
    >
      <p className={styles.prompt}>Drop statement CSVs here</p>
      <p className={styles.hint}>Amex, Capital One, Discover, Citi, or Schwab exports. Multiple files OK.</p>
      <button
        type="button"
        className={styles.browseButton}
        onClick={() => inputRef.current?.click()}
        disabled={disabled}
      >
        Choose files
      </button>
      <input
        ref={inputRef}
        className={styles.hiddenInput}
        type="file"
        accept=".csv"
        multiple
        onChange={handleInputChange}
        disabled={disabled}
        tabIndex={-1}
        aria-hidden="true"
        data-testid="upload-file-input"
      />
    </div>
  )
}
