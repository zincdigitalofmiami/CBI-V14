import React, { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Loader2, Sparkles, Info } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

/**
 * FeatureImportanceCard
 * - Purely data-driven from your API (Vertex → BigQuery → Next.js).
 * - NO placeholders, NO mock arrays, NO Math.random().
 * - If the API returns no rows → shows a clean "No data" state.
 *
 * Expected API response shape:
 * { horizon: "1W", rows: [{ feature: "feature_vix_stress", importance: 0.28 }, ...] }
 */

export default function FeatureImportanceCard({
  horizon = "1w",
  title = "Top Price Drivers (Vertex Explainability)",
  maxBars = 10,
}: {
  horizon?: string;
  title?: string;
  maxBars?: number;
}) {
  const [rows, setRows] = useState<Array<{ feature: string; importance: number }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    (async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(`/api/v4/feature-importance/${horizon}`, { cache: "no-store" });

        if (!res.ok) {
          const msg = `API ${res.status}: ${res.statusText}`;
          throw new Error(msg);
        }

        const data = await res.json();

        if (!alive) return;

        // Strict validation – reject anything that looks mocked
        if (!data || typeof data !== "object" || !Array.isArray(data.rows)) {
          throw new Error("Invalid response shape");
        }

        const cleaned = data.rows
          .filter((d: any) =>
            d && typeof d.feature === "string" && typeof d.importance === "number"
          )
          .map((d: any) => ({ ...d, importance: Number(d.importance) }))
          .filter((d: any) => Number.isFinite(d.importance));

        // Sort & take top N
        cleaned.sort((a: any, b: any) => b.importance - a.importance);
        setRows(cleaned.slice(0, maxBars));
      } catch (e: any) {
        if (alive) setError(e?.message || "Unknown error");
      } finally {
        if (alive) setLoading(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, [horizon, maxBars]);

  const total = useMemo(
    () => rows.reduce((acc, r) => acc + (r.importance || 0), 0),
    [rows]
  );

  return (
    <div className="bg-[#0a0e17] border border-white/5 shadow-xl rounded-2xl">
      <div className="flex items-center justify-between px-5 pt-5">
        <h3 className="text-sm md:text-base text-[#E0E0E3] font-medium tracking-wide flex items-center gap-2">
          <Sparkles className="w-4 h-4" /> {title}
        </h3>
        <div className="text-[11px] md:text-xs text-[#9099a6]">Source: Vertex → BigQuery</div>
      </div>

      <div className="p-5">
        {loading ? (
          <div className="flex items-center justify-center gap-2 py-10 text-[#9099a6]">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading…
          </div>
        ) : error ? (
          <div className="flex items-start gap-3 p-4 rounded-lg bg-red-950/40 border border-red-800/40 text-red-200">
            <AlertTriangle className="w-4 h-4 mt-0.5" />
            <div>
              <div className="font-medium">Error</div>
              <div className="text-sm opacity-80">{error}</div>
            </div>
          </div>
        ) : rows.length === 0 ? (
          <div className="flex items-start gap-3 p-4 rounded-lg bg-white/5 border border-white/10 text-[#E0E0E3]">
            <Info className="w-4 h-4 mt-0.5" />
            <div>
              <div className="font-medium">No data</div>
              <div className="text-sm text-[#9099a6]">
                The API returned zero rows. This component never uses placeholder
                data. Once BigQuery has explainability rows, they'll render here.
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Chart */}
            <div className="col-span-1 lg:col-span-2 h-[260px] rounded-xl bg-[#0f1522] border border-white/5 p-3">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={rows} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2a3a" />
                  <XAxis
                    dataKey="feature"
                    tick={{ fill: "#9099a6", fontSize: 11 }}
                    tickLine={false}
                    axisLine={{ stroke: "#273248" }}
                    interval={0}
                    height={48}
                    angle={-25}
                    textAnchor="end"
                  />
                  <YAxis
                    tick={{ fill: "#9099a6", fontSize: 11 }}
                    axisLine={{ stroke: "#273248" }}
                    tickLine={false}
                    width={40}
                  />
                  <Tooltip
                    contentStyle={{ background: "#0f1522", border: "1px solid #243047", borderRadius: 10 }}
                    labelStyle={{ color: "#E0E0E3" }}
                    itemStyle={{ color: "#E0E0E3" }}
                    formatter={(v: any) => [Number(v).toFixed(3), "importance"]}
                  />
                  <Bar dataKey="importance" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Ranked list */}
            <div className="col-span-1 space-y-3">
              {rows.map((r, i) => (
                <div key={r.feature} className="flex items-center justify-between gap-4 p-3 rounded-xl bg-[#0f1522] border border-white/5">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs text-[#9099a6] w-6 text-right">{i + 1}</span>
                    <span className="text-sm text-[#E0E0E3] truncate" title={r.feature}>
                      {r.feature}
                    </span>
                  </div>
                  <div className="text-sm tabular-nums text-[#E0E0E3] ml-2">
                    {r.importance.toFixed(3)}
                  </div>
                </div>
              ))}
              <div className="text-[11px] text-[#9099a6] pt-2">
                Total shown: {rows.length} • Sum importance: {total.toFixed(3)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}




