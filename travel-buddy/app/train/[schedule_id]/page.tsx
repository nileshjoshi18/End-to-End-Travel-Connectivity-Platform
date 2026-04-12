"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"

interface Stop {
  sequence_no: number
  stop_id: string
  stop_name: string
  arrival_time: string
}

interface TrainDetails {
  schedule_id: string
  route_id: string
  origin_departure: string
  total_stops: number
  stops: Stop[]
}

export default function TrainDetailPage() {
  const params = useParams()                                    
  const schedule_id = Array.isArray(params.schedule_id)        
    ? params.schedule_id[0]
    : params.schedule_id

  const router = useRouter()
  const [details, setDetails] = useState<TrainDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    console.log("schedule_id from params:", schedule_id)       

    if (!schedule_id) {
      setError("No schedule ID in URL.")
      setLoading(false)
      return
    }

    fetch(`http://127.0.0.1:8001/get-train-details?schedule_id=${encodeURIComponent(schedule_id)}`)
      .then((r) => {
        if (!r.ok) throw new Error(`Server returned ${r.status}`)
        return r.json()
      })
      .then((data) => {
        console.log("API response:", data)                     
        setDetails(data)
      })
      .catch((e) => {
        console.error("Fetch error:", e)
        setError(e.message)
      })
      .finally(() => setLoading(false))
  }, [schedule_id])

  if (loading) return (
    <div className="flex items-center justify-center h-screen bg-gray-50">
      <div className="text-center space-y-3">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm text-gray-400">Loading train schedule…</p>
      </div>
    </div>
  )

  if (error || !details) return (
    <div className="flex items-center justify-center h-screen bg-gray-50">
      <div className="text-center space-y-4">
        <p className="text-gray-500 font-medium">Could not load train details</p>
        <p className="text-sm text-red-400">{error}</p>
        <button
          onClick={() => router.back()}
          className="text-blue-600 text-sm underline"
        >
          Go back
        </button>
      </div>
    </div>
  )

  // ── Detail view ──────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-blue-700 px-6 py-4 flex items-center gap-4">
        <button
          onClick={() => router.back()}
          className="text-blue-200 hover:text-white transition-colors"
          aria-label="Back"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h1 className="text-white font-bold text-base leading-tight">Train {details.schedule_id}</h1>
          <p className="text-blue-200 text-xs">Route {details.route_id} · departs {details.origin_departure}</p>
        </div>
        <div className="ml-auto text-right">
          <p className="text-white font-bold text-base">{details.total_stops}</p>
          <p className="text-blue-200 text-xs">stops</p>
        </div>
      </div>
      <div className="max-w-lg mx-auto px-4 py-6">
        <div className="relative">
          <div className="absolute left-[27px] top-4 bottom-4 w-0.5 bg-gray-200" />
          <div className="space-y-0">
            {details.stops.map((stop, i) => {
              const isFirst = i === 0
              const isLast  = i === details.stops.length - 1
              const isTerminal = isFirst || isLast

              return (
                <div key={stop.stop_id} className="relative flex items-start gap-4 py-3">
                  <div className={`relative z-10 flex-shrink-0 rounded-full border-2 mt-1 ${
                    isTerminal
                      ? "w-4 h-4 ml-5 bg-blue-600 border-blue-600"
                      : "w-3 h-3 ml-[22px] bg-white border-gray-300"
                  }`} />
                  <div className="flex-1 flex items-center justify-between min-w-0">
                    <div className="min-w-0">
                      <p className={`text-sm leading-tight truncate ${
                        isTerminal ? "font-bold text-gray-900" : "font-medium text-gray-700"
                      }`}>
                        {stop.stop_name}
                      </p>
                      <p className="text-[11px] text-gray-400 mt-0.5">Stop {stop.sequence_no}</p>
                    </div>
                    <p className={`tabular-nums text-sm ml-4 flex-shrink-0 ${
                      isTerminal ? "font-bold text-blue-600" : "text-gray-500"
                    }`}>
                      {stop.arrival_time}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}