// app/route-map/page.tsx
"use client"
import { Suspense } from "react"
import { useSearchParams } from "next/navigation"
import RouteSidebar from "@/components/RouteSidebar"
import Map from "@/components/Maps"

// ── Inner component reads search params ──────────────────
function RouteMapContent() {
  const searchParams = useSearchParams()

  const src         = searchParams.get("src") ?? ""
  const dest        = searchParams.get("dest") ?? ""
  const srcStation  = searchParams.get("src_station") ?? ""
  const destStation = searchParams.get("dest_station") ?? ""
  const trainId     = searchParams.get("train_id") ?? ""
  const departure   = searchParams.get("departure") ?? ""
  const arrival     = searchParams.get("arrival") ?? ""
  const duration    = searchParams.get("duration") ?? ""

  // Rebuild travelInfo shape so sidebar renders correctly
  const travelInfo = srcStation ? {
    current_time:    "",
    source_station:  srcStation,
    source_distance: "",
    source_walk:     "",
    dest_station:    destStation,
    dest_distance:   "",
    dest_walk:       "",
    trains: trainId ? [{
      train_id:  trainId,
      departure,
      arrival,
      duration,
    }] : [],
  } : null

  return (
    <div className="flex h-screen overflow-hidden">

      {/* Sidebar — readonly, shows the selected train */}
      <RouteSidebar
        mode="readonly"
        source={src}
        destination={dest}
        travelInfo={travelInfo}
        loading={false}
      />

      {/* Map — two separate legs */}
      <div className="flex-1 relative">
        <Map
          // Leg 1: user's address → boarding station
          // Leg 2: alighting station → user's destination
          source={src}
          destination={dest}
          sourceStation={srcStation}
          destStation={destStation}
        />
      </div>
    </div>
  )
}

// ── Page wraps in Suspense — fixes the "1 Issue" error ───
export default function RouteMapPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center text-gray-400 text-sm">
        Loading route…
      </div>
    }>
      <RouteMapContent />
    </Suspense>
  )
}