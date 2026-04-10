// components/RouteSidebar.tsx
"use client"
import { useState } from "react"

export default function RouteSidebar({ onCalculate, travelInfo, loading }: any) {
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
          disabled={loading || !tempSource || !tempDestination}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white font-bold py-3 rounded-lg transition-all shadow-lg active:scale-95"
        >
          {loading ? "Calculating..." : "Find Route"}
        </button>
      </div>

      {/* Distance result */}
      {travelInfo && (
        <div className="mt-auto space-y-3">
          {/* Source station card */}
          <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
            <p className="text-xs font-semibold text-blue-500 uppercase mb-1">Board at</p>
            <p className="font-bold text-gray-900">{travelInfo.source_station}</p>
            <p className="text-sm text-gray-500">{travelInfo.source_distance} · {travelInfo.source_walk} walk</p>
          </div>

          {/* Destination station card */}
          <div className="p-4 bg-green-50 rounded-xl border border-green-200">
            <p className="text-xs font-semibold text-green-600 uppercase mb-1">Alight at</p>
            <p className="font-bold text-gray-900">{travelInfo.dest_station}</p>
            <p className="text-sm text-gray-500">{travelInfo.dest_distance} · {travelInfo.dest_walk} walk</p>
          </div>
        </div>
      )}
    </div>
  )
}