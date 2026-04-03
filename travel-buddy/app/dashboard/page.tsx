"use client"

import { useState } from "react"
import Map from "@/components/Maps" // Corrected import path
import RouteSidebar from "@/components/RouteSidebar"

export default function Dashboard() {
  const [source, setSource] = useState("")
  const [destination, setDestination] = useState("")
  const [travelInfo, setTravelInfo] = useState<{ distance: string; duration: string } | null>(null)

  return (
    <div className="flex h-screen overflow-hidden">
      <RouteSidebar
        setSource={setSource}
        setDestination={setDestination}
        travelInfo={travelInfo}
      />

      <div className="flex-1 relative">
        {/* The component from step 1 */}
        <Map
          source={source}
          destination={destination}
          onRouteCalculated={(info) => setTravelInfo(info)}
        />
      </div>
    </div>
  )
}