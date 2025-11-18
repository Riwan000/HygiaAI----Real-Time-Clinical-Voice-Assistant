/**
 * Multimodal Case Viewer Component
 * 
 * Comprehensive viewer for displaying retrieved cases with multimodal content
 * and similarity visualization.
 */

import { useState, useEffect } from 'react';
import type { Case, CaseMetadata, SOAPNote } from '../types';
import { CaseCard } from './CaseCard';
import { SOAPNoteViewer } from './SOAPNoteViewer';
import { SimilarityScore } from './SimilarityScore';
import { Loading } from './Loading';
import {
  DocumentTextIcon,
  PhotoIcon,
  MusicalNoteIcon,
  ChartBarIcon,
  ArrowsPointingOutIcon,
  XMarkIcon,
  PlayIcon,
  PauseIcon,
} from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

interface MultimodalCaseViewerProps {
  cases: Case[];
  similarityScores?: Record<string, number | null | undefined>;
  isLoading?: boolean;
  onCaseSelect?: (caseData: Case) => void;
  onCompare?: (case1: Case, case2: Case) => void;
  showSimilarityVisualization?: boolean;
  className?: string;
}

interface CaseDetailModalProps {
  caseData: Case;
  similarityScore?: number;
  onClose: () => void;
  onCompare?: (case1: Case) => void;
}

/**
 * Similarity Visualization Component
 */
function SimilarityVisualization({
  cases,
  similarityScores,
}: {
  cases: Case[];
  similarityScores: Record<string, number | null | undefined>;
}) {
  // Filter out null/undefined scores and get valid scores
  const validScores = Object.values(similarityScores).filter(
    (score): score is number => score !== null && score !== undefined && score > 0
  );
  
  // Don't show visualization if no valid scores (no query was provided)
  if (validScores.length === 0) {
    return null;
  }
  
  const maxScore = Math.max(...validScores, 0);
  const minScore = Math.min(...validScores, 1);

  const getColor = (score: number) => {
    const normalized = (score - minScore) / (maxScore - minScore || 1);
    if (normalized >= 0.8) return 'bg-green-500';
    if (normalized >= 0.6) return 'bg-blue-500';
    if (normalized >= 0.4) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-white dark:bg-[#1E293B] rounded-lg p-4 border border-slate/20 dark:border-[#475569]/30">
      <h3 className="text-sm font-semibold text-charcoal dark:text-white mb-3">
        Similarity Distribution
      </h3>
      <div className="space-y-2">
        {cases.slice(0, 10).map((caseData) => {
          const score = similarityScores[caseData.id] ?? caseData.similarity_score ?? null;
          // Skip cases with no similarity score
          if (score === null || score === undefined || score === 0) {
            return null;
          }
          return (
            <div key={caseData.id} className="flex items-center gap-2">
              <span className="text-xs text-slate dark:text-white/70 w-20 truncate">
                Case {caseData.id.slice(0, 8)}...
              </span>
              <div className="flex-1 h-4 bg-slate/20 dark:bg-white/10 rounded-full overflow-hidden">
                <div
                  className={clsx('h-full transition-all', getColor(score))}
                  style={{ width: `${score * 100}%` }}
                  role="progressbar"
                  aria-valuenow={score * 100}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`Similarity score: ${Math.round(score * 100)}%`}
                />
              </div>
              <span className="text-xs text-slate dark:text-white/70 w-12 text-right">
                {Math.round(score * 100)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Case Detail Modal
 */
function CaseDetailModal({ caseData, similarityScore, onClose, onCompare }: CaseDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'soap' | 'multimodal'>('overview');
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  useEffect(() => {
    // Cleanup audio URL on unmount
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  const handlePlayAudio = () => {
    // In a real implementation, this would fetch the audio file from the API
    // For now, we'll just toggle the state
    setAudioPlaying(!audioPlaying);
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="case-detail-title"
    >
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-charcoal bg-opacity-75 transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white dark:bg-primary rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-5xl sm:w-full">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate/30 dark:border-white/20">
            <div className="flex items-center gap-4">
              <h3
                id="case-detail-title"
                className="text-lg font-semibold text-primaryDark dark:text-white font-heading"
              >
                Case {caseData.id} - Details
              </h3>
              {similarityScore !== undefined && (
                <SimilarityScore score={similarityScore} />
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="text-slate dark:text-white/70 hover:text-charcoal dark:hover:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2 rounded"
              aria-label="Close case details"
            >
              <XMarkIcon className="h-6 w-6" aria-hidden="true" />
            </button>
          </div>

          {/* Tabs */}
          <div className="border-b border-slate/30 dark:border-white/20">
            <nav className="flex -mb-px px-6" aria-label="Tabs">
              {[
                { id: 'overview', label: 'Overview' },
                { id: 'soap', label: 'SOAP Note' },
                { id: 'multimodal', label: 'Multimodal Content' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={clsx(
                    'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
                    activeTab === tab.id
                      ? 'border-[#2563EB] text-[#2563EB] dark:text-[#60A5FA]'
                      : 'border-transparent text-slate dark:text-white/70 hover:text-charcoal dark:hover:text-white hover:border-slate/30'
                  )}
                  aria-selected={activeTab === tab.id}
                  role="tab"
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="px-6 py-4 max-h-[calc(100vh-300px)] overflow-y-auto">
            {activeTab === 'overview' && (
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-charcoal dark:text-white mb-2">
                    Patient Information
                  </h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate dark:text-white/70">Patient ID:</span>{' '}
                      <span className="text-charcoal dark:text-white">{caseData.patient_id}</span>
                    </div>
                    {caseData.metadata.age_group && (
                      <div>
                        <span className="text-slate dark:text-white/70">Age Group:</span>{' '}
                        <span className="text-charcoal dark:text-white">
                          {caseData.metadata.age_group}
                        </span>
                      </div>
                    )}
                    {caseData.metadata.region && (
                      <div>
                        <span className="text-slate dark:text-white/70">Region:</span>{' '}
                        <span className="text-charcoal dark:text-white">
                          {caseData.metadata.region}
                        </span>
                      </div>
                    )}
                    {caseData.metadata.diagnosis && (
                      <div>
                        <span className="text-slate dark:text-white/70">Diagnosis:</span>{' '}
                        <span className="text-charcoal dark:text-white">
                          {caseData.metadata.diagnosis}
                        </span>
                      </div>
                    )}
                    {caseData.metadata.outcome && (
                      <div>
                        <span className="text-slate dark:text-white/70">Outcome:</span>{' '}
                        <span className="text-charcoal dark:text-white">
                          {caseData.metadata.outcome}
                        </span>
                      </div>
                    )}
                    {caseData.metadata.timestamp && (
                      <div>
                        <span className="text-slate dark:text-white/70">Date:</span>{' '}
                        <span className="text-charcoal dark:text-white">
                          {new Date(caseData.metadata.timestamp).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {caseData.metadata.comorbidities && caseData.metadata.comorbidities.length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-charcoal dark:text-white mb-2">
                      Comorbidities
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {caseData.metadata.comorbidities.map((comorbidity, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-1 rounded text-xs bg-slate/10 dark:bg-white/10 text-charcoal dark:text-white"
                        >
                          {comorbidity}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {caseData.transcript && (
                  <div>
                    <h4 className="text-sm font-semibold text-charcoal dark:text-white mb-2">
                      Transcript Preview
                    </h4>
                    <p className="text-sm text-slate dark:text-white/80 line-clamp-3">
                      {caseData.transcript}
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'soap' && caseData.soap_note && (
              <SOAPNoteViewer
                soapNote={caseData.soap_note}
                patientInfo={{
                  id: caseData.patient_id,
                  age: caseData.metadata.age_group,
                }}
                caseMetadata={caseData.metadata}
              />
            )}

            {activeTab === 'multimodal' && (
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-charcoal dark:text-white mb-3">
                    Available Content Types
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Audio */}
                    {caseData.transcript && (
                      <div className="border border-slate/20 dark:border-[#475569]/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <MusicalNoteIcon className="h-5 w-5 text-[#2563EB] dark:text-[#60A5FA]" />
                          <span className="text-sm font-medium text-charcoal dark:text-white">
                            Audio Transcription
                          </span>
                        </div>
                        <button
                          onClick={handlePlayAudio}
                          className="flex items-center gap-2 px-3 py-2 text-sm bg-slate/10 dark:bg-white/10 hover:bg-slate/20 dark:hover:bg-white/20 rounded transition-colors"
                          aria-label={audioPlaying ? 'Pause audio' : 'Play audio'}
                        >
                          {audioPlaying ? (
                            <PauseIcon className="h-4 w-4" />
                          ) : (
                            <PlayIcon className="h-4 w-4" />
                          )}
                          <span>{audioPlaying ? 'Playing...' : 'Play Audio'}</span>
                        </button>
                      </div>
                    )}

                    {/* Text */}
                    {caseData.transcript && (
                      <div className="border border-slate/20 dark:border-[#475569]/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <DocumentTextIcon className="h-5 w-5 text-[#2563EB] dark:text-[#60A5FA]" />
                          <span className="text-sm font-medium text-charcoal dark:text-white">
                            Text Content
                          </span>
                        </div>
                        <p className="text-sm text-slate dark:text-white/80 line-clamp-2">
                          {caseData.transcript.substring(0, 150)}...
                        </p>
                      </div>
                    )}

                    {/* SOAP Note */}
                    {caseData.soap_note && (
                      <div className="border border-slate/20 dark:border-[#475569]/30 rounded-lg p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <DocumentTextIcon className="h-5 w-5 text-[#2563EB] dark:text-[#60A5FA]" />
                          <span className="text-sm font-medium text-charcoal dark:text-white">
                            SOAP Note
                          </span>
                        </div>
                        <p className="text-sm text-slate dark:text-white/80">
                          {caseData.soap_note.subjective.substring(0, 100)}...
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-slate/30 dark:border-white/20 flex justify-between">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate dark:text-white/70 hover:text-charcoal dark:hover:text-white"
            >
              Close
            </button>
            {onCompare && (
              <button
                type="button"
                onClick={() => onCompare(caseData)}
                className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primaryDark focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2 flex items-center gap-2"
              >
                <ArrowsPointingOutIcon className="h-4 w-4" />
                Compare with Another Case
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Main Multimodal Case Viewer Component
 */
export function MultimodalCaseViewer({
  cases,
  similarityScores = {},
  isLoading = false,
  onCaseSelect,
  onCompare,
  showSimilarityVisualization = true,
  className,
}: MultimodalCaseViewerProps) {
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [comparisonCase, setComparisonCase] = useState<Case | null>(null);

  const handleCaseClick = (caseData: Case) => {
    setSelectedCase(caseData);
    onCaseSelect?.(caseData);
  };

  const handleCloseDetail = () => {
    setSelectedCase(null);
  };

  const handleCompareClick = (case1: Case) => {
    setComparisonCase(case1);
    // If onCompare is provided, it will handle the comparison
    // Otherwise, we'll show a selection UI
  };

  if (isLoading) {
    return (
      <div className={clsx('flex items-center justify-center py-12', className)}>
        <Loading />
      </div>
    );
  }

  if (cases.length === 0) {
    return (
      <div className={clsx('text-center py-12', className)}>
        <p className="text-slate dark:text-white/70">No cases found</p>
      </div>
    );
  }

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Similarity Visualization */}
      {showSimilarityVisualization && (
        <SimilarityVisualization cases={cases} similarityScores={similarityScores} />
      )}

      {/* Cases Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {cases.map((caseData) => {
          const score = similarityScores[caseData.id] ?? caseData.similarity_score ?? undefined;
          return (
            <CaseCard
              key={caseData.id}
              case={caseData}
              similarityScore={score}
              onClick={() => handleCaseClick(caseData)}
            />
          );
        })}
      </div>

      {/* Case Detail Modal */}
      {selectedCase && (
        <CaseDetailModal
          caseData={selectedCase}
          similarityScore={similarityScores[selectedCase.id] || selectedCase.similarity_score}
          onClose={handleCloseDetail}
          onCompare={onCompare ? () => handleCompareClick(selectedCase) : undefined}
        />
      )}
    </div>
  );
}

