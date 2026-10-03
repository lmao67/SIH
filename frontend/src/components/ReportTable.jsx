import React, { useState, useMemo } from 'react';
import { 
  Search, Filter, ChevronDown, ChevronRight, AlertOctagon, 
  CheckCircle2, ArrowUpDown, ArrowUp, ArrowDown, Shield, 
  Cpu, Zap, Flame, Truck, Anchor, Crosshair, Wrench, FileText
} from 'lucide-react';

const ENERGY_COLORS = {
  height: { bg: 'bg-indigo-500/15', text: 'text-indigo-400', border: 'border-indigo-500/30', label: 'Gravitational' },
  vehicle: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30', label: 'Vehicle' },
  thermal: { bg: 'bg-orange-500/15', text: 'text-orange-400', border: 'border-orange-500/30', label: 'Thermal' },
  electrical: { bg: 'bg-yellow-500/15', text: 'text-yellow-400', border: 'border-yellow-500/30', label: 'Electrical' },
  pressure: { bg: 'bg-cyan-500/15', text: 'text-cyan-400', border: 'border-cyan-500/30', label: 'Pressure' },
  toxic: { bg: 'bg-purple-500/15', text: 'text-purple-400', border: 'border-purple-500/30', label: 'Toxic/Asphyxiant' },
  mechanical: { bg: 'bg-blue-500/15', text: 'text-blue-400', border: 'border-blue-500/30', label: 'Mechanical' },
  none: { bg: 'bg-slate-700/30', text: 'text-slate-400', border: 'border-slate-700/40', label: 'Low Energy' },
};

const LSR_LIST = [
  "Bypassing Safety Controls",
  "Confined Space",
  "Driving",
  "Energy Isolation",
  "Hot Work",
  "Line of Fire",
  "Safe Mechanical Lifting",
  "Work Authorisation",
  "Working at Height",
  "None",
];

export default function ReportTable({ 
  reports = [], 
  selectedSite, 
  setSelectedSite, 
  sifFilter, 
  setSifFilter, 
  lsrFilter, 
  setLsrFilter 
}) {
  const [expandedRowId, setExpandedRowId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('id');
  const [sortAsc, setSortAsc] = useState(true);

  // Extract unique sites
  const uniqueSites = useMemo(() => {
    const sites = new Set();
    reports.forEach(r => {
      if (r.site) sites.add(r.site);
    });
    return Array.from(sites).sort();
  }, [reports]);

  // Filter reports
  const filteredReports = useMemo(() => {
    return reports.filter(r => {
      // Site filter
      if (selectedSite && selectedSite !== 'All' && r.site !== selectedSite) {
        return false;
      }
      // SIF filter
      if (sifFilter === 'true' && r.sif_potential !== true) {
        return false;
      }
      if (sifFilter === 'false' && r.sif_potential !== false) {
        return false;
      }
      // LSR filter
      if (lsrFilter && lsrFilter !== 'All' && r.lsr_tag !== lsrFilter) {
        return false;
      }
      // Search term
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const narr = (r.report_text || '').toLowerCase();
        const act = (r.activity || '').toLowerCase();
        const loc = (r.location || '').toLowerCase();
        const bar = (r.barrier_failure || '').toLowerCase();
        const site = (r.site || '').toLowerCase();
        if (!narr.includes(query) && !act.includes(query) && !loc.includes(query) && !bar.includes(query) && !site.includes(query)) {
          return false;
        }
      }
      return true;
    });
  }, [reports, selectedSite, sifFilter, lsrFilter, searchTerm]);

  // Sort reports
  const sortedReports = useMemo(() => {
    return [...filteredReports].sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      if (sortField === 'id') {
        aVal = Number(aVal) || 0;
        bVal = Number(bVal) || 0;
      } else if (sortField === 'confidence') {
        aVal = Number(aVal) || 0;
        bVal = Number(bVal) || 0;
      } else {
        aVal = String(aVal || '').toLowerCase();
        bVal = String(bVal || '').toLowerCase();
      }

      if (aVal < bVal) return sortAsc ? -1 : 1;
      if (aVal > bVal) return sortAsc ? 1 : -1;
      return 0;
    });
  }, [filteredReports, sortField, sortAsc]);

  const toggleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  const toggleRow = (id) => {
    setExpandedRowId(expandedRowId === id ? null : id);
  };

  const getSortIcon = (field) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-3 w-3 text-slate-500 opacity-60 group-hover:opacity-100" />;
    }
    return sortAsc 
      ? <ArrowUp className="h-3.5 w-3.5 text-amber-400" />
      : <ArrowDown className="h-3.5 w-3.5 text-amber-400" />;
  };

  return (
    <div className="glass-panel rounded-xl overflow-hidden border border-slate-800 shadow-panel">
      
      {/* Table Header & Filter Bar */}
      <div className="p-4 sm:p-5 border-b border-slate-800/80 bg-[#0c121e]">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          
          <div>
            <h2 className="text-base font-bold text-white tracking-wide flex items-center gap-2">
              <span>Incident Classification Registry</span>
              <span className="text-xs font-mono font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                {sortedReports.length} of {reports.length} records
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Click any row to inspect model reasoning and structured precursor fields
            </p>
          </div>

          {/* Search Box */}
          <div className="relative w-full lg:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search narrative, activity, barrier..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-900/80 border border-slate-700 rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors font-sans"
            />
          </div>

        </div>

        {/* Filter Dropdowns Row */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4 pt-3 border-t border-slate-800/60">
          
          {/* Site Filter */}
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400 font-mono font-medium shrink-0">Site:</span>
            <select
              value={selectedSite}
              onChange={(e) => setSelectedSite(e.target.value)}
              className="w-full bg-slate-900/90 border border-slate-700/80 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-amber-500 font-sans"
            >
              <option value="All">All Sites ({uniqueSites.length})</option>
              {uniqueSites.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* SIF Filter */}
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400 font-mono font-medium shrink-0">SIF Potential:</span>
            <select
              value={sifFilter}
              onChange={(e) => setSifFilter(e.target.value)}
              className="w-full bg-slate-900/90 border border-slate-700/80 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-amber-500 font-sans"
            >
              <option value="All">All Classifications</option>
              <option value="true">SIF-Precursor Only (True)</option>
              <option value="false">Non-SIF (False)</option>
            </select>
          </div>

          {/* LSR Tag Filter */}
          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-400 font-mono font-medium shrink-0">Life-Saving Rule:</span>
            <select
              value={lsrFilter}
              onChange={(e) => setLsrFilter(e.target.value)}
              className="w-full bg-slate-900/90 border border-slate-700/80 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-amber-500 font-sans"
            >
              <option value="All">All Life-Saving Rules</option>
              {LSR_LIST.map(rule => (
                <option key={rule} value={rule}>{rule}</option>
              ))}
            </select>
          </div>

        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-[#090f19] text-slate-400 font-mono font-semibold uppercase tracking-wider">
              <th 
                className="py-3 px-3.5 cursor-pointer hover:text-white transition-colors group w-16"
                onClick={() => toggleSort('id')}
              >
                <div className="flex items-center gap-1.5">
                  <span>ID</span>
                  {getSortIcon('id')}
                </div>
              </th>
              <th 
                className="py-3 px-3.5 cursor-pointer hover:text-white transition-colors group w-36"
                onClick={() => toggleSort('site')}
              >
                <div className="flex items-center gap-1.5">
                  <span>Site</span>
                  {getSortIcon('site')}
                </div>
              </th>
              <th className="py-3 px-3.5 min-w-[280px]">
                <span>Narrative Extract</span>
              </th>
              <th 
                className="py-3 px-3 cursor-pointer hover:text-white transition-colors group w-28"
                onClick={() => toggleSort('energy_type')}
              >
                <div className="flex items-center gap-1.5">
                  <span>Energy Type</span>
                  {getSortIcon('energy_type')}
                </div>
              </th>
              <th 
                className="py-3 px-3.5 cursor-pointer hover:text-white transition-colors group w-44"
                onClick={() => toggleSort('lsr_tag')}
              >
                <div className="flex items-center gap-1.5">
                  <span>Life-Saving Rule</span>
                  {getSortIcon('lsr_tag')}
                </div>
              </th>
              <th 
                className="py-3 px-3.5 cursor-pointer hover:text-white transition-colors group w-24 text-right"
                onClick={() => toggleSort('confidence')}
              >
                <div className="flex items-center justify-end gap-1.5">
                  <span>Confidence</span>
                  {getSortIcon('confidence')}
                </div>
              </th>
              <th className="py-3 px-2 w-8"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {sortedReports.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-12 text-slate-400 font-sans">
                  <div className="flex flex-col items-center justify-center space-y-2">
                    <Filter className="h-8 w-8 text-slate-600 mb-1" />
                    <span className="text-sm font-semibold text-slate-300">No matching reports found</span>
                    <span className="text-xs text-slate-500">Try adjusting your filters or search keywords</span>
                  </div>
                </td>
              </tr>
            ) : (
              sortedReports.map((report) => {
                const isSif = report.sif_potential === true;
                const isExpanded = expandedRowId === report.id;
                const energy = ENERGY_COLORS[report.energy_type] || ENERGY_COLORS.none;
                const confPercent = Math.round((report.confidence || 0) * 100);

                // Row classes: SIF-flagged rows tinted red
                const rowClass = isSif
                  ? "bg-red-950/20 hover:bg-red-950/35 border-l-4 border-l-red-500 text-red-100"
                  : "bg-slate-900/20 hover:bg-slate-800/40 border-l-4 border-l-slate-700/60 text-slate-300";

                return (
                  <React.Fragment key={report.id || report.sha256}>
                    <tr 
                      onClick={() => toggleRow(report.id)}
                      className={`cursor-pointer transition-colors duration-150 ${rowClass} ${isExpanded ? 'bg-slate-800/60' : ''}`}
                    >
                      {/* ID */}
                      <td className="py-3 px-3.5 font-mono font-semibold">
                        <div className="flex items-center gap-1.5">
                          {isSif ? (
                            <span className="w-2 h-2 rounded-full bg-red-500 shrink-0 shadow-[0_0_8px_rgba(239,68,68,0.8)]"></span>
                          ) : (
                            <span className="w-2 h-2 rounded-full bg-slate-600 shrink-0"></span>
                          )}
                          <span className={isSif ? 'text-red-400' : 'text-slate-400'}>
                            #{report.id}
                          </span>
                        </div>
                      </td>

                      {/* Site */}
                      <td className="py-3 px-3.5">
                        <span className="font-semibold text-white truncate block max-w-[130px]" title={report.site || 'N/A'}>
                          {report.site || 'N/A'}
                        </span>
                      </td>

                      {/* Truncated Narrative */}
                      <td className="py-3 px-3.5">
                        <div className="line-clamp-2 text-slate-300 font-sans leading-relaxed">
                          {report.report_text}
                        </div>
                      </td>

                      {/* Energy Type */}
                      <td className="py-3 px-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium border ${energy.bg} ${energy.text} ${energy.border}`}>
                          {energy.label}
                        </span>
                      </td>

                      {/* LSR Tag */}
                      <td className="py-3 px-3.5">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${
                          report.lsr_tag !== 'None' 
                            ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30' 
                            : 'bg-slate-800 text-slate-400 border border-slate-700/60'
                        }`}>
                          {report.lsr_tag}
                        </span>
                      </td>

                      {/* Confidence */}
                      <td className="py-3 px-3.5 text-right font-mono font-semibold">
                        <div className="flex items-center justify-end gap-1.5">
                          <span className={confPercent >= 80 ? 'text-emerald-400' : 'text-amber-400'}>
                            {confPercent}%
                          </span>
                        </div>
                      </td>

                      {/* Chevron */}
                      <td className="py-3 px-2 text-center text-slate-400">
                        {isExpanded ? (
                          <ChevronDown className="h-4 w-4 text-amber-400 inline" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-slate-500 inline" />
                        )}
                      </td>
                    </tr>

                    {/* Expandable Details Drawer */}
                    {isExpanded && (
                      <tr className="bg-[#0b101a] border-b border-slate-800">
                        <td colSpan={7} className="p-4 sm:p-6">
                          <div className="space-y-4 text-xs">
                            
                            {/* Top Details Header */}
                            <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-sm font-bold text-white">
                                  Incident Case #{report.id}
                                </span>
                                {isSif ? (
                                  <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30 font-semibold font-mono text-[11px] flex items-center gap-1">
                                    <AlertOctagon className="h-3 w-3" /> SIF-PRECURSOR: TRUE
                                  </span>
                                ) : (
                                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 font-semibold font-mono text-[11px] flex items-center gap-1">
                                    <CheckCircle2 className="h-3 w-3 text-emerald-400" /> SIF-PRECURSOR: FALSE
                                  </span>
                                )}
                                <span className="text-slate-400 font-mono text-[11px]">
                                  Model: {report.model || 'gemini-3.8-flash'} (Temp 0.1)
                                </span>
                              </div>
                              <span className="text-[11px] font-mono text-slate-500 truncate max-w-xs" title={report.sha256}>
                                SHA-256: {report.sha256}
                              </span>
                            </div>

                            {/* Full Narrative Box */}
                            <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3.5">
                              <div className="font-mono uppercase text-[11px] text-slate-400 font-semibold mb-1.5 flex items-center gap-1.5">
                                <FileText className="h-3.5 w-3.5 text-blue-400" /> Complete Incident Narrative
                              </div>
                              <p className="text-slate-200 text-xs font-sans leading-relaxed whitespace-pre-wrap">
                                {report.report_text}
                              </p>
                            </div>

                            {/* Model Reasoning */}
                            <div className="bg-slate-950/80 border border-amber-500/30 rounded-lg p-3.5 shadow-hazard">
                              <div className="font-mono uppercase text-[11px] text-amber-400 font-semibold mb-1.5 flex items-center gap-1.5">
                                <Cpu className="h-3.5 w-3.5 text-amber-400" /> Evaluator Reasoning (Two-Part Test)
                              </div>
                              <p className="text-amber-100/90 text-xs font-sans leading-relaxed">
                                {report.reasoning}
                              </p>
                            </div>

                            {/* Structured Precursor Fields */}
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
                              
                              {/* Activity */}
                              <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-3">
                                <div className="text-[10px] font-mono uppercase text-slate-400 font-semibold mb-1">
                                  Precursor Activity
                                </div>
                                <div className="text-white font-medium text-xs">
                                  {report.activity || 'None stated'}
                                </div>
                              </div>

                              {/* Location */}
                              <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-3">
                                <div className="text-[10px] font-mono uppercase text-slate-400 font-semibold mb-1">
                                  Operational Location
                                </div>
                                <div className="text-white font-medium text-xs">
                                  {report.location || 'None stated'}
                                </div>
                              </div>

                              {/* Barrier Failure */}
                              <div className={`rounded-lg p-3 border ${
                                report.barrier_failure && !report.barrier_failure.includes('not stated')
                                  ? 'bg-red-950/20 border-red-500/30'
                                  : 'bg-slate-900/70 border-slate-800'
                              }`}>
                                <div className="text-[10px] font-mono uppercase text-slate-400 font-semibold mb-1">
                                  Barrier Failure
                                </div>
                                <div className={`font-medium text-xs ${
                                  report.barrier_failure && !report.barrier_failure.includes('not stated')
                                    ? 'text-red-300 font-semibold'
                                    : 'text-slate-400'
                                }`}>
                                  {report.barrier_failure || 'not stated in narrative'}
                                </div>
                              </div>

                            </div>

                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>

    </div>
  );
}
