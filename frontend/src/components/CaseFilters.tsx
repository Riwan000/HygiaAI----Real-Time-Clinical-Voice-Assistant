/**
 * Case Filters Component
 * 
 * Filter options for cases (age, region, diagnosis, time range).
 */

import { useState } from 'react';
import { FunnelIcon } from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

export type FilterOptions = {
  age_group?: string;
  region?: string;
  diagnosis?: string;
  time_range_days?: number;
  score_threshold?: number;
};

interface CaseFiltersProps {
  filters: FilterOptions;
  onChange: (filters: FilterOptions) => void;
  onReset: () => void;
}

const ageGroups = ['pediatric', 'adult', 'elderly'];
const timeRanges = [
  { label: 'Last 7 days', value: 7 },
  { label: 'Last 30 days', value: 30 },
  { label: 'Last 90 days', value: 90 },
  { label: 'Last year', value: 365 },
];

export function CaseFilters({ filters, onChange, onReset }: CaseFiltersProps) {
  const [isOpen, setIsOpen] = useState(false);

  const hasActiveFilters =
    filters.age_group ||
    filters.region ||
    filters.diagnosis ||
    filters.time_range_days ||
    filters.score_threshold;

  const handleChange = (key: keyof FilterOptions, value: any) => {
    onChange({ ...filters, [key]: value || undefined });
  };

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={clsx(
          'inline-flex items-center px-4 py-2.5 border rounded-lg text-sm font-medium transition-all duration-200',
          hasActiveFilters
            ? 'bg-[#C4B5FD]/20 dark:bg-[#8B5CF6]/20 border-[#8B5CF6] dark:border-[#C4B5FD] text-[#8B5CF6] dark:text-[#C4B5FD] shadow-sm'
            : 'bg-white dark:bg-[#334155] border-slate/30 dark:border-[#475569]/30 text-[#0F172A] dark:text-white hover:bg-slate/5 dark:hover:bg-[#475569]/30 hover:border-primary/30 dark:hover:border-[#2563EB]/50'
        )}
      >
        <FunnelIcon className="h-4 w-4 mr-2" />
        Filters
        {hasActiveFilters && (
          <span className="ml-2 px-2.5 py-0.5 text-xs font-semibold bg-[#2563EB] text-white rounded-full">
            {Object.values(filters).filter(Boolean).length}
          </span>
        )}
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-[#1E293B] rounded-xl shadow-lg border border-slate/20 dark:border-[#475569]/30 z-20 p-5">
            <div className="space-y-5">
              {/* Age Group */}
              <div>
                <label className="block text-sm font-semibold text-[#1E3A8A] dark:text-white mb-2.5" style={{ fontWeight: 600 }}>
                  Age Group
                </label>
                <select
                  value={filters.age_group || ''}
                  onChange={(e) => handleChange('age_group', e.target.value)}
                  className="w-full px-3 py-2.5 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                >
                  <option value="" className="text-[#0F172A] dark:text-white bg-white dark:bg-[#334155]">All</option>
                  {ageGroups.map((age) => (
                    <option key={age} value={age} className="text-[#0F172A] dark:text-white bg-white dark:bg-[#334155]">
                      {age.charAt(0).toUpperCase() + age.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              {/* Region */}
              <div>
                <label className="block text-sm font-semibold text-[#1E3A8A] dark:text-white mb-2.5" style={{ fontWeight: 600 }}>
                  Region
                </label>
                <input
                  type="text"
                  value={filters.region || ''}
                  onChange={(e) => handleChange('region', e.target.value)}
                  placeholder="Enter region..."
                  className="w-full px-3 py-2.5 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white placeholder-[#64748B] dark:placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                />
              </div>

              {/* Diagnosis */}
              <div>
                <label className="block text-sm font-semibold text-[#1E3A8A] dark:text-white mb-2.5" style={{ fontWeight: 600 }}>
                  Diagnosis
                </label>
                <input
                  type="text"
                  value={filters.diagnosis || ''}
                  onChange={(e) => handleChange('diagnosis', e.target.value)}
                  placeholder="Enter diagnosis..."
                  className="w-full px-3 py-2.5 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white placeholder-[#64748B] dark:placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                />
              </div>

              {/* Time Range */}
              <div>
                <label 
                  htmlFor="time-range-filter"
                  className="block text-sm font-semibold text-[#1E3A8A] dark:text-white mb-2.5" 
                  style={{ fontWeight: 600 }}
                >
                  Time Range
                </label>
                <select
                  id="time-range-filter"
                  value={filters.time_range_days || ''}
                  onChange={(e) =>
                    handleChange('time_range_days', e.target.value ? parseInt(e.target.value) : undefined)
                  }
                  className="w-full px-3 py-2.5 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
                  aria-label="Filter cases by time range"
                >
                  <option value="" className="text-[#0F172A] dark:text-white bg-white dark:bg-[#334155]">All time</option>
                  {timeRanges.map((range) => (
                    <option key={range.value} value={range.value} className="text-[#0F172A] dark:text-white bg-white dark:bg-[#334155]">
                      {range.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Score Threshold */}
              <div>
                <label 
                  htmlFor="similarity-score-filter"
                  className="block text-sm font-semibold text-[#1E3A8A] dark:text-white mb-2.5" 
                  style={{ fontWeight: 600 }}
                >
                  Min Similarity Score: {filters.score_threshold ? (filters.score_threshold * 100).toFixed(0) + '%' : '0%'}
                </label>
                <input
                  id="similarity-score-filter"
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={filters.score_threshold || 0}
                  onChange={(e) => handleChange('score_threshold', parseFloat(e.target.value))}
                  className="w-full accent-[#2563EB] dark:accent-[#60A5FA] focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
                  aria-label={`Minimum similarity score: ${filters.score_threshold ? (filters.score_threshold * 100).toFixed(0) : 0} percent`}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={filters.score_threshold ? Math.round(filters.score_threshold * 100) : 0}
                />
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-3">
                <button
                  type="button"
                  onClick={onReset}
                  className="flex-1 px-4 py-2.5 text-sm font-medium text-[#0F172A] dark:text-white bg-slate/10 dark:bg-[#475569]/30 rounded-lg hover:bg-slate/20 dark:hover:bg-[#475569]/40 transition-all"
                >
                  Reset
                </button>
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="flex-1 px-4 py-2.5 text-sm font-semibold text-white bg-[#2563EB] dark:bg-[#3B82F6] rounded-lg hover:bg-[#1E3A8A] dark:hover:bg-[#2563EB] shadow-sm hover:shadow-md transition-all duration-200"
                >
                  Apply
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

