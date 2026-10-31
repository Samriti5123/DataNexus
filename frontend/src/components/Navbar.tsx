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

const tabs = [
  { id: 'upload' as TabType, label: '1. Data Intake', icon: UploadCloud, desc: 'Load your HR file' },
  { id: 'clean' as TabType, label: '2. Preparation', icon: Sparkles, desc: 'Fix & prepare' },
  { id: 'eda' as TabType, label: '3. Explorer', icon: BarChart3, desc: 'Distributions & pivots' },
  { id: 'visualize' as TabType, label: '4. Chart Studio', icon: PieChart, desc: 'Build charts' },
  { id: 'insights' as TabType, label: '5. HR Insights', icon: Lightbulb, desc: 'Findings & report' }
];

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
  return (
    <header className="sticky top-0 z-40 border-b border-[#24454D] bg-[#0A1A1F]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Brand Logo & Name */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onTabChange('upload')}>
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-teal-600 via-teal-500 to-amber-400 flex items-center justify-center shadow-lg shadow-teal-500/25 text-white font-black text-xl">
              <Layers className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
                  DataNexus
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-teal-500/10 text-amber-400 border border-amber-500/30">
                  Workforce Analytics
                </span>
              </div>
              <p className="text-[11px] text-slate-400">HR Attrition Analysis & Insights</p>
            </div>
          </div>

          {/* Stepped Navigation Pipeline */}
          <nav className="hidden items-center space-x-1 p-1 bg-[#10262C] rounded-2xl border border-[#24454D]">
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
                      ? 'bg-gradient-to-r from-teal-600 to-amber-600 text-white shadow-md shadow-teal-900/40 font-semibold'
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
                  className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-[#10262C] border border-[#24454D] hover:border-teal-500/50 text-xs text-slate-200 transition-colors"
                  title="Switch or inspect loaded dataset"
                >
                  <Database className="w-3.5 h-3.5 text-amber-400" />
                  <span className="max-w-[130px] truncate font-medium">{activeSession.name}</span>
                  <span className="text-[10px] text-slate-400">({activeSession.rows.toLocaleString()}r)</span>
                </button>

                <button
                  onClick={onExportCsv}
                  className="p-1.5 rounded-lg bg-[#10262C] hover:bg-slate-800 border border-[#24454D] text-slate-300 hover:text-amber-400 transition-colors"
                  title="Export Cleaned CSV"
                >
                  <FileSpreadsheet className="w-4 h-4" />
                </button>

                <button
                  onClick={onExportReport}
                  className="flex items-center space-x-1 px-2.5 py-1.5 rounded-lg bg-teal-500/10 hover:bg-teal-500/20 border border-teal-500/30 text-amber-300 text-xs font-semibold transition-colors"
                  title="Open Executive HTML Report"
                >
                  <FileText className="w-3.5 h-3.5 text-amber-400" />
                  <span className="hidden sm:inline">Report</span>
                </button>
              </div>
            ) : (
              <div className="text-xs text-slate-500 italic">Nothing loaded yet</div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

interface SidebarProps {
  currentTab: TabType;
  onTabChange: (tab: TabType) => void;
  activeSession: DatasetSessionInfo | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onTabChange, activeSession }) => (
  <aside className="hidden md:flex w-60 shrink-0 flex-col gap-1 border-r border-[#24454D] bg-[#0A1A1F] px-4 py-6 sticky top-16 self-start h-[calc(100vh-4rem)]">
    <p className="text-[10px] font-bold uppercase tracking-widest text-amber-400/80 mb-3 px-2">Workflow Steps</p>
    {tabs.map((tab) => {
      const Icon = tab.icon;
      const num = tab.label.split('.')[0];
      const name = tab.label.replace(/^\d+\.\s*/, '');
      const isActive = currentTab === tab.id;
      const isEnabled = tab.id === 'upload' || activeSession !== null;
      return (
        <button
          key={tab.id}
          disabled={!isEnabled}
          onClick={() => isEnabled && onTabChange(tab.id)}
          className={`flex items-center gap-3 px-3 py-3 text-left transition-all ${
            isActive
              ? 'bg-gradient-to-r from-teal-600/30 to-amber-500/20 border border-teal-500/40 text-white'
              : isEnabled
              ? 'text-slate-300 hover:bg-[#10262C] border border-transparent'
              : 'text-slate-600 cursor-not-allowed opacity-50 border border-transparent'
          }`}
          style={{ borderRadius: 16 }}
        >
          <span className={`w-7 h-7 shrink-0 rounded-full flex items-center justify-center text-xs font-bold ${isActive ? 'bg-amber-400 text-slate-900' : 'bg-[#10262C] text-slate-400'}`}>{num}</span>
          <span className="min-w-0">
            <span className="flex items-center gap-1.5 text-sm font-semibold"><Icon className="w-3.5 h-3.5" />{name}</span>
            <span className="block text-[11px] text-slate-400 truncate">{tab.desc}</span>
          </span>
        </button>
      );
    })}
  </aside>
);
