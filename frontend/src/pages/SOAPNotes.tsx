/**
 * SOAP Notes Page
 * 
 * Displays list of SOAP notes with viewer and management capabilities.
 */

import { useState, useEffect } from 'react';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { SOAPNoteViewer } from '../components/SOAPNoteViewer';
import { Loading, LoadingOverlay } from '../components/Loading';
import { ClinicalMemoryService } from '../services/clinicalMemoryService';
import type { SOAPNote, Case, CaseMetadata, RecallResponse } from '../types';
import { DocumentTextIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

interface SOAPNoteItem {
  id: string;
  case_id: string;
  patient_id: string;
  soap_note: SOAPNote;
  metadata: CaseMetadata;
  generated_at: string;
}

export function SOAPNotes() {
  const [soapNotes, setSoapNotes] = useState<SOAPNoteItem[]>([]);
  const [selectedNote, setSelectedNote] = useState<SOAPNoteItem | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  /**
   * Fetch SOAP notes
   */
  const fetchSOAPNotes = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch SOAP notes from API
      // The API will return SOAP notes from stored cases
      // Note: API limit is maximum 20
      // Using a generic query that matches all clinical cases
      const response = await ClinicalMemoryService.recallSimilarCases({
        query_text: 'clinical case patient consultation', // Generic query to match all cases
        limit: 20, // Maximum allowed by API
        score_threshold: 0.0, // Low threshold to get all cases
      });

      if (response.success && response.data) {
        const recallData = response.data as RecallResponse;
        
        // Transform API response to SOAPNoteItem format
        const notes: SOAPNoteItem[] = recallData.similar_cases
          .filter(item => item.case_data?.soap_note) // Only include cases with SOAP notes
          .map((item, index) => ({
            id: item.case_id,
            case_id: item.case_id,
            patient_id: item.patient_id || `patient_${index + 1}`,
            soap_note: item.case_data!.soap_note!,
            metadata: {
              ...item.metadata,
              timestamp: item.metadata.timestamp || new Date().toISOString(),
            },
            generated_at: item.metadata.timestamp || new Date().toISOString(),
          }));

        setSoapNotes(notes);
      } else {
        setError(response.error || 'Failed to fetch SOAP notes');
        setSoapNotes([]);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch SOAP notes');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSOAPNotes();
  }, []);

  /**
   * Filter notes by search query
   */
  const filteredNotes = soapNotes.filter((note) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      note.patient_id.toLowerCase().includes(query) ||
      note.case_id.toLowerCase().includes(query) ||
      note.soap_note.subjective.toLowerCase().includes(query) ||
      note.soap_note.assessment.toLowerCase().includes(query) ||
      note.metadata.diagnosis?.toLowerCase().includes(query) ||
      false
    );
  });

  /**
   * Format date
   */
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <Breadcrumbs items={[{ name: 'SOAP Notes' }]} />

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-[#1E3A8A] dark:text-white mb-3 font-heading" style={{ fontWeight: 600 }}>
          SOAP Notes
        </h1>
        <p className="text-[#64748B] dark:text-[#94A3B8] text-base">
          View, edit, and export structured clinical documentation
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Notes List */}
        <div className="lg:col-span-1">
          <div className="bg-white dark:bg-[#1E293B] rounded-2xl shadow-sm border border-slate/20 dark:border-[#475569]/30 p-6">
            {/* Search */}
            <div className="mb-4">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-[#64748B] dark:text-[#94A3B8]" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search SOAP notes..."
                  className="w-full pl-10 pr-4 py-2.5 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white placeholder-[#64748B] dark:placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30 focus:border-[#2563EB] transition-all"
                />
              </div>
            </div>

            {/* Notes List */}
            {isLoading ? (
              <Loading size="sm" />
            ) : error ? (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
              </div>
            ) : filteredNotes.length === 0 ? (
              <div className="text-center py-8">
                <DocumentTextIcon className="h-12 w-12 text-[#64748B] dark:text-[#94A3B8] mx-auto mb-3" />
                <p className="text-sm text-[#64748B] dark:text-[#94A3B8]">
                  {searchQuery ? 'No notes found matching your search' : 'No SOAP notes available'}
                </p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {filteredNotes.map((note) => (
                  <button
                    key={note.id}
                    type="button"
                    onClick={() => setSelectedNote(note)}
                    className={clsx(
                      'w-full text-left p-4 rounded-lg border transition-all',
                      selectedNote?.id === note.id
                        ? 'border-[#2563EB] dark:border-[#60A5FA] bg-[#2563EB]/5 dark:bg-[#2563EB]/10'
                        : 'border-slate/20 dark:border-[#475569]/30 hover:border-[#2563EB]/30 dark:hover:border-[#60A5FA]/30 bg-white dark:bg-[#1E293B]'
                    )}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="text-sm font-semibold text-[#1E3A8A] dark:text-white">
                          Case {note.case_id}
                        </p>
                        <p className="text-xs text-[#64748B] dark:text-[#94A3B8]">
                          Patient: {note.patient_id}
                        </p>
                      </div>
                      <DocumentTextIcon className="h-5 w-5 text-[#64748B] dark:text-[#94A3B8] flex-shrink-0" />
                    </div>
                    {note.metadata.diagnosis && (
                      <p className="text-xs text-[#64748B] dark:text-[#94A3B8] mb-2">
                        {note.metadata.diagnosis}
                      </p>
                    )}
                    <p className="text-xs text-[#64748B] dark:text-[#94A3B8]">
                      {formatDate(note.generated_at)}
                    </p>
                    <div className="mt-2 text-xs text-[#64748B] dark:text-[#94A3B8] line-clamp-2">
                      <strong>S:</strong> {note.soap_note.subjective.substring(0, 60)}...
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* SOAP Note Viewer */}
        <div className="lg:col-span-2">
          {selectedNote ? (
            <SOAPNoteViewer
              soapNote={selectedNote.soap_note}
              patientInfo={{
                id: selectedNote.patient_id,
                age: selectedNote.metadata.age_group,
              }}
              caseMetadata={selectedNote.metadata}
              editable={true}
              showVersionHistory={true}
              showAnnotations={true}
              versionHistory={[
                {
                  version: 1,
                  timestamp: selectedNote.generated_at,
                  changes: 'Initial SOAP note generation',
                },
              ]}
              annotations={[]}
              onSave={async (updatedNote) => {
                // In a real implementation, this would call an API to save the updated note
                console.log('Saving updated SOAP note:', updatedNote);
                // Update local state
                setSoapNotes((prev) =>
                  prev.map((note) =>
                    note.id === selectedNote.id
                      ? { ...note, soap_note: updatedNote }
                      : note
                  )
                );
                setSelectedNote({ ...selectedNote, soap_note: updatedNote });
              }}
            />
          ) : (
            <div className="bg-white dark:bg-[#1E293B] rounded-2xl shadow-sm border border-slate/20 dark:border-[#475569]/30 p-16 text-center">
              <DocumentTextIcon className="h-16 w-16 text-[#64748B] dark:text-[#94A3B8] mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-[#1E3A8A] dark:text-white mb-2">
                Select a SOAP Note
              </h3>
              <p className="text-sm text-[#64748B] dark:text-[#94A3B8]">
                Choose a SOAP note from the list to view details
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Default export for compatibility
export default SOAPNotes;
