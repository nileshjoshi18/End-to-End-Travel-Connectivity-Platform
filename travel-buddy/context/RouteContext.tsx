// context/RouteContext.tsx
//
// Holds the full dashboard search state in memory (React context), not
// localStorage/sessionStorage — it only needs to survive client-side
// navigation (e.g. dashboard -> train detail -> back), and should reset
// on a hard reload, which is exactly what plain in-memory state does.
"use client"

import { createContext, useContext, useState, type ReactNode } from "react"
import type { RouteMode } from "@/app/dashboard/page"

interface RouteContextValue {
  travelInfo: any | null
  setTravelInfo: (v: any | null) => void
  multiLegInfo: any | null
  setMultiLegInfo: (v: any | null) => void
  alternates: any[]
  setAlternates: (v: any[]) => void
  aiSummary: string | null
  setAiSummary: (v: string | null) => void
  activeSrc: string
  setActiveSrc: (v: string) => void
  activeDest: string
  setActiveDest: (v: string) => void
  routeMode: RouteMode
  setRouteMode: (v: RouteMode) => void
  errorMsg: string | null
  setErrorMsg: (v: string | null) => void
}

const RouteContext = createContext<RouteContextValue | null>(null)

export function RouteProvider({ children }: { children: ReactNode }) {
  const [travelInfo, setTravelInfo]     = useState<any | null>(null)
  const [multiLegInfo, setMultiLegInfo] = useState<any | null>(null)
  const [alternates, setAlternates]     = useState<any[]>([])
  const [aiSummary, setAiSummary]       = useState<string | null>(null)
  const [activeSrc, setActiveSrc]       = useState("")
  const [activeDest, setActiveDest]     = useState("")
  const [routeMode, setRouteMode]       = useState<RouteMode>(null)
  const [errorMsg, setErrorMsg]         = useState<string | null>(null)

  return (
    <RouteContext.Provider
      value={{
        travelInfo, setTravelInfo,
        multiLegInfo, setMultiLegInfo,
        alternates, setAlternates,
        aiSummary, setAiSummary,
        activeSrc, setActiveSrc,
        activeDest, setActiveDest,
        routeMode, setRouteMode,
        errorMsg, setErrorMsg,
      }}
    >
      {children}
    </RouteContext.Provider>
  )
}

export function useRouteContext() {
  const ctx = useContext(RouteContext)
  if (!ctx) throw new Error("useRouteContext must be used within RouteProvider")
  return ctx
}