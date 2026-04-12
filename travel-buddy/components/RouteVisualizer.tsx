// components/RouteVisualizer.tsx
import {calculateAutoFare} from "@/utils/fare";

export default function RouteVisualizer({ info }: { info: any }) {
  // Parse distances (assuming strings like "1.5 km")
  const distSrc = parseFloat(info.source_distance) || 0;
  const distDest = parseFloat(info.dest_distance) || 0;
  
  const fareSrc = calculateAutoFare(distSrc);
  const fareDest = calculateAutoFare(distDest);
  const totalPrice = fareSrc + fareDest;

  return (
    <div className="bg-white p-8 rounded-3xl border border-gray-100 shadow-sm">
      <div className="flex items-center justify-between">
        {/* Source */}
        <div className="text-center">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">🚶</div>
          <p className="text-xs font-bold mt-2">Start</p>
        </div>

        {/* Source to Station */}
        <div className="flex-1 flex flex-col items-center px-4">
          <span className="text-[10px] font-bold text-blue-600">₹{fareSrc}</span>
          <div className="w-full h-px bg-gray-300 my-1" />
          <span className="text-[10px] text-gray-500">{info.source_walk}</span>
        </div>

        {/* Station Nodes */}
        <div className="flex gap-4">
          <div className="bg-blue-600 text-white px-4 py-2 rounded-xl text-xs font-bold">{info.source_station}</div>
          <div className="text-gray-400">→</div>
          <div className="bg-blue-600 text-white px-4 py-2 rounded-xl text-xs font-bold">{info.dest_station}</div>
        </div>

        {/* Station to Dest */}
        <div className="flex-1 flex flex-col items-center px-4">
          <span className="text-[10px] font-bold text-blue-600">₹{fareDest}</span>
          <div className="w-full h-px bg-gray-300 my-1" />
          <span className="text-[10px] text-gray-500">{info.dest_walk}</span>
        </div>

        {/* Destination */}
        <div className="text-center">
          <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">📍</div>
          <p className="text-xs font-bold mt-2">End</p>
        </div>
      </div>

      {/* Total Price Footer */}
      <div className="mt-8 pt-6 border-t border-gray-100 flex justify-between items-center">
        <p className="text-sm font-bold text-gray-500 uppercase">Total Auto Fare</p>
        <p className="text-2xl font-black text-blue-700">₹{totalPrice}</p>
      </div>
    </div>
  );
}