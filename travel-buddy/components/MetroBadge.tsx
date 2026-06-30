// components/MetroBadge.tsx
//
// Renders a metro-style circular line pictogram, similar to real Mumbai
// Metro signage (a filled circle with the line number/short code).
// Only used when the line is a metro line — getLineStyle().isMetro gates this.
import { getLineStyle } from "@/utils/transitDesign"

interface Props {
  line: string
  size?: "sm" | "md"
}

export default function MetroBadge({ line, size = "sm" }: Props) {
  const style = getLineStyle(line)
  const dims  = size === "sm" ? "w-4 h-4 text-[8px]" : "w-6 h-6 text-[10px]"

  return (
    <span
      className={`inline-flex items-center justify-center rounded-full ${style.bg} text-white font-black ${dims} shadow-sm ring-1 ring-white/40 flex-shrink-0`}
      title={style.label}
      aria-label={style.label}
    >
      {style.badge}
    </span>
  )
}