import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  ShieldAlert, 
  ShieldCheck, 
  Undo2, 
  Redo2, 
  RotateCcw, 
  Code2, 
  Search, 
  ChevronLeft, 
  ChevronRight, 
  ArrowUpDown, 
  Sliders, 
  Filter, 
  PlusCircle, 
  Trash2, 
  Scissors, 
  Type, 
  Check, 
  AlertTriangle,
  FileSpreadsheet,
  Layers,
  ArrowRight
} from 'lucide-react';
import { DatasetSessionInfo, DataPreviewResponse, HealthAuditResponse } from '../types';
import { api } from '../services/api';

interface CleanViewProps {
  activeSession: DatasetSessionInfo;
  onSessionUpdated: (session: DatasetSessionInfo) => void;
  onOpenRecipeModal: () => void;
  onProceedToEda: () => void;
  setToast: (toast: { type: 'success' | 'error' | 'info'; message: string } | null) => void;
}

export const CleanView: React.FC<CleanViewProps> = ({
  activeSession,
  onSessionUpdated,
  onOpenRecipeModal,
  onProceedToEda,
  setToast
}) => {
  const [audit, setAudit] = useState<HealthAuditResponse | null>(null);
  const [preview, setPreview] = useState<DataPreviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTool, setActiveTool] = useState<string>('missing');

  // Table pagination, sort & search
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);
  const [sortBy, setSortBy] = useState<string | undefined>(undefined);
  const [sortAsc, setSortAsc] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  // Tool Form States
  // 1. Missing
  const [missingCols, setMissingCols] = useState<string[]>([]);
  const [missingStrategy, setMissingStrategy] = useState('mean');
  const [missingCustomVal, setMissingCustomVal] = useState('');

  // 2. Outliers
  const [outlierCols, setOutlierCols] = useState<string[]>([]);
  const [outlierMethod, setOutlierMethod] = useState('iqr');
  const [outlierAction, setOutlierAction] = useState('clip');
  const [outlierThreshold, setOutlierThreshold] = useState(1.5);

  // 3. Deduplicate
  const [dedupSubset, setDedupSubset] = useState<string[]>([]);
  const [dedupKeep, setDedupKeep] = useState('first');

  // 4. Cast Types
  const [castCol, setCastCol] = useState('');
  const [castType, setCastType] = useState('float');

  // 5. Text Normalization
  const [normCols, setNormCols] = useState<string[]>([]);
  const [normOp, setNormOp] = useState('trim');
  const [normSearch, setNormSearch] = useState('');
  const [normReplace, setNormReplace] = useState('');

  // 6. Calculated Column
  const [calcColName, setCalcColName] = useState('');
  const [calcType, setCalcType] = useState('arithmetic');
  const [calcColA, setCalcColA] = useState('');
  const [calcOp, setCalcOp] = useState('+');
  const [calcColBOrVal, setCalcColBOrVal] = useState('');

  // 7. Filter Builder
  const [filterConditions, setFilterConditions] = useState<{ column: string; operator: string; value: string }[]>([
    { column: '', operator: '==', value: '' }
  ]);

  // Load audit & preview
  const refreshData = async () => {
    setLoading(true);
    try {
      const [auditRes, previewRes] = await Promise.all([
        api.getAudit(activeSession.session_id),
        api.getPreview(activeSession.session_id, page, pageSize, sortBy, sortAsc, searchTerm)
      ]);
      setAudit(auditRes);
      setPreview(previewRes);

      // Auto set initial column selection
      if (previewRes.columns.length > 0) {
        if (!calcColA) setCalcColA(previewRes.columns[0]);
        if (!castCol) setCastCol(previewRes.columns[0]);
        if (filterConditions[0].column === '') {
          setFilterConditions([{ column: previewRes.columns[0], operator: '==', value: '' }]);
        }

        const numCols = Object.entries(previewRes.column_types).filter(([_, t]) => t === 'numeric').map(([c]) => c);
        if (numCols.length > 0 && outlierCols.length === 0) {
          const detected = auditRes.issues.filter(i => i.type === 'outlier' && i.column).map(i => i.column!) || [];
          setOutlierCols(detected.length > 0 ? detected : numCols);
        }
      }
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Failed to fetch dataset audit.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, [activeSession.session_id, page, pageSize, sortBy, sortAsc]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    refreshData();
  };

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortAsc(!sortAsc);
    } else {
      setSortBy(column);
      setSortAsc(true);
    }
  };

  // Cleaning Actions Handlers
  const handleApplyMissing = async () => {
    try {
      setLoading(true);
      const res = await api.cleanMissing(activeSession.session_id, {
        columns: missingCols,
        strategy: missingStrategy,
        custom_value: missingCustomVal || undefined
      });
      setToast({ type: 'success', message: res.action });
      onSessionUpdated({ ...activeSession, rows: res.total_rows, columns: res.total_columns });
      await refreshData();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyOutliers = async () => {
    try {
      setLoading(true);
      const targetCols = outlierCols.length > 0 ? outlierCols : numericColumns;
      const res = await api.cleanOutliers(activeSession.session_id, {
        columns: targetCols,
        method: outlierMethod,
        action: outlierAction,
        threshold: outlierThreshold
      });
      setToast({ type: 'success', message: res.action });
      onSessionUpdated({ ...activeSession, rows: res.total_rows, columns: res.total_columns });
      await refreshData();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyDeduplicate = async () => {
    try {
      setLoading(true);
      const res = await api.cleanDeduplicate(activeSession.session_id, {
        subset: dedupSubset.length > 0 ? dedupSubset : undefined,
        keep: dedupKeep
      });
      setToast({ type: 'success', message: res.action });
      onSessionUpdated({ ...activeSession, rows: res.total_rows, columns: res.total_columns });
      await refreshData();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyCast = async () => {
    if (!castCol) return;
    try {
      setLoading(true);
      const res = await api.cleanCast(activeSession.session_id, { [castCol]: castType });
      setToast({ type: 'success', message: res.action });
      onSessionUpdated({ ...activeSession, rows: res.total_rows, columns: res.total_columns });
      await refreshData();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyNormalize = async () => {
    try {
      setLoading(true);
      const res = await api.cleanNormalize(activeSession.session_id, {
        columns: normCols,
        operation: normOp,
        search_term: normSearch || undefined,
        replace_term: normReplace || undefined
      });
      setToast({ type: 'success', message: res.action });
      onSessionUpdated({ ...activeSession, rows: res.total_rows, columns: res.total_columns });
      await refreshData();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyCalculatedCol = async () => {
    if (!calcColName || !calcColA) return;
    try {
      setLoading(true);
      const res = await api.cleanCalcColumn(activeSession.session_id, {
        new_col_name: calcColName,
        calc_type: calcType,
        col_a: calcColA,
        operator: calcOp,
        col_b_or_val: calcColBOrVal
      });
      setToast({ type: 'success', message: res.action });
      onSessionUpdated({ ...activeSession, rows: res.total_rows, columns: res.total_columns });
      setCalcColName('');
      await refreshData();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleApplyFilter = async () => {
    const validConds = filterConditions.filter(c => c.column && c.value !== '');
    if (validConds.length === 0) return;
    try {
      setLoading(true);
      const res = await api.cleanFilter(activeSession.session_id, {
        conditions: validConds,
        match_all: true
      });
      setToast({ type: 'success', message: res.action });
      onSessionUpdated({ ...activeSession, rows: res.total_rows, columns: res.total_columns });
      await refreshData();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleUndo = async () => {
    try {
      setLoading(true);
      const res = await api.cleanUndo(activeSession.session_id);
      setToast({ type: 'info', message: res.message });
      onSessionUpdated({ ...activeSession, rows: res.total_rows, columns: res.total_columns });
      await refreshData();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleRedo = async () => {
    try {
      setLoading(true);
      const res = await api.cleanRedo(activeSession.session_id);
      setToast({ type: 'info', message: res.message });
      onSessionUpdated({ ...activeSession, rows: res.total_rows, columns: res.total_columns });
      await refreshData();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Reset dataset back to original raw uploaded state?')) return;
    try {
      setLoading(true);
      const res = await api.cleanReset(activeSession.session_id);
      setToast({ type: 'info', message: res.message });
      onSessionUpdated({ ...activeSession, rows: res.total_rows, columns: res.total_columns });
      await refreshData();
    } catch (err: any) {
      setToast({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const numericColumns = preview ? Object.entries(preview.column_types).filter(([_, t]) => t === 'numeric').map(([c]) => c) : [];

  return (
    <div className="space-y-8 pb-16">
      
      {/* Header & Step Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-amber-400 text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Stage 2: Check Health & Prepare the Data</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Data Preparation Workbench</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Resolve missing values, clip extreme outliers, convert data types, and prepare your data for deep analysis.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleUndo}
            disabled={!preview?.can_undo}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Undo last step"
          >
            <Undo2 className="w-3.5 h-3.5" />
            <span>Undo</span>
          </button>

          <button
            onClick={handleRedo}
            disabled={!preview?.can_redo}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            title="Redo step"
          >
            <Redo2 className="w-3.5 h-3.5" />
            <span>Redo</span>
          </button>

          <button
            onClick={handleReset}
            className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-rose-400 transition-colors"
            title="Reset to raw dataset"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <button
            onClick={onOpenRecipeModal}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#10262C] border border-teal-500/30 text-amber-400 text-xs font-semibold hover:bg-teal-500/10 transition-colors"
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Download Python Script</span>
          </button>

          <button
            onClick={onProceedToEda}
            className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-gradient-to-r from-teal-600 to-amber-600 hover:from-teal-500 hover:to-amber-500 text-white text-xs font-bold shadow-md shadow-teal-900/40 transition-all hover:scale-[1.02]"
          >
            <span>Proceed to EDA</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Top Section: Health Score & Audit Banner */}
      {audit && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          
          {/* Health Score Gauge */}
          <div className="glass-panel rounded-2xl p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Data Health Score</span>
              {audit.overall_score >= 85 ? (
                <ShieldCheck className="w-5 h-5 text-amber-400" />
              ) : (
                <ShieldAlert className="w-5 h-5 text-amber-400" />
              )}
            </div>

            <div className="my-4 text-center">
              <div className={`text-4xl sm:text-5xl font-black ${
                audit.overall_score >= 85 ? 'text-emerald-400' : audit.overall_score >= 60 ? 'text-amber-400' : 'text-rose-400'
              }`}>
                {audit.overall_score}%
              </div>
              <p className="text-xs text-slate-400 mt-1 font-medium">
                {audit.overall_score >= 85 ? 'Excellent Quality' : audit.overall_score >= 60 ? 'Moderate Health • Needs Prep' : 'Low Quality • Needs Cleaning'}
              </p>
            </div>

            <div className="space-y-1.5 text-[11px] text-slate-400">
              <div className="flex justify-between">
                <span>Completeness</span>
                <span className="text-slate-200 font-semibold">{audit.completeness_score}%</span>
              </div>
              <div className="flex justify-between">
                <span>Uniqueness</span>
                <span className="text-slate-200 font-semibold">{audit.uniqueness_score}%</span>
              </div>
              <div className="flex justify-between">
                <span>Consistency</span>
                <span className="text-slate-200 font-semibold">{audit.consistency_score}%</span>
              </div>
            </div>
          </div>

          {/* Issue Summary Cards */}
          <div className="lg:col-span-3 glass-panel rounded-2xl p-5 flex flex-col justify-between">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-bold uppercase tracking-wider text-white">Data Issues Spotted</span>
              </div>
              <span className="text-xs text-slate-400">
                {audit.issues.length} {audit.issues.length === 1 ? 'alert' : 'alerts'} detected
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 my-3 max-h-[140px] overflow-y-auto pr-1">
              {audit.issues.length === 0 ? (
                <div className="col-span-2 flex items-center space-x-2 text-amber-400 text-xs py-4">
                  <Check className="w-4 h-4" />
                  <span>No problems found. The data is complete and consistent.</span>
                </div>
              ) : (
                audit.issues.map((issue, idx) => (
                  <div key={idx} className="flex items-start space-x-2 p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
                    <span className={`w-2 h-2 rounded-full mt-1 shrink-0 ${
                      issue.severity === 'high' ? 'bg-rose-400' : issue.severity === 'medium' ? 'bg-amber-400' : 'bg-teal-400'
                    }`} />
                    <span className="text-slate-300 leading-snug">{issue.message}</span>
                  </div>
                ))
              )}
            </div>

            <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-900/60 px-3 py-2 rounded-lg border border-slate-800/80">
              <span className="font-semibold text-amber-400">Tip:</span>
              <span>Use the Prep Toolkit below to apply one-click transformations.</span>
            </div>
          </div>

        </div>
      )}

      {/* Main Workspace: Prep Toolkit (Left) + Interactive Data Table (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Prep Toolkit Controls */}
        <div className="lg:col-span-4 space-y-4">
          
          <div className="glass-panel rounded-2xl p-5 space-y-4">
            <h2 className="text-sm font-bold text-white flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-amber-400" />
              <span>Prep Toolkit</span>
            </h2>

            {/* Tool Selector Tabs */}
            <div className="grid grid-cols-3 gap-1.5 p-1 bg-slate-900 rounded-2xl border border-slate-800 text-[11px] font-medium">
              {[
                { id: 'missing', label: 'Missing' },
                { id: 'outliers', label: 'Outliers' },
                { id: 'dedup', label: 'Dedup' },
                { id: 'cast', label: 'Data Type' },
                { id: 'normalize', label: 'Text/Regex' },
                { id: 'calc', label: 'Calc Col' },
                { id: 'filter', label: 'Filter Rows' }
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => setActiveTool(t.id)}
                  className={`py-1.5 px-2 rounded-lg transition-colors ${
                    activeTool === t.id
                      ? 'bg-teal-600 text-white font-bold shadow-md shadow-teal-900/30'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Active Tool Form Panel */}
            <div className="pt-2">
              
              {/* 1. Missing Values Tool */}
              {activeTool === 'missing' && (
                <div className="space-y-3 text-xs">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="block text-slate-300 font-medium">Target Columns</label>
                      <button
                        type="button"
                        onClick={() => {
                          if (missingCols.length === (preview?.columns.length || 0)) {
                            setMissingCols([]);
                          } else {
                            setMissingCols([...(preview?.columns || [])]);
                          }
                        }}
                        className="text-[10px] text-amber-400 hover:text-amber-300 font-semibold"
                      >
                        {missingCols.length === (preview?.columns.length || 0) ? 'Deselect All' : 'Select All'}
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1.5 p-2 bg-slate-900 border border-slate-800 rounded-lg max-h-32 overflow-y-auto">
                      {preview?.columns.map(c => {
                        const isSelected = missingCols.includes(c);
                        return (
                          <button
                            key={c}
                            type="button"
                            onClick={() => {
                              if (isSelected) {
                                setMissingCols(missingCols.filter(x => x !== c));
                              } else {
                                setMissingCols([...missingCols, c]);
                              }
                            }}
                            className={`px-2 py-1 rounded-md text-[11px] font-medium transition-all flex items-center space-x-1 ${
                              isSelected
                                ? 'bg-teal-500/20 text-amber-300 border border-teal-500/40 shadow-sm'
                                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:border-slate-700'
                            }`}
                          >
                            <span>{c}</span>
                            {isSelected && <Check className="w-3 h-3 text-amber-400" />}
                          </button>
                        );
                      })}
                    </div>
                    <p className="text-[10px] text-slate-400">
                      {missingCols.length === 0 ? '⚡ Targets all columns with missing values' : `Selected ${missingCols.length} column(s)`}
                    </p>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Strategy</label>
                    <select
                      value={missingStrategy}
                      onChange={(e) => setMissingStrategy(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200 focus:outline-none focus:border-teal-500"
                    >
                      <option value="mean">Impute with Mean (Numeric)</option>
                      <option value="median">Impute with Median (Numeric)</option>
                      <option value="mode">Impute with Mode (Most Frequent)</option>
                      <option value="ffill">Forward Fill (ffill)</option>
                      <option value="bfill">Backward Fill (bfill)</option>
                      <option value="constant">Fill with Constant Value</option>
                      <option value="drop_rows">Drop Rows with Missing Values</option>
                      <option value="drop_cols">Drop Selected Columns</option>
                    </select>
                  </div>

                  {missingStrategy === 'constant' && (
                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Constant Value</label>
                      <input
                        type="text"
                        value={missingCustomVal}
                        onChange={(e) => setMissingCustomVal(e.target.value)}
                        placeholder="e.g. Unknown or 0"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                      />
                    </div>
                  )}

                  <button
                    onClick={handleApplyMissing}
                    disabled={loading}
                    className="w-full py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs shadow transition-colors"
                  >
                    {loading ? 'Processing...' : 'Apply Missing Value Fix'}
                  </button>
                </div>
              )}

              {/* 2. Outliers Tool */}
              {activeTool === 'outliers' && (
                <div className="space-y-3 text-xs">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="block text-slate-300 font-medium">Number Columns</label>
                      <button
                        type="button"
                        onClick={() => {
                          if (outlierCols.length === numericColumns.length) {
                            setOutlierCols([]);
                          } else {
                            setOutlierCols([...numericColumns]);
                          }
                        }}
                        className="text-[10px] text-amber-400 hover:text-amber-300 font-semibold"
                      >
                        {outlierCols.length === numericColumns.length ? 'Deselect All' : 'Select All'}
                      </button>
                    </div>
                    
                    <div className="flex flex-wrap gap-1.5 p-2 bg-slate-900 border border-slate-800 rounded-lg max-h-32 overflow-y-auto">
                      {numericColumns.length === 0 ? (
                        <span className="text-[11px] text-slate-500 italic p-1">No numeric columns detected in dataset</span>
                      ) : (
                        numericColumns.map(c => {
                          const isSelected = outlierCols.includes(c);
                          return (
                            <button
                              key={c}
                              type="button"
                              onClick={() => {
                                if (isSelected) {
                                  setOutlierCols(outlierCols.filter(x => x !== c));
                                } else {
                                  setOutlierCols([...outlierCols, c]);
                                }
                              }}
                              className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-all flex items-center space-x-1 ${
                                isSelected
                                  ? 'bg-teal-500/20 text-amber-300 border border-teal-500/40 shadow-sm'
                                  : 'bg-slate-950 text-slate-400 border border-slate-800 hover:border-slate-700 hover:text-slate-200'
                              }`}
                            >
                              <span>{c}</span>
                              {isSelected && <Check className="w-3 h-3 text-amber-400" />}
                            </button>
                          );
                        })
                      )}
                    </div>
                    <p className="text-[10px] text-slate-400">
                      {outlierCols.length === 0 ? '⚡ All numeric columns will be treated' : `Selected ${outlierCols.length} of ${numericColumns.length} column(s)`}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Method</label>
                      <select
                        value={outlierMethod}
                        onChange={(e) => setOutlierMethod(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                      >
                        <option value="iqr">IQR (1.5x / 3x)</option>
                        <option value="zscore">Z-Score (Standard Dev)</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Action</label>
                      <select
                        value={outlierAction}
                        onChange={(e) => setOutlierAction(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                      >
                        <option value="clip">Clip / Winsorize (Safe)</option>
                        <option value="remove">Remove Rows (Drop)</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Threshold ({outlierThreshold}x)</label>
                    <input
                      type="range"
                      min="1.0"
                      max="3.5"
                      step="0.5"
                      value={outlierThreshold}
                      onChange={(e) => setOutlierThreshold(parseFloat(e.target.value))}
                      className="w-full accent-teal-500"
                    />
                  </div>

                  <button
                    onClick={handleApplyOutliers}
                    disabled={loading || numericColumns.length === 0}
                    className="w-full py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs shadow transition-colors disabled:opacity-50"
                  >
                    {loading ? 'Processing...' : `Apply Outlier Treatment (${outlierCols.length > 0 ? outlierCols.length + ' cols' : 'All Numeric'})`}
                  </button>
                </div>
              )}

              {/* 3. Deduplication Tool */}
              {activeTool === 'dedup' && (
                <div className="space-y-3 text-xs">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="block text-slate-300 font-medium">Match Columns (Subset)</label>
                      <button
                        type="button"
                        onClick={() => {
                          if (dedupSubset.length === (preview?.columns.length || 0)) {
                            setDedupSubset([]);
                          } else {
                            setDedupSubset([...(preview?.columns || [])]);
                          }
                        }}
                        className="text-[10px] text-amber-400 hover:text-amber-300 font-semibold"
                      >
                        {dedupSubset.length === (preview?.columns.length || 0) ? 'Deselect All' : 'Select All'}
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1.5 p-2 bg-slate-900 border border-slate-800 rounded-lg max-h-32 overflow-y-auto">
                      {preview?.columns.map(c => {
                        const isSelected = dedupSubset.includes(c);
                        return (
                          <button
                            key={c}
                            type="button"
                            onClick={() => {
                              if (isSelected) {
                                setDedupSubset(dedupSubset.filter(x => x !== c));
                              } else {
                                setDedupSubset([...dedupSubset, c]);
                              }
                            }}
                            className={`px-2 py-1 rounded-md text-[11px] font-medium transition-all flex items-center space-x-1 ${
                              isSelected
                                ? 'bg-teal-500/20 text-amber-300 border border-teal-500/40'
                                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:border-slate-700'
                            }`}
                          >
                            <span>{c}</span>
                            {isSelected && <Check className="w-3 h-3 text-amber-400" />}
                          </button>
                        );
                      })}
                    </div>
                    <p className="text-[10px] text-slate-400">
                      {dedupSubset.length === 0 ? '⚡ Match across exact entire row' : `Matching on ${dedupSubset.length} column(s)`}
                    </p>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Keep Record</label>
                    <select
                      value={dedupKeep}
                      onChange={(e) => setDedupKeep(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                    >
                      <option value="first">Keep First Occurrence</option>
                      <option value="last">Keep Last Occurrence</option>
                    </select>
                  </div>

                  <button
                    onClick={handleApplyDeduplicate}
                    disabled={loading}
                    className="w-full py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs shadow transition-colors"
                  >
                    {loading ? 'Processing...' : 'Remove Duplicate Rows'}
                  </button>
                </div>
              )}

              {/* 4. Type Casting Tool */}
              {activeTool === 'cast' && (
                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Target Column</label>
                    <select
                      value={castCol}
                      onChange={(e) => setCastCol(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                    >
                      {preview?.columns.map(c => (
                        <option key={c} value={c}>{c} ({preview.column_types[c]})</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Convert Type To</label>
                    <select
                      value={castType}
                      onChange={(e) => setCastType(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                    >
                      <option value="float">Float / Decimal Numeric</option>
                      <option value="integer">Integer Whole Number</option>
                      <option value="datetime">Datetime (YYYY-MM-DD)</option>
                      <option value="category">Categorical</option>
                      <option value="boolean">Boolean (True/False)</option>
                      <option value="string">Text / String</option>
                    </select>
                  </div>

                  <button
                    onClick={handleApplyCast}
                    disabled={loading}
                    className="w-full py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs shadow transition-colors"
                  >
                    {loading ? 'Processing...' : 'Cast Data Type'}
                  </button>
                </div>
              )}

              {/* 5. Text Normalizer Tool */}
              {activeTool === 'normalize' && (
                <div className="space-y-3 text-xs">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="block text-slate-300 font-medium">Text Columns</label>
                      <button
                        type="button"
                        onClick={() => {
                          const textCols = preview?.columns.filter(c => preview.column_types[c] === 'categorical' || preview.column_types[c] === 'string') || [];
                          if (normCols.length === textCols.length) {
                            setNormCols([]);
                          } else {
                            setNormCols([...textCols]);
                          }
                        }}
                        className="text-[10px] text-amber-400 hover:text-amber-300 font-semibold"
                      >
                        Select All Text
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1.5 p-2 bg-slate-900 border border-slate-800 rounded-lg max-h-32 overflow-y-auto">
                      {preview?.columns.map(c => {
                        const isSelected = normCols.includes(c);
                        return (
                          <button
                            key={c}
                            type="button"
                            onClick={() => {
                              if (isSelected) {
                                setNormCols(normCols.filter(x => x !== c));
                              } else {
                                setNormCols([...normCols, c]);
                              }
                            }}
                            className={`px-2 py-1 rounded-md text-[11px] font-medium transition-all flex items-center space-x-1 ${
                              isSelected
                                ? 'bg-teal-500/20 text-amber-300 border border-teal-500/40'
                                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:border-slate-700'
                            }`}
                          >
                            <span>{c}</span>
                            {isSelected && <Check className="w-3 h-3 text-amber-400" />}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <label className="block text-slate-300 font-medium mb-1">Operation</label>
                    <select
                      value={normOp}
                      onChange={(e) => setNormOp(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                    >
                      <option value="trim">Trim Leading & Trailing Whitespace</option>
                      <option value="lowercase">Convert to lowercase</option>
                      <option value="uppercase">Convert to UPPERCASE</option>
                      <option value="titlecase">Convert to Title Case</option>
                      <option value="remove_special">Strip Special Characters & Symbols</option>
                      <option value="replace">Find & Replace Substring</option>
                    </select>
                  </div>

                  {normOp === 'replace' && (
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        value={normSearch}
                        onChange={(e) => setNormSearch(e.target.value)}
                        placeholder="Search for..."
                        className="bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                      />
                      <input
                        type="text"
                        value={normReplace}
                        onChange={(e) => setNormReplace(e.target.value)}
                        placeholder="Replace with..."
                        className="bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                      />
                    </div>
                  )}

                  <button
                    onClick={handleApplyNormalize}
                    disabled={loading}
                    className="w-full py-2.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs shadow transition-colors"
                  >
                    {loading ? 'Processing...' : 'Normalize Text'}
                  </button>
                </div>
              )}

              {/* 6. Calculated Column Tool */}
              {activeTool === 'calc' && (
                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block text-slate-300 font-medium mb-1">New Column Name</label>
                    <input
                      type="text"
                      value={calcColName}
                      onChange={(e) => setCalcColName(e.target.value)}
                      placeholder="e.g. Net_Margin or Profit_Ratio"
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Column A</label>
                      <select
                        value={calcColA}
                        onChange={(e) => setCalcColA(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                      >
                        {preview?.columns.map(c => (
                          <option key={c} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Operator</label>
                      <select
                        value={calcOp}
                        onChange={(e) => setCalcOp(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                      >
                        <option value="+">+</option>
                        <option value="-">-</option>
                        <option value="*">*</option>
                        <option value="/">/</option>
                        <option value="%">% Ratio</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-slate-300 font-medium mb-1">Col B / Val</label>
                      <input
                        type="text"
                        value={calcColBOrVal}
                        onChange={(e) => setCalcColBOrVal(e.target.value)}
                        placeholder="Column or number"
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-slate-200"
                      />
                    </div>
                  </div>

                  <button
                    onClick={handleApplyCalculatedCol}
                    disabled={loading || !calcColName}
                    className="w-full py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs shadow transition-colors disabled:opacity-50"
                  >
                    {loading ? 'Processing...' : 'Create Column'}
                  </button>
                </div>
              )}

              {/* 7. Filter Rows Tool */}
              {activeTool === 'filter' && (
                <div className="space-y-3 text-xs">
                  {filterConditions.map((cond, idx) => (
                    <div key={idx} className="space-y-1.5 p-2 bg-slate-900/80 rounded-lg border border-slate-800">
                      <div className="grid grid-cols-3 gap-1.5">
                        <select
                          value={cond.column}
                          onChange={(e) => {
                            const updated = [...filterConditions];
                            updated[idx].column = e.target.value;
                            setFilterConditions(updated);
                          }}
                          className="bg-slate-950 border border-slate-800 rounded p-1.5 text-slate-200 text-[11px]"
                        >
                          {preview?.columns.map(c => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>

                        <select
                          value={cond.operator}
                          onChange={(e) => {
                            const updated = [...filterConditions];
                            updated[idx].operator = e.target.value;
                            setFilterConditions(updated);
                          }}
                          className="bg-slate-950 border border-slate-800 rounded p-1.5 text-slate-200 text-[11px]"
                        >
                          <option value="==">== Equals</option>
                          <option value="!=">!= Not Equals</option>
                          <option value=">">&gt; Greater</option>
                          <option value="<">&lt; Less</option>
                          <option value=">=">&gt;= Greater/Equal</option>
                          <option value="<=">&lt;= Less/Equal</option>
                          <option value="contains">Contains</option>
                          <option value="not_null">Not Null</option>
                        </select>

                        <input
                          type="text"
                          value={cond.value}
                          onChange={(e) => {
                            const updated = [...filterConditions];
                            updated[idx].value = e.target.value;
                            setFilterConditions(updated);
                          }}
                          placeholder="Value..."
                          className="bg-slate-950 border border-slate-800 rounded p-1.5 text-slate-200 text-[11px]"
                        />
                      </div>
                    </div>
                  ))}

                  <button
                    onClick={handleApplyFilter}
                    disabled={loading}
                    className="w-full py-2 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-bold text-xs shadow transition-colors"
                  >
                    {loading ? 'Processing...' : 'Apply Filter'}
                  </button>
                </div>
              )}

            </div>
          </div>

          {/* Transformation Audit Log */}
          {preview && (
            <div className="glass-panel rounded-2xl p-4 space-y-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                Applied Recipe Steps ({preview.action_history.length - 1})
              </span>
              <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
                {preview.action_history.map((act, i) => (
                  <div key={i} className="text-[11px] text-slate-300 flex items-center space-x-2 py-1 px-2 rounded bg-slate-900/60 border border-slate-800/60">
                    <span className="w-4 h-4 rounded-full bg-teal-500/20 text-amber-400 flex items-center justify-center text-[9px] font-bold shrink-0">
                      {i}
                    </span>
                    <span className="truncate">{act}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* Live Interactive Data Table (Right) */}
        <div className="lg:col-span-8 glass-panel rounded-2xl p-5 space-y-4 flex flex-col justify-between">
          
          {/* Search & Meta Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search across all columns..."
                className="w-full bg-slate-900 border border-slate-800 rounded-2xl pl-9 pr-4 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-teal-500"
              />
            </form>

            <div className="flex items-center space-x-3 text-xs text-slate-400">
              <span>Rows: <strong className="text-white">{preview?.total_rows.toLocaleString()}</strong></span>
              <span>Cols: <strong className="text-white">{preview?.columns.length}</strong></span>
            </div>
          </div>

          {/* Table View */}
          <div className="overflow-x-auto rounded-2xl border border-slate-800 max-h-[500px]">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="sticky top-0 bg-slate-950 z-10">
                <tr className="border-b border-slate-800 text-slate-400 font-medium">
                  {preview?.columns.map((col) => (
                    <th
                      key={col}
                      onClick={() => handleSort(col)}
                      className="px-3.5 py-2.5 whitespace-nowrap cursor-pointer hover:bg-slate-900 transition-colors"
                    >
                      <div className="flex items-center space-x-1.5">
                        <span className="text-slate-200 font-semibold">{col}</span>
                        <ArrowUpDown className="w-3 h-3 text-slate-500" />
                        <span className="text-[9px] px-1 py-0.2 rounded bg-slate-800 text-slate-400">
                          {preview.column_types[col] || 'str'}
                        </span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {preview?.data.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 text-slate-300">
                    {preview.columns.map((col) => (
                      <td key={col} className="px-3.5 py-2 whitespace-nowrap max-w-[180px] truncate font-mono text-[11px]">
                        {row[col] === null || row[col] === undefined ? (
                          <span className="text-rose-400/80 italic font-mono">null</span>
                        ) : (
                          String(row[col])
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {preview && (
            <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs text-slate-400">
              <div>
                Page <strong>{preview.page}</strong> of <strong>{preview.total_pages}</strong> ({preview.total_rows.toLocaleString()} records)
              </div>
              <div className="flex items-center space-x-2">
                <button
                  disabled={page <= 1}
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button
                  disabled={page >= preview.total_pages}
                  onClick={() => setPage(p => p + 1)}
                  className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

        </div>

      </div>

    </div>
  );
};
