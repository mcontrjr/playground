import styles from './ComingSoon.module.css'

interface ComingSoonProps {
  eyebrow: string
  title: string
  note: string
}

export function ComingSoon({ eyebrow, title, note }: ComingSoonProps) {
  return (
    <section className={styles.wrap}>
      <span className={styles.eyebrow}>{eyebrow}</span>
      <h1 className={styles.heading}>{title}</h1>
      <p className={styles.note}>{note}</p>
    </section>
  )
}
