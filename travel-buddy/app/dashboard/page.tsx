// app/dashboard/page.tsx
"use client"
import { useState } from "react"
import RouteSidebar from "@/components/RouteSidebar"
import ComparisonPanel from "@/components/ComparisonPanel"
import RouteVisualizer from "@/components/RouteVisualizer"
import { useSession } from "next-auth/react"
export default function Dashboard() {
  const [travelInfo, setTravelInfo] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const { data: session } = useSession()

  const handleCalculateRoute = async (src: string, dest: string) => {
    setLoading(true);
    try {
        const res = await fetch(`http://127.0.0.1:8000/get-connectivity?source=${src}&destination=${dest}`);
        const data = await res.json();
        
        // Ensure you are mapping the nested API response to the flat structure the UI expects
        setTravelInfo({
        source_station: data.source_connectivity?.station_name || "Unknown",
        source_distance: data.source_connectivity?.distance_to_station || "0km",
        source_walk: data.source_connectivity?.walking_time || "0 min",
        dest_station: data.destination_connectivity?.station_name || "Unknown",
        dest_distance: data.destination_connectivity?.distance_to_station || "0km",
        dest_walk: data.destination_connectivity?.walking_time || "0 min",
        trains: data.trains || [],
        current_time: data.current_time
        });
    } catch (err) {
        console.error(err);
    } finally {
        setLoading(false);
    }
    }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <RouteSidebar 
        onCalculate={handleCalculateRoute} 
        travelInfo={travelInfo} 
        loading={loading} 
      />

      <main className="flex-1 p-10 overflow-y-auto">
        <div className="max-w-4xl mx-auto space-y-8">
          <h1 className="text-2xl font-bold text-gray-800">Route Optimization</h1>
          
          {travelInfo ? (
            <>
              <RouteVisualizer info={travelInfo} />

              {/* Fix: Pass the data as structured objects defined in ComparisonPanel */}
              {/* <ComparisonPanel 
                transitData={{
                  cost: "₹20",
                  time: travelInfo.source_walk || "10 mins",
                  description: `Includes train from ${travelInfo.source_connectivity?.station_name || 'Station'}`
                }}
                uberData={{
                  cost: "₹350",
                  time: "45 mins",
                  description: "Direct point-to-point travel"
                }}
              /> */}
            </>
          ) : (
            <div className="h-96 border-2 border-dashed border-gray-200 rounded-3xl flex items-center justify-center text-gray-400">
              {loading ? "Finding the best route..." : "Enter your journey details to see the most cost-effective route."}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}