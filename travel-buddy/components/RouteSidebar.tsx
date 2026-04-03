import { Dispatch, SetStateAction } from "react"

interface SidebarProps {
  setSource: Dispatch<SetStateAction<string>>;
  setDestination: Dispatch<SetStateAction<string>>;
  travelInfo: { distance: string; duration: string } | null;
}

export default function RouteSidebar({ setSource, setDestination, travelInfo }: SidebarProps) {
  return (
    <div className="w-80 p-6 bg-white shadow-lg z-20">
      {/* Input for Source */}
      <input 
        onChange={(e) => setSource(e.target.value)} 
        placeholder="Starting point"
        className="border p-2 w-full mb-2"
      />
      {/* Input for Destination */}
      <input 
        onChange={(e) => setDestination(e.target.value)} 
        placeholder="Destination"
        className="border p-2 w-full"
      />

      {/* Displaying the result */}
      {travelInfo && (
        <div className="mt-4 p-4 bg-blue-50 rounded">
          <p className="text-xs text-blue-600 font-bold">ROAD TRIP</p>
          <p>Dist: {travelInfo.distance}</p>
          <p>Time: {travelInfo.duration}</p>
        </div>
      )}
    </div>
  )
}