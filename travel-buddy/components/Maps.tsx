"use client"

import {
  GoogleMap,
  LoadScript,
  DirectionsRenderer
} from "@react-google-maps/api"
import { useState, useEffect, useCallback, useRef } from "react"

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

export default function MapComponent({ source, destination, onRouteCalculated }: MapProps) {
  const [directions, setDirections] = useState<google.maps.DirectionsResult | null>(null)
  
  // Use a Ref for the callback to prevent infinite re-render loops
  const onRouteRef = useRef(onRouteCalculated);
  useEffect(() => {
    onRouteRef.current = onRouteCalculated;
  }, [onRouteCalculated]);

  const calculateRoute = useCallback(() => {
    if (!source || !destination || typeof google === 'undefined') return

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
          
          // Send the data back to the parent (Dashboard)
          if (onRouteRef.current) {
            onRouteRef.current(info)
          }
        } else {
          console.error(`Error fetching directions: ${status}`)
        }
      }
    )
  }, [source, destination])

  useEffect(() => {
    if (source && destination) {
      calculateRoute()
    }
  }, [source, destination, calculateRoute])

  return (
    <LoadScript 
      googleMapsApiKey={process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY!}
    >
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
    </LoadScript>
  )
}