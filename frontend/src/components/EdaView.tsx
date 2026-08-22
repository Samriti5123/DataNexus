import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Table as TableIcon, 
  Flame, 
  Layers, 
  HelpCircle, 
  Activity, 
  ArrowRight,
  TrendingUp,
  Hash,
  Calendar,
  Grid,
  Sparkles
} from 'lucide-react';
import { DatasetSessionInfo, EdaSummary, ColumnProfile, CorrelationResponse } from '../types';
import { api } from '../services/api';

interface EdaViewProps {
  activeSession: DatasetSessionInfo;
  onProceedToVisualize: () => void;
  setToast: (toast: { type: 'success' | 'error' | 'info'; message: string } | null) => void;
}

export const EdaView: React.FC<EdaViewProps> = ({
  activeSession,
  onProceedToVisualize,
  setToast
}) => {
  const [summary, setSummary] = useState<EdaSummary | null>(null);
  const [profiles, setProfiles] = useState<ColumnProfile[]>([]);
  const [correlations, setCorrelations] = useState<CorrelationResponse | null>(null);
  const [corrMethod, setCorrMethod] = useState<'pearson' | 'spearman'>('pearson');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'profiles' | 'correlations' | 'pivot'>('profiles');

  // Pivot Table Sandbox State
  const [pivotRow, setPivotRow] = useState<string>('');
  const [pivotCol, setPivotCol] = useState<string>('');
  const [pivotVal, setPivotVal] = useState<string>('');
  const [pivotAgg, setPivotAgg] = useState<string>('sum');
  const [pivotResult, setPivotResult] = useState<any>(null);
  const [pivotLoading, setPivotLoading] = useState<boolean>(false);

  useEffect(() => {
    loadEdaData();
  }, [activeSession.session_id, corrMethod]);

  const loadEdaData = async () => {
    setLoading(true);
    try {
      const [sumRes, profRes, corrRes] = await Promise.all([
        api.getEdaSummary(activeSession.session_id),
        api.getColumnProfiles(activeSession.session_id),
        api.getCorrelation(activeSession.session_id, corrMethod, 0.0)
      ]);
      setSummary(sumRes);
      setProfiles(profRes.profiles);
      setCorrelations(corrRes);

      if (profRes.profiles.length > 0) {
        const catCols = profRes.profiles.filter(p => p.semantic_type === 'categorical' || p.semantic_type === 'boolean').map(p => p.name);
        const numCols = profRes.profiles.filter(p => p.semantic_type === 'numeric').map(p => p.name);
        if (catCols.length > 0 && !pivotRow) setPivotRow(catCols[0]);
        if (catCols.length > 1 && !pivotCol) setPivotCol(catCols[1]);
        if (numCols.length > 0 && !pivotVal) setPivotVal(numCols[0]);
      }
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Failed to load EDA data.' });
    } finally {
      setLoading(false);
    }
  };

  const handleRunPivot = async () => {
    if (!pivotRow) return;
    setPivotLoading(true);
    try {
      const res = await api.computePivot(activeSession.session_id, {
        rows: [pivotRow],
        columns: pivotCol ? [pivotCol] : undefined,
        values: pivotVal || undefined,
        aggfunc: pivotAgg
      });
      setPivotResult(res);
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Pivot computation failed.' });
    } finally {
      setPivotLoading(false);
    }
  };

  // Run pivot automatically once dimensions are ready
  useEffect(() => {
    if (pivotRow && activeTab === 'pivot' && !pivotResult) {
      handleRunPivot();
    }
  }, [pivotRow, activeTab]);

  return (
    <div className="space-y-8 pb-16">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-2">
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Stage 3: Exploratory Data Analysis (EDA)</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Statistical & Structural Profiling</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Deep dive into distributions, skewness, Pearson/Spearman correlation matrices, and dynamic multidimensional pivots.
          </p>
        </div>

        <button
          onClick={onProceedToVisualize}
          className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold shadow-md shadow-emerald-900/30 transition-all hover:scale-[1.02]"
        >
          <span>Launch Chart Studio</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Overview Stat Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          <div className="glass-panel rounded-xl p-4">
            <span className="text-[11px] text-slate-400 font-medium">Total Rows</span>
            <div className="text-xl font-bold text-white mt-1">{summary.total_rows.toLocaleString()}</div>
          </div>
          <div className="glass-panel rounded-xl p-4">
            <span className="text-[11px] text-slate-400 font-medium">Attributes / Cols</span>
            <div className="text-xl font-bold text-white mt-1">{summary.total_columns}</div>
          </div>
          <div className="glass-panel rounded-xl p-4">
            <span className="text-[11px] text-slate-400 font-medium">Memory Usage</span>
            <div className="text-xl font-bold text-emerald-400 mt-1">{summary.memory_usage_mb} MB</div>
          </div>
          <div className="glass-panel rounded-xl p-4">
            <span className="text-[11px] text-slate-400 font-medium">Missing Cells</span>
            <div className="text-xl font-bold text-white mt-1">{summary.missing_cells} <span className="text-xs text-slate-400 font-normal">({summary.missing_percentage}%)</span></div>
          </div>
          <div className="glass-panel rounded-xl p-4">
            <span className="text-[11px] text-slate-400 font-medium">Numeric Columns</span>
            <div className="text-xl font-bold text-cyan-400 mt-1">{summary.type_counts.numeric}</div>
          </div>
          <div className="glass-panel rounded-xl p-4">
            <span className="text-[11px] text-slate-400 font-medium">Categorical Columns</span>
            <div className="text-xl font-bold text-purple-400 mt-1">{summary.type_counts.categorical}</div>
          </div>
        </div>
      )}

      {/* Sub-Navigation Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
        <button
          onClick={() => setActiveTab('profiles')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === 'profiles'
              ? 'bg-emerald-600 text-white shadow'
              : 'bg-slate-900 text-slate-400 hover:text-white'
          }`}
        >
          <Activity className="w-4 h-4" />
          <span>Column Profiles & Histograms ({profiles.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('correlations')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === 'correlations'
              ? 'bg-emerald-600 text-white shadow'
              : 'bg-slate-900 text-slate-400 hover:text-white'
          }`}
        >
          <Flame className="w-4 h-4" />
          <span>Correlation Matrix & Heatmap</span>
        </button>

        <button
          onClick={() => setActiveTab('pivot')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors ${
            activeTab === 'pivot'
              ? 'bg-emerald-600 text-white shadow'
              : 'bg-slate-900 text-slate-400 hover:text-white'
          }`}
        >
          <Grid className="w-4 h-4" />
          <span>Dynamic Pivot & GroupBy Sandbox</span>
        </button>
      </div>

      {/* TAB 1: Column Profiles */}
      {activeTab === 'profiles' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {profiles.map((p) => {
            const isNumeric = p.semantic_type === 'numeric' && p.stats;
            const isCategorical = (p.semantic_type === 'categorical' || p.semantic_type === 'boolean') && p.top_values;
            const maxHistCount = isNumeric ? Math.max(...p.stats!.histogram.map(h => h.count), 1) : 1;

            return (
              <div key={p.name} className="glass-panel rounded-2xl p-5 space-y-4 flex flex-col justify-between">
                
                {/* Column Header */}
                <div>
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white truncate max-w-[190px]" title={p.name}>
                      {p.name}
                    </h3>
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                      p.semantic_type === 'numeric'
                        ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20'
                        : p.semantic_type === 'categorical'
                        ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20'
                        : p.semantic_type === 'datetime'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : 'bg-slate-800 text-slate-400'
                    }`}>
                      {p.semantic_type}
                    </span>
                  </div>

                  <div className="flex items-center space-x-3 text-[11px] text-slate-400 mt-1">
                    <span>Unique: <strong>{p.unique_count.toLocaleString()}</strong> ({p.unique_percentage}%)</span>
                    <span>Missing: <strong className={p.missing_count > 0 ? 'text-rose-400' : 'text-slate-400'}>{p.missing_count}</strong></span>
                  </div>
                </div>

                {/* Numeric Profiling & Mini Histogram */}
                {isNumeric && p.stats && (
                  <div className="space-y-3 pt-2 border-t border-slate-800/80">
                    <div className="grid grid-cols-4 gap-1.5 text-center text-[10px]">
                      <div className="bg-slate-900/80 p-1.5 rounded">
                        <div className="text-slate-500">Min</div>
                        <div className="text-white font-bold">{p.stats.min}</div>
                      </div>
                      <div className="bg-slate-900/80 p-1.5 rounded">
                        <div className="text-slate-500">Mean</div>
                        <div className="text-white font-bold">{p.stats.mean}</div>
                      </div>
                      <div className="bg-slate-900/80 p-1.5 rounded">
                        <div className="text-slate-500">Median</div>
                        <div className="text-white font-bold">{p.stats.median}</div>
                      </div>
                      <div className="bg-slate-900/80 p-1.5 rounded">
                        <div className="text-slate-500">Max</div>
                        <div className="text-white font-bold">{p.stats.max}</div>
                      </div>
                    </div>

                    {/* Mini Histogram Bars */}
                    <div className="space-y-1">
                      <span className="text-[10px] text-slate-400 font-medium">Distribution Histogram</span>
                      <div className="h-16 flex items-end space-x-1 pt-2 bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                        {p.stats.histogram.map((bin, i) => {
                          const heightPct = Math.round((bin.count / maxHistCount) * 100);
                          return (
                            <div
                              key={i}
                              className="flex-1 bg-gradient-to-t from-emerald-600 to-teal-400 hover:from-emerald-400 hover:to-teal-300 rounded-t transition-all cursor-pointer relative group"
                              style={{ height: `${Math.max(4, heightPct)}%` }}
                            >
                              <div className="opacity-0 group-hover:opacity-100 absolute bottom-full mb-1 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[9px] px-1.5 py-0.5 rounded shadow whitespace-nowrap z-20 pointer-events-none border border-slate-700">
                                {bin.label}: {bin.count}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}

                {/* Categorical Profiling (Top Values Bar) */}
                {isCategorical && p.top_values && (
                  <div className="space-y-2 pt-2 border-t border-slate-800/80">
                    <span className="text-[10px] text-slate-400 font-medium">Top Frequency Categories</span>
                    <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                      {p.top_values.slice(0, 5).map((val, idx) => (
                        <div key={idx} className="space-y-0.5 text-[11px]">
                          <div className="flex justify-between text-slate-300">
                            <span className="truncate max-w-[140px]">{val.value}</span>
                            <span className="text-slate-400 font-mono text-[10px]">{val.count} ({val.percentage}%)</span>
                          </div>
                          <div className="h-1.5 bg-slate-900 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-purple-500 to-indigo-400 rounded-full"
                              style={{ width: `${val.percentage}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Datetime Profiling */}
                {p.semantic_type === 'datetime' && p.date_stats && (
                  <div className="space-y-2 pt-2 border-t border-slate-800/80 text-xs">
                    <div className="flex justify-between text-slate-300">
                      <span className="text-slate-500">Earliest Date</span>
                      <span className="font-semibold text-white">{p.date_stats.min_date.split('T')[0]}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span className="text-slate-500">Latest Date</span>
                      <span className="font-semibold text-white">{p.date_stats.max_date.split('T')[0]}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span className="text-slate-500">Total Timespan</span>
                      <span className="font-semibold text-amber-400">{p.date_stats.timespan_days} days</span>
                    </div>
                  </div>
                )}

              </div>
            );
          })}
        </div>
      )}

      {/* TAB 2: Correlation Matrix & Heatmap */}
      {activeTab === 'correlations' && correlations && (
        <div className="space-y-6">
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-xs font-semibold text-slate-300">Method:</span>
              <button
                onClick={() => setCorrMethod('pearson')}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
                  corrMethod === 'pearson' ? 'bg-emerald-600 text-white' : 'bg-slate-900 text-slate-400'
                }`}
              >
                Pearson (Linear)
              </button>
              <button
                onClick={() => setCorrMethod('spearman')}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-colors ${
                  corrMethod === 'spearman' ? 'bg-emerald-600 text-white' : 'bg-slate-900 text-slate-400'
                }`}
              >
                Spearman (Rank)
              </button>
            </div>
            <span className="text-xs text-slate-400">
              Evaluates relationship strength between all {correlations.columns.length} numeric variables
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Heatmap Grid */}
            <div className="lg:col-span-8 glass-panel rounded-2xl p-5 overflow-x-auto">
              <table className="w-full text-center text-xs border-collapse">
                <thead>
                  <tr>
                    <th className="p-2 text-left text-slate-400 font-semibold"></th>
                    {correlations.columns.map((c) => (
                      <th key={c} className="p-2 text-slate-200 font-semibold max-w-[100px] truncate" title={c}>
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {correlations.matrix.map((row) => (
                    <tr key={row.column} className="border-t border-slate-800/60">
                      <td className="p-2 text-left text-slate-300 font-semibold max-w-[120px] truncate" title={row.column}>
                        {row.column}
                      </td>
                      {correlations.columns.map((col) => {
                        const val = row[col] !== undefined ? row[col] : 0;
                        const isPos = val > 0;
                        const opacity = Math.min(1, Math.max(0.1, Math.abs(val)));
                        const bgStyle = val === 1 ? 'rgba(16, 185, 129, 0.4)' : isPos ? `rgba(16, 185, 129, ${opacity * 0.7})` : `rgba(239, 68, 68, ${opacity * 0.7})`;

                        return (
                          <td
                            key={col}
                            style={{ backgroundColor: bgStyle }}
                            className="p-2.5 font-mono text-[11px] text-white font-medium rounded transition-all hover:scale-105"
                          >
                            {val.toFixed(2)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Top Correlation Insights Ranking */}
            <div className="lg:col-span-4 glass-panel rounded-2xl p-5 space-y-3">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Flame className="w-4 h-4 text-amber-400" />
                <span>Top Correlated Pairs</span>
              </h3>

              <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                {correlations.top_correlations.slice(0, 8).map((pair, i) => (
                  <div key={i} className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white truncate max-w-[180px]">
                        {pair.col1} ↔ {pair.col2}
                      </span>
                      <span className={`font-mono font-bold ${
                        pair.correlation > 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}>
                        {pair.correlation > 0 ? '+' : ''}{pair.correlation}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center justify-between">
                      <span>{pair.relationship}</span>
                      <span className="text-slate-500">Rank #{i + 1}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>

        </div>
      )}

      {/* TAB 3: Dynamic Pivot Table Sandbox */}
      {activeTab === 'pivot' && (
        <div className="space-y-6">
          
          {/* Controls Bar */}
          <div className="glass-panel rounded-2xl p-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 items-end">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Row Dimension</label>
                <select
                  value={pivotRow}
                  onChange={(e) => setPivotRow(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                >
                  {profiles.map(p => (
                    <option key={p.name} value={p.name}>{p.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Column Dimension (Optional)</label>
                <select
                  value={pivotCol}
                  onChange={(e) => setPivotCol(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                >
                  <option value="">None (Standard GroupBy)</option>
                  {profiles.filter(p => p.name !== pivotRow).map(p => (
                    <option key={p.name} value={p.name}>{p.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Metric Value</label>
                <select
                  value={pivotVal}
                  onChange={(e) => setPivotVal(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                >
                  <option value="">Record Count</option>
                  {profiles.filter(p => p.semantic_type === 'numeric').map(p => (
                    <option key={p.name} value={p.name}>{p.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Aggregation</label>
                <select
                  value={pivotAgg}
                  onChange={(e) => setPivotAgg(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
                >
                  <option value="sum">Sum</option>
                  <option value="mean">Average / Mean</option>
                  <option value="median">Median</option>
                  <option value="min">Min</option>
                  <option value="max">Max</option>
                  <option value="count">Count</option>
                </select>
              </div>

              <button
                onClick={handleRunPivot}
                disabled={pivotLoading}
                className="py-2 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow transition-colors"
              >
                {pivotLoading ? 'Calculating...' : 'Compute Pivot Table'}
              </button>
            </div>
          </div>

          {/* Pivot Table Result Preview */}
          {pivotResult && (
            <div className="glass-panel rounded-2xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white">
                  Aggregated Output ({pivotResult.data.length} rows)
                </h3>
                <span className="text-xs text-slate-400">
                  {pivotAgg.toUpperCase()} of {pivotVal || 'Count'} by {pivotRow} {pivotCol ? `& ${pivotCol}` : ''}
                </span>
              </div>

              <div className="overflow-x-auto rounded-xl border border-slate-800 max-h-[400px]">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="sticky top-0 bg-slate-950 z-10">
                    <tr className="border-b border-slate-800 text-slate-400 font-medium">
                      {pivotResult.columns.map((col: string) => (
                        <th key={col} className="px-4 py-2.5 whitespace-nowrap text-slate-200 font-semibold">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {pivotResult.data.map((row: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-800/40 text-slate-300">
                        {pivotResult.columns.map((col: string) => (
                          <td key={col} className="px-4 py-2 whitespace-nowrap font-mono text-[11px]">
                            {typeof row[col] === 'number' ? row[col].toLocaleString() : String(row[col])}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

        </div>
      )}

    </div>
  );
};
