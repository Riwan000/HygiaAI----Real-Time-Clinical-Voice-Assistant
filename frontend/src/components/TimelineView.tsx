/**
 * TimelineView Component
 * 
 * Interactive timeline visualization for patient case history
 */

import { useState, useEffect } from 'react';
import {
  CalendarIcon,
  BeakerIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowDownTrayIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';
import type { Case, CaseMetadata } from '../types';

export interface TimelineEvent {
  id: string;
  type: 'diagnosis' | 'treatment' | 'followup' | 'lab_result' | 'outcome' | 'recurrence';
  timestamp: string;
  title: string;
  description: string;
  metadata?: {
    diagnosis?: string;
    treatment?: string;
    outcome?: string;
    severity?: 'low' | 'medium' | 'high';
    effectiveness?: number; // 0-100
  };
  case?: Case;
}

interface TimelineViewProps {
  events: TimelineEvent[];
  patientId?: string;
  showFilters?: boolean;
  showExport?: boolean;
  onEventClick?: (event: TimelineEvent) => void;
  className?: string;
}

export function TimelineView({
  events,
  patientId,
  showFilters = true,
  showExport = true,
  onEventClick,
  className = '',
}: TimelineViewProps) {
  const [filteredEvents, setFilteredEvents] = useState<TimelineEvent[]>(events);
  const [selectedEventTypes, setSelectedEventTypes] = useState<Set<string>>(
    new Set(['diagnosis', 'treatment', 'followup', 'lab_result', 'outcome', 'recurrence'])
  );
  const [dateRange, setDateRange] = useState<{ start: string; end: string }>({
    start: '',
    end: '',
  });

  // Sort events by timestamp
  const sortedEvents = [...filteredEvents].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  /**
   * Get event type icon
   */
  const getEventIcon = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'diagnosis':
        return BeakerIcon;
      case 'treatment':
        return BeakerIcon;
      case 'followup':
        return CalendarIcon;
      case 'lab_result':
        return DocumentTextIcon;
      case 'outcome':
        return CheckCircleIcon;
      case 'recurrence':
        return ExclamationTriangleIcon;
      default:
        return CalendarIcon;
    }
  };

  /**
   * Get event type color
   */
  const getEventColor = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'diagnosis':
        return 'bg-blue-500 dark:bg-blue-600';
      case 'treatment':
        return 'bg-green-500 dark:bg-green-600';
      case 'followup':
        return 'bg-purple-500 dark:bg-purple-600';
      case 'lab_result':
        return 'bg-yellow-500 dark:bg-yellow-600';
      case 'outcome':
        return 'bg-emerald-500 dark:bg-emerald-600';
      case 'recurrence':
        return 'bg-red-500 dark:bg-red-600';
      default:
        return 'bg-gray-500 dark:bg-gray-600';
    }
  };

  /**
   * Format date
   */
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  /**
   * Apply filters
   */
  const applyFilters = () => {
    let filtered = [...events];

    // Filter by event type
    filtered = filtered.filter((event) => selectedEventTypes.has(event.type));

    // Filter by date range
    if (dateRange.start) {
      filtered = filtered.filter(
        (event) => new Date(event.timestamp) >= new Date(dateRange.start)
      );
    }
    if (dateRange.end) {
      filtered = filtered.filter(
        (event) => new Date(event.timestamp) <= new Date(dateRange.end)
      );
    }

    setFilteredEvents(filtered);
  };

  /**
   * Toggle event type filter
   */
  const toggleEventType = (type: string) => {
    setSelectedEventTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  /**
   * Reset filters
   */
  const resetFilters = () => {
    setSelectedEventTypes(
      new Set(['diagnosis', 'treatment', 'followup', 'lab_result', 'outcome', 'recurrence'])
    );
    setDateRange({ start: '', end: '' });
    setFilteredEvents(events);
  };

  /**
   * Export timeline
   */
  const handleExport = () => {
    // Create a text representation of the timeline
    const timelineText = sortedEvents
      .map((event) => {
        return `${formatDate(event.timestamp)} - ${event.type.toUpperCase()}\n${event.title}\n${event.description}\n\n`;
      })
      .join('');

    const blob = new Blob([timelineText], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `timeline_${patientId || 'patient'}_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  // Apply filters when they change
  useEffect(() => {
    applyFilters();
  }, [selectedEventTypes, dateRange.start, dateRange.end, events]);

  const eventTypes: Array<{ type: TimelineEvent['type']; label: string }> = [
    { type: 'diagnosis', label: 'Diagnosis' },
    { type: 'treatment', label: 'Treatment' },
    { type: 'followup', label: 'Follow-up' },
    { type: 'lab_result', label: 'Lab Result' },
    { type: 'outcome', label: 'Outcome' },
    { type: 'recurrence', label: 'Recurrence' },
  ];

  return (
    <div 
      className={clsx('bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30', className)}
      role="region"
      aria-label="Case timeline"
    >
      {/* Header */}
      <div className="p-6 border-b border-slate/20 dark:border-[#475569]/30">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-semibold text-[#1E3A8A] dark:text-white mb-2" style={{ fontWeight: 600 }}>
              Case Timeline
            </h2>
            {patientId && (
              <p className="text-sm text-[#64748B] dark:text-[#94A3B8]">
                Patient ID: {patientId}
              </p>
            )}
          </div>

          {showExport && (
            <button
              type="button"
              onClick={handleExport}
              className="px-4 py-2 text-sm font-medium text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 rounded-lg transition-colors flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
              aria-label="Export timeline"
            >
              <ArrowDownTrayIcon className="h-4 w-4" aria-hidden="true" />
              <span>Export</span>
            </button>
          )}
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="space-y-4">
            {/* Event Type Filters */}
            <div>
              <label className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
                <FunnelIcon className="h-4 w-4 inline mr-1" aria-hidden="true" />
                Event Types
              </label>
              <div className="flex flex-wrap gap-2">
                {eventTypes.map(({ type, label }) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => {
                      toggleEventType(type);
                      setTimeout(applyFilters, 0);
                    }}
                    className={clsx(
                      'px-3 py-1.5 text-xs font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2',
                      selectedEventTypes.has(type)
                        ? 'bg-[#2563EB] dark:bg-[#3B82F6] text-white'
                        : 'bg-[#F8FAFC] dark:bg-[#334155] text-[#64748B] dark:text-[#94A3B8] hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30'
                    )}
                    aria-label={`${selectedEventTypes.has(type) ? 'Hide' : 'Show'} ${label} events`}
                    aria-pressed={selectedEventTypes.has(type)}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Date Range Filters */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="timeline-start-date" className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
                  Start Date
                </label>
                <input
                  id="timeline-start-date"
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => {
                    setDateRange({ ...dateRange, start: e.target.value });
                    setTimeout(applyFilters, 0);
                  }}
                  className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
                  aria-label="Filter timeline by start date"
                />
              </div>
              <div>
                <label htmlFor="timeline-end-date" className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
                  End Date
                </label>
                <input
                  id="timeline-end-date"
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => {
                    setDateRange({ ...dateRange, end: e.target.value });
                    setTimeout(applyFilters, 0);
                  }}
                  className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
                  aria-label="Filter timeline by end date"
                />
              </div>
            </div>

            <button
              type="button"
              onClick={resetFilters}
              className="text-sm text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:underline focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2 rounded"
              aria-label="Reset timeline filters"
            >
              Reset Filters
            </button>
          </div>
        )}
      </div>

      {/* Timeline */}
      <div className="p-6">
        {sortedEvents.length === 0 ? (
          <div className="text-center py-12">
            <CalendarIcon className="h-12 w-12 text-[#64748B] dark:text-[#94A3B8] mx-auto mb-3" aria-hidden="true" />
            <p className="text-[#64748B] dark:text-[#94A3B8]">No timeline events found</p>
          </div>
        ) : (
          <div className="relative">
            {/* Timeline Line */}
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-[#64748B]/30 dark:bg-[#475569]/30" />

            {/* Events */}
            <div className="space-y-8">
              {sortedEvents.map((event, index) => {
                const Icon = getEventIcon(event.type);
                const isLast = index === sortedEvents.length - 1;

                return (
                  <div
                    key={event.id}
                    className="relative flex items-start space-x-4 cursor-pointer hover:opacity-80 transition-opacity focus-within:outline-none focus-within:ring-2 focus-within:ring-[#2563EB] focus-within:ring-offset-2 rounded"
                    onClick={() => onEventClick?.(event)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onEventClick?.(event);
                      }
                    }}
                    role="button"
                    tabIndex={0}
                    aria-label={`${event.type} event: ${event.title} on ${formatDate(event.timestamp)}`}
                  >
                    {/* Timeline Dot */}
                    <div className="relative z-10 flex-shrink-0">
                      <div
                        className={clsx(
                          'w-16 h-16 rounded-full flex items-center justify-center text-white shadow-lg',
                          getEventColor(event.type)
                        )}
                      >
                        <Icon className="h-6 w-6" aria-hidden="true" />
                      </div>
                    </div>

                    {/* Event Content */}
                    <div className="flex-1 pb-8">
                      <div className="bg-[#F8FAFC] dark:bg-[#334155] rounded-lg border border-slate/20 dark:border-[#475569]/30 p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between mb-2">
                          <div>
                            <div className="flex items-center space-x-2 mb-1">
                              <span className="px-2 py-0.5 text-xs font-semibold bg-[#2563EB]/10 dark:bg-[#2563EB]/20 text-[#2563EB] dark:text-[#60A5FA] rounded uppercase">
                                {event.type}
                              </span>
                              {event.metadata?.severity && (
                                <span
                                  className={clsx(
                                    'px-2 py-0.5 text-xs font-semibold rounded uppercase',
                                    event.metadata.severity === 'high'
                                      ? 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-300'
                                      : event.metadata.severity === 'medium'
                                      ? 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-300'
                                      : 'bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300'
                                  )}
                                >
                                  {event.metadata.severity}
                                </span>
                              )}
                            </div>
                            <h3 className="text-lg font-semibold text-[#1E3A8A] dark:text-white mb-1" style={{ fontWeight: 600 }}>
                              {event.title}
                            </h3>
                            <p className="text-sm text-[#64748B] dark:text-[#94A3B8] mb-2">
                              {formatDate(event.timestamp)}
                            </p>
                          </div>
                        </div>

                        <p className="text-sm text-[#0F172A] dark:text-white mb-3">
                          {event.description}
                        </p>

                        {/* Metadata */}
                        {event.metadata && (
                          <div className="mt-3 pt-3 border-t border-slate/20 dark:border-[#475569]/30 space-y-2">
                            {event.metadata.diagnosis && (
                              <div className="flex items-center text-sm">
                                <BeakerIcon className="h-4 w-4 text-[#64748B] dark:text-[#94A3B8] mr-2" aria-hidden="true" />
                                <span className="text-[#64748B] dark:text-[#94A3B8]">
                                  <strong>Diagnosis:</strong> {event.metadata.diagnosis}
                                </span>
                              </div>
                            )}
                            {event.metadata.treatment && (
                              <div className="flex items-center text-sm">
                                <BeakerIcon className="h-4 w-4 text-[#64748B] dark:text-[#94A3B8] mr-2" aria-hidden="true" />
                                <span className="text-[#64748B] dark:text-[#94A3B8]">
                                  <strong>Treatment:</strong> {event.metadata.treatment}
                                </span>
                              </div>
                            )}
                            {event.metadata.outcome && (
                              <div className="flex items-center text-sm">
                                <CheckCircleIcon className="h-4 w-4 text-[#64748B] dark:text-[#94A3B8] mr-2" aria-hidden="true" />
                                <span className="text-[#64748B] dark:text-[#94A3B8]">
                                  <strong>Outcome:</strong> {event.metadata.outcome}
                                </span>
                              </div>
                            )}
                            {event.metadata.effectiveness !== undefined && (
                              <div className="flex items-center text-sm">
                                <span className="text-[#64748B] dark:text-[#94A3B8] mr-2">
                                  <strong>Effectiveness:</strong>
                                </span>
                                <div className="flex-1 bg-[#64748B]/20 dark:bg-[#475569]/30 rounded-full h-2 max-w-xs">
                                  <div
                                    className={clsx(
                                      'h-2 rounded-full',
                                      event.metadata.effectiveness >= 70
                                        ? 'bg-green-500 dark:bg-green-400'
                                        : event.metadata.effectiveness >= 40
                                        ? 'bg-yellow-500 dark:bg-yellow-400'
                                        : 'bg-red-500 dark:bg-red-400'
                                    )}
                                    style={{ width: `${event.metadata.effectiveness}%` }}
                                  />
                                </div>
                                <span className="text-xs text-[#64748B] dark:text-[#94A3B8] ml-2">
                                  {event.metadata.effectiveness}%
                                </span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

