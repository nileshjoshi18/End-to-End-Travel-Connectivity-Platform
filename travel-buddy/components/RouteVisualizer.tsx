// components/RouteVisualizer.tsx
"use client"
import { calculateAutoFare } from "@/utils/fare"
import { useRouter } from "next/navigation"

interface Train {
  train_id: string
  departure: string
  arrival: string
  duration: string
}

interface RouteVisualizerProps {
  info: any
  src: string
  dest: string
  selectedTrain?: Train
}

export default function RouteVisualizer({ info, src, dest, selectedTrain }: RouteVisualizerProps) {
  const distSrc  = parseFloat(info.source_distance) || 0
  const distDest = parseFloat(info.dest_distance)   || 0
  const router   = useRouter()

  const autoFareSrc  = calculateAutoFare(distSrc)
  const autoFareDest = calculateAutoFare(distDest)
  const trainFare    = info.train_fare ?? null          // from API, null if unavailable
  const totalFare    = autoFareSrc + (trainFare ?? 0) + autoFareDest

  const handleRedirect = () => {
    const train = selectedTrain ?? info.trains?.[0]
    const params = new URLSearchParams({
      src:          src,
      dest:         dest,
      src_station:  info.source_station ?? "",
      dest_station: info.dest_station   ?? "",
      train_id:     train?.train_id     ?? "",
      departure:    train?.departure    ?? "",
      arrival:      train?.arrival      ?? "",
      duration:     train?.duration     ?? "",
      fare:         String(trainFare ?? ""),
    })
  }

  return (
    <div
      onClick={handleRedirect}
      className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
    >
      <div className="flex items-center justify-between">

        {/* Start */}
        <div className="text-center flex-shrink-0">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">🚶</div>
          <p className="text-xs font-bold mt-2">Start</p>
        </div>

        {/* Walk to source station */}
        <div className="flex-1 flex flex-col items-center px-4">
          <span className="text-[10px] font-bold text-blue-600">₹{autoFareSrc}</span>
          <div className="w-full h-px bg-gray-300 my-1" />
          <span className="text-[10px] text-gray-500">{info.source_walk}</span>
        </div>

        {/* Stations + train fare */}
        <div className="flex flex-col items-center gap-1 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="bg-blue-600 text-white px-4 py-2 rounded-xl text-xs font-bold">{info.source_station}</div>
            <div className="flex flex-col items-center gap-0.5">
              <span className="text-gray-400 text-xs">→</span>
              {trainFare != null && (
                <span className="text-[10px] font-black text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full tabular-nums">
                  🚂 ₹{trainFare}
                </span>
              )}
            </div>
            <div className="bg-blue-600 text-white px-4 py-2 rounded-xl text-xs font-bold">{info.dest_station}</div>
          </div>
        </div>

        {/* Walk from dest station */}
        <div className="flex-1 flex flex-col items-center px-4">
          <span className="text-[10px] font-bold text-blue-600">₹{autoFareDest}</span>
          <div className="w-full h-px bg-gray-300 my-1" />
          <span className="text-[10px] text-gray-500">{info.dest_walk}</span>
        </div>

        {/* End */}
        <div className="text-center flex-shrink-0">
          <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">📍</div>
          <p className="text-xs font-bold mt-2">End</p>
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-gray-100 space-y-3">

        <div className="flex flex-wrap gap-x-5 gap-y-1">
          {autoFareSrc > 0 && (
            <span className="text-[11px] text-gray-400">
              🚶 Auto to station <span className="font-bold text-gray-600">₹{autoFareSrc}</span>
            </span>
          )}
          {trainFare != null && (
            <span className="text-[11px] text-gray-400">
              🚂 Train fare <span className="font-bold text-gray-600">₹{trainFare}</span>
            </span>
          )}
          {autoFareDest > 0 && (
            <span className="text-[11px] text-gray-400">
              🚶 Auto from station <span className="font-bold text-gray-600">₹{autoFareDest}</span>
            </span>
          )}
        </div>

        {/* Total */}
        <div className="flex justify-between items-center">
          <p className="text-sm font-bold text-gray-500 uppercase">Total Cost</p>
          <p className="text-2xl font-black text-blue-700">₹{totalFare}</p>
        </div>
      </div>

      <p className="text-center text-[10px] text-gray-300 mt-4 uppercase tracking-widest">
        tap to view on map →
      </p>
    </div>
  )
}