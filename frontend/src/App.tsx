import React, { useState, useEffect } from 'react';
import { Navbar, Sidebar, TabType } from './components/Navbar';
import { UploadView } from './components/UploadView';
import { CleanView } from './components/CleanView';
import { EdaView } from './components/EdaView';
import { VisualizeView } from './components/VisualizeView';
import { InsightsView } from './components/InsightsView';
import { RecipeModal } from './components/RecipeModal';
import { SessionsModal } from './components/SessionsModal';
import { Toast } from './components/Toast';
import { SampleDatasetInfo, DatasetSessionInfo } from './types';
import { api } from './services/api';

export function App() {
  const [currentTab, setCurrentTab] = useState<TabType>('upload');
  const [samples, setSamples] = useState<SampleDatasetInfo[]>([]);
  const [activeSession, setActiveSession] = useState<DatasetSessionInfo | null>(null);
  const [isRecipeModalOpen, setIsRecipeModalOpen] = useState(false);
  const [isSessionModalOpen, setIsSessionModalOpen] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

  // Initialize sample datasets and default session
  useEffect(() => {
    api.getSamples()
      .then(res => setSamples(res.samples))
      .catch(err => console.error('Failed to load samples:', err));

    // Check if there is an active session in backend
    api.listSessions()
      .then(data => {
        if (data.sessions && data.sessions.length > 0) {
          const first = data.sessions[0];
          setActiveSession({
            session_id: first.session_id,
            name: first.name,
            rows: first.rows,
            columns: first.columns,
            column_names: []
          });
        }
      })
      .catch(console.error);
  }, []);

  const handleDatasetLoaded = (session: DatasetSessionInfo) => {
    setActiveSession(session);
  };

  const handleExportCsv = () => {
    if (!activeSession) return;
    window.location.href = api.getCsvExportUrl(activeSession.session_id);
    setToast({ type: 'success', message: 'Downloading cleaned dataset CSV...' });
  };

  const handleExportReport = () => {
    if (!activeSession) return;
    window.open(api.getReportUrl(activeSession.session_id), '_blank');
  };

  return (
    <div className="min-h-screen bg-[#0A1A1F] text-[#F8FAFC] flex flex-col selection:bg-teal-500/30 selection:text-teal-300">
      
      {/* Top Navbar */}
      <Navbar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        activeSession={activeSession}
        onOpenSessionModal={() => setIsSessionModalOpen(true)}
        onExportCsv={handleExportCsv}
        onExportReport={handleExportReport}
      />

      <div className="flex flex-1">
      <Sidebar currentTab={currentTab} onTabChange={setCurrentTab} activeSession={activeSession} />
      <div className="flex-1 min-w-0 flex flex-col">
      {/* Main Container */}
      <main className="flex-1 w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {currentTab === 'upload' && (
          <UploadView
            samples={samples}
            activeSession={activeSession}
            onDatasetLoaded={handleDatasetLoaded}
            onProceedToClean={() => setCurrentTab('clean')}
            setToast={setToast}
          />
        )}

        {currentTab === 'clean' && activeSession && (
          <CleanView
            activeSession={activeSession}
            onSessionUpdated={setActiveSession}
            onOpenRecipeModal={() => setIsRecipeModalOpen(true)}
            onProceedToEda={() => setCurrentTab('eda')}
            setToast={setToast}
          />
        )}

        {currentTab === 'eda' && activeSession && (
          <EdaView
            activeSession={activeSession}
            onProceedToVisualize={() => setCurrentTab('visualize')}
            setToast={setToast}
          />
        )}

        {currentTab === 'visualize' && activeSession && (
          <VisualizeView
            activeSession={activeSession}
            onProceedToInsights={() => setCurrentTab('insights')}
            setToast={setToast}
          />
        )}

        {currentTab === 'insights' && activeSession && (
          <InsightsView
            activeSession={activeSession}
            onOpenReport={handleExportReport}
            setToast={setToast}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-[#24454D] bg-[#0A1A1F]/80 py-6 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>DataNexus · HR attrition analysis made simple</span>
          <span>FastAPI • Pandas • Scikit-Learn • React 19 • Vite • TailwindCSS</span>
        </div>
      </footer>
      </div>
      </div>

      {/* Modals & Toast */}
      {activeSession && (
        <RecipeModal
          sessionId={activeSession.session_id}
          isOpen={isRecipeModalOpen}
          onClose={() => setIsRecipeModalOpen(false)}
          setToast={setToast}
        />
      )}

      <SessionsModal
        activeSession={activeSession}
        isOpen={isSessionModalOpen}
        onClose={() => setIsSessionModalOpen(false)}
        onSelectSession={setActiveSession}
      />

      <Toast toast={toast} onClose={() => setToast(null)} />

    </div>
  );
}

export default App;
