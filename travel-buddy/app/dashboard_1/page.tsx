// app/dashboard/page.tsx
"use client"

import { useState } from "react"
import { useSession } from "next-auth/react"
import Map from "@/components/Maps"
import RouteSidebar from "@/components/RouteSidebar"

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

export default function Dashboard() {
  const { data: session } = useSession()

  const [activeSource, setActiveSource] = useState("")
  const [activeDestination, setActiveDestination] = useState("")
  const [travelInfo, setTravelInfo] = useState<TravelInfo | null>(null)
  const [loading, setLoading] = useState(false)

  const handleCalculateRoute = async (src: string, dest: string) => {
    setActiveSource(src)
    setActiveDestination(dest)
    setTravelInfo(null)

    try {
      setLoading(true)
      const res = await fetch(
        `http://127.0.0.1:8000/get-connectivity?source=${encodeURIComponent(src)}&destination=${encodeURIComponent(dest)}`
      )

      if (!res.ok) throw new Error("API request failed")

      const data = await res.json()

      setTravelInfo((prev) => {
        console.log("travelInfo.trains:", data.trains)   // ← add this
        return {
          current_time:    data.current_time ?? "",
          source_station:  data.source_connectivity.station_name,
          source_distance: data.source_connectivity.distance_to_station,
          source_walk:     data.source_connectivity.walking_time,
          dest_station:    data.destination_connectivity.station_name,
          dest_distance:   data.destination_connectivity.distance_to_station,
          dest_walk:       data.destination_connectivity.walking_time,
          trains:          data.trains ?? [],
        }
      })
    } catch (err) {
      console.error("Route fetch error:", err)
      setTravelInfo(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <RouteSidebar
        onCalculate={handleCalculateRoute}
        travelInfo={travelInfo}
        loading={loading}
      />
      <div className="flex-1 relative">
        <Map
          source={activeSource}
          destination={activeDestination}
          onRouteCalculated={(info: any) => setTravelInfo(info)}
        />
      </div>
    </div>
  )
}