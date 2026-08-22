import React from 'react';
import { 
  Layers, 
  UploadCloud, 
  Sparkles, 
  BarChart3, 
  PieChart, 
  Lightbulb, 
  FileSpreadsheet, 
  FileText,
  RefreshCw,
  Database
} from 'lucide-react';
import { DatasetSessionInfo } from '../types';

export type TabType = 'upload' | 'clean' | 'eda' | 'visualize' | 'insights';

interface NavbarProps {
  currentTab: TabType;
  onTabChange: (tab: TabType) => void;
  activeSession: DatasetSessionInfo | null;
  onOpenSessionModal: () => void;
  onExportCsv: () => void;
  onExportReport: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onTabChange,
  activeSession,
  onOpenSessionModal,
  onExportCsv,
  onExportReport
}) => {
  const tabs = [
    { id: 'upload' as TabType, label: '1. Ingestion', icon: UploadCloud, desc: 'Upload or pick sample' },
    { id: 'clean' as TabType, label: '2. Clean & Prep', icon: Sparkles, desc: 'Impute, filter, sanitize' },
    { id: 'eda' as TabType, label: '3. Exploratory EDA', icon: BarChart3, desc: 'Distributions & pivots' },
    { id: 'visualize' as TabType, label: '4. Visualizer', icon: PieChart, desc: 'Multi-chart studio' },
    { id: 'insights' as TabType, label: '5. AI Insights', icon: Lightbulb, desc: 'Drivers & executive report' }
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-slate-800/80 bg-slate-950/85 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Brand Logo & Name */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onTabChange('upload')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 via-teal-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20 text-slate-950 font-black text-xl">
              <Layers className="w-6 h-6 text-slate-950" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                  DataLens
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  Analytics OS
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Interactive Data Analysis & Business Intelligence</p>
            </div>
          </div>

          {/* Stepped Navigation Pipeline */}
          <nav className="hidden md:flex items-center space-x-1 p-1 bg-slate-900/90 rounded-xl border border-slate-800/80">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = currentTab === tab.id;
              const isEnabled = tab.id === 'upload' || activeSession !== null;

              return (
                <button
                  key={tab.id}
                  disabled={!isEnabled}
                  onClick={() => isEnabled && onTabChange(tab.id)}
                  className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-md shadow-emerald-900/30'
                      : isEnabled
                      ? 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      : 'text-slate-600 cursor-not-allowed opacity-50'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Active Dataset Badge & Action Buttons */}
          <div className="flex items-center space-x-2">
            {activeSession ? (
              <div className="flex items-center space-x-2">
                <button
                  onClick={onOpenSessionModal}
                  className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700/70 hover:border-slate-600 text-xs text-slate-200 transition-colors"
                  title="Switch or inspect loaded dataset"
                >
                  <Database className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="max-w-[130px] truncate font-medium">{activeSession.name}</span>
                  <span className="text-[10px] text-slate-400">({activeSession.rows.toLocaleString()}r)</span>
                </button>

                <button
                  onClick={onExportCsv}
                  className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-emerald-400 transition-colors"
                  title="Export Cleaned CSV"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                </button>

                <button
                  onClick={onExportReport}
                  className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 text-xs font-semibold transition-colors"
                  title="Open Executive HTML Report"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Report</span>
                </button>
              </div>
            ) : (
              <div className="text-xs text-slate-500 italic">No dataset loaded</div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
