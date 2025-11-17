/**
 * Case Viewer Page
 * 
 * Dedicated page for viewing and exploring retrieved cases with multimodal content
 * and similarity visualization.
 */

import { useState, useEffect, useCallback } from 'react';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { SearchBox } from '../components/SearchBox';
import { CaseFilters, type FilterOptions } from '../components/CaseFilters';
import { MultimodalCaseViewer } from '../components/MultimodalCaseViewer';
import { CaseComparison } from '../components/CaseComparison';
import { Pagination } from '../components/Pagination';
import { Loading } from '../components/Loading';
import { ClinicalMemoryService } from '../services/clinicalMemoryService';
import type { RecallRequest, RecallResponse } from '../services/clinicalMemoryService';
import { ApiError } from '../services/api';
import type { Case } from '../types';
import {
  ArrowsUpDownIcon,
  Squares2X2Icon,
  ListBulletIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

type SortOption = 'similarity' | 'date' | 'relevance';
type ViewMode = 'grid' | 'list';

const PAGE_SIZE = 12;

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'similarity', label: 'Similarity' },
  { value: 'date', label: 'Date' },
  { value: 'relevance', label: 'Relevance' },
];

export function CaseViewer() {
  const [searchQuery, setSearchQuery] = useState('');
  const [cases, setCases] = useState<Case[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterOptions>({});
  const [sortBy, setSortBy] = useState<SortOption>('similarity');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [similarityScores, setSimilarityScores] = useState<Record<string, number>>({});
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [comparisonCase, setComparisonCase] = useState<Case | null>(null);
  const [showComparison, setShowComparison] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const fetchCases = useCallback(async () => {
    if (!searchQuery.trim()) {
      setCases([]);
      setTotalItems(0);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const request: RecallRequest = {
        query_text: searchQuery,
        limit: PAGE_SIZE * currentPage,
        score_threshold: filters.score_threshold,
        age_group: filters.age_group,
        region: filters.region,
        diagnosis: filters.diagnosis,
        time_range_days: filters.time_range_days,
      };

      const response = await ClinicalMemoryService.recallSimilarCases(request);

      if (response.success && response.data) {
        const recallData = response.data as RecallResponse;

        // Transform API response to Case objects
        const transformedCases: Case[] = recallData.similar_cases.map((item) => ({
          id: item.case_id,
          patient_id: item.patient_id,
          transcript: item.case_data?.transcript,
          soap_note: item.case_data?.soap_note,
          metadata: {
            ...item.metadata,
            timestamp: item.metadata.timestamp || new Date().toISOString(),
          },
          similarity_score: item.similarity_score,
        }));

        // Store similarity scores
        const scores: Record<string, number> = {};
        recallData.similar_cases.forEach((item) => {
          scores[item.case_id] = item.similarity_score;
        });
        setSimilarityScores(scores);

        // Sort cases
        const sortedCases = sortCases(transformedCases, sortBy, scores);

        // Paginate
        const startIndex = (currentPage - 1) * PAGE_SIZE;
        const endIndex = startIndex + PAGE_SIZE;
        const paginatedCases = sortedCases.slice(startIndex, endIndex);

        setCases(paginatedCases);
        setTotalItems(recallData.total_found);
      } else {
        setError(response.error || 'Failed to fetch cases');
        setCases([]);
        setTotalItems(0);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
      setCases([]);
      setTotalItems(0);
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, filters, sortBy, currentPage]);

  const sortCases = useCallback(
    (casesToSort: Case[], sort: SortOption, scores: Record<string, number>): Case[] => {
      const sorted = [...casesToSort];

      switch (sort) {
        case 'similarity':
          return sorted.sort((a, b) => {
            const scoreA = scores[a.id] || a.similarity_score || 0;
            const scoreB = scores[b.id] || b.similarity_score || 0;
            return scoreB - scoreA;
          });
        case 'date':
          return sorted.sort((a, b) => {
            const dateA = new Date(a.metadata.timestamp).getTime();
            const dateB = new Date(b.metadata.timestamp).getTime();
            return dateB - dateA;
          });
        case 'relevance':
          return sorted.sort((a, b) => {
            const scoreA = (scores[a.id] || a.similarity_score || 0) * 0.7;
            const dateA = new Date(a.metadata.timestamp).getTime();
            const recencyA =
              Math.max(0, 1 - (Date.now() - dateA) / (365 * 24 * 60 * 60 * 1000)) * 0.3;
            const relevanceA = scoreA + recencyA;

            const scoreB = (scores[b.id] || b.similarity_score || 0) * 0.7;
            const dateB = new Date(b.metadata.timestamp).getTime();
            const recencyB =
              Math.max(0, 1 - (Date.now() - dateB) / (365 * 24 * 60 * 60 * 1000)) * 0.3;
            const relevanceB = scoreB + recencyB;

            return relevanceB - relevanceA;
          });
        default:
          return sorted;
      }
    },
    []
  );

  useEffect(() => {
    if (searchQuery.trim()) {
      fetchCases();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery, filters, sortBy, currentPage]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1);
  };

  const handleFilterChange = (newFilters: FilterOptions) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  const handleFilterReset = () => {
    setFilters({});
    setCurrentPage(1);
  };

  const handleSortChange = (newSort: SortOption) => {
    setSortBy(newSort);
  };

  const handleCaseSelect = (caseData: Case) => {
    setSelectedCase(caseData);
  };

  const handleCompare = (case1: Case, case2?: Case) => {
    if (case2) {
      setSelectedCase(case1);
      setComparisonCase(case2);
      setShowComparison(true);
    } else {
      // If only one case provided, set it as the first case for comparison
      setSelectedCase(case1);
      setShowComparison(true);
    }
  };

  const handleCloseComparison = () => {
    setShowComparison(false);
    setComparisonCase(null);
  };

  const totalPages = Math.ceil(totalItems / PAGE_SIZE);

  return (
    <div className="min-h-screen bg-slate/5 dark:bg-primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumbs */}
        <Breadcrumbs
          items={[
            { label: 'Home', href: '/' },
            { label: 'Case Viewer', href: '/case-viewer' },
          ]}
        />

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-charcoal dark:text-white mb-2 font-heading">
            Multimodal Case Viewer
          </h1>
          <p className="text-slate dark:text-white/70">
            Explore retrieved cases with multimodal content and similarity visualization
          </p>
        </div>

        {/* Search and Controls */}
        <div className="mb-6 space-y-4">
          {/* Search Box */}
          <SearchBox
            value={searchQuery}
            onChange={handleSearch}
            placeholder="Search for similar cases (e.g., symptoms, diagnosis, patient history)..."
            suggestions={[
              'fever and cough',
              'chest pain',
              'headache with nausea',
              'abdominal pain',
              'respiratory symptoms',
            ]}
          />

          {/* Controls Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            {/* Sort and View Mode */}
            <div className="flex items-center gap-4">
              {/* Sort Dropdown */}
              <div className="relative">
                <select
                  value={sortBy}
                  onChange={(e) => handleSortChange(e.target.value as SortOption)}
                  className="appearance-none bg-white dark:bg-[#1E293B] border border-slate/20 dark:border-[#475569]/30 rounded-md px-4 py-2 pr-8 text-sm text-charcoal dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:border-transparent"
                  aria-label="Sort cases"
                >
                  {SORT_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      Sort by {option.label}
                    </option>
                  ))}
                </select>
                <ArrowsUpDownIcon
                  className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-slate dark:text-white/70 pointer-events-none"
                  aria-hidden="true"
                />
              </div>

              {/* View Mode Toggle */}
              <div className="flex items-center gap-1 bg-white dark:bg-[#1E293B] border border-slate/20 dark:border-[#475569]/30 rounded-md p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={clsx(
                    'p-2 rounded transition-colors',
                    viewMode === 'grid'
                      ? 'bg-primary text-white'
                      : 'text-slate dark:text-white/70 hover:text-charcoal dark:hover:text-white'
                  )}
                  aria-label="Grid view"
                  aria-pressed={viewMode === 'grid'}
                >
                  <Squares2X2Icon className="h-5 w-5" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={clsx(
                    'p-2 rounded transition-colors',
                    viewMode === 'list'
                      ? 'bg-primary text-white'
                      : 'text-slate dark:text-white/70 hover:text-charcoal dark:hover:text-white'
                  )}
                  aria-label="List view"
                  aria-pressed={viewMode === 'list'}
                >
                  <ListBulletIcon className="h-5 w-5" />
                </button>
              </div>

              {/* Filters Toggle */}
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  showFilters
                    ? 'bg-primary text-white'
                    : 'bg-white dark:bg-[#1E293B] border border-slate/20 dark:border-[#475569]/30 text-charcoal dark:text-white hover:bg-slate/5 dark:hover:bg-white/5'
                )}
                aria-label="Toggle filters"
                aria-expanded={showFilters}
              >
                <FunnelIcon className="h-4 w-4" />
                Filters
              </button>
            </div>

            {/* Results Count */}
            {totalItems > 0 && (
              <div className="text-sm text-slate dark:text-white/70">
                {totalItems} {totalItems === 1 ? 'case' : 'cases'} found
              </div>
            )}
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="bg-white dark:bg-[#1E293B] border border-slate/20 dark:border-[#475569]/30 rounded-lg p-4">
              <CaseFilters
                filters={filters}
                onChange={handleFilterChange}
                onReset={handleFilterReset}
              />
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {/* Cases Viewer */}
        <MultimodalCaseViewer
          cases={cases}
          similarityScores={similarityScores}
          isLoading={isLoading}
          onCaseSelect={handleCaseSelect}
          onCompare={handleCompare}
          showSimilarityVisualization={true}
        />

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-8">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
            />
          </div>
        )}

        {/* Case Comparison Modal */}
        {showComparison && selectedCase && comparisonCase && (
          <CaseComparison
            case1={selectedCase}
            case2={comparisonCase}
            similarityScore={
              similarityScores[selectedCase.id] || similarityScores[comparisonCase.id] || 0
            }
            onClose={handleCloseComparison}
          />
        )}
      </div>
    </div>
  );
}

