import React, { useState, useRef } from 'react';
import { 
  Upload, 
  FileText, 
  Sparkles, 
  Database, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  Zap,
  Users,
  CreditCard,
  Layers
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { SampleDatasetInfo, DatasetSessionInfo, DataPreviewResponse } from '../types';
import { api } from '../services/api';

interface UploadViewProps {
  samples: SampleDatasetInfo[];
  activeSession: DatasetSessionInfo | null;
  onDatasetLoaded: (session: DatasetSessionInfo) => void;
  onProceedToClean: () => void;
  setToast: (toast: { type: 'success' | 'error' | 'info'; message: string } | null) => void;
}

export const UploadView: React.FC<UploadViewProps> = ({
  samples,
  activeSession,
  onDatasetLoaded,
  onProceedToClean,
  setToast
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [loadingSample, setLoadingSample] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [previewData, setPreviewData] = useState<DataPreviewResponse | null>(null);
  const [customName, setCustomName] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch preview when activeSession changes
  React.useEffect(() => {
    if (activeSession) {
      api.getPreview(activeSession.session_id, 1, 8)
        .then(setPreviewData)
        .catch(console.error);
    }
  }, [activeSession]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      await uploadFile(e.target.files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    try {
      const res = await api.uploadFile(file, customName || undefined);
      confetti({ particleCount: 60, spread: 60, origin: { y: 0.8 } });
      onDatasetLoaded(res);
      setToast({ type: 'success', message: `Uploaded '${res.name}' successfully (${res.rows.toLocaleString()} rows).` });
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'File upload failed.' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleLoadSample = async (key: string) => {
    setLoadingSample(key);
    try {
      const res = await api.loadSample(key);
      confetti({ particleCount: 50, spread: 50, origin: { y: 0.7 } });
      onDatasetLoaded(res);
      setToast({ type: 'success', message: `Loaded sample dataset '${res.name}'.` });
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Failed to load sample dataset.' });
    } finally {
      setLoadingSample(null);
    }
  };

  const getSampleIcon = (key: string) => {
    switch (key) {
      case 'superstore_sales': return TrendingUp;
      case 'telecom_churn': return Users;
      case 'hr_analytics': return Users;
      case 'fintech_transactions': return CreditCard;
      case 'saas_metrics': return Zap;
      default: return Database;
    }
  };

  return (
    <div className="space-y-10 pb-16">
      
      {/* Hero Header */}
      <div className="text-center max-w-3xl mx-auto pt-6 space-y-4">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-amber-400 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Stage 1: Bring In Your Data</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-black text-white tracking-tight leading-tight">
          Turn Raw Data into <span className="bg-gradient-to-r from-teal-400 via-amber-300 to-teal-300 bg-clip-text text-transparent">Decision-Ready Findings</span>
        </h1>
        <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
          Upload any CSV, Excel, or JSON file — or select an enterprise sample dataset below to explore interactive automated cleaning, statistical profiling, chart studios, and C-suite AI reports.
        </p>
      </div>

      {/* File Upload Zone */}
      <div className="max-w-4xl mx-auto">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative group cursor-pointer rounded-2xl border-2 border-dashed transition-all duration-300 p-8 sm:p-12 text-center ${
            isDragging
              ? 'border-amber-400 bg-teal-500/10 scale-[1.01]'
              : 'border-[#24454D] hover:border-teal-500/50 bg-[#10262C]/60 hover:bg-[#10262C]/90'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls,.json,.tsv,.txt"
            onChange={handleFileInput}
            className="hidden"
          />

          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-teal-600 to-amber-500 flex items-center justify-center shadow-lg shadow-teal-500/25 group-hover:scale-110 transition-transform">
              <Upload className="w-8 h-8 text-white" />
            </div>
            
            <div className="space-y-1">
              <p className="text-base font-semibold text-white">
                {isUploading ? 'Ingesting and parsing dataset...' : 'Drag & drop your dataset file here, or browse files'}
              </p>
              <p className="text-xs text-slate-400">
                Supports CSV, Excel (.xlsx, .xls), JSON, TSV • Auto-detects delimiters and UTF-8/Latin encodings
              </p>
            </div>

            <div className="flex items-center space-x-2 pt-2">
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">.CSV</span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">.XLSX</span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">.JSON</span>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">.TSV</span>
            </div>
          </div>
        </div>
      </div>

      {/* 1-Click Enterprise Sample Datasets */}
      <div className="max-w-6xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Database className="w-4 h-4 text-amber-400" />
            <h2 className="text-lg font-bold text-white">Or try one of the ready-made sample files</h2>
          </div>
          <span className="text-xs text-slate-400">Ready-made data to start right away</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {samples.map((s) => {
            const Icon = getSampleIcon(s.key);
            const isCurrent = activeSession?.name.toLowerCase().includes(s.name.toLowerCase().split(' ')[0]);
            const isLoading = loadingSample === s.key;

            return (
              <div
                key={s.key}
                onClick={() => handleLoadSample(s.key)}
                className={`relative group cursor-pointer p-5 rounded-2xl border transition-all duration-200 ${
                  isCurrent
                    ? 'bg-teal-950/40 border-teal-500/50 shadow-lg shadow-teal-950/40'
                    : 'bg-[#10262C]/80 border-[#24454D] hover:border-teal-500/40 hover:bg-[#10262C]'
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="w-9 h-9 rounded-lg bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-amber-400 group-hover:text-amber-300 group-hover:scale-105 transition-all">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 border border-slate-700">
                    {s.category}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-white mb-1 group-hover:text-amber-400 transition-colors">
                  {s.name}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  {s.description}
                </p>

                <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-800">
                  <span className="text-slate-500 font-medium">
                    {isCurrent ? 'Active Dataset' : 'Click to Load'}
                  </span>
                  <div className="flex items-center space-x-1 text-amber-400 font-semibold group-hover:translate-x-1 transition-transform">
                    <span>{isLoading ? 'Loading...' : 'Launch'}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Raw Preview & Quick Proceed */}
      {activeSession && previewData && (
        <div className="max-w-6xl mx-auto bg-[#10262C]/90 border border-[#24454D] rounded-2xl p-6 space-y-6 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#24454D] pb-4">
            <div>
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <h3 className="text-base font-bold text-white">Dataset Loaded: {activeSession.name}</h3>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {activeSession.rows.toLocaleString()} rows • {activeSession.columns} columns loaded into memory session
              </p>
            </div>

            <button
              onClick={onProceedToClean}
              className="flex items-center justify-center space-x-2 px-5 py-2.5 rounded-2xl bg-gradient-to-r from-teal-600 to-amber-600 hover:from-teal-500 hover:to-amber-500 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-teal-900/40 transition-all hover:scale-[1.02]"
            >
              <span>Continue to Preparation</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {/* Quick Table Preview */}
          <div className="overflow-x-auto rounded-2xl border border-slate-800">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-medium">
                  {previewData.columns.map((col) => (
                    <th key={col} className="px-4 py-2.5 whitespace-nowrap">
                      <div className="flex items-center space-x-1.5">
                        <span className="text-slate-200">{col}</span>
                        <span className="text-[9px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                          {previewData.column_types[col] || 'str'}
                        </span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {previewData.data.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 text-slate-300">
                    {previewData.columns.map((col) => (
                      <td key={col} className="px-4 py-2 whitespace-nowrap max-w-[200px] truncate">
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
        </div>
      )}

    </div>
  );
};
