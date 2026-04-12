// components/RouteSidebar.tsx
"use client"
import { useState } from "react"
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
  onCalculate: (src: string, dst: string) => void
  travelInfo: TravelInfo | null
  loading: boolean
}

export default function RouteSidebar({ onCalculate, travelInfo, loading }: Props) {
  const [tempSource, setTempSource] = useState("")
  const [tempDestination, setTempDestination] = useState("")
  const router = useRouter()
  console.log(travelInfo?.source_station)
  return (
    <div className="w-80 h-full bg-white shadow-xl flex flex-col overflow-hidden">

      <div className="bg-blue-700 px-6 py-5">
        <h2 className="text-lg font-bold text-white tracking-wide">Mumbai Local Planner</h2>
        <p className="text-blue-200 text-xs mt-0.5">Find the next trains between stations</p>
      </div>

      <div className="px-5 py-5 space-y-3 border-b border-gray-100">
        <div>
          <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">From</label>
          <input
            type="text"
            placeholder="e.g. Churchgate, Mumbai"
            value={tempSource}
            onChange={(e) => setTempSource(e.target.value)}
            className="w-full mt-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
          />
        </div>
        <div>
          <label className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">To</label>
          <input
            type="text"
            placeholder="e.g. Goregaon, Mumbai"
            value={tempDestination}
            onChange={(e) => setTempDestination(e.target.value)}
            className="w-full mt-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
          />
        </div>
        <button
          onClick={() => onCalculate(tempSource, tempDestination)}
          disabled={loading || !tempSource || !tempDestination}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-sm font-bold py-2.5 rounded-lg transition-all active:scale-95"
        >
          {loading ? "Searching…" : "Find Trains"}
        </button>
      </div>

      {travelInfo && (
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">

          <div className="grid grid-cols-2 gap-2">
            <div className="p-3 bg-blue-50 rounded-xl border border-blue-100">
              <p className="text-[9px] font-bold text-blue-500 uppercase tracking-widest mb-1">Board at</p>
              <p className="text-sm font-bold text-gray-900 leading-tight">{travelInfo.source_station}</p>
              <p className="text-[11px] text-gray-400 mt-1">{travelInfo.source_distance} · {travelInfo.source_walk} walk</p>
            </div>
            <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
              <p className="text-[9px] font-bold text-emerald-600 uppercase tracking-widest mb-1">Alight at</p>
              <p className="text-sm font-bold text-gray-900 leading-tight">{travelInfo.dest_station}</p>
              <p className="text-[11px] text-gray-400 mt-1">{travelInfo.dest_distance} · {travelInfo.dest_walk} walk</p>
            </div>
          </div>

          {(travelInfo.trains ?? []).length > 0 ? (
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Next trains</p>
                {travelInfo.current_time && (
                  <span className="text-[10px] text-gray-400">as of {travelInfo.current_time}</span>
                )}
              </div>
              <div className="space-y-2">
                {travelInfo.trains.map((train, i) => (
                  <div
                    key={train.train_id}
                    onClick={() => router.push(`/train/${train.train_id}`)}
                    className={`relative flex items-center justify-between px-4 py-3 rounded-xl border cursor-pointer transition-all hover:scale-[1.01] hover:shadow-md active:scale-[0.99] ${
                      i === 0
                        ? "bg-blue-600 border-blue-600 text-white"
                        : "bg-gray-50 border-gray-100 text-gray-800"
                    }`}
                  >
                    {/* Tap hint */}
                    <span className={`absolute top-2 right-3 text-[9px] font-medium uppercase tracking-widest ${i === 0 ? "text-blue-300" : "text-gray-300"}`}>
                      details →
                    </span>

                    {/* Left: train ID + departure */}
                    <div>
                      <p className={`text-[10px] font-semibold uppercase tracking-wide ${i === 0 ? "text-blue-200" : "text-gray-400"}`}>
                        Train {train.train_id}
                      </p>
                      <p className={`text-xl font-bold tabular-nums leading-tight ${i === 0 ? "text-white" : "text-gray-900"}`}>
                        {train.departure}
                      </p>
                    </div>

                    {/* Center: duration */}
                    <div className="flex flex-col items-center px-2">
                      <p className={`text-[10px] font-medium ${i === 0 ? "text-blue-200" : "text-gray-400"}`}>{train.duration}</p>
                      <div className={`w-16 h-px mt-1 ${i === 0 ? "bg-blue-400" : "bg-gray-300"}`} />
                      <svg className={`w-3 h-3 mt-0.5 ${i === 0 ? "text-blue-200" : "text-gray-300"}`} fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 18l8-8-8-8v5H2v6h8v5z"/>
                      </svg>
                    </div>

                    {/* Right: arrival */}
                    <div className="text-right">
                      <p className={`text-[10px] font-semibold uppercase tracking-wide ${i === 0 ? "text-blue-200" : "text-gray-400"}`}>arrives</p>
                      <p className={`text-xl font-bold tabular-nums leading-tight ${i === 0 ? "text-white" : "text-gray-900"}`}>
                        {train.arrival}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-6 text-sm text-gray-400">
              No trains found for this route right now.
            </div>
          )}
        </div>
      )}
    </div>
  )
}