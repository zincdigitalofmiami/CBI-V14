'use client'

import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import dynamic from 'next/dynamic'

// Dynamically import Leaflet to avoid SSR issues
const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
)
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
)
const CircleMarker = dynamic(
  () => import('react-leaflet').then((mod) => mod.CircleMarker),
  { ssr: false }
)
const Popup = dynamic(
  () => import('react-leaflet').then((mod) => mod.Popup),
  { ssr: false }
)

interface HeatPoint {
  lat: number
  lng: number
  weight: number
  type: 'event' | 'restaurant'
  name: string
}

async function fetchHeatmapData(): Promise<HeatPoint[]> {
  const response = await fetch('/api/v4/vegas/heatmap-data')
  if (!response.ok) return []
  return response.json()
}

// Heat color based on weight (impact score)
function getHeatColor(weight: number): string {
  if (weight >= 8) return '#EF4444'    // Red: High impact
  if (weight >= 6) return '#F97316'    // Orange: Medium-high
  if (weight >= 4) return '#F59E0B'    // Amber: Medium
  if (weight >= 2) return '#10B981'    // Green: Low-medium
  return '#3B82F6'                     // Blue: Low
}

function getRadius(weight: number): number {
  return Math.min(20, Math.max(5, weight * 2))
}

export function VegasHeatMap() {
  const { data: points, isLoading } = useQuery({
    queryKey: ['vegas-heatmap'],
    queryFn: fetchHeatmapData,
    refetchInterval: 300000, // 5 minutes
  })

  const heatPoints = points || []

  if (isLoading) {
    return (
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6 h-96 flex items-center justify-center">
        <div className="text-text-tertiary">Loading map...</div>
      </div>
    )
  }

  return (
    <div className="bg-background-secondary border border-border-primary rounded-lg overflow-hidden">
      <div className="p-4 border-b border-border-secondary">
        <h2 className="text-xl font-semibold text-text-primary mb-1">
          Event Proximity Intelligence
        </h2>
        <p className="text-sm text-text-secondary">
          Geographic analysis of event impact on restaurant oil demand
        </p>
      </div>
      
      <div className="h-96 relative">
        {typeof window !== 'undefined' && (
          <MapContainer
            center={[36.1699, -115.1398]} // Las Vegas center
            zoom={11}
            style={{ height: '100%', width: '100%' }}
            className="z-0"
          >
            {/* FREE OpenStreetMap tiles */}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            
            {/* Plot points with heat colors */}
            {heatPoints.map((point, idx) => (
              <CircleMarker
                key={idx}
                center={[point.lat, point.lng]}
                radius={getRadius(point.weight)}
                fillColor={getHeatColor(point.weight)}
                color={getHeatColor(point.weight)}
                weight={2}
                opacity={0.8}
                fillOpacity={0.4}
              >
                <Popup>
                  <div className="text-sm">
                    <div className="font-semibold">{point.name}</div>
                    <div className="text-xs text-gray-600">
                      Type: {point.type === 'event' ? 'Event' : 'Restaurant'}
                    </div>
                    <div className="text-xs text-gray-600">
                      Impact Score: {point.weight.toFixed(1)}
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        )}
      </div>
      
      {/* Legend */}
      <div className="p-4 border-t border-border-secondary bg-background-tertiary">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-text-tertiary">High Impact (8+)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-orange-500"></div>
              <span className="text-text-tertiary">Medium (4-8)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-text-tertiary">Low (&lt;4)</span>
            </div>
          </div>
          <div className="text-text-tertiary">
            Powered by OpenStreetMap
          </div>
        </div>
      </div>
    </div>
  )
}

