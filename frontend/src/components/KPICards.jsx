import React from 'react';
import { ClipboardList, AlertOctagon, Flame, MapPin, TrendingUp, ShieldAlert } from 'lucide-react';

export default function KPICards({ reports = [] }) {
  const totalReports = reports.length;
  const sifCount = reports.filter(r => r.sif_potential === true).length;
  const density = totalReports > 0 ? ((sifCount / totalReports) * 100).toFixed(1) : "0.0";

  // Calculate highest-risk site
  const siteStats = {};
  reports.forEach(r => {
    const site = r.site || "Unassigned Site";
    if (!siteStats[site]) {
      siteStats[site] = { total: 0, sif: 0 };
    }
    siteStats[site].total += 1;
    if (r.sif_potential === true) {
      siteStats[site].sif += 1;
    }
  });

  let highestRiskSite = "None";
  let maxSif = -1;
  let highestRiskDensity = "0.0";

  Object.entries(siteStats).forEach(([site, stats]) => {
    if (stats.sif > maxSif) {
      maxSif = stats.sif;
      highestRiskSite = site;
      highestRiskDensity = stats.total > 0 ? ((stats.sif / stats.total) * 100).toFixed(0) : "0";
    }
  });

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      
      {/* Card 1: Total Reports */}
      <div className="glass-panel rounded-xl p-5 relative overflow-hidden transition-all duration-200 hover:-translate-y-0.5 hover:shadow-panel group">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-medium text-slate-400 uppercase tracking-wider">
            Total Ingested Reports
          </span>
          <div className="p-2 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300 group-hover:text-blue-400 transition-colors">
            <ClipboardList className="h-5 w-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-white font-mono tracking-tight">
            {totalReports}
          </span>
          <span className="text-xs text-slate-400 font-medium">narratives</span>
        </div>
        <div className="mt-3 flex items-center text-xs text-slate-400">
          <span className="inline-flex items-center text-emerald-400 mr-1.5 font-medium">
            <TrendingUp className="h-3.5 w-3.5 mr-1" /> Active
          </span>
          Live operational dataset
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-slate-700/50 group-hover:bg-blue-500/80 transition-colors"></div>
      </div>

      {/* Card 2: SIF-Flagged Count */}
      <div className="glass-panel rounded-xl p-5 relative overflow-hidden transition-all duration-200 hover:-translate-y-0.5 hover:shadow-danger-glow group border-red-500/30 bg-gradient-to-br from-red-950/20 to-slate-900/90">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-medium text-red-400 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
            SIF-Flagged Incidents
          </span>
          <div className="p-2 rounded-lg bg-red-500/20 border border-red-500/40 text-red-400 group-hover:scale-110 transition-transform">
            <AlertOctagon className="h-5 w-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-red-400 font-mono tracking-tight">
            {sifCount}
          </span>
          <span className="text-xs text-red-300/70 font-medium">precursors detected</span>
        </div>
        <div className="mt-3 flex items-center text-xs text-red-300/80">
          <ShieldAlert className="h-3.5 w-3.5 mr-1 text-red-400" />
          High-energy hazard + failed control
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-red-500 group-hover:h-[3px] transition-all"></div>
      </div>

      {/* Card 3: SIF-Precursor Density */}
      <div className="glass-panel rounded-xl p-5 relative overflow-hidden transition-all duration-200 hover:-translate-y-0.5 hover:shadow-hazard group border-amber-500/30 bg-gradient-to-br from-amber-950/20 to-slate-900/90">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-medium text-amber-400 uppercase tracking-wider">
            SIF Precursor Density
          </span>
          <div className="p-2 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-400 group-hover:scale-110 transition-transform">
            <Flame className="h-5 w-5" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl font-extrabold text-amber-400 font-mono tracking-tight">
            {density}%
          </span>
          <span className="text-xs text-amber-300/70 font-medium">of total reports</span>
        </div>
        <div className="mt-3 flex items-center text-xs text-amber-300/80">
          <span>Density threshold: </span>
          <span className="font-mono ml-1 font-semibold text-amber-400">
            {parseFloat(density) > 25 ? 'High Criticality' : 'Baseline'}
          </span>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-amber-500 group-hover:h-[3px] transition-all"></div>
      </div>

      {/* Card 4: Highest-Risk Site */}
      <div className="glass-panel rounded-xl p-5 relative overflow-hidden transition-all duration-200 hover:-translate-y-0.5 hover:shadow-panel group border-purple-500/30 bg-gradient-to-br from-purple-950/20 to-slate-900/90">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono font-medium text-purple-400 uppercase tracking-wider">
            Highest-Risk Operational Site
          </span>
          <div className="p-2 rounded-lg bg-purple-500/20 border border-purple-500/40 text-purple-400 group-hover:scale-110 transition-transform">
            <MapPin className="h-5 w-5" />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-lg font-bold text-white tracking-tight truncate" title={highestRiskSite}>
            {highestRiskSite}
          </div>
          <div className="text-xs text-purple-300/80 font-mono mt-1">
            {maxSif > 0 ? (
              <span>
                <strong className="text-purple-300">{maxSif}</strong> precursors ({highestRiskDensity}% site density)
              </span>
            ) : (
              <span>Zero flagged precursors</span>
            )}
          </div>
        </div>
        <div className="mt-2.5 flex items-center text-xs text-purple-300/70">
          <span className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono text-[10px] border border-purple-500/30">
            PRIORITY AUDIT
          </span>
        </div>
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-purple-500 group-hover:h-[3px] transition-all"></div>
      </div>

    </div>
  );
}
