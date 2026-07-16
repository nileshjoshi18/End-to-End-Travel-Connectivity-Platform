// utils/api.ts

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000"
const ASK_TIMEOUT_MS = 30_000 // 30 seconds

export interface RouteQueryResult {
  data: any
  source: "ask" | "get_routes"
}

function withTimeout(ms: number): { signal: AbortSignal; cancel: () => void } {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), ms)
  return { signal: controller.signal, cancel: () => clearTimeout(id) }
}

async function fetchGetRoutes(src: string, dest: string, userTime: string) {
  const res = await fetch(
    `${API_BASE}/get_routes?start_stop=${encodeURIComponent(src)}&end_stop=${encodeURIComponent(dest)}&user_time=${encodeURIComponent(userTime)}`
  )

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw {
      status: res.status,
      detail: body.detail || `get_routes failed (${res.status})`,
    }
  }

  return res.json()
}

/**
 * Try /ask first; fallback to /get_routes on:
 * - timeout
 * - network failure
 * - server error (500, 422, etc.)
 *
 * DO NOT fallback on 404 (true "no route" case)
 */
export async function fetchRoute(
  src: string,
  dest: string,
  userTime: string
): Promise<RouteQueryResult> {
  const { signal, cancel } = withTimeout(ASK_TIMEOUT_MS)

  try {
    const res = await fetch(
      `${API_BASE}/ask?source=${encodeURIComponent(src)}&destination=${encodeURIComponent(dest)}&user_time=${encodeURIComponent(userTime)}`,
      { signal }
    )

    cancel()

    if (!res.ok) {
      const body = await res.json().catch(() => ({}))

      // ❌ True "no route" → do NOT fallback
      if (res.status === 404) {
        throw {
          status: 404,
          detail: body.detail || "No route found",
        }
      }

      // ✅ Any other HTTP error → fallback
      const data = await fetchGetRoutes(src, dest, userTime)
      return { data, source: "get_routes" }
    }

    const data = await res.json()
    return { data, source: "ask" }

  } catch (err: any) {
    cancel()

    const isAbort = err?.name === "AbortError"
    const isNetwork = err instanceof TypeError

    // ❌ If it's a real "no route" error, rethrow
    if (err?.status === 404) {
      throw err
    }

    // ✅ For timeout, network, or unexpected errors → fallback
    if (isAbort || isNetwork || true) {
      const data = await fetchGetRoutes(src, dest, userTime)
      return { data, source: "get_routes" }
    }
  }
}

export async function fetchAlternates(src: string, dest: string, userTime: string) {
  const res = await fetch(
    `${API_BASE}/get_alternate_routes?start_stop=${encodeURIComponent(src)}&end_stop=${encodeURIComponent(dest)}&user_time=${encodeURIComponent(userTime)}`
  )

  if (!res.ok) return []

  const body = await res.json()
  return body.alternates ?? []
}

export async function fetchTrainDetails(scheduleId: string) {
  const res = await fetch(
    `${API_BASE}/get_train_details?schedule_id=${encodeURIComponent(scheduleId)}`
  )

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Server returned ${res.status}`)
  }

  return res.json()
}

export function currentTimeHHMM(): string {
  return new Date().toLocaleTimeString("en-IN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })
}