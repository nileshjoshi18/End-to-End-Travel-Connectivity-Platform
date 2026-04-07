"use client"

import { useState } from "react"
import { useSession, signOut } from "next-auth/react"
import Map from "@/components/Maps"
import RouteSidebar from "@/components/RouteSidebar"

export default function Dashboard() {
  const { data: session } = useSession()
  
  // These only update when "Submit" is clicked
  const [activeSource, setActiveSource] = useState("")
  const [activeDestination, setActiveDestination] = useState("")
  
  const [travelInfo, setTravelInfo] = useState<{ distance: string; duration: string } | null>(null)

  // This function will be passed to the Sidebar
  const handleCalculateRoute = (src: string, dest: string) => {
    setActiveSource(src)
    setActiveDestination(dest)
  }

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* 1. Added handleCalculateRoute to the Sidebar props */}
      <RouteSidebar
        onCalculate={handleCalculateRoute}
        travelInfo={travelInfo}
      />

      <div className="flex-1 relative">
        {/* User Profile / Sign Out Overlay */}
        {/* <div className="absolute top-4 right-4 z-10">
          <div className="bg-white p-3 rounded-lg shadow-md flex items-center gap-4">
            <p className="text-sm font-medium">{session?.user?.email}</p>
            <button
              onClick={() => signOut()}
              className="bg-red-500 hover:bg-red-600 text-white text-xs px-3 py-1.5 rounded shadow-sm transition-all"
            >
              Logout
            </button>
          </div>
        </div> */}

        {/* 2. Map only receives the "Active" confirmed locations */}
        <Map
          source={activeSource}
          destination={activeDestination}
          onRouteCalculated={(info: any) => setTravelInfo(info)}
        />
      </div>
    </div>
  )
}