/**
 * SOAP Note Viewer Component
 * 
 * Comprehensive SOAP note viewer with expand/collapse, export, editing, and annotations.
 */

import { useState } from 'react';
import {
  ChevronDownIcon,
  ChevronUpIcon,
  DocumentArrowDownIcon,
  DocumentTextIcon,
  ClipboardDocumentIcon,
  PrinterIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  ChatBubbleLeftRightIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';
import { ClinicalMemoryService } from '../services/clinicalMemoryService';
import type { SOAPNote, CaseMetadata } from '../types';

interface SOAPNoteViewerProps {
  soapNote: SOAPNote;
  patientInfo?: {
    name?: string;
    id?: string;
    age?: string;
    gender?: string;
    dob?: string;
  };
  clinicianInfo?: {
    name?: string;
    title?: string;
    license?: string;
  };
  caseMetadata?: CaseMetadata;
  onEdit?: (updatedNote: SOAPNote) => void;
  onSave?: (note: SOAPNote) => Promise<void>;
  showVersionHistory?: boolean;
  versionHistory?: Array<{
    version: number;
    timestamp: string;
    changes: string;
    editedBy?: string;
  }>;
  showAnnotations?: boolean;
  annotations?: Array<{
    id: string;
    section: 'subjective' | 'objective' | 'assessment' | 'plan';
    text: string;
    author: string;
    timestamp: string;
  }>;
  editable?: boolean;
}

export function SOAPNoteViewer({
  soapNote,
  patientInfo,
  clinicianInfo,
  caseMetadata,
  onEdit,
  onSave,
  showVersionHistory = false,
  versionHistory = [],
  showAnnotations = false,
  annotations = [],
  editable = false,
}: SOAPNoteViewerProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['subjective', 'objective', 'assessment', 'plan'])
  );
  const [isEditing, setIsEditing] = useState(false);
  const [editedNote, setEditedNote] = useState<SOAPNote>(soapNote);
  const [isSaving, setIsSaving] = useState(false);
  const [showAnnotationsPanel, setShowAnnotationsPanel] = useState(false);
  const [showVersionPanel, setShowVersionPanel] = useState(false);
  const [newAnnotation, setNewAnnotation] = useState({ section: 'subjective' as const, text: '' });

  /**
   * Toggle section expansion
   */
  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  };

  /**
   * Expand/collapse all sections
   */
  const toggleAllSections = () => {
    if (expandedSections.size === 4) {
      setExpandedSections(new Set());
    } else {
      setExpandedSections(new Set(['subjective', 'objective', 'assessment', 'plan']));
    }
  };

  /**
   * Start editing
   */
  const handleStartEdit = () => {
    setIsEditing(true);
    setEditedNote({ ...soapNote });
  };

  /**
   * Cancel editing
   */
  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditedNote({ ...soapNote });
  };

  /**
   * Save edited note
   */
  const handleSaveEdit = async () => {
    setIsSaving(true);
    try {
      if (onSave) {
        await onSave(editedNote);
      }
      if (onEdit) {
        onEdit(editedNote);
      }
      setIsEditing(false);
    } catch (error) {
      console.error('Error saving SOAP note:', error);
    } finally {
      setIsSaving(false);
    }
  };

  /**
   * Copy to clipboard
   */
  const handleCopyToClipboard = async () => {
    const text = formatSOAPNoteForCopy(editedNote);
    try {
      await navigator.clipboard.writeText(text);
      // Could show a toast notification here
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  /**
   * Format SOAP note for copy
   */
  const formatSOAPNoteForCopy = (note: SOAPNote): string => {
    return `SOAP NOTE

SUBJECTIVE:
${note.subjective}

OBJECTIVE:
${note.objective}

ASSESSMENT:
${note.assessment}

PLAN:
${note.plan}

${patientInfo ? `Patient: ${patientInfo.name || patientInfo.id || 'N/A'}\n` : ''}
${clinicianInfo ? `Clinician: ${clinicianInfo.name || 'N/A'}\n` : ''}
${caseMetadata?.timestamp ? `Date: ${new Date(caseMetadata.timestamp).toLocaleDateString()}\n` : ''}`;
  };

  /**
   * Print SOAP note
   */
  const handlePrint = () => {
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <title>SOAP Note</title>
            <style>
              body { font-family: Arial, sans-serif; padding: 20px; }
              h1 { color: #1E3A8A; }
              h2 { color: #2563EB; margin-top: 20px; }
              .section { margin-bottom: 20px; }
              .metadata { margin-top: 30px; font-size: 12px; color: #666; }
            </style>
          </head>
          <body>
            <h1>SOAP NOTE</h1>
            ${formatSOAPNoteForPrint(editedNote, patientInfo, clinicianInfo, caseMetadata)}
          </body>
        </html>
      `);
      printWindow.document.close();
      printWindow.print();
    }
  };

  /**
   * Format for print
   */
  const formatSOAPNoteForPrint = (
    note: SOAPNote,
    patient?: SOAPNoteViewerProps['patientInfo'],
    clinician?: SOAPNoteViewerProps['clinicianInfo'],
    metadata?: CaseMetadata
  ): string => {
    return `
      <div class="section">
        <h2>SUBJECTIVE</h2>
        <p>${note.subjective.replace(/\n/g, '<br>')}</p>
      </div>
      <div class="section">
        <h2>OBJECTIVE</h2>
        <p>${note.objective.replace(/\n/g, '<br>')}</p>
      </div>
      <div class="section">
        <h2>ASSESSMENT</h2>
        <p>${note.assessment.replace(/\n/g, '<br>')}</p>
      </div>
      <div class="section">
        <h2>PLAN</h2>
        <p>${note.plan.replace(/\n/g, '<br>')}</p>
      </div>
      <div class="metadata">
        ${patient ? `<p><strong>Patient:</strong> ${patient.name || patient.id || 'N/A'}</p>` : ''}
        ${clinician ? `<p><strong>Clinician:</strong> ${clinician.name || 'N/A'}</p>` : ''}
        ${metadata?.timestamp ? `<p><strong>Date:</strong> ${new Date(metadata.timestamp).toLocaleDateString()}</p>` : ''}
      </div>
    `;
  };

  /**
   * Export to PDF using backend API
   */
  const handleExportPDF = async () => {
    try {
      // Show loading state (you could add a loading indicator here)
      await ClinicalMemoryService.exportSOAPToPDF(
        editedNote,
        patientInfo,
        clinicianInfo
      );
      // Success - file should download automatically
    } catch (error: any) {
      console.error('Error exporting PDF:', error);
      const errorMessage = error?.message || 'Unknown error occurred';
      // Replace \n with actual line breaks for better readability
      const formattedMessage = errorMessage.replace(/\\n/g, '\n');
      alert(`Failed to export PDF:\n\n${formattedMessage}`);
    }
  };

  /**
   * Export to DOCX (would need backend API or client library)
   */
  const handleExportDOCX = async () => {
    // This would typically call a backend API endpoint
    // For now, show a message that this requires backend support
    alert('DOCX export requires backend API support. Please use PDF export or contact support.');
  };

  /**
   * Add annotation
   */
  const handleAddAnnotation = () => {
    if (newAnnotation.text.trim()) {
      // In a real implementation, this would call an API
      const annotation = {
        id: Date.now().toString(),
        section: newAnnotation.section,
        text: newAnnotation.text,
        author: 'Current User', // Would come from auth context
        timestamp: new Date().toISOString(),
      };
      // Add to annotations array (would be managed by parent component)
      setNewAnnotation({ section: 'subjective', text: '' });
    }
  };

  /**
   * Get section annotations
   */
  const getSectionAnnotations = (section: string) => {
    return annotations.filter((a) => a.section === section);
  };

  /**
   * Format date
   */
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString('en-US', {
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

  const sections = [
    { key: 'subjective', label: 'Subjective', content: editedNote.subjective },
    { key: 'objective', label: 'Objective', content: editedNote.objective },
    { key: 'assessment', label: 'Assessment', content: editedNote.assessment },
    { key: 'plan', label: 'Plan', content: editedNote.plan },
  ] as const;

  return (
    <div className="bg-white dark:bg-[#1E293B] rounded-2xl shadow-sm border border-slate/20 dark:border-[#475569]/30">
      {/* Header */}
      <div className="p-6 border-b border-slate/20 dark:border-[#475569]/30">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-semibold text-[#1E3A8A] dark:text-white mb-2" style={{ fontWeight: 600 }}>
              SOAP Note
            </h2>
            {caseMetadata?.timestamp && (
              <p className="text-sm text-[#64748B] dark:text-[#94A3B8]">
                Generated: {formatDate(caseMetadata.timestamp)}
              </p>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2">
            {editable && !isEditing && (
              <button
                type="button"
                onClick={handleStartEdit}
                className="p-2 rounded-lg text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 transition-colors"
                aria-label="Edit SOAP note"
              >
                <PencilIcon className="h-5 w-5" />
              </button>
            )}

            {isEditing && (
              <>
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  className="p-2 rounded-lg text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                  aria-label="Cancel editing"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
                <button
                  type="button"
                  onClick={handleSaveEdit}
                  disabled={isSaving}
                  className="p-2 rounded-lg text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors disabled:opacity-50"
                  aria-label="Save changes"
                >
                  <CheckIcon className="h-5 w-5" />
                </button>
              </>
            )}

            <button
              type="button"
              onClick={handleCopyToClipboard}
              className="p-2 rounded-lg text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 transition-colors"
              aria-label="Copy to clipboard"
            >
              <ClipboardDocumentIcon className="h-5 w-5" />
            </button>

            <button
              type="button"
              onClick={handleExportPDF}
              className="p-2 rounded-lg text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 transition-colors"
              aria-label="Export to PDF"
            >
              <DocumentArrowDownIcon className="h-5 w-5" />
            </button>

            <button
              type="button"
              onClick={handlePrint}
              className="p-2 rounded-lg text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 transition-colors"
              aria-label="Print"
            >
              <PrinterIcon className="h-5 w-5" />
            </button>

            {showAnnotations && (
              <button
                type="button"
                onClick={() => setShowAnnotationsPanel(!showAnnotationsPanel)}
                className={clsx(
                  'p-2 rounded-lg transition-colors',
                  showAnnotationsPanel
                    ? 'text-[#2563EB] dark:text-[#60A5FA] bg-[#2563EB]/10 dark:bg-[#2563EB]/20'
                    : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30'
                )}
                aria-label="Toggle annotations"
              >
                <ChatBubbleLeftRightIcon className="h-5 w-5" />
              </button>
            )}

            {showVersionHistory && (
              <button
                type="button"
                onClick={() => setShowVersionPanel(!showVersionPanel)}
                className={clsx(
                  'p-2 rounded-lg transition-colors',
                  showVersionPanel
                    ? 'text-[#2563EB] dark:text-[#60A5FA] bg-[#2563EB]/10 dark:bg-[#2563EB]/20'
                    : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30'
                )}
                aria-label="Toggle version history"
              >
                <ClockIcon className="h-5 w-5" />
              </button>
            )}
          </div>
        </div>

        {/* Patient & Clinician Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 pt-4 border-t border-slate/20 dark:border-[#475569]/30">
          {patientInfo && (
            <div>
              <h3 className="text-sm font-semibold text-[#1E3A8A] dark:text-white mb-2">Patient Information</h3>
              <div className="space-y-1 text-sm text-[#64748B] dark:text-[#94A3B8]">
                {patientInfo.name && <p><strong>Name:</strong> {patientInfo.name}</p>}
                {patientInfo.id && <p><strong>ID:</strong> {patientInfo.id}</p>}
                {patientInfo.age && <p><strong>Age:</strong> {patientInfo.age}</p>}
                {patientInfo.gender && <p><strong>Gender:</strong> {patientInfo.gender}</p>}
                {patientInfo.dob && <p><strong>DOB:</strong> {patientInfo.dob}</p>}
              </div>
            </div>
          )}

          {clinicianInfo && (
            <div>
              <h3 className="text-sm font-semibold text-[#1E3A8A] dark:text-white mb-2">Clinician Information</h3>
              <div className="space-y-1 text-sm text-[#64748B] dark:text-[#94A3B8]">
                {clinicianInfo.name && <p><strong>Name:</strong> {clinicianInfo.name}</p>}
                {clinicianInfo.title && <p><strong>Title:</strong> {clinicianInfo.title}</p>}
                {clinicianInfo.license && <p><strong>License:</strong> {clinicianInfo.license}</p>}
              </div>
            </div>
          )}
        </div>

        {/* Metadata */}
        {caseMetadata && (
          <div className="mt-4 pt-4 border-t border-slate/20 dark:border-[#475569]/30">
            <div className="flex flex-wrap gap-4 text-xs text-[#64748B] dark:text-[#94A3B8]">
              {caseMetadata.age_group && (
                <span><strong>Age Group:</strong> {caseMetadata.age_group}</span>
              )}
              {caseMetadata.region && (
                <span><strong>Region:</strong> {caseMetadata.region}</span>
              )}
              {caseMetadata.diagnosis && (
                <span><strong>Diagnosis:</strong> {caseMetadata.diagnosis}</span>
              )}
              {caseMetadata.comorbidities && caseMetadata.comorbidities.length > 0 && (
                <span><strong>Comorbidities:</strong> {caseMetadata.comorbidities.join(', ')}</span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* SOAP Sections */}
      <div className="p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-[#1E3A8A] dark:text-white" style={{ fontWeight: 600 }}>
            Clinical Notes
          </h3>
          <button
            type="button"
            onClick={toggleAllSections}
            className="text-sm text-[#2563EB] dark:text-[#60A5FA] hover:underline"
          >
            {expandedSections.size === 4 ? 'Collapse All' : 'Expand All'}
          </button>
        </div>

        <div className="space-y-4">
          {sections.map((section) => {
            const isExpanded = expandedSections.has(section.key);
            const sectionAnnotations = getSectionAnnotations(section.key);

            return (
              <div
                key={section.key}
                className="border border-slate/20 dark:border-[#475569]/30 rounded-lg overflow-hidden"
              >
                {/* Section Header */}
                <button
                  type="button"
                  onClick={() => toggleSection(section.key)}
                  className="w-full flex items-center justify-between p-4 bg-[#F8FAFC] dark:bg-[#334155] hover:bg-[#64748B]/5 dark:hover:bg-[#475569]/20 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-lg font-semibold text-[#1E3A8A] dark:text-white" style={{ fontWeight: 600 }}>
                      {section.label}
                    </span>
                    {sectionAnnotations.length > 0 && (
                      <span className="px-2 py-0.5 text-xs font-medium bg-[#C4B5FD]/20 dark:bg-[#8B5CF6]/20 text-[#8B5CF6] dark:text-[#C4B5FD] rounded-full">
                        {sectionAnnotations.length} annotation{sectionAnnotations.length !== 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                  {isExpanded ? (
                    <ChevronUpIcon className="h-5 w-5 text-[#64748B] dark:text-[#94A3B8]" />
                  ) : (
                    <ChevronDownIcon className="h-5 w-5 text-[#64748B] dark:text-[#94A3B8]" />
                  )}
                </button>

                {/* Section Content */}
                {isExpanded && (
                  <div className="p-4 bg-white dark:bg-[#1E293B]">
                    {isEditing ? (
                      <textarea
                        value={section.content}
                        onChange={(e) =>
                          setEditedNote({
                            ...editedNote,
                            [section.key]: e.target.value,
                          })
                        }
                        className="w-full min-h-[100px] px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30 focus:border-[#2563EB] transition-all"
                        placeholder={`Enter ${section.label.toLowerCase()} information...`}
                      />
                    ) : (
                      <div className="prose prose-sm max-w-none text-[#0F172A] dark:text-white">
                        <p className="whitespace-pre-wrap">{section.content || 'No content available.'}</p>
                      </div>
                    )}

                    {/* Section Annotations */}
                    {sectionAnnotations.length > 0 && (
                      <div className="mt-4 pt-4 border-t border-slate/20 dark:border-[#475569]/30">
                        <h4 className="text-sm font-semibold text-[#1E3A8A] dark:text-white mb-2">Annotations</h4>
                        <div className="space-y-2">
                          {sectionAnnotations.map((annotation) => (
                            <div
                              key={annotation.id}
                              className="p-3 bg-[#F8FAFC] dark:bg-[#334155] rounded-lg border border-slate/20 dark:border-[#475569]/30"
                            >
                              <p className="text-sm text-[#0F172A] dark:text-white">{annotation.text}</p>
                              <p className="text-xs text-[#64748B] dark:text-[#94A3B8] mt-1">
                                {annotation.author} • {formatDate(annotation.timestamp)}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Annotations Panel */}
      {showAnnotationsPanel && (
        <div className="p-6 border-t border-slate/20 dark:border-[#475569]/30 bg-[#F8FAFC] dark:bg-[#334155]">
          <h3 className="text-lg font-semibold text-[#1E3A8A] dark:text-white mb-4" style={{ fontWeight: 600 }}>
            Add Annotation
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
                Section
              </label>
              <select
                value={newAnnotation.section}
                onChange={(e) =>
                  setNewAnnotation({ ...newAnnotation, section: e.target.value as any })
                }
                className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#1E293B] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
              >
                <option value="subjective">Subjective</option>
                <option value="objective">Objective</option>
                <option value="assessment">Assessment</option>
                <option value="plan">Plan</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
                Comment
              </label>
              <textarea
                value={newAnnotation.text}
                onChange={(e) => setNewAnnotation({ ...newAnnotation, text: e.target.value })}
                className="w-full min-h-[100px] px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#1E293B] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
                placeholder="Enter your annotation or comment..."
              />
            </div>
            <button
              type="button"
              onClick={handleAddAnnotation}
              className="px-4 py-2 bg-[#2563EB] dark:bg-[#3B82F6] text-white rounded-lg hover:bg-[#1E3A8A] dark:hover:bg-[#2563EB] transition-colors"
            >
              Add Annotation
            </button>
          </div>
        </div>
      )}

      {/* Version History Panel */}
      {showVersionPanel && versionHistory.length > 0 && (
        <div className="p-6 border-t border-slate/20 dark:border-[#475569]/30 bg-[#F8FAFC] dark:bg-[#334155]">
          <h3 className="text-lg font-semibold text-[#1E3A8A] dark:text-white mb-4" style={{ fontWeight: 600 }}>
            Version History
          </h3>
          <div className="space-y-3">
            {versionHistory.map((version) => (
              <div
                key={version.version}
                className="p-3 bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold text-[#1E3A8A] dark:text-white">
                    Version {version.version}
                  </span>
                  <span className="text-xs text-[#64748B] dark:text-[#94A3B8]">
                    {formatDate(version.timestamp)}
                  </span>
                </div>
                {version.changes && (
                  <p className="text-sm text-[#64748B] dark:text-[#94A3B8]">{version.changes}</p>
                )}
                {version.editedBy && (
                  <p className="text-xs text-[#64748B] dark:text-[#94A3B8] mt-1">
                    Edited by: {version.editedBy}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

