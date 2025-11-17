/**
 * Dashboard Page
 * 
 * Main clinical memory dashboard with search, case display, and comparison.
 */

import { useState, useEffect, useCallback } from 'react';
import { Breadcrumbs } from '../components/Breadcrumbs';
import { SearchBox } from '../components/SearchBox';
import { CaseCard } from '../components/CaseCard';
import { CaseFilters } from '../components/CaseFilters';
import type { FilterOptions } from '../components/CaseFilters';
import { CaseComparison } from '../components/CaseComparison';
import { Pagination } from '../components/Pagination';
import { Loading, LoadingOverlay } from '../components/Loading';
import { ClinicalMemoryService } from '../services/clinicalMemoryService';
import type { RecallRequest, RecallResponse } from '../services/clinicalMemoryService';
import { ApiError } from '../services/api';
import type { Case } from '../types';
import { 
  ArrowsUpDownIcon, 
  Squares2X2Icon, 
  ListBulletIcon,
  ChartBarIcon,
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

export function Dashboard() {
  console.log('Dashboard component rendering...');
  
  const [searchQuery, setSearchQuery] = useState('');
  const [cases, setCases] = useState<Case[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterOptions>({});
  const [sortBy, setSortBy] = useState<SortOption>('similarity');
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [selectedCases, setSelectedCases] = useState<Case[]>([]);
  const [showComparison, setShowComparison] = useState(false);
  const [similarityScores, setSimilarityScores] = useState<Record<string, number>>({});
  const [suggestions] = useState<string[]>([
    'fever',
    'cough',
    'headache',
    'chest pain',
    'abdominal pain',
    'nausea',
    'dizziness',
  ]);

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

  const sortCases = useCallback((casesToSort: Case[], sort: SortOption, scores: Record<string, number>): Case[] => {
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
        // Combine similarity and recency
        return sorted.sort((a, b) => {
          const scoreA = (scores[a.id] || a.similarity_score || 0) * 0.7;
          const dateA = new Date(a.metadata.timestamp).getTime();
          const recencyA = Math.max(0, 1 - (Date.now() - dateA) / (365 * 24 * 60 * 60 * 1000)) * 0.3;
          const relevanceA = scoreA + recencyA;

          const scoreB = (scores[b.id] || b.similarity_score || 0) * 0.7;
          const dateB = new Date(b.metadata.timestamp).getTime();
          const recencyB = Math.max(0, 1 - (Date.now() - dateB) / (365 * 24 * 60 * 60 * 1000)) * 0.3;
          const relevanceB = scoreB + recencyB;

          return relevanceB - relevanceA;
        });
      default:
        return sorted;
    }
  }, []);

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
    setSelectedCases((prev) => {
      if (prev.find((c) => c.id === caseData.id)) {
        return prev.filter((c) => c.id !== caseData.id);
      }
      if (prev.length < 2) {
        return [...prev, caseData];
      }
      return [prev[1], caseData];
    });
  };

  const handleCompare = () => {
    if (selectedCases.length === 2) {
      setShowComparison(true);
    }
  };

  const totalPages = Math.ceil(totalItems / PAGE_SIZE);

  return (
    <div className="max-w-7xl mx-auto">
      <Breadcrumbs items={[{ name: 'Dashboard' }]} />
      
      {/* Header Section */}
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-[#1E3A8A] dark:text-white mb-3 font-heading" style={{ fontWeight: 600 }}>
          Clinical Memory Dashboard
        </h1>
        <p className="text-[#64748B] dark:text-[#94A3B8] text-base">
          Search for similar cases, view SOAP notes, and compare treatment outcomes
        </p>
      </div>

      {/* Search and Filters Card */}
      <div className="bg-white dark:bg-[#1E293B] rounded-2xl shadow-sm border border-slate/20 dark:border-[#475569]/30 p-6 mb-8">
        <div className="mb-6">
          <SearchBox
            value={searchQuery}
            onChange={setSearchQuery}
            onSubmit={handleSearch}
            suggestions={suggestions}
            isLoading={isLoading}
          />
        </div>

        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <CaseFilters
              filters={filters}
              onChange={handleFilterChange}
              onReset={handleFilterReset}
            />

            {/* Sort Dropdown */}
            <div className="relative">
              <select
                value={sortBy}
                onChange={(e) => handleSortChange(e.target.value as SortOption)}
                className="appearance-none bg-white dark:bg-[#334155] border border-slate/30 dark:border-[#475569]/30 rounded-lg px-4 py-2.5 pr-10 text-sm font-medium text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value} className="text-[#0F172A] dark:text-white bg-white dark:bg-[#334155]">
                    Sort by {option.label}
                  </option>
                ))}
              </select>
              <ArrowsUpDownIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-[#8B5CF6] dark:text-[#C4B5FD] pointer-events-none" />
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] p-1">
              <button
                type="button"
                onClick={() => setViewMode('grid')}
                className={clsx(
                  'p-2 rounded-md transition-all',
                  viewMode === 'grid'
                    ? 'bg-primary/10 dark:bg-[#2563EB]/20 text-primary dark:text-[#60A5FA] shadow-sm'
                    : 'text-slate dark:text-[#94A3B8] hover:bg-slate/10 dark:hover:bg-[#475569]/30'
                )}
              >
                <Squares2X2Icon className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => setViewMode('list')}
                className={clsx(
                  'p-2 rounded-md transition-all',
                  viewMode === 'list'
                    ? 'bg-primary/10 dark:bg-[#2563EB]/20 text-primary dark:text-[#60A5FA] shadow-sm'
                    : 'text-slate dark:text-[#94A3B8] hover:bg-slate/10 dark:hover:bg-[#475569]/30'
                )}
              >
                <ListBulletIcon className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Compare Button */}
          {selectedCases.length === 2 && (
            <button
              type="button"
              onClick={handleCompare}
              className="inline-flex items-center px-5 py-2.5 border border-transparent text-sm font-semibold rounded-lg text-white bg-[#2563EB] hover:bg-[#1E3A8A] shadow-sm hover:shadow-md transition-all duration-200"
            >
              <ChartBarIcon className="h-4 w-4 mr-2" />
              Compare Cases
            </button>
          )}
        </div>
      </div>

      {/* Results */}
      {isLoading && cases.length === 0 ? (
        <Loading fullScreen message="Searching for similar cases..." />
      ) : error ? (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
        </div>
      ) : !searchQuery.trim() ? (
        <div className="bg-white dark:bg-[#1E293B] rounded-2xl shadow-sm border border-slate/20 dark:border-[#475569]/30 p-16 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#8B5CF6]/10 dark:bg-[#8B5CF6]/20 mb-6">
            <ChartBarIcon className="h-8 w-8 text-[#8B5CF6] dark:text-[#C4B5FD]" />
          </div>
          <h3 className="text-xl font-semibold text-[#1E3A8A] dark:text-white mb-2 font-heading" style={{ fontWeight: 600 }}>
            Start Searching
          </h3>
          <p className="text-[#64748B] dark:text-[#94A3B8] text-base max-w-md mx-auto">
            Enter symptoms, transcript text, or case descriptions to find similar cases
          </p>
        </div>
      ) : cases.length === 0 ? (
        <div className="bg-white dark:bg-[#1E293B] rounded-2xl shadow-sm border border-slate/20 dark:border-[#475569]/30 p-16 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#8B5CF6]/10 dark:bg-[#8B5CF6]/20 mb-6">
            <ChartBarIcon className="h-8 w-8 text-[#8B5CF6] dark:text-[#C4B5FD]" />
          </div>
          <h3 className="text-xl font-semibold text-[#1E3A8A] dark:text-white mb-2 font-heading" style={{ fontWeight: 600 }}>
            No Cases Found
          </h3>
          <p className="text-[#64748B] dark:text-[#94A3B8] text-base max-w-md mx-auto">
            Try adjusting your search query or filters
          </p>
        </div>
      ) : (
        <>
          <LoadingOverlay isLoading={isLoading}>
            <div
              className={clsx(
                'grid gap-6',
                viewMode === 'grid'
                  ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
                  : 'grid-cols-1'
              )}
            >
              {cases.map((caseData) => (
                <CaseCard
                  key={caseData.id}
                  case={caseData}
                  similarityScore={similarityScores[caseData.id] || caseData.similarity_score}
                  onClick={() => handleCaseSelect(caseData)}
                  isSelected={selectedCases.some((c) => c.id === caseData.id)}
                />
              ))}
            </div>
          </LoadingOverlay>

          {totalPages > 1 && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
              pageSize={PAGE_SIZE}
              totalItems={totalItems}
            />
          )}
        </>
      )}

      {/* Comparison Modal */}
      {showComparison && selectedCases.length === 2 && (
        <CaseComparison
          case1={selectedCases[0]}
          case2={selectedCases[1]}
          similarityScore={
            similarityScores[selectedCases[0].id] || selectedCases[0].similarity_score
          }
          onClose={() => {
            setShowComparison(false);
            setSelectedCases([]);
          }}
        />
      )}
    </div>
  );
}
