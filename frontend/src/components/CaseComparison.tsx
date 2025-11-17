/**
 * Case Comparison Component
 * 
 * Side-by-side comparison view for two cases.
 */

import type { Case } from '../types';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { CaseCard } from './CaseCard';
import { SimilarityScore } from './SimilarityScore';

interface CaseComparisonProps {
  case1: Case;
  case2: Case;
  similarityScore?: number;
  onClose: () => void;
}

export function CaseComparison({
  case1,
  case2,
  similarityScore,
  onClose,
}: CaseComparisonProps) {
  return (
    <div 
      className="fixed inset-0 z-50 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="case-comparison-title"
      aria-describedby="case-comparison-description"
    >
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 bg-charcoal bg-opacity-75 transition-opacity"
          onClick={onClose}
          aria-hidden="true"
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white dark:bg-primary rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-7xl sm:w-full">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate/30 dark:border-white/20">
            <div>
              <h3 
                id="case-comparison-title"
                className="text-lg font-semibold text-primaryDark dark:text-white font-heading"
              >
                Case Comparison
              </h3>
              {similarityScore !== undefined && (
                <div className="mt-2">
                  <SimilarityScore score={similarityScore} size="sm" />
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="text-slate dark:text-white/70 hover:text-charcoal dark:hover:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2 rounded"
              aria-label="Close case comparison"
            >
              <XMarkIcon className="h-6 w-6" aria-hidden="true" />
            </button>
          </div>

          {/* Comparison Content */}
          <div className="px-6 py-4">
            <p id="case-comparison-description" className="sr-only">
              Comparing two cases side by side with key differences highlighted
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6" role="region" aria-label="Case comparison">
              {/* Case 1 */}
              <div role="region" aria-label="First case">
                <h4 className="text-sm font-medium text-charcoal dark:text-white mb-3">
                  Case 1
                </h4>
                <CaseCard case={case1} />
              </div>

              {/* Case 2 */}
              <div role="region" aria-label="Second case">
                <h4 className="text-sm font-medium text-charcoal mb-3">
                  Case 2
                </h4>
                <CaseCard case={case2} />
              </div>
            </div>

            {/* Comparison Details */}
            <div className="mt-6 pt-6 border-t border-slate/30 dark:border-white/20" role="region" aria-label="Key differences">
              <h4 className="text-sm font-medium text-charcoal dark:text-white mb-3">
                Key Differences
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-charcoal dark:text-white">
                    Age Group:
                  </span>{' '}
                  <span className="text-slate dark:text-white/80">
                    {case1.metadata.age_group || 'N/A'} vs{' '}
                    {case2.metadata.age_group || 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-charcoal dark:text-white">
                    Region:
                  </span>{' '}
                  <span className="text-slate dark:text-white/80">
                    {case1.metadata.region || 'N/A'} vs{' '}
                    {case2.metadata.region || 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-charcoal dark:text-white">
                    Diagnosis:
                  </span>{' '}
                  <span className="text-slate dark:text-white/80">
                    {case1.metadata.diagnosis || 'N/A'} vs{' '}
                    {case2.metadata.diagnosis || 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-charcoal dark:text-white">
                    Outcome:
                  </span>{' '}
                  <span className="text-slate dark:text-white/80">
                    {case1.metadata.outcome || 'N/A'} vs{' '}
                    {case2.metadata.outcome || 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-slate/30 flex justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primaryDark focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
              aria-label="Close case comparison dialog"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

