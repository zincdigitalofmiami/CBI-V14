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
          fetch('/api/v4/live/zl'),
          fetch('/api/v4/forecasts/all'),
        ]);
        
        const zlJson = await zlRes.json();
        const forecastsJson = await forecastsRes.json();
        
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
  const highs = zlData.map(d => d.high);
  const lows = zlData.map(d => d.low);

  // Build forecast traces
  const forecastTraces: any[] = [];
  const horizonColors = {
    '1w': 'rgba(16, 185, 129, 0.3)',
    '1m': 'rgba(34, 211, 153, 0.3)',
    '3m': 'rgba(110, 231, 183, 0.3)',
    '6m': 'rgba(167, 243, 208, 0.3)',
  };
  const horizonLineColors = {
    '1w': '#10b981',
    '1m': '#22d3a5',
    '3m': '#6ee7b7',
    '6m': '#a7f3d0',
  };

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  forecasts.forEach((forecast) => {
    const targetDate = new Date(forecast.target_date);
    const predictionDate = new Date(forecast.prediction_date);
    
    // Probability band (shaded area)
    forecastTraces.push({
      x: [predictionDate.toISOString().split('T')[0], targetDate.toISOString().split('T')[0]],
      y: [forecast.confidence_lower, forecast.confidence_lower],
      type: 'scatter',
      mode: 'lines',
      name: `${forecast.horizon.toUpperCase()} Lower`,
      line: { width: 0 },
      showlegend: false,
      hoverinfo: 'skip',
      fill: 'tonexty',
      fillcolor: horizonColors[forecast.horizon as keyof typeof horizonColors] || 'rgba(16, 185, 129, 0.1)',
    });

    forecastTraces.push({
      x: [predictionDate.toISOString().split('T')[0], targetDate.toISOString().split('T')[0]],
      y: [forecast.confidence_upper, forecast.confidence_upper],
      type: 'scatter',
      mode: 'lines',
      name: `${forecast.horizon.toUpperCase()} Upper`,
      line: { width: 0 },
      showlegend: false,
      hoverinfo: 'skip',
      fillcolor: horizonColors[forecast.horizon as keyof typeof horizonColors] || 'rgba(16, 185, 129, 0.1)',
    });

    // Forecast line (thin, semi-transparent)
    forecastTraces.push({
      x: [predictionDate.toISOString().split('T')[0], targetDate.toISOString().split('T')[0]],
      y: [forecast.prediction, forecast.prediction],
      type: 'scatter',
      mode: 'lines',
      name: `${forecast.horizon.toUpperCase()} Forecast`,
      line: {
        color: horizonLineColors[forecast.horizon as keyof typeof horizonLineColors] || '#10b981',
        width: 1.5,
        dash: 'dot',
      },
      opacity: 0.6,
      hovertemplate: `${forecast.horizon.toUpperCase()}: $%{y:.2f}<extra></extra>`,
    });
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-text-secondary">Loading ZL data...</p>
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
        </div>
      </div>

      {/* Full-width chart - takes up entire remaining space */}
      <div className="flex-1 bg-background-primary">
        <Plot
          data={[
            // Historical ZL Price (thick, primary)
            {
              x: dates,
              y: closes,
              type: 'scatter',
              mode: 'lines',
              name: 'ZL Price',
              line: { color: '#10b981', width: 3, shape: 'spline' },
              hovertemplate: '$%{y:.2f}<extra></extra>',
            },
            // High/Low range (subtle)
            {
              x: dates,
              y: highs,
              type: 'scatter',
              mode: 'lines',
              name: 'High',
              line: { color: '#10b981', width: 0.5, dash: 'dot' },
              opacity: 0.2,
              showlegend: false,
              hoverinfo: 'skip',
            },
            {
              x: dates,
              y: lows,
              type: 'scatter',
              mode: 'lines',
              name: 'Low',
              fill: 'tonexty',
              fillcolor: 'rgba(16, 185, 129, 0.03)',
              line: { color: '#10b981', width: 0.5, dash: 'dot' },
              opacity: 0.2,
              showlegend: false,
              hoverinfo: 'skip',
            },
            // Forecast traces (probability bands + lines)
            ...forecastTraces,
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
