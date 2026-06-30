// utils/transitDesign.ts
//
// Single source of truth for how lines, metro badges, and crowd scores
// are rendered across the app — sidebar, visualizers, train detail page.

export interface LineStyle {
  bg: string
  pill: string
  text: string
  bar: string
  border: string
  dot: string
  label: string
  isMetro: boolean
  badge: string // short pictogram text, e.g. "M1", "WR"
}

// Mumbai Suburban Railway + Metro — real line identities
const LINE_STYLES: Record<string, LineStyle> = {
  Western: {
    bg: "bg-[#1d4ed8]", pill: "bg-blue-100 text-blue-700", text: "text-blue-700",
    bar: "bg-blue-400", border: "border-blue-200", dot: "bg-blue-600",
    label: "Western Line", isMetro: false, badge: "WR",
  },
  Central: {
    bg: "bg-[#c2410c]", pill: "bg-orange-100 text-orange-700", text: "text-orange-700",
    bar: "bg-orange-400", border: "border-orange-200", dot: "bg-orange-600",
    label: "Central Line", isMetro: false, badge: "CR",
  },
  Harbour: {
    bg: "bg-[#0f766e]", pill: "bg-teal-100 text-teal-700", text: "text-teal-700",
    bar: "bg-teal-400", border: "border-teal-200", dot: "bg-teal-600",
    label: "Harbour Line", isMetro: false, badge: "HR",
  },
  "Trans-Harbour": {
    bg: "bg-[#0e7490]", pill: "bg-cyan-100 text-cyan-700", text: "text-cyan-700",
    bar: "bg-cyan-400", border: "border-cyan-200", dot: "bg-cyan-600",
    label: "Trans-Harbour Line", isMetro: false, badge: "THR",
  },
  MLN1: {
    bg: "bg-[#7c3aed]", pill: "bg-violet-100 text-violet-700", text: "text-violet-700",
    bar: "bg-violet-400", border: "border-violet-200", dot: "bg-violet-600",
    label: "Metro Line 1", isMetro: true, badge: "M1",
  },
  MLN3: {
    bg: "bg-[#be185d]", pill: "bg-pink-100 text-pink-700", text: "text-pink-700",
    bar: "bg-pink-400", border: "border-pink-200", dot: "bg-pink-600",
    label: "Metro Line 3", isMetro: true, badge: "M3",
  },
}

const FALLBACK_STYLE: LineStyle = {
  bg: "bg-[#475569]", pill: "bg-slate-100 text-slate-700", text: "text-slate-700",
  bar: "bg-slate-400", border: "border-slate-200", dot: "bg-slate-600",
  label: "Line", isMetro: false, badge: "—",
}

/** Normalises whatever string the backend sends ("Western", "WR", "MLN1"...) to a style. */
export function getLineStyle(line: string | undefined | null): LineStyle {
  if (!line) return FALLBACK_STYLE
  if (LINE_STYLES[line]) return LINE_STYLES[line]

  const upper = line.toUpperCase()
  const aliasMap: Record<string, string> = {
    WR: "Western", CR: "Central", HR: "Harbour", THR: "Trans-Harbour",
    MLN1: "MLN1", MLN3: "MLN3", METRO1: "MLN1", METRO3: "MLN3",
  }
  const key = aliasMap[upper]
  return key ? LINE_STYLES[key] : FALLBACK_STYLE
}

/** True if a stop_id (e.g. "VER_MLN1") or line code belongs to the metro network. */
export function isMetroStop(stopIdOrLine: string | undefined | null): boolean {
  if (!stopIdOrLine) return false
  return /MLN\d/i.test(stopIdOrLine)
}

// ── Crowd scoring ──────────────────────────────────────────────────────

export type CrowdLevel = "light" | "moderate" | "heavy" | "unknown"

export interface CrowdStyle {
  level: CrowdLevel
  label: string
  bg: string
  text: string
  dot: string
  icon: string
}

export function getCrowdStyle(score: number | null | undefined): CrowdStyle {
  if (score === null || score === undefined) {
    return { level: "unknown", label: "No data", bg: "bg-gray-100", text: "text-gray-400", dot: "bg-gray-300", icon: "·" }
  }
  if (Number.isNaN(score)) {
    return { level: "unknown", label: "No data", bg: "bg-gray-100", text: "text-gray-400", dot: "bg-gray-300", icon: "·" }
  }
  if (score <= 0.3) {
    return { level: "light", label: "Light", bg: "bg-emerald-50", text: "text-emerald-700", dot: "bg-emerald-500", icon: "○" }
  }
  if (score <= 0.6) {
    return { level: "moderate", label: "Moderate", bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500", icon: "◐" }
  }
  return { level: "heavy", label: "Heavy", bg: "bg-red-50", text: "text-red-700", dot: "bg-red-500", icon: "●" }
}