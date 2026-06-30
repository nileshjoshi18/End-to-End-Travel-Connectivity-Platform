// components/Footer.tsx
export default function Footer() {
  return (
    <footer className="border-t border-gray-100 bg-white">
      <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="w-7 h-7 rounded-full bg-blue-700 text-white text-[10px] font-black flex items-center justify-center">
            TB
          </span>
          <div>
            <p className="text-xs font-bold text-gray-700">Wayfr</p>
            <p className="text-[10px] text-gray-400">Multimodal Public Transport Platform</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-[11px] text-gray-400">
          <span>Western · Central · Harbour · Trans-Harbour</span>
          <span className="hidden sm:inline">·</span>
          <span className="inline-flex items-center gap-1">
            <span className="w-3.5 h-3.5 rounded-full bg-violet-600 text-white text-[7px] font-black flex items-center justify-center">M1</span>
            <span className="w-3.5 h-3.5 rounded-full bg-pink-600 text-white text-[7px] font-black flex items-center justify-center">M3</span>
            Metro
          </span>
        </div>

        <p className="text-[10px] text-gray-300">Built for commuters and tourists.</p>
      </div>
    </footer>
  )
}