import React, { useState, useEffect } from 'react';
import { 
  Lightbulb, 
  TrendingUp, 
  TrendingDown, 
  AlertCircle, 
  CheckCircle2, 
  FileText, 
  Send, 
  Search, 
  Sparkles, 
  Target, 
  BarChart, 
  Award, 
  Flame, 
  ShieldAlert,
  Printer,
  Compass
} from 'lucide-react';
import { DatasetSessionInfo, BusinessInsightsResponse, QueryResponse } from '../types';
import { api } from '../services/api';

interface InsightsViewProps {
  activeSession: DatasetSessionInfo;
  onOpenReport: () => void;
  setToast: (toast: { type: 'success' | 'error' | 'info'; message: string } | null) => void;
}

export const InsightsView: React.FC<InsightsViewProps> = ({
  activeSession,
  onOpenReport,
  setToast
}) => {
  const [insights, setInsights] = useState<BusinessInsightsResponse | null>(null);
  const [targetCol, setTargetCol] = useState<string>('');
  const [loading, setLoading] = useState(false);

  // NLP Query Assistant State
  const [queryInput, setQueryInput] = useState('');
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [suggestionChips, setSuggestionChips] = useState<string[]>([]);

  useEffect(() => {
    loadInsights();
    loadSuggestionChips();
  }, [activeSession.session_id, targetCol]);

  const loadInsights = async () => {
    setLoading(true);
    try {
      const res = await api.getInsights(activeSession.session_id, targetCol || undefined);
      setInsights(res);
      if (!targetCol && res.target_column) {
        setTargetCol(res.target_column);
      }
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Failed to generate insights.' });
    } finally {
      setLoading(false);
    }
  };

  const loadSuggestionChips = async () => {
    try {
      const res = await api.getSuggestionChips(activeSession.session_id);
      setSuggestionChips(res.suggestions || []);
    } catch (err: any) {
      // Fallback to static suggestions
      setSuggestionChips([
        `Top 5 by ${targetCol || 'Sales'}`,
        `Average ${targetCol || 'Profit'} by ${activeSession.column_names[1] || 'Category'}`,
        `Filter ${targetCol || 'Sales'} > 500`
      ]);
    }
  };

  const handleQuerySubmit = async (queryText?: string) => {
    const q = queryText || queryInput;
    if (!q.trim()) return;
    setQueryLoading(true);
    try {
      const res = await api.queryAssistant(activeSession.session_id, q);
      setQueryResult(res);
      setToast({ type: 'success', message: 'Executed Natural Language query.' });
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Query execution failed.' });
    } finally {
      setQueryLoading(false);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      
      {/* Header & Target Metric Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-amber-400 text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Stage 5: Findings & Business Insights</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Leadership Summary & Key Factors</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Machine-learned key drivers, statistical variances, cohort performance and strategic recommendations.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 bg-slate-900 border border-slate-800 rounded-2xl px-3 py-1.5 text-xs">
            <Target className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-slate-400">Target KPI:</span>
            <select
              value={targetCol}
              onChange={(e) => setTargetCol(e.target.value)}
              className="bg-transparent text-white font-bold focus:outline-none cursor-pointer"
            >
              {activeSession.column_names.map(c => (
                <option key={c} value={c} className="bg-slate-950 text-white">{c}</option>
              ))}
            </select>
          </div>

          <button
            onClick={onOpenReport}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-2xl bg-gradient-to-r from-teal-600 to-amber-600 hover:from-teal-500 hover:to-amber-500 text-white text-xs font-bold shadow-md shadow-teal-900/40 transition-all hover:scale-[1.02]"
          >
            <Printer className="w-4 h-4" />
            <span>Create Summary Report</span>
          </button>
        </div>
      </div>

      {/* 1. Executive KPI Summary Cards */}
      {insights && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {insights.kpi_highlights.map((kpi, idx) => (
            <div key={idx} className="glass-panel rounded-2xl p-5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 truncate max-w-[160px]">
                  {kpi.name}
                </span>
                <span className="w-6 h-6 rounded-lg bg-slate-800 flex items-center justify-center text-amber-400">
                  <TrendingUp className="w-3.5 h-3.5" />
                </span>
              </div>
              <div className="text-2xl font-black text-white">{kpi.total}</div>
              <div className="text-[11px] text-slate-400 flex items-center justify-between pt-1 border-t border-slate-800">
                <span>Average: <strong className="text-slate-200">{kpi.average}</strong></span>
                <span>Peak: <strong className="text-amber-400">{kpi.max}</strong></span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 2. Key Driver Analysis (ML & Random Forest) & Cohorts */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Key Drivers */}
        <div className="lg:col-span-7 glass-panel rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Compass className="w-4 h-4 text-amber-400" />
              <h2 className="text-sm font-bold text-white">Key Factor Analysis</h2>
            </div>
            <span className="text-[11px] text-slate-400">
              Factors impacting <strong>{targetCol}</strong>
            </span>
          </div>

          <div className="space-y-4 pt-1">
            {insights?.key_drivers.map((d, i) => (
              <div key={i} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-white">{d.feature}</span>
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.2 rounded ${
                      d.impact_level === 'Critical'
                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                        : d.impact_level === 'High'
                        ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        : 'bg-teal-500/10 text-teal-400 border border-teal-500/20'
                    }`}>
                      {d.impact_level}
                    </span>
                  </div>
                  <span className="font-mono font-bold text-amber-400 text-xs">
                    {d.importance_pct}% Relative Influence
                  </span>
                </div>

                <div className="h-2 bg-slate-900 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-teal-600 via-teal-500 to-amber-400 rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(6, d.importance_pct * 1.5)}%` }}
                  />
                </div>

                <p className="text-[11px] text-slate-400">{d.summary}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Group-wise Results Breakdown */}
        <div className="lg:col-span-5 glass-panel rounded-2xl p-6 space-y-4 flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Award className="w-4 h-4 text-purple-400" />
              <h2 className="text-sm font-bold text-white">Group-wise Results</h2>
            </div>
            <span className="text-[11px] text-slate-400">Top vs Bottom</span>
          </div>

          <div className="space-y-4 my-2">
            {insights?.cohort_insights.map((cohort, idx) => (
              <div key={idx} className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  By {cohort.category_dimension}
                </span>

                <div className="space-y-1.5 text-xs">
                  <div className="flex items-center justify-between p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300">
                    <span className="font-bold truncate max-w-[130px]">🏆 {cohort.top_performer.name}</span>
                    <span className="font-mono font-bold">{cohort.top_performer.mean_value.toLocaleString()} avg</span>
                  </div>

                  <div className="flex items-center justify-between p-2 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300">
                    <span className="font-bold truncate max-w-[130px]">🔻 {cohort.bottom_performer.name}</span>
                    <span className="font-mono font-bold">{cohort.bottom_performer.mean_value.toLocaleString()} avg</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="text-[11px] text-slate-400 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
            Replicate top performing playbooks to uplift lagging segments.
          </div>
        </div>

      </div>

      {/* 3. Strategic C-Level Recommendations */}
      <div className="glass-panel rounded-2xl p-6 space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
          <CheckCircle2 className="w-4 h-4 text-amber-400" />
          <h2 className="text-sm font-bold text-white">Leadership Action Points</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
          {insights?.strategic_recommendations.map((rec, i) => (
            <div key={i} className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {rec.badge}
                </span>
                <h3 className="text-xs font-bold text-white mt-2 leading-snug">{rec.title}</h3>
                <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{rec.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. "Ask DataNexus AI" Natural Language Query Console */}
      <div className="glass-panel rounded-2xl p-6 space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <h2 className="text-sm font-bold text-white">Ask a Question – Plain-Language Data Helper</h2>
          </div>
          <span className="text-xs text-slate-400">Type your question in everyday words</span>
        </div>

        {/* Search Bar */}
        <form onSubmit={(e) => { e.preventDefault(); handleQuerySubmit(); }} className="relative flex items-center">
          <Search className="w-4 h-4 text-slate-400 absolute left-4" />
          <input
            type="text"
            value={queryInput}
            onChange={(e) => setQueryInput(e.target.value)}
            placeholder={`e.g. "Top 5 by ${activeSession.column_names.find(c => c.toLowerCase().includes('income') || c.toLowerCase().includes('sales')) || activeSession.column_names[1] || 'Sales'}" or "Average ${activeSession.column_names.find(c => c.toLowerCase().includes('income') || c.toLowerCase().includes('age')) || targetCol || 'Value'} by ${activeSession.column_names.find(c => c.toLowerCase().includes('department') || c.toLowerCase().includes('category')) || activeSession.column_names[0] || 'Group'}"`}
            className="w-full bg-slate-900 border border-slate-700/80 rounded-2xl pl-11 pr-24 py-3 text-xs sm:text-sm text-white focus:outline-none focus:border-teal-500 placeholder:text-slate-500 shadow-inner"
          />
          <button
            type="submit"
            disabled={queryLoading || !queryInput.trim()}
            className="absolute right-2 px-4 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs shadow transition-colors disabled:opacity-40"
          >
            {queryLoading ? 'Thinking...' : 'Ask AI'}
          </button>
        </form>

        {/* Dynamic Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-500 text-[11px]">Suggestions:</span>
          {suggestionChips.map((sq, i) => (
            <button
              key={i}
              onClick={() => {
                setQueryInput(sq);
                handleQuerySubmit(sq);
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-amber-400 hover:border-teal-500/40 text-[11px] transition-colors"
            >
              {sq}
            </button>
          ))}
        </div>

        {/* Query Result Output */}
        {queryResult && (
          <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-4 animate-in fade-in duration-300">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <span className="text-[10px] font-bold uppercase text-amber-400">Interpretation</span>
                <p className="text-xs text-slate-200 font-semibold">{queryResult.interpretation}</p>
              </div>
              <span className="text-[11px] text-slate-500">{queryResult.total_results} matching records</span>
            </div>

            {/* Explanation Sentence */}
            {queryResult.explanation && (
              <div className="p-3 rounded-lg bg-teal-500/10 border border-teal-500/20">
                <p className="text-xs text-amber-300 font-medium">{queryResult.explanation}</p>
              </div>
            )}

            {/* Friendly Fallback: Supported Types */}
            {queryResult.supported_types && queryResult.supported_types.length > 0 && (
              <div className="p-4 rounded-lg bg-slate-800/60 border border-slate-700 space-y-3">
                <h4 className="text-xs font-bold text-white">Questions you can ask:</h4>
                <ul className="space-y-1.5">
                  {queryResult.supported_types.map((t, i) => (
                    <li key={i} className="text-[11px] text-slate-300">{t}</li>
                  ))}
                </ul>
                {queryResult.examples && queryResult.examples.length > 0 && (
                  <div className="pt-2 border-t border-slate-700">
                    <span className="text-[11px] text-slate-400">Sample questions:</span>
                    <div className="flex flex-wrap gap-2 mt-1.5">
                      {queryResult.examples.map((ex, i) => (
                        <button
                          key={i}
                          onClick={() => {
                            setQueryInput(ex);
                            handleQuerySubmit(ex);
                          }}
                          className="px-2.5 py-1 rounded-lg bg-slate-900 border border-teal-500/30 text-amber-400 hover:bg-teal-500/10 text-[11px] transition-colors"
                        >
                          {ex}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Result Table */}
            {queryResult.data.length > 0 && (
              <div className="overflow-x-auto rounded-lg border border-slate-800 max-h-56">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="sticky top-0 bg-slate-950">
                    <tr className="border-b border-slate-800 text-slate-400 font-medium">
                      {queryResult.columns.map(c => (
                        <th key={c} className="px-3 py-2 text-slate-300 font-semibold">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {queryResult.data.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40 text-slate-300 font-mono text-[11px]">
                        {queryResult.columns.map(c => (
                          <td key={c} className="px-3 py-1.5 whitespace-nowrap">
                            {typeof row[c] === 'number' ? row[c].toLocaleString() : String(row[c] ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

      </div>

    </div>
  );
};
