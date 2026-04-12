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
  src: string        // ← raw address from dashboard
  dest: string       // ← raw address from dashboard
  selectedTrain?: Train  // ← first train or whichever is selected
}

export default function RouteVisualizer({ info, src, dest, selectedTrain }: RouteVisualizerProps) {
  const distSrc  = parseFloat(info.source_distance) || 0
  const distDest = parseFloat(info.dest_distance) || 0
  const router   = useRouter()

  const fareSrc   = calculateAutoFare(distSrc)
  const fareDest  = calculateAutoFare(distDest)
  const totalPrice = fareSrc + fareDest

  const handleRedirect = () => {
    const train = selectedTrain ?? info.trains?.[0]
    const params = new URLSearchParams({
      src:          src,
      dest:         dest,
      src_station:  info.source_station ?? "",
      dest_station: info.dest_station ?? "",
      train_id:     train?.train_id  ?? "",
      departure:    train?.departure ?? "",
      arrival:      train?.arrival   ?? "",
      duration:     train?.duration  ?? "",
    })
    router.push(`/route-map?${params.toString()}`)
  }

  return (
    <div onClick={handleRedirect} className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm cursor-pointer hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div className="text-center">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">🚶</div>
          <p className="text-xs font-bold mt-2">Start</p>
        </div>

        <div className="flex-1 flex flex-col items-center px-4">
          <span className="text-[10px] font-bold text-blue-600">₹{fareSrc}</span>
          <div className="w-full h-px bg-gray-300 my-1" />
          <span className="text-[10px] text-gray-500">{info.source_walk}</span>
        </div>

        <div className="flex gap-4">
          <div className="bg-blue-600 text-white px-4 py-2 rounded-xl text-xs font-bold">{info.source_station}</div>
          <div className="text-gray-400">→</div>
          <div className="bg-blue-600 text-white px-4 py-2 rounded-xl text-xs font-bold">{info.dest_station}</div>
        </div>

        <div className="flex-1 flex flex-col items-center px-4">
          <span className="text-[10px] font-bold text-blue-600">₹{fareDest}</span>
          <div className="w-full h-px bg-gray-300 my-1" />
          <span className="text-[10px] text-gray-500">{info.dest_walk}</span>
        </div>

        <div className="text-center">
          <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">📍</div>
          <p className="text-xs font-bold mt-2">End</p>
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-gray-100 flex justify-between items-center">
        <p className="text-sm font-bold text-gray-500 uppercase">Total Auto Fare</p>
        <p className="text-2xl font-black text-blue-700">₹{totalPrice}</p>
      </div>

      {/* Click hint */}
      <p className="text-center text-[10px] text-gray-300 mt-4 uppercase tracking-widest">tap to view on map →</p>
    </div>
  )
}