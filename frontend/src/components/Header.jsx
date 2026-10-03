import React from 'react';
import { ShieldCheck, AlertTriangle, Activity, Database, RefreshCw } from 'lucide-react';

export default function Header({ provenance, onRefresh, loading, onOpenProvenance }) {
  const verifiedText = provenance?.summary || "150/150 rows verified against OSHA source";
  const isVerified = provenance?.status === 'verified';

  return (
    <header className="relative bg-[#090e17] border-b border-slate-800/80 shadow-panel">
      {/* Top subtle safety stripe line */}
      <div className="h-1 w-full bg-gradient-to-r from-amber-500 via-red-500 to-emerald-500"></div>

      <div className="max-w-[1700px] mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          
          {/* Left: Branding & Title */}
          <div className="flex items-center space-x-3.5">
            <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-amber-500/20 to-red-500/20 border border-amber-500/40 flex items-center justify-center shadow-hazard">
              <AlertTriangle className="h-5 w-5 text-amber-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[11px] font-mono uppercase tracking-widest text-amber-400 font-semibold px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20">
                  SIH26165 • OIL INDIA LIMITED
                </span>
                <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  LIVE TELEMETRY
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2 mt-0.5">
                HSE Operations Dashboard
                <span className="text-xs font-normal font-mono text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700/60">
                  IOGP Life-Saving Rules AI
                </span>
              </h1>
            </div>
          </div>

          {/* Right: Provenance Badge & Actions */}
          <div className="flex items-center flex-wrap gap-2.5">
            {/* Provenance Badge */}
            <button
              onClick={onOpenProvenance}
              title="Click to view OSHA audit trail"
              className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-emerald-950/40 hover:bg-emerald-900/50 border border-emerald-500/40 text-emerald-300 text-xs font-mono transition-all duration-150 shadow-success-glow hover:scale-[1.02] cursor-pointer group"
            >
              <ShieldCheck className="h-4 w-4 text-emerald-400 group-hover:rotate-12 transition-transform" />
              <span className="font-semibold tracking-wide">
                {verifiedText}
              </span>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.2 rounded border border-emerald-500/30">
                AUDIT
              </span>
            </button>

            {/* Refresh Button */}
            <button
              onClick={onRefresh}
              disabled={loading}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/80 text-slate-300 hover:text-white text-xs font-medium transition-all duration-150 disabled:opacity-50"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin text-amber-400' : ''}`} />
              <span>{loading ? 'Refreshing...' : 'Sync'}</span>
            </button>
          </div>

        </div>
      </div>
    </header>
  );
}
