// app/page.tsx
import Link from "next/link"
import Footer from "@/components/Footer"

const LINES = [
  { code: "WR",  name: "Western",       color: "bg-blue-600" },
  { code: "CR",  name: "Central",       color: "bg-orange-600" },
  { code: "HR",  name: "Harbour",       color: "bg-teal-600" },
  { code: "THR", name: "Trans-Harbour", color: "bg-cyan-600" },
  { code: "M1",  name: "Metro Line 1",  color: "bg-violet-600" },
  { code: "M3",  name: "Metro Line 3",  color: "bg-pink-600" },
]

export default function HomePage() {
  return (
    <div className="flex flex-col min-h-screen bg-[#0b1220]">
      <main className="flex-1 flex items-center justify-center px-6 py-20">
        <div className="max-w-3xl w-full">

          {/* Departure-board eyebrow */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-amber-400/10 border border-amber-400/30 mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-[10px] font-bold text-amber-300 uppercase tracking-[0.2em]">
              Live · Mumbai Suburban &amp; Metro
            </span>
          </div>

          <h1
            className="text-5xl sm:text-6xl font-bold text-white leading-[1.05] mb-6"
            style={{ fontFamily: "var(--font-display)" }}
          >
            Wayfr
          </h1>

          <p className="text-lg text-slate-400 leading-relaxed max-w-xl mb-10">
            Punch in where you're standing and where you need to be. Wayfr
            finds the next train on your line, or builds a multi-leg route across
            lines when there isn't a direct one — fares, interchange points, and
            platform crowding included, the way the announcer would tell you
            if announcers were useful.
          </p>

          <Link
            href="/dashboard"
            className="inline-flex items-center gap-3 bg-amber-400 hover:bg-amber-300 text-[#0b1220] font-bold text-sm px-7 py-3.5 rounded-xl transition-all active:scale-95 shadow-lg shadow-amber-400/20"
          >
            Open the Dashboard
            <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </Link>

          {/* Line chips — sets expectation for what's covered */}
          <div className="mt-16 pt-8 border-t border-white/10">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-4">
              Networks covered
            </p>
            <div className="flex flex-wrap gap-2.5">
              {LINES.map((l) => (
                <div
                  key={l.code}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10"
                >
                  <span className={`w-5 h-5 rounded-full ${l.color} text-white text-[9px] font-black flex items-center justify-center flex-shrink-0`}>
                    {l.code}
                  </span>
                  <span className="text-xs text-slate-300 font-medium">{l.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* What it does, in commuter terms */}
          <div className="mt-10 grid sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
              <p className="text-amber-400 text-xl mb-1 font-mono">→</p>
              <p className="text-xs font-bold text-white mb-1">Direct &amp; interchange routes</p>
              <p className="text-[11px] text-slate-400 leading-relaxed">Same-line trains or a full multi-leg plan when you need to change lines.</p>
            </div>
            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
              <p className="text-amber-400 text-xl mb-1 font-mono">●</p>
              <p className="text-xs font-bold text-white mb-1">Crowd at every stop</p>
              <p className="text-[11px] text-slate-400 leading-relaxed">Light, moderate, or heavy — at boarding, interchange, and arrival.</p>
            </div>
            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
              <p className="text-amber-400 text-xl mb-1 font-mono">₹</p>
              <p className="text-xs font-bold text-white mb-1">Fare, compared to a cab</p>
              <p className="text-[11px] text-slate-400 leading-relaxed">See the train fare next to a door-to-door cab estimate, side by side.</p>
            </div>
          </div>
        </div>
      </main>

      <div className="bg-white">
        <Footer />
      </div>
    </div>
  )
}