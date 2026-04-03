"use client"

import {
  GoogleMap,
  useJsApiLoader, // Using useJsApiLoader is more stable for Next.js
  DirectionsRenderer
} from "@react-google-maps/api"
import { useState, useEffect, useCallback, useRef, useMemo } from "react"

const containerStyle = {
  width: "100%",
  height: "100vh"
}

const center = {
  lat: 19.076,
  lng: 72.8777
}

interface MapProps {
  source: string;
  destination: string;
  onRouteCalculated?: (info: { distance: string; duration: string }) => void;
}

export default function Map({ source, destination, onRouteCalculated }: MapProps) {
  const [directions, setDirections] = useState<google.maps.DirectionsResult | null>(null)
  
  const { isLoaded } = useJsApiLoader({
    id: 'google-map-script',
    googleMapsApiKey: process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!
  })

  const onRouteRef = useRef(onRouteCalculated);
  useEffect(() => {
    onRouteRef.current = onRouteCalculated;
  }, [onRouteCalculated]);

  const calculateRoute = useCallback(() => {
    if (!source || !destination || !isLoaded) return

    const directionsService = new google.maps.DirectionsService()

    directionsService.route(
      {
        origin: source,
        destination: destination,
        travelMode: google.maps.TravelMode.DRIVING
      },
      (result, status) => {
        if (status === "OK" && result) {
          setDirections(result)
          const leg = result.routes[0].legs[0]
          const info = { 
            distance: leg.distance?.text || "", 
            duration: leg.duration?.text || "" 
          }
          if (onRouteRef.current) onRouteRef.current(info)
        }
      }
    )
  }, [source, destination, isLoaded])

  useEffect(() => {
    calculateRoute()
  }, [calculateRoute])

  // Prevent map from rendering until script is loaded
  if (!isLoaded) return <div className="flex items-center justify-center h-full">Loading Maps...</div>

  return (
    <GoogleMap
      mapContainerStyle={containerStyle}
      center={center}
      zoom={12}
    >
      {directions && (
        <DirectionsRenderer 
          directions={directions} 
          options={{
            polylineOptions: {
              strokeColor: "#3b82f6",
              strokeWeight: 5
            }
          }}
        />
      )}
    </GoogleMap>
  )
}
