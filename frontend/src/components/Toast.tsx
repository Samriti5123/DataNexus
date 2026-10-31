import React, { useEffect } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

interface ToastProps {
  toast: { type: 'success' | 'error' | 'info'; message: string } | null;
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ toast, onClose }) => {
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(onClose, 4000);
      return () => clearTimeout(timer);
    }
  }, [toast, onClose]);

  if (!toast) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-5 fade-in duration-300">
      <div className={`flex items-center space-x-3 px-4 py-3 rounded-2xl border shadow-xl backdrop-blur-md ${
        toast.type === 'success'
          ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-200'
          : toast.type === 'error'
          ? 'bg-rose-950/90 border-rose-500/40 text-rose-200'
          : 'bg-slate-900/90 border-slate-700 text-slate-200'
      }`}>
        {toast.type === 'success' && <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />}
        {toast.type === 'error' && <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />}
        {toast.type === 'info' && <Info className="w-5 h-5 text-amber-400 shrink-0" />}
        
        <span className="text-xs font-medium max-w-sm">{toast.message}</span>

        <button onClick={onClose} className="text-slate-400 hover:text-white ml-2">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
