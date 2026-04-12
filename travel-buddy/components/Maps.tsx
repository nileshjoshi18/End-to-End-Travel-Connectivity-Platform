// components/Maps.tsx
"use client"

import {
  GoogleMap,
  LoadScript,
  DirectionsRenderer
} from "@react-google-maps/api"
import { useState, useEffect, useRef, useCallback } from "react"

const containerStyle = {
  width: "100%",
  height: "100vh"
}

const center = {
  lat: 19.076,
  lng: 72.8777
}

interface MapProps {
  source: string
  destination: string
  sourceStation?: string
  destStation?: string
  onRouteCalculated?: (info: any) => void
}

export default function MapComponent({
  source,
  destination,
  sourceStation,
  destStation,
  onRouteCalculated
}: MapProps) {
  const [directionsLeg1, setDirectionsLeg1] = useState<google.maps.DirectionsResult | null>(null)
  const [directionsLeg2, setDirectionsLeg2] = useState<google.maps.DirectionsResult | null>(null)
  const [isLoaded, setIsLoaded] = useState(false)

  const onRouteRef = useRef(onRouteCalculated)
  useEffect(() => {
    onRouteRef.current = onRouteCalculated
  }, [onRouteCalculated])

  const calculateRoutes = useCallback(() => {
    if (!isLoaded || typeof google === "undefined") return

    const svc = new google.maps.DirectionsService()

    // Leg 1: source address → boarding station (walking, BLUE)
    if (source && sourceStation) {
      svc.route(
        {
          origin:      source,
          destination: sourceStation + ", Mumbai",
          travelMode:  google.maps.TravelMode.WALKING,
        },
        (result, status) => {
          if (status === "OK" && result) {
            setDirectionsLeg1(result)

            // Send duration/distance back to parent if needed
            const leg = result.routes[0].legs[0]
            onRouteRef.current?.({
              distance: leg.distance?.text ?? "",
              duration: leg.duration?.text ?? "",
            })
          } else {
            console.error("Leg 1 directions error:", status)
          }
        }
      )
    }

    // Leg 2: alighting station → destination address (walking, GREEN)
    if (destStation && destination) {
      svc.route(
        {
          origin:      destStation + ", Mumbai",
          destination: destination,
          travelMode:  google.maps.TravelMode.WALKING,
        },
        (result, status) => {
          if (status === "OK" && result) {
            setDirectionsLeg2(result)
          } else {
            console.error("Leg 2 directions error:", status)
          }
        }
      )
    }
  }, [source, destination, sourceStation, destStation, isLoaded])

  useEffect(() => {
    calculateRoutes()
  }, [calculateRoutes])

  return (
    <LoadScript
      googleMapsApiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!}
      onLoad={() => setIsLoaded(true)}
    >
      <GoogleMap
        mapContainerStyle={containerStyle}
        center={center}
        zoom={12}
      >
        {/* Walk to boarding station — blue */}
        {directionsLeg1 && (
          <DirectionsRenderer
            directions={directionsLeg1}
            options={{
              polylineOptions: { strokeColor: "#2563eb", strokeWeight: 4 },
              suppressMarkers: false,
            }}
          />
        )}

        {/* Walk from alighting station to destination — green */}
        {directionsLeg2 && (
          <DirectionsRenderer
            directions={directionsLeg2}
            options={{
              polylineOptions: { strokeColor: "#059669", strokeWeight: 4 },
              suppressMarkers: false,
            }}
          />
        )}
      </GoogleMap>
    </LoadScript>
  )
}