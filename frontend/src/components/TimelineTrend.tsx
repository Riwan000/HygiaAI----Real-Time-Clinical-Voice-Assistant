/**
 * TimelineTrend Component
 * 
 * Shows improvement/decline trends for patient cases
 */

import { TrendChart, type TrendDataPoint } from './TrendChart';
import { clsx } from '../utils/clsx';

export interface TrendMetric {
  date: string;
  value: number;
  label: string;
  type: 'improvement' | 'decline' | 'stable';
}

interface TimelineTrendProps {
  metrics: TrendMetric[];
  title?: string;
  className?: string;
}

export function TimelineTrend({ metrics, title = 'Patient Progress Trend', className = '' }: TimelineTrendProps) {
  // Filter out invalid metrics
  const validMetrics = metrics.filter((m) => 
    m && 
    m.date && 
    typeof m.value === 'number' && 
    !isNaN(m.value) &&
    m.label &&
    m.label.trim() !== ''
  );
  
  // Convert metrics to TrendDataPoint format
  const trendData: TrendDataPoint[] = validMetrics.map((metric) => ({
    date: metric.date,
    value: metric.value,
    label: metric.label || 'Unknown',
    confidence_interval: {
      lower: Math.max(0, metric.value * 0.9), // 10% margin, ensure non-negative
      upper: metric.value * 1.1,
    },
  }));

  // Calculate statistics
  const avgValue = validMetrics.length > 0
    ? validMetrics.reduce((sum, m) => sum + m.value, 0) / validMetrics.length
    : 0;
  const improvementCount = validMetrics.filter((m) => m.type === 'improvement').length;
  const declineCount = validMetrics.filter((m) => m.type === 'decline').length;
  const stableCount = validMetrics.filter((m) => m.type === 'stable').length;

  return (
    <div 
      className={clsx('bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30 p-6', className)}
      role="region"
      aria-label={title}
    >
      <h3 className="text-lg font-semibold text-[#1E3A8A] dark:text-white mb-4" style={{ fontWeight: 600 }}>
        {title}
      </h3>

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">
            {improvementCount}
          </div>
          <div className="text-sm text-green-800 dark:text-green-300">Improvements</div>
        </div>
        <div className="text-center p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
          <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
            {stableCount}
          </div>
          <div className="text-sm text-yellow-800 dark:text-yellow-300">Stable</div>
        </div>
        <div className="text-center p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
          <div className="text-2xl font-bold text-red-600 dark:text-red-400">
            {declineCount}
          </div>
          <div className="text-sm text-red-800 dark:text-red-300">Declines</div>
        </div>
      </div>

      {/* Trend Chart */}
      {trendData.length > 0 ? (
        <TrendChart
          data={trendData}
          title="Progress Over Time"
          yAxisLabel="Score"
          showConfidenceInterval={true}
          height={300}
          aria-label="Patient progress trend chart showing improvement, stable, and decline metrics over time"
        />
      ) : (
        <div className="text-center py-8 text-[#64748B] dark:text-[#94A3B8]">
          <p>No trend data available</p>
          <p className="text-sm mt-2">
            {metrics.length > 0 
              ? 'Trend metrics require outcome data. Add outcomes to cases to see trends.'
              : 'Add cases with outcomes to see patient progress trends.'}
          </p>
        </div>
      )}

      {/* Average */}
      {avgValue > 0 && (
        <div className="mt-4 text-center">
          <span className="text-sm text-[#64748B] dark:text-[#94A3B8]">
            Average Score: <strong className="text-[#1E3A8A] dark:text-white">{avgValue.toFixed(1)}</strong>
          </span>
        </div>
      )}
    </div>
  );
}

