/**
 * Analytics Page
 * 
 * Comprehensive analytics dashboard with trends, clusters, heatmaps, and outbreak alerts
 */

import { useState, useEffect } from 'react';
import { Breadcrumbs } from '../components/Breadcrumbs';
import {
  TrendChart,
  ClusterMap,
  HeatmapView,
  OutbreakAlert,
  AnalyticsFilters,
  Loading,
} from '../components';
import { ClinicalMemoryService } from '../services/clinicalMemoryService';
import type {
  TrendDataPoint,
  ClusterData,
  HeatmapData,
  OutbreakAlertData,
  FilterOptions as AnalyticsFilterOptions,
} from '../components';
import { ChartBarIcon } from '@heroicons/react/24/outline';

export function Analytics() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Filter state
  const [filters, setFilters] = useState<AnalyticsFilterOptions>(() => {
    const today = new Date();
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);
    
    return {
      timeRange: {
        start: thirtyDaysAgo.toISOString().split('T')[0],
        end: today.toISOString().split('T')[0],
      },
      timeGranularity: 'weekly',
    };
  });

  // Data state
  const [trendData, setTrendData] = useState<TrendDataPoint[]>([]);
  const [clusterData, setClusterData] = useState<ClusterData[]>([]);
  const [heatmapData, setHeatmapData] = useState<HeatmapData[]>([]);
  const [outbreakAlerts, setOutbreakAlerts] = useState<OutbreakAlertData[]>([]);
  const [availableRegions, setAvailableRegions] = useState<string[]>([]);
  const [availableDiseases, setAvailableDiseases] = useState<string[]>([]);

  /**
   * Fetch analytics data
   */
  const fetchAnalyticsData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch temporal clustering data
      const clusteringResponse = await ClinicalMemoryService.performTemporalClustering({
        time_granularity: filters.timeGranularity || 'weekly',
        start_time: filters.timeRange.start,
        end_time: filters.timeRange.end,
        region: filters.region,
        min_cluster_size: 3,
      });

      if (clusteringResponse.success && clusteringResponse.data) {
        // Convert clusters to ClusterData format
        const clusters: ClusterData[] = clusteringResponse.data.clusters.map((cluster: any) => ({
          cluster_id: cluster.cluster_id || cluster.id || '',
          time_window: cluster.time_window || '',
          case_count: cluster.case_count || 0,
          characteristics: cluster.characteristics || {
            symptoms: [],
            diagnoses: [],
            locations: [],
          },
          pattern_insights: cluster.pattern_insights || [],
        }));
        setClusterData(clusters);

        // Generate trend data from clusters
        const trendPoints: TrendDataPoint[] = clusters.map((cluster) => ({
          date: cluster.time_window,
          value: cluster.case_count,
          label: cluster.characteristics.diagnoses[0] || 'Unknown',
        }));
        setTrendData(trendPoints);
      }

      // Fetch regional analytics if region is selected
      if (filters.region) {
        const analyticsResponse = await ClinicalMemoryService.getRegionalAnalytics({
          region: filters.region,
          period_days: Math.ceil(
            (new Date(filters.timeRange.end).getTime() -
              new Date(filters.timeRange.start).getTime()) /
              (1000 * 60 * 60 * 24)
          ),
          compare_with_previous: true,
        });

        if (analyticsResponse.success && analyticsResponse.data) {
          // Convert disease trends to heatmap data
          const heatmap: HeatmapData[] = analyticsResponse.data.disease_trends.map(
            (trend: any) => ({
              clinic: filters.region || 'Unknown',
              disease: trend.disease || trend.disease_name || 'Unknown',
              cases: trend.current_count || trend.current_frequency || 0,
              severity:
                trend.change_percentage && trend.change_percentage > 20
                  ? 'high'
                  : trend.change_percentage && trend.change_percentage > 10
                  ? 'medium'
                  : 'low',
            })
          );
          setHeatmapData(heatmap);

          // Set outbreak alerts
          const alerts: OutbreakAlertData[] = analyticsResponse.data.outbreak_alerts.map(
            (alert: any) => ({
              disease: alert.disease || alert.disease_name || 'Unknown',
              severity: alert.severity || 'low',
              cases: alert.cases || 0,
              recommendation: alert.recommendation || 'Monitor closely',
              region: filters.region,
            })
          );
          setOutbreakAlerts(alerts);

          // Extract available diseases
          const diseases = analyticsResponse.data.disease_trends.map(
            (trend: any) => trend.disease || trend.disease_name
          );
          setAvailableDiseases([...new Set(diseases)]);
        }
      } else {
        // If no region selected, clear region-specific data
        setHeatmapData([]);
        setOutbreakAlerts([]);
      }
    } catch (err: any) {
      console.error('Error fetching analytics data:', err);
      setError(err?.message || 'Failed to load analytics data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();
  }, [filters]);

  const handleDismissAlert = (disease: string) => {
    setOutbreakAlerts((prev) => prev.filter((alert) => alert.disease !== disease));
  };

  return (
    <div className="max-w-7xl mx-auto">
      <Breadcrumbs items={[{ name: 'Trends & Analytics' }]} />

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-3">
          <ChartBarIcon className="h-8 w-8 text-[#2563EB] dark:text-[#60A5FA]" />
          <h1 className="text-3xl font-semibold text-[#1E3A8A] dark:text-white font-heading" style={{ fontWeight: 600 }}>
            Trends & Analytics
          </h1>
        </div>
        <p className="text-[#64748B] dark:text-[#94A3B8] text-base">
          Interactive visualizations for disease trends, clusters, and outbreak detection
        </p>
      </div>

      {/* Filters */}
      <div className="mb-6">
        <AnalyticsFilters
          filters={filters}
          onFiltersChange={setFilters}
          availableRegions={availableRegions}
          availableDiseases={availableDiseases}
        />
      </div>

      {/* Error State */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="mb-6">
          <Loading size="lg" message="Loading analytics data..." />
        </div>
      )}

      {/* Outbreak Alerts */}
      {outbreakAlerts.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-[#1E3A8A] dark:text-white mb-4" style={{ fontWeight: 600 }}>
            Outbreak Alerts
          </h2>
          <OutbreakAlert alerts={outbreakAlerts} onDismiss={handleDismissAlert} />
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Trend Chart */}
        <div>
          <h2 className="text-xl font-semibold text-[#1E3A8A] dark:text-white mb-4" style={{ fontWeight: 600 }}>
            Disease Trends
          </h2>
          <TrendChart
            data={trendData}
            title="Cases Over Time"
            yAxisLabel="Number of Cases"
            showConfidenceInterval={true}
            height={400}
          />
        </div>

        {/* Cluster Map */}
        <div>
          <h2 className="text-xl font-semibold text-[#1E3A8A] dark:text-white mb-4" style={{ fontWeight: 600 }}>
            Disease Clusters
          </h2>
          <ClusterMap
            clusters={clusterData}
            title="Temporal Clusters"
            height={400}
            onClusterClick={(clusterId) => {
              console.log('Cluster clicked:', clusterId);
              // Could navigate to cluster details or filter by cluster
            }}
          />
        </div>
      </div>

      {/* Heatmap */}
      {heatmapData.length > 0 && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-[#1E3A8A] dark:text-white mb-4" style={{ fontWeight: 600 }}>
            Clinic-Level Disease Patterns
          </h2>
          <HeatmapView data={heatmapData} height={500} />
        </div>
      )}

      {/* Empty State */}
      {!isLoading && trendData.length === 0 && clusterData.length === 0 && (
        <div className="text-center py-12 bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30">
          <ChartBarIcon className="h-12 w-12 text-[#64748B] dark:text-[#94A3B8] mx-auto mb-3" />
          <p className="text-[#64748B] dark:text-[#94A3B8]">
            No analytics data available for the selected filters.
          </p>
          <p className="text-sm text-[#64748B] dark:text-[#94A3B8] mt-2">
            Try adjusting the time range or selecting a different region.
          </p>
        </div>
      )}
    </div>
  );
}
