import React, { useMemo } from 'react';
import { 
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, 
  PieChart, Pie, Cell, Legend 
} from 'recharts';
import { BarChart3, PieChart as PieChartIcon } from 'lucide-react';

const LSR_COLORS = [
  '#ef4444', // red
  '#f59e0b', // amber
  '#3b82f6', // blue
  '#10b981', // emerald
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#f97316', // orange
  '#14b8a6', // teal
  '#64748b', // slate (for None)
];

export default function AnalyticsCharts({ reports = [] }) {
  // 1. Calculate SIF-precursor density by site for Horizontal Bar Chart
  const siteDensityData = useMemo(() => {
    const siteMap = {};
    reports.forEach(r => {
      const site = r.site || 'Unknown Site';
      if (!siteMap[site]) {
        siteMap[site] = { site, total: 0, sifCount: 0 };
      }
      siteMap[site].total += 1;
      if (r.sif_potential === true) {
        siteMap[site].sifCount += 1;
      }
    });

    return Object.values(siteMap)
      .map(item => ({
        site: item.site,
        total: item.total,
        sifCount: item.sifCount,
        density: item.total > 0 ? parseFloat(((item.sifCount / item.total) * 100).toFixed(1)) : 0,
      }))
      .sort((a, b) => b.density - a.density) // highest density first
      .slice(0, 8); // Top 8 sites for clean chart layout
  }, [reports]);

  // 2. Calculate flagged reports by Life-Saving Rule for Donut Chart
  const lsrDonutData = useMemo(() => {
    const flagged = reports.filter(r => r.sif_potential === true);
    const lsrCounts = {};

    flagged.forEach(r => {
      const tag = r.lsr_tag || 'None';
      lsrCounts[tag] = (lsrCounts[tag] || 0) + 1;
    });

    return Object.entries(lsrCounts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  }, [reports]);

  const totalFlaggedCount = useMemo(() => {
    return reports.filter(r => r.sif_potential === true).length;
  }, [reports]);

  return (
    <div className="flex flex-col gap-6">
      
      {/* Chart 1: Horizontal Bar Chart - Precursor Density by Site */}
      <div className="glass-panel rounded-xl p-5 border border-slate-800 shadow-panel">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400">
              <BarChart3 className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white tracking-wide">
                SIF Density by Site (%)
              </h3>
              <p className="text-[11px] text-slate-400">
                Precursors / Total Reports ratio per facility
              </p>
            </div>
          </div>
          <span className="text-[10px] font-mono uppercase bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">
            Top Risk Sites
          </span>
        </div>

        <div className="h-64 w-full">
          {siteDensityData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">
              No site telemetry available
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={siteDensityData}
                margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
              >
                <XAxis 
                  type="number" 
                  domain={[0, 100]} 
                  unit="%" 
                  tick={{ fill: '#64748b', fontSize: 10, fontFamily: 'monospace' }}
                  axisLine={{ stroke: '#1e293b' }}
                  tickLine={{ stroke: '#1e293b' }}
                />
                <YAxis 
                  dataKey="site" 
                  type="category" 
                  width={110}
                  tick={{ fill: '#cbd5e1', fontSize: 10, fontFamily: 'sans-serif' }}
                  axisLine={{ stroke: '#1e293b' }}
                  tickLine={false}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-[#0b121f] border border-slate-700 p-3 rounded-lg shadow-xl text-xs space-y-1">
                          <p className="font-bold text-white">{data.site}</p>
                          <p className="text-amber-400 font-mono">
                            SIF Density: <span className="font-bold">{data.density}%</span>
                          </p>
                          <p className="text-slate-400 font-mono text-[11px]">
                            SIF Flagged: {data.sifCount} of {data.total} reports
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar 
                  dataKey="density" 
                  fill="#f59e0b" 
                  radius={[0, 4, 4, 0]}
                  barSize={14}
                >
                  {siteDensityData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.density > 40 ? '#ef4444' : entry.density > 20 ? '#f59e0b' : '#3b82f6'} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Chart 2: Donut Chart - Flagged Reports by Life-Saving Rule */}
      <div className="glass-panel rounded-xl p-5 border border-slate-800 shadow-panel">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
              <PieChartIcon className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white tracking-wide">
                Life-Saving Rules Distribution
              </h3>
              <p className="text-[11px] text-slate-400">
                Breakdown of {totalFlaggedCount} SIF precursor incidents
              </p>
            </div>
          </div>
          <span className="text-[10px] font-mono uppercase bg-red-500/20 text-red-300 px-2 py-0.5 rounded border border-red-500/30">
            IOGP 9 RULES
          </span>
        </div>

        <div className="h-64 w-full relative">
          {lsrDonutData.length === 0 ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">
              No SIF precursor records found
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={lsrDonutData}
                    cx="50%"
                    cy="45%"
                    innerRadius={50}
                    outerRadius={78}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {lsrDonutData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={LSR_COLORS[index % LSR_COLORS.length]} 
                        stroke="#0f172a" 
                        strokeWidth={2}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0];
                        const pct = totalFlaggedCount > 0 
                          ? ((data.value / totalFlaggedCount) * 100).toFixed(1) 
                          : '0.0';
                        return (
                          <div className="bg-[#0b121f] border border-slate-700 p-2.5 rounded-lg shadow-xl text-xs space-y-0.5">
                            <p className="font-bold text-white">{data.name}</p>
                            <p className="text-red-400 font-mono font-semibold">
                              {data.value} incidents ({pct}%)
                            </p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Legend 
                    layout="horizontal" 
                    verticalAlign="bottom" 
                    align="center"
                    wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }}
                    formatter={(value) => <span className="text-slate-300 font-medium">{value}</span>}
                  />
                </PieChart>
              </ResponsiveContainer>

              {/* Center donut label */}
              <div className="absolute top-[45%] left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none text-center">
                <div className="text-lg font-extrabold font-mono text-white leading-none">
                  {totalFlaggedCount}
                </div>
                <div className="text-[9px] uppercase tracking-wider text-slate-400 font-mono mt-0.5">
                  SIF PRECURSORS
                </div>
              </div>
            </>
          )}
        </div>
      </div>

    </div>
  );
}
