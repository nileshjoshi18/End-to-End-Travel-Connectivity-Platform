// app/dashboard/page.tsx
"use client"
import RouteSidebar from "@/components/RouteSidebar"
import RouteVisualizer from "@/components/RouteVisualizer"
import MultiLegVisualizer from "@/components/MultiLegVisualizer"
import Footer from "@/components/Footer"
import { useRouteContext } from "@/context/RouteContext"
import { fetchRoute, fetchAlternates, currentTimeHHMM } from "@/utils/api"
import { useState } from "react"

// Backend now always returns the same unified shape from get_routes/ask
// (legs[] with 1 entry for a direct journey, multiple for an interchange
// journey) — routeMode purely reflects how many legs came back so the UI
// can pick a layout, it no longer reflects two different backend paths.
export type RouteMode = "single" | "multi" | null

export default function Dashboard() {
  const {
    travelInfo, setTravelInfo,
    multiLegInfo, setMultiLegInfo,
    alternates, setAlternates,
    aiSummary, setAiSummary,
    activeSrc, setActiveSrc,
    activeDest, setActiveDest,
    routeMode, setRouteMode,
    errorMsg, setErrorMsg,
  } = useRouteContext()

  const [loading, setLoading] = useState(false)
  const [loadingNote, setLoadingNote] = useState("")
  const [showAlternates, setShowAlternates] = useState(false)

  const handleCalculateRoute = async (src: string, dest: string) => {
    setActiveSrc(src)
    setActiveDest(dest)
    setLoading(true)
    setLoadingNote("Asking the route agent…")
    setTravelInfo(null)
    setMultiLegInfo(null)
    setAlternates([])
    setAiSummary(null)
    setRouteMode(null)
    setErrorMsg(null)
    setShowAlternates(false)

    const userTime = currentTimeHHMM()

    // Bump the loading copy after a few seconds so a slow /ask doesn't feel stuck
    const slowTimer = setTimeout(() => setLoadingNote("Still thinking — checking the timetable directly…"), 8000)

    try {
      const { data, source } = await fetchRoute(src, dest, userTime)
      clearTimeout(slowTimer)

      const legs: any[] = data.legs ?? []
      if (legs.length === 0) {
        setErrorMsg("No routes found between these locations — try differe  nt addresses.")
        return
      }

      if (source === "ask") {
        setAiSummary(data.ai_summary ?? null)
      }

      if (legs.length === 1) {
        // Single-leg: shape RouteSidebar/RouteVisualizer expect
        const leg = legs[0]
        setTravelInfo({
          current_time:    data.requested_time,
          source_station:  data.source_station,
          source_distance: "",
          dest_station:    data.dest_station,
          dest_distance:   "",
          start_stop:      data.start_stop,
          end_stop:        data.end_stop,
          source_lat:      leg.start_latitude,
          source_long:     leg.start_longitude,
          dest_lat:        leg.end_latitude,
          dest_long:       leg.end_longitude,
          trains: [{
            train_id:  leg.train_id,
            departure: leg.departure,
            arrival:   leg.arrival,
            duration:  data.final_arrival,
            line:      leg.line,
          }],
          train_fare:   data.leg_fares?.[0] ?? null,
          crowd_scores: data.crowd_scores ?? {},
        })
        setRouteMode("single")
      } else {
        setMultiLegInfo({
          ...data,
          source_distance: "",
          dest_distance:   "",
          source_walk:     "",
          dest_walk:       "",
          source_lat:      legs[0]?.start_latitude,
          source_long:     legs[0]?.start_longitude,
          dest_lat:        legs[legs.length - 1]?.end_latitude,
          dest_long:       legs[legs.length - 1]?.end_longitude,
        })
        setRouteMode("multi")

        // Fetch alternates in the background — only meaningful for multi-leg
        fetchAlternates(src, dest, userTime).then(setAlternates).catch(() => setAlternates([]))
      }
    } catch (err: any) {
      console.error(err)
      setErrorMsg(err?.message || "Something went wrong. Please check your connection and try again.")
    } finally {
      clearTimeout(slowTimer)
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <div className="flex flex-1 overflow-hidden">
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
          <div className="max-w-4xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-gray-800">Route Optimization</h1>

            {aiSummary && (
              <div className="bg-amber-50 border border-amber-200 rounded-2xl px-5 py-4 flex gap-3">
                <span className="text-amber-500 text-lg flex-shrink-0">✦</span>
                <div>
                  <p className="text-[10px] font-bold text-amber-700 uppercase tracking-widest mb-1">Agent summary</p>
                  <p className="text-sm text-amber-900 leading-relaxed">{aiSummary}</p>
                </div>
              </div>
            )}

            {routeMode === "single" && travelInfo && (
              <RouteVisualizer
                info={travelInfo}
                src={activeSrc}
                dest={activeDest}
                selectedTrain={travelInfo.trains?.[0]}
                srcCoords={travelInfo.source_lat != null && travelInfo.source_long != null
                  ? [travelInfo.source_long, travelInfo.source_lat] as [number, number]
                  : undefined}
                destCoords={travelInfo.dest_lat != null && travelInfo.dest_long != null
                  ? [travelInfo.dest_long, travelInfo.dest_lat] as [number, number]
                  : undefined}
              />
            )}

            {routeMode === "multi" && multiLegInfo && (
              <>
                <MultiLegVisualizer
                  info={multiLegInfo}
                  src={activeSrc}
                  dest={activeDest}
                  srcCoords={multiLegInfo.source_lat != null && multiLegInfo.source_long != null
                    ? [multiLegInfo.source_long, multiLegInfo.source_lat] as [number, number]
                    : undefined}
                  destCoords={multiLegInfo.dest_lat != null && multiLegInfo.dest_long != null
                    ? [multiLegInfo.dest_long, multiLegInfo.dest_lat] as [number, number]
                    : undefined}
                />

                {alternates.length > 0 && (
                  <div className="space-y-4">
                    {/* Toggle button */}
                    <button
                      onClick={() => setShowAlternates(prev => !prev)}
                      className="group w-full flex items-center justify-between px-5 py-3.5 rounded-2xl border border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 shadow-sm hover:shadow"
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="text-base">🔀</span>
                        <span className="text-sm font-semibold text-gray-700 group-hover:text-blue-700 transition-colors">
                          {showAlternates ? "Hide alternate routes" : `Show ${alternates.length} alternate route${alternates.length !== 1 ? "s" : ""}`}
                        </span>
                      </div>
                      <span className={`text-gray-400 group-hover:text-blue-500 transition-all duration-300 ${showAlternates ? "rotate-180" : "rotate-0"}`}>
                        ▾
                      </span>
                    </button>

                    {/* Animated reveal */}
                    <div className={`overflow-hidden transition-all duration-500 ease-in-out ${showAlternates ? "max-h-[2000px] opacity-100" : "max-h-0 opacity-0"}`}>
                      <div className="space-y-3 pt-1">
                        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest px-1">
                          {alternates.length} alternate route{alternates.length !== 1 ? "s" : ""}
                        </p>
                        {alternates.map((alt, i) => (
                          <div key={i} className="transition-all duration-300" style={{ transitionDelay: `${i * 60}ms` }}>
                            <MultiLegVisualizer
                              info={{ ...alt, source_distance: "", dest_distance: "", source_walk: "", dest_walk: "" }}
                              src={activeSrc}
                              dest={activeDest}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </>
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
                  <p className="text-sm text-gray-400">{loadingNote || "Finding the best route…"}</p>
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
      <Footer />
    </div>
  )
}