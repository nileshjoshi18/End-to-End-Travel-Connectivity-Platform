// components/CrowdBadge.tsx
import { getCrowdStyle } from "@/utils/transitDesign"

interface Props {
  score: number | null | undefined
  compact?: boolean
}

export default function CrowdBadge({ score, compact = false }: Props) {
  const style = getCrowdStyle(score)

  if (compact) {
    return (
      <span
        className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold ${style.bg} ${style.text}`}
        title={`Crowd: ${style.label}`}
      >
        <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
        {style.label} Crowd
      </span>
    )
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-bold ${style.bg} ${style.text}`}>
      <span className={`w-2 h-2 rounded-full ${style.dot}`} />
      {style.label} crowd
    </span>
  )
}