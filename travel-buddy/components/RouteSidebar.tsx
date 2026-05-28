// components/RouteSidebar.tsx
"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import type { RouteMode } from "@/app/dashboard/page"

interface Train {
  train_id: string
  departure: string
  arrival: string
  duration: string
}

interface TravelInfo {
  current_time: string
  source_station: string
  source_distance: string
  source_walk: string
  dest_station: string
  dest_distance: string
  dest_walk: string
  trains: Train[]
}

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
  onCalculate?: (src: string, dst: string) => void
  travelInfo: TravelInfo | null
  multiLegInfo: MultiLegInfo | null
  loading: boolean
  mode?: "input" | "readonly"
  source?: string
  destination?: string
  routeMode: RouteMode
}

export default function RouteSidebar({
  onCalculate,
  travelInfo,
  multiLegInfo,
  loading,
  mode = "input",
  source = "",
  destination = "",
  routeMode,
}: Props) {
  const [tempSource, setTempSource] = useState(source)
  const [tempDestination, setTempDestination] = useState(destination)
  const router = useRouter()

  useEffect(() => {
    setTempSource(source)
    setTempDestination(destination)
  }, [source, destination])

  const handleTrainClick = (train: Train) => {
    router.push(`/train/${train.train_id}`)
  }

  const handleLegClick = (leg: Leg) => {
    router.push(`/train/${leg.train_id}`)
  }

  // ── Line colour helper ────────────────────────────────────────────────────
  const lineColors: Record<string, { bg: string; text: string; border: string; dot: string }> = {
    "Western":  { bg: "bg-blue-50",   text: "text-blue-700",   border: "border-blue-200",   dot: "bg-blue-500"   },
    "Central":  { bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200", dot: "bg-orange-500" },
    "Harbour":  { bg: "bg-teal-50",   text: "text-teal-700",   border: "border-teal-200",   dot: "bg-teal-500"   },
  }
  const fallbackColor = { bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200", dot: "bg-purple-500" }

  const getLineColor = (line: string) => lineColors[line] ?? fallbackColor

  return (
    <div className="w-80 h-full bg-white shadow-xl flex flex-col overflow-hidden border-r border-gray-100">

      {/* Header */}
      <div className="bg-blue-700 px-6 py-5">
        <h2 className="text-lg font-bold text-white tracking-wide">Mumbai Transport Planner</h2>
        <p className="text-blue-200 text-xs mt-0.5">
          {mode === "input" ? "Find the next trains between stations" : "Viewing active route details"}
        </p>
      </div>

      {/* Input / Read-Only */}
      <div className="px-5 py-5 space-y-3 border-b border-gray-100 bg-white">
        {mode === "input" ? (
          <>
            <div>
              <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">From</label>
              <input
                type="text"
                placeholder="e.g. Gateway of India"
                value={tempSource}
                onChange={(e) => setTempSource(e.target.value)}
                className="w-full mt-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
              />
            </div>
            <div>
              <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">To</label>
              <input
                type="text"
                placeholder="e.g. Infiniti Mall"
                value={tempDestination}
                onChange={(e) => setTempDestination(e.target.value)}
                className="w-full mt-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none transition"
              />
            </div>
            <button
              onClick={() => onCalculate?.(tempSource, tempDestination)}
              disabled={loading || !tempSource || !tempDestination}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-bold py-2.5 rounded-lg transition-all active:scale-95"
            >
              {loading ? "Searching…" : "Find Routes"}
            </button>
          </>
        ) : (
          <div className="space-y-4 py-1">
            <div className="relative pl-4 border-l-2 border-blue-500">
              <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Starting Point</p>
              <p className="text-sm font-bold text-gray-800 break-words">{source}</p>
            </div>
            <div className="relative pl-4 border-l-2 border-emerald-500">
              <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Destination</p>
              <p className="text-sm font-bold text-gray-800 break-words">{destination}</p>
            </div>
          </div>
        )}
      </div>

      {/* ── SINGLE LINE: Connectivity + Trains ────────────────────────────── */}
      {routeMode === "single" && travelInfo && (
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 bg-gray-50/30">
          <div className="grid grid-cols-2 gap-2">
            <div className="p-3 bg-blue-50 rounded-xl border border-blue-100">
              <p className="text-[9px] font-bold text-blue-500 uppercase tracking-widest mb-1">Board at</p>
              <p className="text-sm font-bold text-gray-900 leading-tight">{travelInfo.source_station}</p>
              <p className="text-[10px] text-gray-400 mt-1">{travelInfo.source_distance} · {travelInfo.source_walk} walk</p>
            </div>
            <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
              <p className="text-[9px] font-bold text-emerald-600 uppercase tracking-widest mb-1">Alight at</p>
              <p className="text-sm font-bold text-gray-900 leading-tight">{travelInfo.dest_station}</p>
              <p className="text-[10px] text-gray-400 mt-1">{travelInfo.dest_distance} · {travelInfo.dest_walk} walk</p>
            </div>
          </div>

          {(travelInfo.trains ?? []).length > 0 ? (
            <div>
              <div className="flex items-center justify-between mb-3 px-1">
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Available Trains</p>
                {travelInfo.current_time && (
                  <span className="text-[9px] font-medium text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                    as of {travelInfo.current_time}
                  </span>
                )}
              </div>
              <div className="space-y-2">
                {travelInfo.trains.map((train, i) => (
                  <div
                    key={train.train_id}
                    onClick={() => handleTrainClick(train)}
                    className={`relative flex items-center justify-between px-4 py-3 rounded-xl border cursor-pointer transition-all hover:scale-[1.01] hover:shadow-md active:scale-[0.99] ${
                      i === 0
                        ? "bg-blue-600 border-blue-600 text-white shadow-md shadow-blue-100"
                        : "bg-white border-gray-100 text-gray-800"
                    }`}
                  >
                    <span className={`absolute bottom-1.5 left-1/2 -translate-x-1/2 text-[8px] uppercase tracking-widest ${i === 0 ? "text-blue-300" : "text-gray-300"}`}>· · ·</span>
                    <div>
                      <p className={`text-[9px] font-bold uppercase tracking-wide ${i === 0 ? "text-blue-200" : "text-gray-400"}`}>{train.train_id}</p>
                      <p className={`text-xl font-black tabular-nums ${i === 0 ? "text-white" : "text-gray-900"}`}>{train.departure}</p>
                    </div>
                    <div className="flex flex-col items-center px-2 opacity-60">
                      <p className="text-[9px] font-bold mb-1">{train.duration}</p>
                      <div className={`w-12 h-px ${i === 0 ? "bg-blue-300" : "bg-gray-300"}`} />
                    </div>
                    <div className="text-right">
                      <p className={`text-[9px] font-bold uppercase tracking-wide ${i === 0 ? "text-blue-200" : "text-gray-400"}`}>Arrives</p>
                      <p className={`text-xl font-black tabular-nums ${i === 0 ? "text-white" : "text-gray-900"}`}>{train.arrival}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-10 bg-white rounded-2xl border border-dashed border-gray-200">
              <p className="text-sm text-gray-400">No active schedules found.</p>
            </div>
          )}
        </div>
      )}

      {/* ── MULTI LINE: Legs ──────────────────────────────────────────────── */}
      {routeMode === "multi" && multiLegInfo && (
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 bg-gray-50/30">

          {/* Badge */}
          <div className="flex items-center gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-xl">
            <span className="text-amber-500 text-base">🔀</span>
            <div>
              <p className="text-[10px] font-bold text-amber-700 uppercase tracking-widest">Interchange Route</p>
              <p className="text-[10px] text-amber-600">{multiLegInfo.legs.length} leg{multiLegInfo.legs.length !== 1 ? "s" : ""} · arrives {multiLegInfo.final_arrival}</p>
            </div>
          </div>

          {/* Walk to first station */}
          <div className="grid grid-cols-2 gap-2">
            <div className="p-3 bg-blue-50 rounded-xl border border-blue-100">
              <p className="text-[9px] font-bold text-blue-500 uppercase tracking-widest mb-1">Walk to</p>
              <p className="text-sm font-bold text-gray-900 leading-tight">{multiLegInfo.source_station}</p>
              <p className="text-[10px] text-gray-400 mt-1">{multiLegInfo.source_walk} walk</p>
            </div>
            <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
              <p className="text-[9px] font-bold text-emerald-600 uppercase tracking-widest mb-1">Walk from</p>
              <p className="text-sm font-bold text-gray-900 leading-tight">{multiLegInfo.dest_station}</p>
              <p className="text-[10px] text-gray-400 mt-1">{multiLegInfo.dest_walk} walk</p>
            </div>
          </div>

          {/* Legs timeline */}
          <div>
            <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3 px-1">Journey Legs</p>
            <div className="relative">
              {/* Vertical connector */}
              <div className="absolute left-3.5 top-5 bottom-5 w-0.5 bg-gray-200 z-0" />

              <div className="space-y-2">
                {multiLegInfo.legs.map((leg, i) => {
                  const colors = getLineColor(leg.line)
                  const isLast = i === multiLegInfo.legs.length - 1
                  return (
                    <div key={i} className="relative z-10">
                      {/* Interchange pill between legs */}
                      {i > 0 && (
                        <div className="flex items-center gap-2 ml-8 mb-2">
                          <div className="flex-1 h-px bg-dashed border-t border-dashed border-gray-300" />
                          <span className="text-[9px] font-bold text-gray-400 uppercase tracking-widest bg-white px-2">
                            change here
                          </span>
                          <div className="flex-1 h-px border-t border-dashed border-gray-300" />
                        </div>
                      )}

                      <div
                        onClick={() => handleLegClick(leg)}
                        className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer transition-all hover:scale-[1.01] hover:shadow-sm active:scale-[0.99] ${colors.bg} ${colors.border}`}
                      >
                        {/* Dot */}
                        <div className={`mt-1 w-3 h-3 rounded-full flex-shrink-0 ${colors.dot}`} />

                        <div className="flex-1 min-w-0">
                          {/* Line badge */}
                          <div className="flex items-center gap-1.5 mb-1.5">
                            <span className={`text-[9px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded-full bg-white/70 ${colors.text}`}>
                              {leg.line} Line
                            </span>
                            <span className={`text-[9px] text-gray-400`}>{leg.train_id}</span>
                          </div>

                          {/* From → To */}
                          <p className="text-[11px] font-bold text-gray-800 truncate">{leg.from_stop}</p>
                          <div className="flex items-center gap-1 my-0.5">
                            <div className="flex-1 h-px bg-gray-300" />
                            <span className="text-[9px] text-gray-400">→</span>
                            <div className="flex-1 h-px bg-gray-300" />
                          </div>
                          <p className="text-[11px] font-bold text-gray-800 truncate">{leg.to_stop}</p>
                        </div>

                        {/* Times */}
                        <div className="text-right flex-shrink-0">
                          <p className={`text-sm font-black tabular-nums ${colors.text}`}>{leg.departure}</p>
                          <p className="text-[9px] text-gray-400 font-bold my-0.5">↓</p>
                          <p className={`text-sm font-black tabular-nums ${colors.text}`}>{leg.arrival}</p>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* Final arrival summary */}
          <div className="flex items-center justify-between px-4 py-3 bg-emerald-600 rounded-xl text-white">
            <div>
              <p className="text-[9px] font-bold uppercase tracking-widest text-emerald-200">Arrive at destination</p>
              <p className="text-xs text-emerald-100">{multiLegInfo.end_stop}</p>
            </div>
            <p className="text-xl font-black tabular-nums">{multiLegInfo.final_arrival}</p>
          </div>
        </div>
      )}
    </div>
  )
}
