// components/RouteSidebar.tsx
"use client"
import { useState } from "react"

export default function RouteSidebar({ onCalculate, travelInfo }: any) {
  const [tempSource, setTempSource] = useState("")
  const [tempDestination, setTempDestination] = useState("")

  return (
    <div className="w-80 h-full bg-white shadow-xl p-6 z-20 flex flex-col">
      <h2 className="text-xl font-bold mb-6">Plan Your Trip</h2>
      
      <div className="space-y-4">
        <div>
          <label className="text-xs font-semibold text-gray-500 uppercase">Starting Point</label>
          <input
            type="text"
            placeholder="Enter source..."
            value={tempSource}
            onChange={(e) => setTempSource(e.target.value)}
            className="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-gray-500 uppercase">Destination</label>
          <input
            type="text"
            placeholder="Enter destination..."
            value={tempDestination}
            onChange={(e) => setTempDestination(e.target.value)}
            className="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>

        <button
          onClick={() => onCalculate(tempSource, tempDestination)}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-lg transition-all shadow-lg active:scale-95"
        >
          Find Route
        </button>
      </div>

      {/* Travel Info displayed at the bottom of sidebar */}
      {travelInfo && (
        <div className="mt-auto p-4 bg-gray-50 rounded-xl border border-dashed border-gray-300">
          <p className="text-sm text-gray-600">Total Distance: <span className="font-bold text-black">{travelInfo.distance}</span></p>
          <p className="text-sm text-gray-600">Est. Time: <span className="font-bold text-black">{travelInfo.duration}</span></p>
        </div>
      )}
    </div>
  )
}