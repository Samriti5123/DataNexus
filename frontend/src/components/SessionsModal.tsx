import React, { useState, useEffect } from 'react';
import { X, Database, Layers, CheckCircle2 } from 'lucide-react';
import { DatasetSessionInfo } from '../types';
import { api } from '../services/api';

interface SessionsModalProps {
  activeSession: DatasetSessionInfo | null;
  isOpen: boolean;
  onClose: () => void;
  onSelectSession: (session: DatasetSessionInfo) => void;
}

export const SessionsModal: React.FC<SessionsModalProps> = ({
  activeSession,
  isOpen,
  onClose,
  onSelectSession
}) => {
  const [sessions, setSessions] = useState<any[]>([]);

  useEffect(() => {
    if (isOpen) {
      api.listSessions()
        .then(data => setSessions(data.sessions || []))
        .catch(console.error);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="glass-panel w-full max-w-xl rounded-2xl border border-slate-700 shadow-2xl p-6 space-y-4">
        
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Database className="w-5 h-5 text-emerald-400" />
            <h2 className="text-sm font-bold text-white">Active Dataset Sessions</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-2 max-h-72 overflow-y-auto">
          {sessions.map((s) => {
            const isCurrent = activeSession?.session_id === s.session_id;
            return (
              <div
                key={s.session_id}
                onClick={() => {
                  onSelectSession({
                    session_id: s.session_id,
                    name: s.name,
                    rows: s.rows,
                    columns: s.columns,
                    column_names: []
                  });
                  onClose();
                }}
                className={`p-3.5 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                  isCurrent
                    ? 'bg-emerald-950/30 border-emerald-500/50'
                    : 'bg-slate-900/80 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="text-xs font-bold text-white flex items-center space-x-2">
                    <span>{s.name}</span>
                    {isCurrent && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {s.rows.toLocaleString()} rows • {s.columns} columns • {s.steps_applied} transformations applied
                  </div>
                </div>

                <span className="text-xs text-emerald-400 font-semibold">
                  {isCurrent ? 'Current' : 'Switch'}
                </span>
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
};
