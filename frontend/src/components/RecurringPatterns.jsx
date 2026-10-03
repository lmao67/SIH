import React, { useMemo } from 'react';
import { Layers, AlertTriangle, ShieldX, Activity as ActivityIcon, ArrowRight, Zap } from 'lucide-react';

export default function RecurringPatterns({ reports = [] }) {
  const topPatterns = useMemo(() => {
    // Only consider SIF-flagged reports
    const flagged = reports.filter(r => r.sif_potential === true);
    const patternMap = {};

    flagged.forEach(r => {
      const act = (r.activity || 'Unspecified Activity').trim();
      const bar = (r.barrier_failure || 'Unspecified Barrier Failure').trim();
      const key = `${act}|||${bar}`;

      if (!patternMap[key]) {
        patternMap[key] = {
          activity: act,
          barrier_failure: bar,
          count: 0,
          lsrTags: new Set(),
          sites: new Set(),
          sampleIds: [],
        };
      }

      patternMap[key].count += 1;
      if (r.lsr_tag) patternMap[key].lsrTags.add(r.lsr_tag);
      if (r.site) patternMap[key].sites.add(r.site);
      if (r.id) patternMap[key].sampleIds.push(r.id);
    });

    return Object.values(patternMap)
      .sort((a, b) => b.count - a.count)
      .slice(0, 5); // Top 5 by frequency
  }, [reports]);

  const rankBadges = [
    { bg: 'bg-red-500/20 text-red-300 border-red-500/40', label: '#1 CRITICAL' },
    { bg: 'bg-amber-500/20 text-amber-300 border-amber-500/40', label: '#2 ELEVATED' },
    { bg: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40', label: '#3 MODERATE' },
    { bg: 'bg-blue-500/20 text-blue-300 border-blue-500/40', label: '#4 RECURRING' },
    { bg: 'bg-slate-700/40 text-slate-300 border-slate-600/40', label: '#5 NOTED' },
  ];

  return (
    <div className="glass-panel rounded-xl p-5 border border-slate-800 shadow-panel mt-6">
      
      {/* Panel Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-4 border-b border-slate-800/80 mb-5">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400">
            <Layers className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
              Recurring Precursor Patterns
              <span className="text-[10px] font-mono uppercase bg-red-500/20 text-red-300 px-2 py-0.5 rounded border border-red-500/30 font-semibold">
                TOP 5 BY FREQUENCY
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Identifies systemic failure modes grouped by precursor activity and failed control barrier
            </p>
          </div>
        </div>

        <div className="text-xs font-mono text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
          Clustering: <span className="text-slate-200 font-semibold">Activity + Barrier Failure</span>
        </div>
      </div>

      {/* Patterns Grid */}
      {topPatterns.length === 0 ? (
        <div className="py-10 text-center text-slate-500 text-xs font-sans">
          No recurring precursor patterns identified in current filter selection.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3.5">
          {topPatterns.map((pattern, idx) => {
            const badge = rankBadges[idx] || rankBadges[4];
            const tags = Array.from(pattern.lsrTags);
            const sites = Array.from(pattern.sites);

            return (
              <div 
                key={idx}
                className="bg-[#0b101a] border border-slate-800 hover:border-slate-700 rounded-xl p-4 flex flex-col justify-between transition-all duration-150 hover:-translate-y-0.5 hover:shadow-panel relative overflow-hidden group"
              >
                {/* Subtle top indicator bar */}
                <div className={`absolute top-0 left-0 right-0 h-1 ${
                  idx === 0 ? 'bg-red-500' : idx === 1 ? 'bg-amber-500' : 'bg-slate-700'
                }`}></div>

                <div>
                  {/* Top: Rank and Count */}
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${badge.bg}`}>
                      {badge.label}
                    </span>
                    <span className="font-mono text-xs font-bold text-white bg-slate-800/90 px-2 py-0.5 rounded border border-slate-700 flex items-center gap-1">
                      <span className="text-red-400">{pattern.count}</span> {pattern.count === 1 ? 'incident' : 'incidents'}
                    </span>
                  </div>

                  {/* Activity */}
                  <div className="mb-3">
                    <div className="text-[10px] font-mono uppercase text-slate-400 flex items-center gap-1 mb-1 font-semibold">
                      <ActivityIcon className="h-3 w-3 text-amber-400" /> Operational Activity
                    </div>
                    <p className="text-xs font-medium text-slate-200 line-clamp-2 leading-snug">
                      {pattern.activity}
                    </p>
                  </div>

                  {/* Barrier Failure */}
                  <div className="mb-3 p-2.5 rounded-lg bg-red-950/20 border border-red-500/25">
                    <div className="text-[10px] font-mono uppercase text-red-400 flex items-center gap-1 mb-1 font-semibold">
                      <ShieldX className="h-3 w-3 text-red-400" /> Barrier Failure
                    </div>
                    <p className="text-xs text-red-200 font-sans line-clamp-3 leading-snug">
                      {pattern.barrier_failure}
                    </p>
                  </div>
                </div>

                {/* Bottom: Tags & Impacted Sites */}
                <div className="pt-2 border-t border-slate-800/80 mt-2 space-y-1.5">
                  <div className="flex flex-wrap gap-1">
                    {tags.map((t, i) => (
                      <span key={i} className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-medium border border-slate-700">
                        {t}
                      </span>
                    ))}
                  </div>
                  <div className="text-[10px] text-slate-400 truncate" title={sites.join(', ')}>
                    Sites: <span className="text-slate-300">{sites.join(', ') || 'N/A'}</span>
                  </div>
                  <div className="text-[10px] font-mono text-slate-500">
                    Cases: {pattern.sampleIds.slice(0, 3).map(id => `#${id}`).join(', ')}
                    {pattern.sampleIds.length > 3 ? '...' : ''}
                  </div>
                </div>

              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
