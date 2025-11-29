'use client';

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export function ZLChart() {
  const [zlData, setZlData] = useState<any[]>([]);
  const [forecasts, setForecasts] = useState<any[]>([]);
  const [latestPrice, setLatestPrice] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [zlRes, forecastsRes] = await Promise.all([
          fetch('/api/v4/live/zl').catch(err => {
            console.error('ZL API error:', err);
            return { ok: false, json: () => ({ success: false, data: [] }) };
          }),
          fetch('/api/v4/forecasts/all').catch(err => {
            console.error('Forecasts API error:', err);
            return { ok: false, json: () => ({ success: false, forecasts: [] }) };
          }),
        ]);
        
        const zlJson = await zlRes.json();
        const forecastsJson = await forecastsRes.json();
        
        console.log('ZL data:', zlJson);
        console.log('Forecasts data:', forecastsJson);
        
        setZlData(zlJson.data || []);
        setForecasts(forecastsJson.forecasts || []);

        if (zlJson.data && zlJson.data.length > 0) {
          const latest = zlJson.data[zlJson.data.length - 1].close;
          setLatestPrice(latest);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
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

  // Build forecast traces - lines extending forward from TODAY
  const forecastTraces: any[] = [];
  const horizonLineColors = {
    '1w': 'rgba(16, 185, 129, 0.4)',
    '1m': 'rgba(34, 211, 153, 0.4)',
    '3m': 'rgba(110, 231, 183, 0.4)',
    '6m': 'rgba(167, 243, 208, 0.4)',
  };

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayStr = today.toISOString().split('T')[0];

  // Add forecast lines - extend forward from TODAY to target_date
  forecasts.forEach((forecast) => {
    if (!forecast.prediction || !forecast.target_date) {
      return; // Skip forecasts without real prediction
    }

    const targetDate = new Date(forecast.target_date);
    const targetDateStr = targetDate.toISOString().split('T')[0];

    // Forecast line extending forward from today
    forecastTraces.push({
      x: [todayStr, targetDateStr],
      y: [latestPrice, forecast.prediction], // Start from current price, end at forecast
      type: 'scatter',
      mode: 'lines',
      name: `${forecast.horizon.toUpperCase()} Forecast`,
      line: {
        color: horizonLineColors[forecast.horizon as keyof typeof horizonLineColors] || 'rgba(16, 185, 129, 0.4)',
        width: 2,
        dash: 'dash',
      },
      opacity: 0.7,
      hovertemplate: `${forecast.horizon.toUpperCase()}: $%{y:.2f}<extra></extra>`,
    });

    // Optional: Add probability bands if they exist
    if (forecast.confidence_lower && forecast.confidence_upper) {
      // Lower band
      forecastTraces.push({
        x: [todayStr, targetDateStr],
        y: [latestPrice, forecast.confidence_lower],
        type: 'scatter',
        mode: 'lines',
        name: `${forecast.horizon.toUpperCase()} Lower`,
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
        fill: 'tonexty',
        fillcolor: horizonLineColors[forecast.horizon as keyof typeof horizonLineColors] || 'rgba(16, 185, 129, 0.1)',
      });

      // Upper band
      forecastTraces.push({
        x: [todayStr, targetDateStr],
        y: [latestPrice, forecast.confidence_upper],
        type: 'scatter',
        mode: 'lines',
        name: `${forecast.horizon.toUpperCase()} Upper`,
        line: { width: 0 },
        showlegend: false,
        hoverinfo: 'skip',
        fillcolor: horizonLineColors[forecast.horizon as keyof typeof horizonLineColors] || 'rgba(16, 185, 129, 0.1)',
      });
    }
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-text-secondary">Loading ZL data...</p>
      </div>
    );
  }

  // Show error if no data
  if (!zlData || zlData.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-text-secondary mb-2">No ZL data available</p>
          <p className="text-text-secondary text-sm">Check API endpoint: /api/v4/live/zl</p>
        </div>
      </div>
    );
  }

  // Ensure we have valid data arrays
  const validDates = dates.filter((d, i) => d && closes[i] !== undefined);
  const validCloses = closes.filter((c, i) => dates[i] && c !== undefined);

  if (validDates.length === 0 || validCloses.length === 0) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <p className="text-text-secondary mb-2">Invalid data format</p>
          <p className="text-text-secondary text-sm">Data: {JSON.stringify(zlData.slice(0, 2))}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full flex flex-col">
      {/* Minimal header */}
      <div className="px-6 py-3 border-b border-border-primary bg-background-primary">
        <div className="flex items-baseline gap-4">
          <h1 className="text-xl font-bold text-text-primary">ZL Soybean Oil Futures</h1>
          <span className="text-2xl font-semibold text-text-primary">${latestPrice.toFixed(2)}</span>
          <span className="text-sm font-medium text-bull-500 animate-pulse">● LIVE</span>
        </div>
      </div>

      {/* Full-width chart - takes up entire remaining space */}
      <div className="flex-1 bg-background-primary">
        <Plot
          data={[
            // Forecast traces FIRST (behind price line)
            ...forecastTraces,
            // LIVE ZL Price (bold line, on top)
            {
              x: validDates,
              y: validCloses,
              type: 'scatter',
              mode: 'lines',
              name: 'ZL Price (LIVE)',
              line: { color: '#10b981', width: 4, shape: 'spline' },
              hovertemplate: 'LIVE: $%{y:.2f}<extra></extra>',
            },
          ]}
          layout={{
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { family: 'system-ui', size: 12, color: '#9ca3af' },
            margin: { t: 40, r: 40, b: 60, l: 80 },
            hovermode: 'x unified',
            showlegend: true,
            legend: {
              orientation: 'h',
              yanchor: 'bottom',
              y: -0.15,
              xanchor: 'center',
              x: 0.5,
              font: { size: 11, color: '#9ca3af' },
            },
            xaxis: {
              gridcolor: '#374151',
              gridwidth: 0.5,
              showline: true,
              linecolor: '#374151',
              linewidth: 0.5,
              tickfont: { size: 11, color: '#9ca3af' },
              zeroline: false,
            },
            yaxis: {
              title: { text: 'ZL Price (¢/lb)', font: { size: 13, color: '#9ca3af' } },
              gridcolor: '#374151',
              gridwidth: 0.5,
              showline: true,
              linecolor: '#374151',
              linewidth: 0.5,
              tickfont: { size: 11, color: '#9ca3af' },
              zeroline: false,
            },
            dragmode: 'pan',
          }}
          config={{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['select2d', 'lasso2d'],
            displaylogo: false,
            toImageButtonOptions: {
              format: 'png',
              filename: 'zl_forecast_chart',
              height: 1200,
              width: 2400,
              scale: 2,
            },
          }}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler={true}
        />
      </div>
    </div>
  );
}
