import {
  SampleDatasetInfo,
  DatasetSessionInfo,
  DataPreviewResponse,
  HealthAuditResponse,
  ColumnProfile,
  EdaSummary,
  CorrelationResponse,
  ChartOptionsResponse,
  ChartDataResponse,
  BusinessInsightsResponse,
  QueryResponse
} from '../types';

// In local dev, Vite proxies "/api" to http://127.0.0.1:8000 (see vite.config.ts).
// In production (e.g. Vercel), set VITE_API_BASE_URL to your deployed backend URL
// (e.g. https://your-backend.onrender.com) as an environment variable.
const RAW_BASE = import.meta.env.VITE_API_BASE_URL as string | undefined;
const API_BASE = RAW_BASE ? `${RAW_BASE.replace(/\/$/, '')}/api` : '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}${url}`, options);
  } catch (netErr: any) {
    throw new Error(
      `Unable to connect to DataNexus backend (${API_BASE}). Please check that the server is running on http://127.0.0.1:8000.`
    );
  }
  if (!res.ok) {
    let errorDetail = 'Request failed';
    try {
      const err = await res.json();
      errorDetail = err.detail || err.message || errorDetail;
    } catch (_) {
      errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Ingestion & Sessions
  getSamples: () => fetchJson<{ samples: SampleDatasetInfo[] }>('/samples'),

  listSessions: () => fetchJson<{ sessions: any[] }>('/sessions'),
  
  loadSample: (key: string) => 
    fetchJson<DatasetSessionInfo>(`/samples/${key}`, { method: 'POST' }),

  uploadFile: async (file: File, datasetName?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (datasetName) formData.append('dataset_name', datasetName);
    
    return fetchJson<DatasetSessionInfo>('/upload', {
      method: 'POST',
      body: formData
    });
  },

  getPreview: (
    sessionId: string,
    page: number = 1,
    pageSize: number = 25,
    sortBy?: string,
    sortAscending: boolean = true,
    search?: string
  ) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      sort_ascending: sortAscending.toString()
    });
    if (sortBy) params.append('sort_by', sortBy);
    if (search) params.append('search', search);

    return fetchJson<DataPreviewResponse>(`/preview/${sessionId}?${params.toString()}`);
  },

  // Cleaning Studio
  getAudit: (sessionId: string) => 
    fetchJson<HealthAuditResponse>(`/clean/audit/${sessionId}`),

  cleanMissing: (sessionId: string, data: { columns: string[]; strategy: string; custom_value?: any }) =>
    fetchJson<any>(`/clean/missing/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  cleanOutliers: (sessionId: string, data: { columns: string[]; method?: string; action?: string; threshold?: number }) =>
    fetchJson<any>(`/clean/outliers/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  cleanDeduplicate: (sessionId: string, data: { subset?: string[]; keep?: string }) =>
    fetchJson<any>(`/clean/deduplicate/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  cleanCast: (sessionId: string, conversions: Record<string, string>) =>
    fetchJson<any>(`/clean/cast/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversions })
    }),

  cleanNormalize: (sessionId: string, data: { columns: string[]; operation: string; search_term?: string; replace_term?: string }) =>
    fetchJson<any>(`/clean/normalize/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  cleanCalcColumn: (sessionId: string, data: any) =>
    fetchJson<any>(`/clean/calculated-column/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  cleanFilter: (sessionId: string, data: { conditions: any[]; match_all?: boolean }) =>
    fetchJson<any>(`/clean/filter/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  cleanManageCols: (sessionId: string, data: { renames?: Record<string, string>; drops?: string[] }) =>
    fetchJson<any>(`/clean/manage-columns/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  cleanUndo: (sessionId: string) =>
    fetchJson<any>(`/clean/undo/${sessionId}`, { method: 'POST' }),

  cleanRedo: (sessionId: string) =>
    fetchJson<any>(`/clean/redo/${sessionId}`, { method: 'POST' }),

  cleanReset: (sessionId: string) =>
    fetchJson<any>(`/clean/reset/${sessionId}`, { method: 'POST' }),

  getRecipe: (sessionId: string) =>
    fetchJson<{ filename: string; script: string; steps_count: number }>(`/clean/recipe/${sessionId}`),

  // Exploratory Data Analysis (EDA)
  getEdaSummary: (sessionId: string) =>
    fetchJson<EdaSummary>(`/eda/summary/${sessionId}`),

  getColumnProfiles: (sessionId: string) =>
    fetchJson<{ profiles: ColumnProfile[] }>(`/eda/profiles/${sessionId}`),

  getCorrelation: (sessionId: string, method: string = 'pearson', minCorr: number = 0.0) =>
    fetchJson<CorrelationResponse>(`/eda/correlation/${sessionId}?method=${method}&min_corr=${minCorr}`),

  computePivot: (sessionId: string, data: { rows: string[]; columns?: string[]; values?: string; aggfunc?: string }) =>
    fetchJson<any>(`/eda/pivot/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  // Visualization
  getChartOptions: (sessionId: string) =>
    fetchJson<ChartOptionsResponse>(`/visualize/options/${sessionId}`),

  generateChart: (sessionId: string, data: any) =>
    fetchJson<ChartDataResponse>(`/visualize/chart/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    }),

  // Insights & Natural Language Query
  getInsights: (sessionId: string, targetColumn?: string) => {
    const query = targetColumn ? `?target_column=${encodeURIComponent(targetColumn)}` : '';
    return fetchJson<BusinessInsightsResponse>(`/insights/generate/${sessionId}${query}`);
  },

  queryAssistant: (sessionId: string, query: string) =>
    fetchJson<QueryResponse>(`/insights/query/${sessionId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    }),

  getSuggestionChips: (sessionId: string) =>
    fetchJson<{ suggestions: string[] }>(`/insights/suggestions/${sessionId}`),

  // Export URLs
  getCsvExportUrl: (sessionId: string) => `${API_BASE}/export/csv/${sessionId}`,
  getExcelExportUrl: (sessionId: string) => `${API_BASE}/export/excel/${sessionId}`,
  getReportUrl: (sessionId: string) => `${API_BASE}/export/report/${sessionId}`
};
