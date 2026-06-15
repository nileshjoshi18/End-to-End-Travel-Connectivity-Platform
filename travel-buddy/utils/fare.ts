// utils/fare.ts

// ── Auto-rickshaw fare ───────────────────────────────────────────────────────
// distanceInMetres: raw value from PostGIS ST_DistanceSphere (always metres)
export const calculateAutoFare = (distanceInMetres: number): number => {
  const distanceInKm = distanceInMetres / 1000;
  const minFare = 26;
  const minDistance = 1.5;
  const ratePerKm = 17.14;

  if (distanceInKm <= minDistance) {
    return minFare;
  }

  const additionalDistance = distanceInKm - minDistance;
  return Math.round(minFare + additionalDistance * ratePerKm);
};

// ── Cab fare constants ───────────────────────────────────────────────────────
const CAB_BASE_FARE = 40;
const CAB_RATE_PER_KM = 26;

export const calculateCabFareFromDistance = (distanceInKm: number): number => {
  return Math.round(CAB_BASE_FARE + distanceInKm * CAB_RATE_PER_KM);
};

// ── ORS road-distance fetch ──────────────────────────────────────────────────
// Returns { distanceKm, durationMin } via OpenRouteService driving-car profile.
// Coordinates: [longitude, latitude]
export interface ORSResult {
  distanceKm: number;
  durationMin: number;
}

export const fetchORSDistance = async (
  fromCoords: [number, number], // [lng, lat]
  toCoords: [number, number]    // [lng, lat]
): Promise<ORSResult | null> => {
  try {
    const apiKey = process.env.NEXT_PUBLIC_ORS_API_KEY;
    if (!apiKey) {
      console.warn("ORS_API_KEY not set in environment");
      return null;
    }

    const response = await fetch(
      "https://api.openrouteservice.org/v2/directions/driving-car",
      {
        method: "POST",
        headers: {
          Authorization: apiKey,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          coordinates: [fromCoords, toCoords],
        }),
      }
    );

    if (!response.ok) {
      console.error("ORS API error:", response.status, await response.text());
      return null;
    }

    const result = await response.json();
    const summary = result?.routes?.[0]?.summary;
    if (!summary) return null;

    return {
      distanceKm: summary.distance / 1000,
      durationMin: summary.duration / 60,
    };
  } catch (err) {
    console.error("fetchORSDistance failed:", err);
    return null;
  }
};

// ── Cab fare via ORS (distance + price) ─────────────────────────────────────
// Pass GPS coords for both ends; returns fare or null on failure.
export const calculateCabFare = async (
  fromCoords: [number, number],
  toCoords: [number, number]
): Promise<{ fare: number; distanceKm: number; durationMin: number } | null> => {
  const ors = await fetchORSDistance(fromCoords, toCoords);
  if (!ors) return null;

  return {
    fare: calculateCabFareFromDistance(ors.distanceKm),
    distanceKm: ors.distanceKm,
    durationMin: ors.durationMin,
  };
};