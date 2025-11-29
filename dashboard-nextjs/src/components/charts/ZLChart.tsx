 'use client';

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export function ZLChart() {
  const [zlData, setZlData] = useState<any[]>([]);
  const [latestPrice, setLatestPrice] = useState(0);
  const [priceChange, setPriceChange] = useState(0);
  const [priceChangePct, setPriceChangePct] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch('/api/v4/live/zl');
        const json = await res.json();
        const zl = json.data || [];

        setZlData(zl);

        if (zl.length > 0) {
          const latest = zl[zl.length - 1].close;
          setLatestPrice(latest);

          if (zl.length > 1) {
            const prev = zl[zl.length - 2].close;
            const change = latest - prev;
            setPriceChange(change);
            setPriceChangePct((change / prev) * 100);
          }
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

  const dates = zlData.map((d) => d.date?.value || d.date);
  const closes = zlData.map((d) => d.close);
  const highs = zlData.map((d) => d.high);
  const lows = zlData.map((d) => d.low);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-text-secondary">Loading ZL data...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Price Header */}
      <div className="flex items-baseline gap-4">
        <h1 className="text-3xl font-bold text-text-primary">ZL Soybean Oil Futures</h1>
        <span className="text-4xl font-semibold text-text-primary">${latestPrice.toFixed(2)}</span>
        <span className={`text-xl font-medium ${priceChange >= 0 ? 'text-bull-500' : 'text-bear-500'}`}>
          {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)} ({priceChangePct >= 0 ? '+' : ''}{priceChangePct.toFixed(2)}%)
        </span>
      </div>

      {/* Chart */}
      <div className="bg-background-secondary border border-border-primary rounded-lg p-6">
        <div className="h-[600px]">
          <Plot
            data={[
              {
                x: dates,
                y: closes,
                type: 'scatter',
                mode: 'lines',
                name: 'ZL Price',
                line: { color: '#10b981', width: 2, shape: 'spline' },
                hovertemplate: '$%{y:.2f}<extra></extra>',
              },
              {
                x: dates,
                y: highs,
                type: 'scatter',
                mode: 'lines',
                name: 'High',
                line: { color: '#10b981', width: 0.5, dash: 'dot' },
                opacity: 0.3,
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
                fillcolor: 'rgba(16, 185, 129, 0.05)',
                line: { color: '#10b981', width: 0.5, dash: 'dot' },
                opacity: 0.3,
                showlegend: false,
                hoverinfo: 'skip',
              },
            ]}
            layout={{
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
              font: { family: 'system-ui', size: 11, color: '#9ca3af' },
              margin: { t: 20, r: 40, b: 50, l: 60 },
              hovermode: 'x unified',
              showlegend: true,
              legend: {
                orientation: 'h',
                yanchor: 'bottom',
                y: 1.02,
                xanchor: 'right',
                x: 1,
                font: { size: 10, color: '#9ca3af' },
              },
              xaxis: {
                gridcolor: '#374151',
                gridwidth: 0.5,
                showline: true,
                linecolor: '#374151',
                linewidth: 0.5,
                tickfont: { size: 10, color: '#9ca3af' },
                zeroline: false,
              },
              yaxis: {
                title: { text: 'ZL Price (¢/lb)', font: { size: 11, color: '#9ca3af' } },
                gridcolor: '#374151',
                gridwidth: 0.5,
                showline: true,
                linecolor: '#374151',
                linewidth: 0.5,
                tickfont: { size: 10, color: '#9ca3af' },
                zeroline: false,
                side: 'left',
              },
              dragmode: 'pan',
            }}
            config={{
              responsive: true,
              displayModeBar: true,
              modeBarButtonsToRemove: ['select2d', 'lasso2d', 'autoScale2d'],
              displaylogo: false,
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler={true}
          />
        </div>
      </div>
    </div>
  );
}


