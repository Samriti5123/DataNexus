import React, { useState, useEffect, useRef } from 'react';
import { 
  Bar, 
  Line, 
  Pie, 
  Doughnut, 
  Scatter 
} from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { 
  PieChart, 
  Download, 
  Sliders, 
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import { DatasetSessionInfo, ChartOptionsResponse, ChartDataResponse } from '../types';
import { api } from '../services/api';

// Register Chart.js elements
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface VisualizeViewProps {
  activeSession: DatasetSessionInfo;
  onProceedToInsights: () => void;
  setToast: (toast: { type: 'success' | 'error' | 'info'; message: string } | null) => void;
}

export const VisualizeView: React.FC<VisualizeViewProps> = ({
  activeSession,
  onProceedToInsights,
  setToast
}) => {
  const [options, setOptions] = useState<ChartOptionsResponse | null>(null);
  const [chartData, setChartData] = useState<ChartDataResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const chartRef = useRef<any>(null);

  // Form Configuration States
  const [chartType, setChartType] = useState('bar');
  const [xAxis, setXAxis] = useState('');
  const [yAxis, setYAxis] = useState('');
  const [groupBy, setGroupBy] = useState('');
  const [aggregation, setAggregation] = useState('sum');
  const [sortBy, setSortBy] = useState('value_desc');
  const [palette, setPalette] = useState('modern_blue');
  const [limit, setLimit] = useState(12);

  useEffect(() => {
    loadOptions();
  }, [activeSession.session_id]);

  const loadOptions = async () => {
    try {
      const res = await api.getChartOptions(activeSession.session_id);
      setOptions(res);

      if (res.categorical_columns.length > 0) {
        setXAxis(res.categorical_columns[0]);
      } else if (res.all_columns.length > 0) {
        setXAxis(res.all_columns[0]);
      }

      if (res.numeric_columns.length > 0) {
        setYAxis(res.numeric_columns[0]);
      }
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Failed to load chart options.' });
    }
  };

  // Generate chart when parameters change
  useEffect(() => {
    if (xAxis) {
      handleGenerateChart();
    }
  }, [chartType, xAxis, yAxis, groupBy, aggregation, sortBy, palette, limit]);

  const handleGenerateChart = async () => {
    if (!xAxis) return;
    setLoading(true);
    try {
      const res = await api.generateChart(activeSession.session_id, {
        chart_type: chartType,
        x_axis: xAxis,
        y_axis: yAxis || undefined,
        group_by: groupBy || undefined,
        aggregation,
        sort_by: sortBy,
        limit,
        palette
      });
      setChartData(res);
    } catch (err: any) {
      setToast({ type: 'error', message: err.message || 'Failed to generate chart.' });
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPng = () => {
    if (chartRef.current) {
      const base64Image = chartRef.current.toBase64Image();
      const link = document.createElement('a');
      link.download = `DataNexus_${chartType}_${xAxis}.png`;
      link.href = base64Image;
      link.click();
      setToast({ type: 'success', message: 'Chart downloaded as high-resolution PNG.' });
    }
  };

  // Chart rendering helper
  const renderChart = () => {
    if (!chartData) return null;

    const commonOptions: any = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#94a3b8', font: { family: 'Inter', size: 12 } }
        },
        title: {
          display: true,
          text: chartData.title,
          color: '#f8fafc',
          font: { size: 15, weight: 'bold', family: 'Inter' },
          padding: { bottom: 16 }
        },
        tooltip: {
          backgroundColor: '#0f172a',
          titleColor: '#f8fafc',
          bodyColor: '#cbd5e1',
          borderColor: '#334155',
          borderWidth: 1,
          padding: 10,
          boxPadding: 4
        }
      },
      scales: chartType === 'pie' || chartType === 'donut' ? {} : {
        x: {
          grid: { color: 'rgba(51, 65, 85, 0.3)' },
          ticks: { color: '#94a3b8', font: { size: 11 } }
        },
        y: {
          grid: { color: 'rgba(51, 65, 85, 0.3)' },
          ticks: { color: '#94a3b8', font: { size: 11 } }
        }
      }
    };

    const dataPayload: any = {
      labels: chartData.labels || [],
      datasets: (chartData.datasets || []).map(d => ({
        ...d,
        stack: d.stack || undefined
      }))
    };

    switch (chartType) {
      case 'bar':
      case 'stacked_bar':
      case 'histogram':
        return <Bar ref={chartRef} data={dataPayload} options={commonOptions} />;
      case 'horizontal_bar': {
        const hOptions = { ...commonOptions, indexAxis: 'y' as const };
        return <Bar ref={chartRef} data={dataPayload} options={hOptions} />;
      }
      case 'line':
      case 'area':
        return <Line ref={chartRef} data={dataPayload} options={commonOptions} />;
      case 'pie':
        return <Pie ref={chartRef} data={dataPayload} options={commonOptions} />;
      case 'donut':
        return <Doughnut ref={chartRef} data={dataPayload} options={commonOptions} />;
      case 'scatter':
      case 'bubble':
        return <Scatter ref={chartRef} data={dataPayload} options={commonOptions} />;
      case 'boxplot':
        return (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 p-4 overflow-y-auto max-h-[440px]">
            {chartData.labels.map((lbl, i) => {
              const b = chartData.box_stats?.[i];
              if (!b) return null;
              return (
                <div key={i} className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
                  <div className="font-bold text-white text-sm">{lbl}</div>
                  <div className="space-y-1 text-xs text-slate-300 font-mono">
                    <div className="flex justify-between"><span>Max:</span><strong>{b.max}</strong></div>
                    <div className="flex justify-between"><span>Q3 (75%):</span><strong className="text-amber-400">{b.q3}</strong></div>
                    <div className="flex justify-between"><span>Median:</span><strong className="text-amber-400">{b.median}</strong></div>
                    <div className="flex justify-between"><span>Q1 (25%):</span><strong className="text-purple-400">{b.q1}</strong></div>
                    <div className="flex justify-between"><span>Min:</span><strong>{b.min}</strong></div>
                    <div className="flex justify-between pt-1 border-t border-slate-800"><span>Mean:</span><strong>{b.mean}</strong></div>
                  </div>
                </div>
              );
            })}
          </div>
        );
      default:
        return <Bar ref={chartRef} data={dataPayload} options={commonOptions} />;
    }
  };

  return (
    <div className="space-y-8 pb-16">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-amber-400 text-xs font-semibold mb-2">
            <PieChart className="w-3.5 h-3.5" />
            <span>Stage 4: Build Your Charts</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">Multi-View Chart Studio</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Build bar, multi-line, scatter, boxplot and pie charts with dynamic aggregations and high-resolution exports.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleDownloadPng}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs font-semibold text-slate-200 hover:text-amber-400 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Save PNG</span>
          </button>

          <button
            onClick={onProceedToInsights}
            className="flex items-center space-x-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-teal-600 to-amber-600 hover:from-teal-500 hover:to-amber-500 text-white text-xs font-bold shadow-md shadow-teal-900/40 transition-all hover:scale-[1.02]"
          >
            <span>Continue to HR Insights</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Controls Sidebar (Left) */}
        <div className="lg:col-span-4 glass-panel rounded-2xl p-5 space-y-4">
          <h2 className="text-sm font-bold text-white flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-amber-400" />
            <span>Chart Settings</span>
          </h2>

          {/* Chart Type Gallery */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Chart Type</label>
            <div className="grid grid-cols-3 gap-1.5 text-[11px]">
              {[
                { id: 'bar', label: 'Bar' },
                { id: 'stacked_bar', label: 'Stacked' },
                { id: 'horizontal_bar', label: 'H-Bar' },
                { id: 'line', label: 'Line' },
                { id: 'area', label: 'Area' },
                { id: 'pie', label: 'Pie' },
                { id: 'donut', label: 'Donut' },
                { id: 'scatter', label: 'Scatter' },
                { id: 'histogram', label: 'Histogram' },
                { id: 'boxplot', label: 'Boxplot' }
              ].map((t) => (
                <button
                  key={t.id}
                  onClick={() => setChartType(t.id)}
                  className={`py-1.5 px-2 rounded-lg font-medium transition-colors ${
                    chartType === t.id
                      ? 'bg-teal-600 text-white font-bold shadow-md shadow-teal-900/30'
                      : 'bg-slate-900 text-slate-400 hover:text-white'
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* X Axis Dimension */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">X-Axis / Category</label>
            <select
              value={xAxis}
              onChange={(e) => setXAxis(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
            >
              {options?.all_columns.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Y Axis Metric */}
          {chartType !== 'histogram' && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Y-Axis Metric</label>
              <select
                value={yAxis}
                onChange={(e) => setYAxis(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
              >
                <option value="">Count of Records</option>
                {options?.numeric_columns.map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          )}

          {/* Group-by Column (Optional) */}
          {['bar', 'stacked_bar', 'line', 'area', 'scatter'].includes(chartType) && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Group Dimension (Color Breakdown)</label>
              <select
                value={groupBy}
                onChange={(e) => setGroupBy(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
              >
                <option value="">None</option>
                {options?.categorical_columns.filter(c => c !== xAxis).map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          )}

          {/* Aggregation Function */}
          {yAxis && chartType !== 'scatter' && chartType !== 'boxplot' && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Aggregation Function</label>
              <select
                value={aggregation}
                onChange={(e) => setAggregation(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
              >
                <option value="sum">Sum</option>
                <option value="mean">Average / Mean</option>
                <option value="median">Median</option>
                <option value="min">Minimum</option>
                <option value="max">Maximum</option>
                <option value="count">Count</option>
              </select>
            </div>
          )}

          {/* Sort & Limit */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Sort Order</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
              >
                <option value="value_desc">Value (High to Low)</option>
                <option value="value_asc">Value (Low to High)</option>
                <option value="label_asc">Category A-Z</option>
                <option value="none">Original Order</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Top Limit ({limit})</label>
              <input
                type="range"
                min="5"
                max="30"
                step="1"
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value))}
                className="w-full accent-teal-500 mt-2"
              />
            </div>
          </div>

          {/* Palette Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Color Palette Theme</label>
            <div className="grid grid-cols-3 gap-1.5 text-[10px]">
              {[
                { id: 'modern_blue', label: 'Blue Nexus' },
                { id: 'cyan_glow', label: 'Cyan Glow' },
                { id: 'cyber_indigo', label: 'Cyber Indigo' },
                { id: 'sunset_warmth', label: 'Sunset' }
              ].map(p => (
                <button
                  key={p.id}
                  onClick={() => setPalette(p.id)}
                  className={`py-1.5 rounded-lg font-semibold border ${
                    palette === p.id
                      ? 'bg-slate-800 border-teal-500 text-amber-400'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

        </div>

        {/* Chart Canvas Display (Right) */}
        <div className="lg:col-span-8 glass-panel rounded-2xl p-6 flex flex-col justify-between min-h-[480px]">
          
          <div className="relative w-full h-[440px] flex items-center justify-center">
            {loading ? (
              <div className="flex items-center space-x-2 text-amber-400 text-sm animate-pulse">
                <RefreshCw className="w-5 h-5 animate-spin" />
                <span>Drawing your chart...</span>
              </div>
            ) : (
              renderChart()
            )}
          </div>

          <div className="flex items-center justify-between text-xs text-slate-500 pt-3 border-t border-slate-800/80">
            <span>Powered by Chart.js 4 & Canvas Engine</span>
            <span>Tip: click a legend item to show or hide that series</span>
          </div>

        </div>

      </div>

    </div>
  );
};
