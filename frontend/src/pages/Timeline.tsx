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
  const [isLoadingPatients, setIsLoadingPatients] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [trendMetrics, setTrendMetrics] = useState<TrendMetric[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [availablePatients, setAvailablePatients] = useState<Array<{id: string; caseCount: number; lastVisit: string}>>([]);

  /**
   * Fetch list of available patients
   */
  const fetchAvailablePatients = async () => {
    setIsLoadingPatients(true);
    try {
      // Fetch all cases to extract unique patient IDs
      const response = await ClinicalMemoryService.recallSimilarCases({
        query_text: '', // Empty query to get all cases
        limit: 200, // Get more cases to find all patients
        time_range_days: 365, // Last year
      });

      if (response.success && response.data) {
        const cases = response.data.similar_cases;
        
        // Group cases by patient_id
        const patientMap = new Map<string, {caseCount: number; lastVisit: string}>();
        
        cases.forEach((caseData: any) => {
          // Try multiple locations for patient_id
          const pid = caseData.patient_id || 
                     caseData.case_data?.patient_id ||
                     caseData.metadata?.patient_id ||
                     caseData.case_id?.split('_').slice(-1)[0]; // Extract from case_id if present
          
          if (pid) {
            const existing = patientMap.get(pid) || {caseCount: 0, lastVisit: ''};
            existing.caseCount += 1;
            
            const timestamp = caseData.metadata?.timestamp || 
                            caseData.case_data?.timestamp || 
                            caseData.timestamp || '';
            if (timestamp && timestamp > existing.lastVisit) {
              existing.lastVisit = timestamp;
            }
            
            patientMap.set(pid, existing);
          }
        });
        
        // Convert to array and sort by last visit (most recent first)
        const patients = Array.from(patientMap.entries())
          .map(([id, data]) => ({
            id,
            caseCount: data.caseCount,
            lastVisit: data.lastVisit
          }))
          .sort((a, b) => b.lastVisit.localeCompare(a.lastVisit));
        
        setAvailablePatients(patients);
        
        // Auto-select first patient if none selected
        if (!patientId && patients.length > 0) {
          setPatientId(patients[0].id);
          fetchTimeline(patients[0].id);
        }
      }
    } catch (err: any) {
      console.error('Error fetching patients:', err);
    } finally {
      setIsLoadingPatients(false);
    }
  };

  /**
   * Fetch timeline data for a patient
   */
  const fetchTimeline = async (id: string) => {
    if (!id.trim()) {
      setError('Please select a patient');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Use patient_id filter for accurate timeline retrieval
      const response = await ClinicalMemoryService.recallSimilarCases({
        query_text: '', // Empty query - we're filtering by patient_id
        patient_id: id, // Use patient_id filter for accurate results
        limit: 100, // Get more cases for timeline (increased from 20)
        time_range_days: 365, // Last year
      });

      if (response.success && response.data) {
        const patientCases = response.data.similar_cases;

        if (patientCases.length === 0) {
          setError(`No cases found for patient ${id}. Try a different patient ID.`);
          setIsLoading(false);
          return;
        }

        // Convert cases to timeline events
        const events: TimelineEvent[] = [];
        const metrics: TrendMetric[] = [];

        console.log(`Processing ${patientCases.length} cases for timeline`);

        patientCases.forEach((caseData: any, index: number) => {
          // Try multiple locations for metadata
          const metadata = caseData.metadata || caseData.case_data?.case_metadata || {};
          const caseDataPayload = caseData.case_data || {};
          
          // Get timestamp from multiple locations
          const timestamp = metadata.timestamp || 
                          caseDataPayload.timestamp || 
                          caseData.timestamp || 
                          new Date().toISOString();
          
          // Get diagnosis from multiple locations
          const diagnosis = metadata.diagnosis || 
                          caseDataPayload.diagnosis || 
                          caseData.diagnosis || 
                          null;
          
          // Get outcome from multiple locations
          const outcome = metadata.outcome || 
                         caseDataPayload.outcome || 
                         caseData.outcome || 
                         null;
          
          // Get transcript for description
          const transcript = caseDataPayload.transcript || 
                           caseData.transcript || 
                           '';
          
          // Always create at least one event per case (case record)
          const caseDescription = transcript 
            ? `${transcript.substring(0, 100)}${transcript.length > 100 ? '...' : ''}`
            : `Case visit on ${new Date(timestamp).toLocaleDateString()}`;
          
          // Create a basic case event (always shown)
          events.push({
            id: `case_${caseData.case_id}`,
            type: 'followup', // Use followup as default type
            timestamp,
            title: `Case Visit ${index + 1}`,
            description: caseDescription,
            metadata: {
              diagnosis: diagnosis || undefined,
              outcome: outcome || undefined,
              severity: 'medium',
            },
          });

          // Create diagnosis event if available
          if (diagnosis && diagnosis !== 'Unknown' && diagnosis !== 'null' && diagnosis.trim() !== '') {
            events.push({
              id: `diagnosis_${caseData.case_id}`,
              type: 'diagnosis',
              timestamp,
              title: `Diagnosis: ${diagnosis}`,
              description: `Patient diagnosed with ${diagnosis}`,
              metadata: {
                diagnosis,
                severity: outcome && outcome.toLowerCase().includes('severe') ? 'high' : 'medium',
              },
            });
          }

          // Create treatment event (if outcome suggests treatment)
          if (outcome && outcome !== 'Pending' && outcome !== 'null' && outcome.trim() !== '') {
            events.push({
              id: `treatment_${caseData.case_id}`,
              type: 'treatment',
              timestamp: new Date(new Date(timestamp).getTime() + 24 * 60 * 60 * 1000).toISOString(), // Next day
              title: `Treatment Plan Initiated`,
              description: `Treatment started${diagnosis ? ` for ${diagnosis}` : ''}`,
              metadata: {
                diagnosis: diagnosis || undefined,
                treatment: outcome,
                effectiveness: outcome.toLowerCase().includes('improved') ? 75 : outcome.toLowerCase().includes('recovered') ? 90 : 50,
              },
            });

            // Add trend metric (only if outcome is meaningful)
            if (outcome && outcome !== 'Pending' && outcome !== 'null' && outcome.trim() !== '') {
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
          }

          // Create outcome event if available
          if (outcome && outcome !== 'Pending' && outcome !== 'null' && outcome.trim() !== '') {
            events.push({
              id: `outcome_${caseData.case_id}`,
              type: 'outcome',
              timestamp: new Date(new Date(timestamp).getTime() + 7 * 24 * 60 * 60 * 1000).toISOString(), // Week later
              title: `Outcome: ${outcome}`,
              description: `Patient outcome: ${outcome}`,
              metadata: {
                diagnosis: diagnosis || undefined,
                outcome,
              },
            });
          }

          // Check for recurrence (same diagnosis appearing multiple times)
          if (diagnosis && diagnosis !== 'Unknown') {
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
          }
        });

        console.log(`Created ${events.length} timeline events from ${patientCases.length} cases`);
        console.log(`Created ${metrics.length} trend metrics`);

        // Sort events chronologically by timestamp (oldest first)
        const sortedEvents = [...events].sort((a, b) => {
          const dateA = new Date(a.timestamp).getTime();
          const dateB = new Date(b.timestamp).getTime();
          return dateA - dateB; // Ascending order (oldest first)
        });

        // Sort metrics chronologically as well
        const sortedMetrics = [...metrics].sort((a, b) => {
          const dateA = new Date(a.date).getTime();
          const dateB = new Date(b.date).getTime();
          return dateA - dateB; // Ascending order (oldest first)
        });

        setTimelineEvents(sortedEvents);
        setTrendMetrics(sortedMetrics);
        
        // Clear error if we have events
        if (events.length > 0) {
          setError(null);
        }
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
    if (patientId.trim()) {
      fetchTimeline(patientId.trim());
    }
  };

  /**
   * Handle patient selection
   */
  const handlePatientSelect = (selectedId: string) => {
    setPatientId(selectedId);
    fetchTimeline(selectedId);
  };

  /**
   * Handle event click
   */
  const handleEventClick = (event: TimelineEvent) => {
    setSelectedEvent(event);
    // Could open a modal or navigate to case details
    console.log('Event clicked:', event);
  };

  // Load available patients on mount
  useEffect(() => {
    fetchAvailablePatients();
  }, []);

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

      {/* Patient Selection Section */}
      <div className="mb-6">
        <div className="bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30 p-6">
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <label className="block text-sm font-medium text-[#0F172A] dark:text-white">
                <UserIcon className="h-4 w-4 inline mr-1" />
                Select Patient
              </label>
              {isLoadingPatients && (
                <span className="text-sm text-[#64748B] dark:text-[#94A3B8]">Loading patients...</span>
              )}
            </div>
            
            {availablePatients.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto">
                {availablePatients.map((patient) => (
                  <button
                    key={patient.id}
                    onClick={() => handlePatientSelect(patient.id)}
                    className={`p-3 rounded-lg border text-left transition-colors ${
                      patientId === patient.id
                        ? 'bg-[#2563EB] dark:bg-[#3B82F6] text-white border-[#2563EB]'
                        : 'bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white border-slate/30 dark:border-[#475569]/30 hover:border-[#2563EB]/50'
                    }`}
                  >
                    <div className="font-medium">{patient.id}</div>
                    <div className={`text-xs mt-1 ${
                      patientId === patient.id
                        ? 'text-white/80'
                        : 'text-[#64748B] dark:text-[#94A3B8]'
                    }`}>
                      {patient.caseCount} case{patient.caseCount !== 1 ? 's' : ''}
                      {patient.lastVisit && (
                        <span className="ml-2">
                          • {new Date(patient.lastVisit).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            ) : !isLoadingPatients ? (
              <div className="text-center py-4 text-[#64748B] dark:text-[#94A3B8]">
                No patients found. Cases will appear here once data is available.
              </div>
            ) : null}
            
            {/* Manual Search Option */}
            <div className="mt-4 pt-4 border-t border-slate/20 dark:border-[#475569]/30">
              <label htmlFor="patient-id" className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
                Or Enter Patient ID Manually
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  id="patient-id"
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
