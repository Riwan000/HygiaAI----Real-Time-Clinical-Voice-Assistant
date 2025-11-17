/**
 * Case Timeline Page
 * 
 * Displays patient case history with timeline visualization
 */

import { useState, useEffect } from 'react';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { TimelineView } from '../components/TimelineView';
import { TimelineTrend } from '../components/TimelineTrend';
import type { TimelineEvent } from '../components/TimelineView';
import type { TrendMetric } from '../components/TimelineTrend';
import { Loading } from '../components/Loading';
import { ClinicalMemoryService } from '../services/clinicalMemoryService';
import { ClockIcon, UserIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';

export function Timeline() {
  const [patientId, setPatientId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [trendMetrics, setTrendMetrics] = useState<TrendMetric[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);

  /**
   * Fetch timeline data for a patient
   */
  const fetchTimeline = async (id: string) => {
    if (!id.trim()) {
      setError('Please enter a patient ID');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Fetch cases (API limit is 20, we'll filter by patient_id client-side)
      // Note: Ideally we'd have a dedicated timeline endpoint with patient_id filtering
      const response = await ClinicalMemoryService.recallSimilarCases({
        query_text: id, // Use patient ID as query to get relevant cases
        limit: 20, // API limit
        time_range_days: 365, // Last year
      });

      if (response.success && response.data) {
        // Filter cases by patient_id (client-side filtering)
        const patientCases = response.data.similar_cases.filter((caseData: any) => {
          const metadata = caseData.metadata || {};
          const caseId = caseData.case_id || '';
          // Check if patient_id matches or is in case_id
          return caseId.includes(id) || metadata.patient_id === id;
        });

        if (patientCases.length === 0) {
          setError(`No cases found for patient ${id}. Try a different patient ID.`);
          setIsLoading(false);
          return;
        }

        // Convert cases to timeline events
        const events: TimelineEvent[] = [];
        const metrics: TrendMetric[] = [];

        patientCases.forEach((caseData: any, index: number) => {
          const metadata = caseData.metadata || {};
          const timestamp = metadata.timestamp || new Date().toISOString();
          const diagnosis = metadata.diagnosis || 'Unknown';
          const outcome = metadata.outcome || 'Pending';

          // Create diagnosis event
          if (diagnosis && diagnosis !== 'Unknown') {
            events.push({
              id: `diagnosis_${caseData.case_id}`,
              type: 'diagnosis',
              timestamp,
              title: `Diagnosis: ${diagnosis}`,
              description: `Patient diagnosed with ${diagnosis}`,
              metadata: {
                diagnosis,
                severity: outcome.toLowerCase().includes('severe') ? 'high' : 'medium',
              },
            });
          }

          // Create treatment event (if outcome suggests treatment)
          if (outcome && outcome !== 'Pending') {
            events.push({
              id: `treatment_${caseData.case_id}`,
              type: 'treatment',
              timestamp: new Date(new Date(timestamp).getTime() + 24 * 60 * 60 * 1000).toISOString(), // Next day
              title: `Treatment Plan Initiated`,
              description: `Treatment started for ${diagnosis}`,
              metadata: {
                diagnosis,
                treatment: outcome,
                effectiveness: outcome.toLowerCase().includes('improved') ? 75 : outcome.toLowerCase().includes('recovered') ? 90 : 50,
              },
            });

            // Add trend metric
            metrics.push({
              date: timestamp,
              value: outcome.toLowerCase().includes('recovered') ? 90 : outcome.toLowerCase().includes('improved') ? 70 : 50,
              label: outcome,
              type: outcome.toLowerCase().includes('recovered') || outcome.toLowerCase().includes('improved')
                ? 'improvement'
                : outcome.toLowerCase().includes('declined') || outcome.toLowerCase().includes('worse')
                ? 'decline'
                : 'stable',
            });
          }

          // Create outcome event
          if (outcome && outcome !== 'Pending') {
            events.push({
              id: `outcome_${caseData.case_id}`,
              type: 'outcome',
              timestamp: new Date(new Date(timestamp).getTime() + 7 * 24 * 60 * 60 * 1000).toISOString(), // Week later
              title: `Outcome: ${outcome}`,
              description: `Patient outcome: ${outcome}`,
              metadata: {
                diagnosis,
                outcome,
              },
            });
          }

          // Check for recurrence (same diagnosis appearing multiple times)
          const sameDiagnosisCount = events.filter(
            (e) => e.metadata?.diagnosis === diagnosis && e.type === 'diagnosis'
          ).length;
          if (sameDiagnosisCount > 1) {
            events.push({
              id: `recurrence_${caseData.case_id}`,
              type: 'recurrence',
              timestamp,
              title: `Recurrence Detected: ${diagnosis}`,
              description: `This is recurrence #${sameDiagnosisCount} of ${diagnosis}`,
              metadata: {
                diagnosis,
                severity: 'medium',
              },
            });
          }
        });

        setTimelineEvents(events);
        setTrendMetrics(metrics);
      } else {
        setError('No cases found for this patient');
      }
    } catch (err: any) {
      console.error('Error fetching timeline:', err);
      setError(err?.message || 'Failed to load timeline data');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle search
   */
  const handleSearch = () => {
    fetchTimeline(patientId);
  };

  /**
   * Handle event click
   */
  const handleEventClick = (event: TimelineEvent) => {
    setSelectedEvent(event);
    // Could open a modal or navigate to case details
    console.log('Event clicked:', event);
  };

  return (
    <div className="max-w-7xl mx-auto">
      <Breadcrumbs items={[{ name: 'Case Timeline' }]} />

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-3">
          <ClockIcon className="h-8 w-8 text-[#2563EB] dark:text-[#60A5FA]" />
          <h1 className="text-3xl font-semibold text-[#1E3A8A] dark:text-white font-heading" style={{ fontWeight: 600 }}>
            Case Timeline
          </h1>
        </div>
        <p className="text-[#64748B] dark:text-[#94A3B8] text-base">
          View patient case history, treatment progress, and intervention outcomes
        </p>
      </div>

      {/* Patient Search */}
      <div className="mb-6 bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30 p-6">
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
              <UserIcon className="h-4 w-4 inline mr-1" />
              Patient ID
            </label>
            <div className="flex space-x-2">
              <input
                type="text"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Enter patient ID to view timeline"
                className="flex-1 px-4 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white placeholder-[#64748B] dark:placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
              />
              <button
                type="button"
                onClick={handleSearch}
                disabled={isLoading}
                className="px-6 py-2 bg-[#2563EB] dark:bg-[#3B82F6] text-white rounded-lg hover:bg-[#1E3A8A] dark:hover:bg-[#2563EB] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                <MagnifyingGlassIcon className="h-5 w-5" />
                <span>Search</span>
              </button>
            </div>
          </div>
        </div>
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
          <Loading size="lg" message="Loading timeline data..." />
        </div>
      )}

      {/* Timeline and Trends */}
      {!isLoading && timelineEvents.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Timeline View */}
          <div className="lg:col-span-2">
            <TimelineView
              events={timelineEvents}
              patientId={patientId}
              showFilters={true}
              showExport={true}
              onEventClick={handleEventClick}
            />
          </div>

          {/* Trend Visualization */}
          <div className="lg:col-span-1">
            {trendMetrics.length > 0 && (
              <TimelineTrend metrics={trendMetrics} title="Patient Progress" />
            )}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && timelineEvents.length === 0 && patientId && (
        <div className="text-center py-12 bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30">
          <ClockIcon className="h-12 w-12 text-[#64748B] dark:text-[#94A3B8] mx-auto mb-3" />
          <p className="text-[#64748B] dark:text-[#94A3B8]">
            No timeline data found for patient {patientId}
          </p>
          <p className="text-sm text-[#64748B] dark:text-[#94A3B8] mt-2">
            Try searching for a different patient ID or ensure cases exist in the system.
          </p>
        </div>
      )}

      {/* Initial State */}
      {!isLoading && !error && !patientId && (
        <div className="text-center py-12 bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30">
          <UserIcon className="h-12 w-12 text-[#64748B] dark:text-[#94A3B8] mx-auto mb-3" />
          <p className="text-[#64748B] dark:text-[#94A3B8]">
            Enter a patient ID to view their case timeline
          </p>
        </div>
      )}
    </div>
  );
}
