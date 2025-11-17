/**
 * KnowledgeBrowser Component
 * 
 * Searchable interface for browsing medical knowledge base
 */

import { useState, useEffect } from 'react';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  XMarkIcon,
  BookOpenIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';
import { KnowledgeCard } from './KnowledgeCard';
import { Pagination } from './Pagination';
import { Loading } from './Loading';
import { ClinicalMemoryService } from '../services/clinicalMemoryService';
import { clsx } from '../utils/clsx';
import type { KnowledgeEntry } from '../types';

interface KnowledgeBrowserProps {
  className?: string;
}

export function KnowledgeBrowser({ className = '' }: KnowledgeBrowserProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<string>('');
  const [selectedSource, setSelectedSource] = useState<string>('');
  const [yearRange, setYearRange] = useState<{ min?: number; max?: number }>({});
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [totalFound, setTotalFound] = useState(0);
  const [domains, setDomains] = useState<string[]>([]);
  const [sources, setSources] = useState<string[]>([]);
  const [availableDomains, setAvailableDomains] = useState<string[]>([]);
  const [availableSources, setAvailableSources] = useState<string[]>([]);
  const [bookmarkedEntries, setBookmarkedEntries] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [showFilters, setShowFilters] = useState(false);

  // Load available domains and sources on mount
  useEffect(() => {
    const loadFilters = async () => {
      try {
        const [domainsRes, sourcesRes] = await Promise.all([
          ClinicalMemoryService.getKnowledgeDomains(),
          ClinicalMemoryService.getKnowledgeSources(),
        ]);

        if (domainsRes.success && domainsRes.data) {
          setAvailableDomains(domainsRes.data);
        }
        if (sourcesRes.success && sourcesRes.data) {
          setAvailableSources(sourcesRes.data);
        }
      } catch (err) {
        console.error('Error loading filters:', err);
      }
    };

    loadFilters();
  }, []);

  // Load bookmarks from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('knowledge_bookmarks');
    if (saved) {
      try {
        const bookmarks = JSON.parse(saved);
        setBookmarkedEntries(new Set(bookmarks));
      } catch {
        // Ignore parse errors
      }
    }
  }, []);

  /**
   * Perform search
   */
  const handleSearch = async (page: number = 1) => {
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setIsSearching(true);
    setError(null);
    setCurrentPage(page);

    try {
      const response = await ClinicalMemoryService.searchKnowledgeBase({
        query: searchQuery,
        domain: selectedDomain || undefined,
        source: selectedSource || undefined,
        year_range: Object.keys(yearRange).length > 0 ? yearRange : undefined,
        limit: pageSize * 2, // Get more results for pagination
        score_threshold: 0.3,
      });

      if (response.success && response.data) {
        setEntries(response.data.entries);
        setTotalFound(response.data.total_found);
        setDomains(response.data.domains);
        setSources(response.data.sources);
      } else {
        setError(response.error || 'Failed to search knowledge base');
        setEntries([]);
        setTotalFound(0);
      }
    } catch (err: any) {
      console.error('Error searching knowledge base:', err);
      setError(err?.message || 'Failed to search knowledge base');
      setEntries([]);
      setTotalFound(0);
    } finally {
      setIsSearching(false);
    }
  };

  /**
   * Handle bookmark toggle
   */
  const handleBookmark = (entry: KnowledgeEntry, bookmarked: boolean) => {
    const newBookmarks = new Set(bookmarkedEntries);
    if (bookmarked) {
      newBookmarks.add(entry.id);
    } else {
      newBookmarks.delete(entry.id);
    }
    setBookmarkedEntries(newBookmarks);
    localStorage.setItem('knowledge_bookmarks', JSON.stringify(Array.from(newBookmarks)));
  };

  /**
   * Handle export
   */
  const handleExport = (entry: KnowledgeEntry) => {
    const content = `Title: ${entry.title}\n\nSource: ${entry.source}\nDomain: ${entry.domain || 'N/A'}\nYear: ${entry.year || 'N/A'}\nSimilarity: ${Math.round(entry.similarity_score * 100)}%\n\n${entry.content}\n\nProvenance: ${entry.provenance_url || 'N/A'}`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `knowledge_${entry.id.substring(0, 8)}_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  /**
   * Reset filters
   */
  const resetFilters = () => {
    setSelectedDomain('');
    setSelectedSource('');
    setYearRange({});
  };

  /**
   * Get paginated entries
   */
  const paginatedEntries = entries.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  const totalPages = Math.ceil(entries.length / pageSize);

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Search Bar */}
      <div className="bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30 p-6">
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-1 relative">
            <label htmlFor="knowledge-search-input" className="sr-only">
              Search medical knowledge base
            </label>
            <MagnifyingGlassIcon 
              className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-[#64748B] dark:text-[#94A3B8]"
              aria-hidden="true"
            />
            <input
              id="knowledge-search-input"
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch(1)}
              placeholder="Search medical knowledge, guidelines, textbooks..."
              className="w-full pl-10 pr-4 py-3 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white placeholder-[#64748B] dark:placeholder-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
              aria-label="Search medical knowledge base"
            />
          </div>
          <button
            type="button"
            onClick={() => handleSearch(1)}
            disabled={isSearching || !searchQuery.trim()}
            className="px-6 py-3 bg-[#2563EB] dark:bg-[#3B82F6] text-white rounded-lg hover:bg-[#1E3A8A] dark:hover:bg-[#2563EB] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
            aria-label={isSearching ? 'Searching...' : 'Search knowledge base'}
            aria-disabled={isSearching || !searchQuery.trim()}
          >
            <MagnifyingGlassIcon className="h-5 w-5" aria-hidden="true" />
            <span>{isSearching ? 'Searching...' : 'Search'}</span>
          </button>
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={clsx(
              'px-4 py-3 rounded-lg transition-colors flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2',
              showFilters
                ? 'bg-[#2563EB] dark:bg-[#3B82F6] text-white'
                : 'bg-[#F8FAFC] dark:bg-[#334155] text-[#64748B] dark:text-[#94A3B8] hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30'
            )}
            aria-label={showFilters ? 'Hide filters' : 'Show filters'}
            aria-expanded={showFilters}
            aria-controls="knowledge-filters-panel"
          >
            <FunnelIcon className="h-5 w-5" aria-hidden="true" />
            <span>Filters</span>
          </button>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div 
            id="knowledge-filters-panel"
            className="mt-4 pt-4 border-t border-slate/20 dark:border-[#475569]/30 space-y-4"
            role="region"
            aria-label="Knowledge base filters"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Domain Filter */}
              <div>
                <label 
                  htmlFor="knowledge-domain-filter"
                  className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2"
                >
                  Domain
                </label>
                <select
                  id="knowledge-domain-filter"
                  value={selectedDomain}
                  onChange={(e) => setSelectedDomain(e.target.value)}
                  className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
                  aria-label="Filter by knowledge domain"
                >
                  <option value="">All Domains</option>
                  {availableDomains.map((domain) => (
                    <option key={domain} value={domain}>
                      {domain}
                    </option>
                  ))}
                </select>
              </div>

              {/* Source Filter */}
              <div>
                <label 
                  htmlFor="knowledge-source-filter"
                  className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2"
                >
                  Source
                </label>
                <select
                  id="knowledge-source-filter"
                  value={selectedSource}
                  onChange={(e) => setSelectedSource(e.target.value)}
                  className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
                  aria-label="Filter by knowledge source"
                >
                  <option value="">All Sources</option>
                  {availableSources.map((source) => (
                    <option key={source} value={source}>
                      {source}
                    </option>
                  ))}
                </select>
              </div>

              {/* Year Range */}
              <div>
                <label 
                  htmlFor="knowledge-year-min"
                  className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2"
                >
                  Year Range
                </label>
                <div className="flex space-x-2">
                  <input
                    id="knowledge-year-min"
                    type="number"
                    placeholder="Min"
                    value={yearRange.min || ''}
                    onChange={(e) =>
                      setYearRange({
                        ...yearRange,
                        min: e.target.value ? parseInt(e.target.value) : undefined,
                      })
                    }
                    className="flex-1 px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
                    aria-label="Minimum year"
                  />
                  <input
                    id="knowledge-year-max"
                    type="number"
                    placeholder="Max"
                    value={yearRange.max || ''}
                    onChange={(e) =>
                      setYearRange({
                        ...yearRange,
                        max: e.target.value ? parseInt(e.target.value) : undefined,
                      })
                    }
                    className="flex-1 px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
                    aria-label="Maximum year"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={resetFilters}
                className="text-sm text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:underline"
              >
                Reset Filters
              </button>
              <button
                type="button"
                onClick={() => setShowFilters(false)}
                className="text-sm text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2 rounded"
                aria-label="Close filters panel"
              >
                <XMarkIcon className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {isSearching && (
        <div className="flex justify-center py-12">
          <Loading size="lg" message="Searching knowledge base..." />
        </div>
      )}

      {/* Results */}
      {!isSearching && entries.length > 0 && (
        <>
          {/* Results Header */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-[#1E3A8A] dark:text-white mb-1" style={{ fontWeight: 600 }}>
                Search Results
              </h2>
              <p className="text-sm text-[#64748B] dark:text-[#94A3B8]">
                Found {totalFound} {totalFound === 1 ? 'entry' : 'entries'}
                {selectedDomain && ` in ${selectedDomain}`}
                {selectedSource && ` from ${selectedSource}`}
              </p>
            </div>
            {entries.length > 0 && (
              <button
                type="button"
                onClick={() => {
                  // Export all entries
                  const content = entries
                    .map(
                      (entry) =>
                        `Title: ${entry.title}\n\nSource: ${entry.source}\nDomain: ${entry.domain || 'N/A'}\nYear: ${entry.year || 'N/A'}\nSimilarity: ${Math.round(entry.similarity_score * 100)}%\n\n${entry.content}\n\nProvenance: ${entry.provenance_url || 'N/A'}\n\n---\n\n`
                    )
                    .join('\n');
                  const blob = new Blob([content], { type: 'text/plain' });
                  const url = window.URL.createObjectURL(blob);
                  const link = document.createElement('a');
                  link.href = url;
                  link.download = `knowledge_search_${new Date().toISOString().split('T')[0]}.txt`;
                  document.body.appendChild(link);
                  link.click();
                  link.remove();
                  window.URL.revokeObjectURL(url);
                }}
                className="px-4 py-2 text-sm font-medium text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 rounded-lg transition-colors flex items-center space-x-2"
              >
                <ArrowDownTrayIcon className="h-4 w-4" />
                <span>Export All</span>
              </button>
            )}
          </div>

          {/* Knowledge Cards */}
          <div className="space-y-4">
            {paginatedEntries.map((entry) => (
              <KnowledgeCard
                key={entry.id}
                entry={entry}
                isBookmarked={bookmarkedEntries.has(entry.id)}
                onBookmark={handleBookmark}
                onExport={handleExport}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center">
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                onPageChange={(page) => {
                  setCurrentPage(page);
                  // Scroll to top
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
              />
            </div>
          )}
        </>
      )}

      {/* Empty State */}
      {!isSearching && entries.length === 0 && searchQuery && !error && (
        <div className="text-center py-12 bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30">
          <BookOpenIcon className="h-12 w-12 text-[#64748B] dark:text-[#94A3B8] mx-auto mb-3" />
          <p className="text-[#64748B] dark:text-[#94A3B8]">No results found</p>
          <p className="text-sm text-[#64748B] dark:text-[#94A3B8] mt-2">
            Try adjusting your search query or filters
          </p>
        </div>
      )}

      {/* Initial State */}
      {!isSearching && entries.length === 0 && !searchQuery && (
        <div className="text-center py-12 bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30">
          <BookOpenIcon className="h-12 w-12 text-[#64748B] dark:text-[#94A3B8] mx-auto mb-3" />
          <p className="text-[#64748B] dark:text-[#94A3B8]">
            Enter a search query to browse the knowledge base
          </p>
          <p className="text-sm text-[#64748B] dark:text-[#94A3B8] mt-2">
            Search for medical guidelines, textbook content, research summaries, and more
          </p>
        </div>
      )}
    </div>
  );
}

