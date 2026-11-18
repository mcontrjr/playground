/** Small inline SVG icon set — no icon library dependency. Every icon
 * uses `stroke="currentColor"` so it inherits whatever color the
 * surrounding button/text already uses, including per-theme tokens. */

interface IconProps {
  size?: number
  className?: string
}

export function PlusIcon({ size = 14, className }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M8 2.5V13.5" />
      <path d="M2.5 8H13.5" />
    </svg>
  )
}
