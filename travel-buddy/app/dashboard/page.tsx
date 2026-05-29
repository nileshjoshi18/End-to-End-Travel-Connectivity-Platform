// app/dashboard/page.tsx
"use client"
import { useState } from "react"
import { useSession } from "next-auth/react"
import RouteSidebar from "@/components/RouteSidebar"
import RouteVisualizer from "@/components/RouteVisualizer"
import MultiLegVisualizer from "@/components/MultiLegVisualizer"

export type RouteMode = "single" | "multi" | null

export default function Dashboard() {
  const { data: session } = useSession()

  const [travelInfo, setTravelInfo]   = useState<any>(null)
  const [multiLegInfo, setMultiLegInfo] = useState<any>(null)
  const [loading, setLoading]         = useState(false)
  const [activeSrc, setActiveSrc]     = useState("")
  const [activeDest, setActiveDest]   = useState("")
  const [routeMode, setRouteMode]     = useState<RouteMode>(null)
  const [errorMsg, setErrorMsg]       = useState<string | null>(null)

  const handleCalculateRoute = async (src: string, dest: string) => {
    setActiveSrc(src)
    setActiveDest(dest)
    setLoading(true)
    setTravelInfo(null)
    setMultiLegInfo(null)
    setRouteMode(null)
    setErrorMsg(null)

    try {
      // ── Step 1: Try single-line connectivity ──────────────────────────────
      const res  = await fetch(
        `http://127.0.0.1:8000/get-connectivity?source=${encodeURIComponent(src)}&destination=${encodeURIComponent(dest)}`
      )
      const data = await res.json()

      const trains: any[] = data.trains ?? []

      if (trains.length > 0) {
        // Single-line route found ✅
        setTravelInfo({
          source_station:  data.source_connectivity?.station_name        || "Unknown",
          source_distance: data.source_connectivity?.distance_to_station  || "0km",
          source_walk:     data.source_connectivity?.walking_time          || "0 min",
          dest_station:    data.destination_connectivity?.station_name        || "Unknown",
          dest_distance:   data.destination_connectivity?.distance_to_station || "0km",
          dest_walk:       data.destination_connectivity?.walking_time        || "0 min",
          trains,
          current_time:    data.current_time || "",
        })
        setRouteMode("single")
        return
      }

      // ── Step 2: Fallback — try multi-line resultant routes 
      const srcStation  = data.source_connectivity?.station_name
      const destStation = data.destination_connectivity?.station_name

      if (!srcStation || !destStation) {
        setErrorMsg("Could not identify nearby stations for your journey.")
        return
      }

      const currentTime = data.current_time || new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false })

      const multiRes = await fetch(
        `http://127.0.0.1:8002/resultant-routes?start_stop=${encodeURIComponent(srcStation)}&end_stop=${encodeURIComponent(destStation)}&user_time=${encodeURIComponent(currentTime)}`
      )

      if (!multiRes.ok) {
        setErrorMsg("No routes found between these locations — try different addresses.")
        return
      }

      const multiData = await multiRes.json()
      setMultiLegInfo({
        ...multiData,
        // Attach connectivity metadata so the visualizer can show walk info
        source_station:  srcStation,
        source_distance: data.source_connectivity?.distance_to_station || "0km",
        source_walk:     data.source_connectivity?.walking_time         || "0 min",
        dest_station:    destStation,
        dest_distance:   data.destination_connectivity?.distance_to_station || "0km",
        dest_walk:       data.destination_connectivity?.walking_time        || "0 min",
      })
      setRouteMode("multi")

    } catch (err) {
      console.error(err)
      setErrorMsg("Something went wrong. Please check your connection and try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <RouteSidebar
        onCalculate={handleCalculateRoute}
        travelInfo={travelInfo}
        multiLegInfo={multiLegInfo}
        loading={loading}
        source={activeSrc}
        destination={activeDest}
        routeMode={routeMode}
      />

      <main className="flex-1 p-10 overflow-y-auto">
        <div className="max-w-4xl mx-auto space-y-8">
          <h1 className="text-2xl font-bold text-gray-800">Route Optimization</h1>

          {routeMode === "single" && travelInfo && (
            <RouteVisualizer
              info={travelInfo}
              src={activeSrc}
              dest={activeDest}
              selectedTrain={travelInfo.trains?.[0]}
            />
          )}

          {routeMode === "multi" && multiLegInfo && (
            <MultiLegVisualizer
              info={multiLegInfo}
              src={activeSrc}
              dest={activeDest}
            />
          )}

          {!routeMode && !loading && !errorMsg && (
            <div className="h-96 border-2 border-dashed border-gray-200 rounded-3xl flex items-center justify-center text-gray-400">
              Enter your journey details to see the most cost-effective route.
            </div>
          )}

          {loading && (
            <div className="h-96 border-2 border-dashed border-gray-200 rounded-3xl flex items-center justify-center">
              <div className="text-center space-y-3">
                <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="text-sm text-gray-400">Finding the best route…</p>
              </div>
            </div>
          )}

          {errorMsg && !loading && (
            <div className="h-96 border-2 border-dashed border-red-200 rounded-3xl flex items-center justify-center">
              <div className="text-center space-y-2">
                <p className="text-2xl">🚫</p>
                <p className="text-sm font-medium text-gray-600">{errorMsg}</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
