export interface SampleDatasetInfo {
  key: string;
  name: string;
  category: string;
  description: string;
}

export interface DatasetSessionInfo {
  session_id: string;
  name: string;
  rows: number;
  columns: number;
  column_names: string[];
  message?: string;
}

export interface DataPreviewResponse {
  columns: string[];
  column_types: Record<string, string>;
  data: Record<string, any>[];
  total_rows: number;
  page: number;
  page_size: number;
  total_pages: number;
  session_name: string;
  action_history: string[];
  can_undo: boolean;
  can_redo: boolean;
}

export interface HealthIssue {
  type: string;
  column?: string;
  count?: number;
  percentage?: number;
  severity: 'low' | 'medium' | 'high';
  message: string;
}

export interface HealthAuditResponse {
  overall_score: number;
  completeness_score: number;
  uniqueness_score: number;
  consistency_score: number;
  total_rows: number;
  total_columns: number;
  total_missing: number;
  duplicate_rows: number;
  outlier_count: number;
  issues: HealthIssue[];
  recommendations: string[];
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  semantic_type: 'numeric' | 'categorical' | 'datetime' | 'boolean' | 'id';
  missing_count: number;
  missing_percentage: number;
  unique_count: number;
  unique_percentage: number;
  sample_values: string[];
  stats?: {
    min: number;
    max: number;
    mean: number;
    median: number;
    std: number;
    q25: number;
    q75: number;
    iqr: number;
    skewness: number;
    kurtosis: number;
    zero_count: number;
    zero_percentage: number;
    outlier_count: number;
    outlier_percentage: number;
    histogram: { bin_start: number; bin_end: number; label: string; count: number }[];
  };
  top_values?: { value: string; count: number; percentage: number }[];
  date_stats?: {
    min_date: string;
    max_date: string;
    timespan_days: number;
  };
}

export interface EdaSummary {
  total_rows: number;
  total_columns: number;
  total_cells: number;
  missing_cells: number;
  missing_percentage: number;
  duplicate_rows: number;
  duplicate_percentage: number;
  memory_usage_mb: number;
  type_counts: {
    numeric: number;
    datetime: number;
    boolean: number;
    categorical: number;
  };
  columns: string[];
}

export interface CorrelationPair {
  col1: string;
  col2: string;
  correlation: number;
  abs_correlation: number;
  relationship: string;
}

export interface CorrelationResponse {
  columns: string[];
  matrix: { column: string; [key: string]: any }[];
  top_correlations: CorrelationPair[];
}

export interface ChartDataset {
  label: string;
  data: any[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
  tension?: number;
  pointRadius?: number | null;
  stack?: string | null;
}

export interface ChartDataResponse {
  chart_type: string;
  title: string;
  labels: string[];
  datasets?: ChartDataset[];
  box_stats?: { min: number; q1: number; median: number; q3: number; max: number; mean: number }[];
  stats?: Record<string, any>;
}

export interface ChartOptionsResponse {
  all_columns: string[];
  numeric_columns: string[];
  categorical_columns: string[];
  datetime_columns: string[];
  chart_types: { id: string; label: string; category: string }[];
  aggregations: string[];
}

export interface KeyDriver {
  feature: string;
  importance_pct: number;
  impact_level: string;
  correlation?: number | null;
  summary: string;
}

export interface StrategicRecommendation {
  title: string;
  badge: string;
  description: string;
}

export interface BusinessInsightsResponse {
  target_column: string;
  target_is_numeric: boolean;
  kpi_highlights: {
    name: string;
    total: string;
    average: string;
    min: string;
    max: string;
    raw_total: number;
    raw_avg: number;
    trend: string;
  }[];
  key_drivers: KeyDriver[];
  anomalies: {
    type: string;
    column: string;
    count: number;
    max_value?: number;
    min_value?: number;
    message: string;
  }[];
  cohort_insights: {
    category_dimension: string;
    top_performer: { name: string; mean_value: number; total_volume: number; count: number };
    bottom_performer: { name: string; mean_value: number; total_volume: number; count: number };
  }[];
  strategic_recommendations: StrategicRecommendation[];
}

export interface QueryResponse {
  query: string;
  interpretation: string;
  columns: string[];
  data: Record<string, any>[];
  total_results: number;
  suggested_chart?: ChartDataResponse | null;
  explanation?: string;
  error?: string;
  supported_types?: string[];
  examples?: string[];
}
