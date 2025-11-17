/**
 * AnalyticsFilters Component
 * 
 * Filter controls for time range, region, and disease type
 */

import { CalendarIcon, MapPinIcon, BeakerIcon } from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

export interface AnalyticsFilterOptions {
  timeRange: {
    start: string;
    end: string;
  };
  region?: string;
  diseaseType?: string;
  timeGranularity?: 'daily' | 'weekly' | 'monthly' | 'seasonal';
}

interface AnalyticsFiltersProps {
  filters: AnalyticsFilterOptions;
  onFiltersChange: (filters: AnalyticsFilterOptions) => void;
  availableRegions?: string[];
  availableDiseases?: string[];
  className?: string;
}

export function AnalyticsFilters({
  filters,
  onFiltersChange,
  availableRegions = [],
  availableDiseases = [],
  className = '',
}: AnalyticsFiltersProps) {
  const handleTimeRangeChange = (field: 'start' | 'end', value: string) => {
    onFiltersChange({
      ...filters,
      timeRange: {
        ...filters.timeRange,
        [field]: value,
      },
    });
  };

  const handleRegionChange = (region: string) => {
    onFiltersChange({
      ...filters,
      region: region || undefined,
    });
  };

  const handleDiseaseChange = (disease: string) => {
    onFiltersChange({
      ...filters,
      diseaseType: disease || undefined,
    });
  };

  const handleGranularityChange = (granularity: 'daily' | 'weekly' | 'monthly' | 'seasonal') => {
    onFiltersChange({
      ...filters,
      timeGranularity: granularity,
    });
  };

  const resetFilters = () => {
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);

    onFiltersChange({
      timeRange: {
        start: thirtyDaysAgo.toISOString().split('T')[0],
        end: today.toISOString().split('T')[0],
      },
      region: undefined,
      diseaseType: undefined,
      timeGranularity: 'weekly',
    });
  };

  return (
    <div className={clsx('bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30 p-4', className)}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Time Range */}
        <div>
          <label htmlFor="analytics-start-date" className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
            <CalendarIcon className="h-4 w-4 inline mr-1" aria-hidden="true" />
            Time Range
          </label>
          <div className="space-y-2">
            <input
              id="analytics-start-date"
              type="date"
              value={filters.timeRange.start}
              onChange={(e) => handleTimeRangeChange('start', e.target.value)}
              className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
              aria-label="Filter start date"
            />
            <input
              id="analytics-end-date"
              type="date"
              value={filters.timeRange.end}
              onChange={(e) => handleTimeRangeChange('end', e.target.value)}
              className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
              aria-label="Filter end date"
            />
          </div>
        </div>

        {/* Region */}
        <div>
          <label htmlFor="analytics-region-filter" className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
            <MapPinIcon className="h-4 w-4 inline mr-1" aria-hidden="true" />
            Region
          </label>
          <select
            id="analytics-region-filter"
            value={filters.region || ''}
            onChange={(e) => handleRegionChange(e.target.value)}
            className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
            aria-label="Filter by region"
          >
            <option value="">All Regions</option>
            {availableRegions.map((region) => (
              <option key={region} value={region}>
                {region}
              </option>
            ))}
          </select>
        </div>

        {/* Disease Type */}
        <div>
          <label htmlFor="analytics-disease-filter" className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
            <BeakerIcon className="h-4 w-4 inline mr-1" aria-hidden="true" />
            Disease Type
          </label>
          <select
            id="analytics-disease-filter"
            value={filters.diseaseType || ''}
            onChange={(e) => handleDiseaseChange(e.target.value)}
            className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
            aria-label="Filter by disease type"
          >
            <option value="">All Diseases</option>
            {availableDiseases.map((disease) => (
              <option key={disease} value={disease}>
                {disease}
              </option>
            ))}
          </select>
        </div>

        {/* Time Granularity */}
        <div>
          <label htmlFor="analytics-granularity-filter" className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
            Granularity
          </label>
          <select
            id="analytics-granularity-filter"
            value={filters.timeGranularity || 'weekly'}
            onChange={(e) => handleGranularityChange(e.target.value as any)}
            className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
            aria-label="Select time granularity"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="seasonal">Seasonal</option>
          </select>
        </div>
      </div>

      {/* Reset Button */}
      <div className="mt-4 flex justify-end">
        <button
          type="button"
          onClick={resetFilters}
          className="px-4 py-2 text-sm font-medium text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
          aria-label="Reset all analytics filters"
        >
          Reset Filters
        </button>
      </div>
    </div>
  );
}

