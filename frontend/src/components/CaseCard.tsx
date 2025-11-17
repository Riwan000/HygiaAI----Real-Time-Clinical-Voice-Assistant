/**
 * Case Card Component
 * 
 * Displays a single case with metadata, similarity score, and SOAP note preview.
 */

import type { Case, CaseMetadata, SOAPNote } from '../types';
import { DocumentTextIcon, CalendarIcon, MapPinIcon, UserIcon } from '@heroicons/react/24/outline';
import { SimilarityScore } from './SimilarityScore';
import { clsx } from '../utils/clsx';

interface CaseCardProps {
  case: Case;
  similarityScore?: number;
  onClick?: () => void;
  isSelected?: boolean;
}

export function CaseCard({ case: caseData, similarityScore, onClick, isSelected }: CaseCardProps) {
  const metadata = caseData.metadata;

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

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      onClick();
    }
  };

  const caseDescription = [
    metadata.age_group && `Age: ${metadata.age_group}`,
    metadata.region && `Region: ${metadata.region}`,
    metadata.diagnosis && `Diagnosis: ${metadata.diagnosis}`,
    metadata.outcome && `Outcome: ${metadata.outcome}`,
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <div
      onClick={onClick}
      onKeyDown={handleKeyDown}
      role={onClick ? 'button' : 'article'}
      tabIndex={onClick ? 0 : -1}
      aria-label={`Case ${caseData.id}${caseDescription ? `. ${caseDescription}` : ''}${similarityScore !== undefined ? `. Similarity: ${Math.round(similarityScore * 100)}%` : ''}`}
      aria-pressed={isSelected ? 'true' : undefined}
      className={clsx(
        'bg-white dark:bg-[#1E293B] rounded-2xl shadow-sm border border-slate/20 dark:border-[#475569]/30 p-6 transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5',
        onClick && 'cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2',
        isSelected
          ? 'border-[#8B5CF6] dark:border-[#C4B5FD] ring-2 ring-[#C4B5FD]/30 dark:ring-[#C4B5FD]/20'
          : 'border-slate/20 dark:border-[#475569]/30 hover:border-primary/30 dark:hover:border-[#2563EB]/50'
      )}
    >
      {/* Header with Similarity Score */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-[#1E3A8A] dark:text-white mb-1 font-heading" style={{ fontWeight: 600 }}>
            Case {caseData.id}
          </h3>
          {similarityScore !== undefined && (
            <SimilarityScore score={similarityScore} />
          )}
        </div>
        {caseData.soap_note && (
          <DocumentTextIcon 
            className="h-5 w-5 text-[#64748B] dark:text-[#94A3B8]"
            aria-hidden="true"
          />
        )}
      </div>

      {/* Metadata */}
      <div className="space-y-2 mb-4">
        {metadata.age_group && (
          <div className="flex items-center text-sm text-[#64748B] dark:text-[#94A3B8]">
            <UserIcon className="h-4 w-4 mr-2" aria-hidden="true" />
            <span>Age group: {metadata.age_group}</span>
          </div>
        )}
        {metadata.region && (
          <div className="flex items-center text-sm text-[#64748B] dark:text-[#94A3B8]">
            <MapPinIcon className="h-4 w-4 mr-2" aria-hidden="true" />
            <span>Region: {metadata.region}</span>
          </div>
        )}
        {metadata.timestamp && (
          <div className="flex items-center text-sm text-[#64748B] dark:text-[#94A3B8]">
            <CalendarIcon className="h-4 w-4 mr-2" aria-hidden="true" />
            <time dateTime={metadata.timestamp}>{formatDate(metadata.timestamp)}</time>
          </div>
        )}
      </div>

      {/* Diagnosis */}
      {metadata.diagnosis && (
        <div className="mb-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-[#C4B5FD]/20 dark:bg-[#8B5CF6]/20 text-[#8B5CF6] dark:text-[#C4B5FD]">
            {metadata.diagnosis}
          </span>
        </div>
      )}

      {/* SOAP Note Preview */}
      {caseData.soap_note && (
        <div className="mt-4 pt-4 border-t border-slate/20 dark:border-[#475569]/30">
          <h4 className="text-sm font-semibold text-[#1E3A8A] dark:text-white mb-2" style={{ fontWeight: 600 }}>
            SOAP Note Preview
          </h4>
          <div className="space-y-1 text-xs text-[#64748B] dark:text-[#94A3B8]">
            <p>
              <span className="font-medium">S:</span>{' '}
              {caseData.soap_note.subjective.substring(0, 100)}
              {caseData.soap_note.subjective.length > 100 ? '...' : ''}
            </p>
            <p>
              <span className="font-medium">A:</span>{' '}
              {caseData.soap_note.assessment.substring(0, 100)}
              {caseData.soap_note.assessment.length > 100 ? '...' : ''}
            </p>
          </div>
        </div>
      )}

      {/* Outcome */}
      {metadata.outcome && (
        <div className="mt-4 pt-4 border-t border-slate/20 dark:border-[#475569]/30">
          <div className="flex items-center">
            <span className="text-sm font-semibold text-[#1E3A8A] dark:text-white mr-2" style={{ fontWeight: 600 }}>
              Outcome:
            </span>
            <span
              className={clsx(
                'text-sm',
                metadata.outcome.toLowerCase().includes('success') ||
                  metadata.outcome.toLowerCase().includes('improved')
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-[#64748B] dark:text-[#94A3B8]'
              )}
            >
              {metadata.outcome}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

