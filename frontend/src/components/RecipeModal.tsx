import React, { useState, useEffect } from 'react';
import { X, Copy, Check, Download, Code2, Terminal } from 'lucide-react';
import { api } from '../services/api';

interface RecipeModalProps {
  sessionId: string;
  isOpen: boolean;
  onClose: () => void;
  setToast: (toast: { type: 'success' | 'error' | 'info'; message: string } | null) => void;
}

export const RecipeModal: React.FC<RecipeModalProps> = ({
  sessionId,
  isOpen,
  onClose,
  setToast
}) => {
  const [recipe, setRecipe] = useState<{ filename: string; script: string; steps_count: number } | null>(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      api.getRecipe(sessionId)
        .then(setRecipe)
        .catch((err) => setToast({ type: 'error', message: err.message }))
        .finally(() => setLoading(false));
    }
  }, [isOpen, sessionId]);

  if (!isOpen) return null;

  const handleCopy = () => {
    if (recipe?.script) {
      navigator.clipboard.writeText(recipe.script);
      setCopied(true);
      setToast({ type: 'success', message: 'Python script copied to clipboard.' });
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (recipe?.script) {
      const blob = new Blob([recipe.script], { type: 'text/x-python' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = recipe.filename || 'cleaning_recipe.py';
      a.click();
      URL.revokeObjectURL(url);
      setToast({ type: 'success', message: 'Downloaded Python script.' });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="glass-panel w-full max-w-3xl rounded-2xl border border-slate-700 shadow-2xl p-6 space-y-4">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-teal-500/10 text-amber-400 flex items-center justify-center">
              <Code2 className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">Auto-Generated Python Prep Script</h2>
              <p className="text-xs text-slate-400">
                Reproducible Python script generated from your {recipe?.steps_count || 0} applied cleaning transformations
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Code Content Box */}
        <div className="relative rounded-2xl bg-slate-950 border border-slate-800 p-4 font-mono text-xs text-amber-300 max-h-[420px] overflow-y-auto">
          {loading ? (
            <div className="text-slate-500 py-8 text-center">Writing the Python script...</div>
          ) : (
            <pre className="leading-relaxed whitespace-pre-wrap">{recipe?.script}</pre>
          )}
        </div>

        {/* Actions Footer */}
        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-slate-500">
            Run locally with: <code className="text-slate-300 bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">python cleaning_recipe.py</code>
          </span>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCopy}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs font-semibold text-slate-200 hover:text-white hover:border-slate-600 transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Code'}</span>
            </button>

            <button
              onClick={handleDownload}
              className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold shadow transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download .py</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
