// components/RouteSidebar.tsx
"use client"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"

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

interface Props {
  onCalculate?: (src: string, dst: string) => void
  travelInfo: TravelInfo | null
  loading: boolean
  mode?: "input" | "readonly"
  source?: string
  destination?: string
}

export default function RouteSidebar({
  onCalculate,
  travelInfo,
  loading,
  mode = "input",
  source = "",
  destination = "",
}: Props) {
  const [tempSource, setTempSource] = useState(source)
  const [tempDestination, setTempDestination] = useState(destination)
  const router = useRouter()

  useEffect(() => {
    setTempSource(source)
    setTempDestination(destination)
  }, [source, destination])

  const handleTrainClick = (train: Train) => {
    const params = new URLSearchParams({
      src:          tempSource || source,
      dest:         tempDestination || destination,
      src_station:  travelInfo?.source_station ?? "",
      dest_station: travelInfo?.dest_station ?? "",
      train_id:     train.train_id,
      departure:    train.departure,
      arrival:      train.arrival,
      duration:     train.duration,
    })
    router.push(`/train/${train.train_id}`) 
  }

  return (
    <div className="w-80 h-full bg-white shadow-xl flex flex-col overflow-hidden border-r border-gray-100">

      {/* Header */}
      <div className="bg-blue-700 px-6 py-5">
        <h2 className="text-lg font-bold text-white tracking-wide">Mumbai Transport Planner</h2>
        <p className="text-blue-200 text-xs mt-0.5">
          {mode === "input" ? "Find the next trains between stations" : "Viewing active route details"}
        </p>
      </div>

      {/* Input or Read-Only Section */}
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

      {/* Connectivity & Train List */}
      {travelInfo && (
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
                    {/* Tap hint */}
                    <span className={`absolute bottom-1.5 left-1/2 -translate-x-1/2 text-[8px] uppercase tracking-widest ${i === 0 ? "text-blue-300" : "text-gray-300"}`}>
                      · · ·
                    </span>
                    <div>
                      <p className={`text-[9px] font-bold uppercase tracking-wide ${i === 0 ? "text-blue-200" : "text-gray-400"}`}>
                        {train.train_id}
                      </p>
                      <p className={`text-xl font-black tabular-nums ${i === 0 ? "text-white" : "text-gray-900"}`}>
                        {train.departure}
                      </p>
                    </div>

                    <div className="flex flex-col items-center px-2 opacity-60">
                      <p className="text-[9px] font-bold mb-1">{train.duration}</p>
                      <div className={`w-12 h-px ${i === 0 ? "bg-blue-300" : "bg-gray-300"}`} />
                    </div>

                    <div className="text-right">
                      <p className={`text-[9px] font-bold uppercase tracking-wide ${i === 0 ? "text-blue-200" : "text-gray-400"}`}>Arrives</p>
                      <p className={`text-xl font-black tabular-nums ${i === 0 ? "text-white" : "text-gray-900"}`}>
                        {train.arrival}
                      </p>
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
    </div>
  )
}