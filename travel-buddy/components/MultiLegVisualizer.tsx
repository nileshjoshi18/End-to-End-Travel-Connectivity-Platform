// components/MultiLegVisualizer.tsx
"use client"
import { calculateAutoFare } from "@/utils/fare"
import { useRouter } from "next/navigation"

interface Leg {
  from_stop: string
  to_stop: string
  line: string
  train_id: string
  departure: string
  arrival: string
  train_details: any
}

interface MultiLegInfo {
  start_stop: string
  end_stop: string
  requested_time: string
  final_arrival: string
  legs: Leg[]
  source_station: string
  source_distance: string
  source_walk: string
  dest_station: string
  dest_distance: string
  dest_walk: string
}

interface Props {
  info: MultiLegInfo
  src: string
  dest: string
}

// ── Colour system per line ────────────────────────────────────────────────────
const LINE_STYLES: Record<string, { bg: string; pill: string; text: string; bar: string }> = {
  "Western": {
    bg:   "bg-blue-600",
    pill: "bg-blue-100 text-blue-700",
    text: "text-blue-600",
    bar:  "bg-blue-500",
  },
  "Central": {
    bg:   "bg-orange-500",
    pill: "bg-orange-100 text-orange-700",
    text: "text-orange-600",
    bar:  "bg-orange-400",
  },
  "Harbour": {
    bg:   "bg-teal-600",
    pill: "bg-teal-100 text-teal-700",
    text: "text-teal-600",
    bar:  "bg-teal-500",
  },
}
const FALLBACK_STYLE = {
  bg:   "bg-purple-600",
  pill: "bg-purple-100 text-purple-700",
  text: "text-purple-600",
  bar:  "bg-purple-400",
}
const getStyle = (line: string) => LINE_STYLES[line] ?? FALLBACK_STYLE

export default function MultiLegVisualizer({ info, src, dest }: Props) {
  const router = useRouter()

  const distSrc  = parseFloat(info.source_distance) || 0
  const distDest = parseFloat(info.dest_distance)   || 0
  const fareSrc  = calculateAutoFare(distSrc)
  const fareDest = calculateAutoFare(distDest)
  const totalAutoFare = fareSrc + fareDest

  // Derive first departure and total duration label
  const firstDep  = info.legs[0]?.departure ?? "—"
  const finalArr  = info.final_arrival

  const handleLegClick = (leg: Leg) => {
    router.push(`/train/${leg.train_id}`)
  }

  return (
    <div className="space-y-4">

      {/* ── Journey header card ──────────────────────────────────────────── */}
      <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-5">
          <span className="text-lg">🔀</span>
          <div>
            <h2 className="text-sm font-bold text-gray-800">Interchange Route</h2>
            <p className="text-[11px] text-gray-400">{info.legs.length} train{info.legs.length !== 1 ? "s" : ""} · direct route unavailable</p>
          </div>
          <div className="ml-auto text-right">
            <p className="text-[10px] text-gray-400 uppercase tracking-widest">Departs</p>
            <p className="text-xl font-black text-gray-900 tabular-nums">{firstDep}</p>
          </div>
        </div>

        {/* Walk → Train legs → Walk */}
        <div className="flex items-stretch gap-0 overflow-x-auto pb-1">

          {/* Walk to first station */}
          <div className="flex flex-col items-center flex-shrink-0 min-w-[64px]">
            <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center text-lg mb-1">🚶</div>
            <p className="text-[9px] font-bold text-gray-500 text-center leading-tight">Walk</p>
            <p className="text-[9px] text-gray-400 text-center">{info.source_walk}</p>
            {fareSrc > 0 && <p className="text-[9px] font-bold text-blue-600">₹{fareSrc}</p>}
          </div>

          {info.legs.map((leg, i) => {
            const style = getStyle(leg.line)
            const isLast = i === info.legs.length - 1
            return (
              <div key={i} className="flex items-stretch flex-shrink-0">

                {/* Connector arrow */}
                <div className="flex items-center px-1">
                  <div className="w-6 h-px bg-gray-300" />
                  <svg className="w-3 h-3 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"/>
                  </svg>
                </div>

                {/* Train leg block */}
                <div
                  onClick={() => handleLegClick(leg)}
                  className={`flex flex-col justify-between px-3 py-2.5 rounded-2xl cursor-pointer transition-all hover:scale-[1.02] hover:shadow-md min-w-[110px] ${style.bg} text-white`}
                >
                  <div>
                    <span className={`text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded-full ${style.pill}`}>
                      {leg.line}
                    </span>
                    <p className="text-[9px] font-bold mt-1.5 opacity-80 truncate max-w-[95px]">{leg.from_stop}</p>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <p className="text-sm font-black tabular-nums">{leg.departure}</p>
                    <div className="flex flex-col items-center opacity-60 px-1">
                      <div className={`w-8 h-px ${style.bar}`} />
                    </div>
                    <p className="text-sm font-black tabular-nums">{leg.arrival}</p>
                  </div>
                  <p className="text-[9px] opacity-70 truncate max-w-[95px] mt-1">{leg.to_stop}</p>
                  {/* Tap hint */}
                  <p className="text-[8px] opacity-40 text-center mt-1 uppercase tracking-widest">· · ·</p>
                </div>

                {/* Interchange badge between legs */}
                {!isLast && (
                  <div className="flex items-center px-1">
                    <div className="w-6 h-px bg-gray-300" />
                    <div className="flex flex-col items-center">
                      <div className="w-6 h-6 bg-amber-100 border-2 border-amber-400 rounded-full flex items-center justify-center">
                        <span className="text-[9px]">⇄</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}

          {/* Connector to walk */}
          <div className="flex items-center px-1">
            <div className="w-6 h-px bg-gray-300" />
            <svg className="w-3 h-3 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"/>
            </svg>
          </div>

          {/* Walk from last station */}
          <div className="flex flex-col items-center flex-shrink-0 min-w-[64px]">
            <div className="w-10 h-10 bg-emerald-50 rounded-full flex items-center justify-center text-lg mb-1">📍</div>
            <p className="text-[9px] font-bold text-gray-500 text-center leading-tight">Walk</p>
            <p className="text-[9px] text-gray-400 text-center">{info.dest_walk}</p>
            {fareDest > 0 && <p className="text-[9px] font-bold text-blue-600">₹{fareDest}</p>}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-5 pt-4 border-t border-gray-100 flex justify-between items-center">
          <p className="text-sm font-bold text-gray-500 uppercase">Total Auto Fare</p>
          <p className="text-2xl font-black text-blue-700">₹{totalAutoFare}</p>
        </div>
      </div>

      {/* ── Per-leg detail cards ──────────────────────────────────────────── */}
      <div className="space-y-3">
        {info.legs.map((leg, i) => {
          const style = getStyle(leg.line)
          const stops: any[] = leg.train_details?.stops ?? []
          // Find the window of stops relevant to this leg
          const fromIdx = stops.findIndex((s: any) => s.stop_name === leg.from_stop || s.stop_id === leg.from_stop)
          const toIdx   = stops.findIndex((s: any) => s.stop_name === leg.to_stop   || s.stop_id === leg.to_stop)
          const legStops = fromIdx !== -1 && toIdx !== -1 ? stops.slice(fromIdx, toIdx + 1) : []

          return (
            <div key={i} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">

              {/* Leg header */}
              <div
                className={`flex items-center justify-between px-5 py-3 cursor-pointer hover:opacity-90 transition ${style.bg} text-white`}
                onClick={() => handleLegClick(leg)}
              >
                <div className="flex items-center gap-2">
                  <span className="text-base font-black opacity-70">#{i + 1}</span>
                  <div>
                    <p className="text-xs font-bold">{leg.line} Line</p>
                    <p className="text-[10px] opacity-70">{leg.train_id}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-black tabular-nums">{leg.departure} → {leg.arrival}</p>
                  <p className="text-[10px] opacity-70">{leg.from_stop} → {leg.to_stop}</p>
                </div>
                <svg className="w-4 h-4 opacity-60 ml-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </div>

              {/* Mini stop list */}
              {legStops.length > 0 && (
                <div className="px-5 py-3 space-y-0">
                  <div className="relative">
                    <div className="absolute left-[7px] top-3 bottom-3 w-0.5 bg-gray-100" />
                    {legStops.map((stop, si) => {
                      const isFirst = si === 0
                      const isLast  = si === legStops.length - 1
                      return (
                        <div key={stop.stop_id} className="relative flex items-center gap-3 py-1.5">
                          <div className={`relative z-10 rounded-full border-2 flex-shrink-0 ${
                            isFirst || isLast
                              ? `w-3.5 h-3.5 ${style.bg} border-current`
                              : "w-2.5 h-2.5 bg-white border-gray-300"
                          }`} />
                          <div className="flex-1 flex justify-between items-center">
                            <p className={`text-xs leading-tight ${isFirst || isLast ? "font-bold text-gray-900" : "text-gray-500"}`}>
                              {stop.stop_name}
                            </p>
                            <p className={`text-xs tabular-nums ${isFirst || isLast ? `font-bold ${style.text}` : "text-gray-400"}`}>
                              {stop.arrival_time}
                            </p>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* ── Tap hint ─────────────────────────────────────────────────────── */}
      <p className="text-center text-[10px] text-gray-300 uppercase tracking-widest">
        tap any train segment to view full schedule →
      </p>
    </div>
  )
}
