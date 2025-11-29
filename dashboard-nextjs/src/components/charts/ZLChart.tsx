'use client';

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export function ZLChart() {
  const [zlData, setZlData] = useState<any[]>([]);
  const [latestPrice, setLatestPrice] = useState(0);
  const [priceChange, setPriceChange] = useState(0);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch('/api/v4/live/zl');
        const json = await res.json();
        
        if (json.data && json.data.length > 0) {
          setZlData(json.data);
          const latest = json.data[json.data.length - 1].close;
          const prev = json.data.length > 1 ? json.data[json.data.length - 2].close : latest;
          setLatestPrice(latest);
          setPriceChange(((latest - prev) / prev) * 100);
          setLastUpdate(new Date());
        }
      } catch (error) {
        console.error('Error fetching ZL data:', error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
    const interval = setInterval(fetchData, 300000); // 5 minutes
    return () => clearInterval(interval);
  }, []);

  const dates = zlData.map(d => d.date?.value || d.date);
  const closes = zlData.map(d => d.close);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-[#0a0a0f]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white/60 text-sm tracking-wide">Loading ZL futures...</p>
        </div>
      </div>
    );
  }

  if (!zlData || zlData.length === 0) {
    return (
      <div className="flex items-center justify-center h-full w-full bg-[#0a0a0f]">
        <p className="text-white/40">No data available</p>
      </div>
    );
  }

  return (
    <div className="h-full w-full relative bg-[#0a0a0f]">
      {/* Floating price overlay - top left */}
      <div className="absolute top-6 left-8 z-10">
        <div className="flex items-baseline gap-3">
          <span className="text-5xl font-extralight text-white tracking-tight">
            {latestPrice.toFixed(2)}
          </span>
          <span className="text-white/40 text-lg font-light">¢/lb</span>
        </div>
        <div className="flex items-center gap-3 mt-1">
          <span className={`text-sm font-medium ${priceChange >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {priceChange >= 0 ? '▲' : '▼'} {Math.abs(priceChange).toFixed(2)}%
          </span>
          <span className="text-white/30 text-xs">24h</span>
        </div>
      </div>

      {/* Floating label - top right */}
      <div className="absolute top-6 right-8 z-10 text-right">
        <div className="text-white/80 text-sm font-medium tracking-widest uppercase">
          ZL1!
        </div>
        <div className="text-white/40 text-xs mt-1">
          Soybean Oil Futures
        </div>
        <div className="flex items-center gap-2 mt-2 justify-end">
          <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          <span className="text-emerald-400/80 text-xs font-medium">LIVE</span>
        </div>
      </div>

      {/* Last update - bottom right */}
      {lastUpdate && (
        <div className="absolute bottom-6 right-8 z-10 text-white/30 text-xs">
          Updated {lastUpdate.toLocaleTimeString()}
        </div>
      )}

      {/* Full screen chart */}
      <Plot
        data={[
          {
            x: dates,
            y: closes,
            type: 'scatter',
            mode: 'lines',
            name: 'ZL',
            line: { 
              color: '#ffffff',
              width: 2.5,
              shape: 'spline',
              smoothing: 1.3
            },
            fill: 'tozeroy',
            fillcolor: 'rgba(255, 255, 255, 0.03)',
            hovertemplate: '<b>%{x}</b><br>$%{y:.2f}<extra></extra>',
          },
        ]}
        layout={{
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: { family: 'system-ui, -apple-system, sans-serif', color: 'rgba(255,255,255,0.4)' },
          margin: { t: 100, r: 60, b: 60, l: 60 },
          hovermode: 'x unified',
          showlegend: false,
          xaxis: {
            showgrid: true,
            gridcolor: 'rgba(255, 255, 255, 0.04)',
            gridwidth: 1,
            showline: false,
            tickfont: { size: 10, color: 'rgba(255,255,255,0.3)' },
            zeroline: false,
            tickformat: '%b %d',
            dtick: 'M1',
            hoverformat: '%b %d, %Y'
          },
          yaxis: {
            showgrid: true,
            gridcolor: 'rgba(255, 255, 255, 0.04)',
            gridwidth: 1,
            showline: false,
            tickfont: { size: 10, color: 'rgba(255,255,255,0.3)' },
            zeroline: false,
            side: 'right',
            tickprefix: '$',
          },
          hoverlabel: {
            bgcolor: 'rgba(10, 10, 15, 0.95)',
            bordercolor: 'rgba(255, 255, 255, 0.1)',
            font: { color: '#ffffff', size: 12 }
          },
          dragmode: 'pan',
        }}
        config={{
          responsive: true,
          displayModeBar: false,
          scrollZoom: true,
        }}
        style={{ width: '100%', height: '100%' }}
        useResizeHandler={true}
      />
    </div>
  );
}
