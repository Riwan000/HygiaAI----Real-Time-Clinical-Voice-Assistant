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
  PlusIcon,
  DocumentArrowUpIcon,
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
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  // Load available domains and sources, and all entries on mount
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [domainsRes, sourcesRes, allEntriesRes] = await Promise.all([
          ClinicalMemoryService.getKnowledgeDomains(),
          ClinicalMemoryService.getKnowledgeSources(),
          ClinicalMemoryService.searchKnowledgeBase({
            query: '', // Empty query to get all entries
            limit: 100,
            score_threshold: 0.0,
          }),
        ]);

        if (domainsRes.success && domainsRes.data) {
          setAvailableDomains(domainsRes.data);
        }
        if (sourcesRes.success && sourcesRes.data) {
          setAvailableSources(sourcesRes.data);
        }
        if (allEntriesRes.success && allEntriesRes.data) {
          setEntries(allEntriesRes.data.entries);
          setTotalFound(allEntriesRes.data.total_found);
          setDomains(allEntriesRes.data.domains);
          setSources(allEntriesRes.data.sources);
        }
      } catch (err) {
        console.error('Error loading initial data:', err);
      }
    };

    loadInitialData();
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
   * Perform search or filter existing entries
   */
  const handleSearch = async (page: number = 1) => {
    setIsSearching(true);
    setError(null);
    setCurrentPage(page);

    try {
      const response = await ClinicalMemoryService.searchKnowledgeBase({
        query: searchQuery.trim() || '', // Empty query returns all entries
        domain: selectedDomain || undefined,
        source: selectedSource || undefined,
        year_range: Object.keys(yearRange).length > 0 ? yearRange : undefined,
        limit: 100, // Get results for pagination (backend max is 500)
        score_threshold: searchQuery.trim() ? 0.3 : 0.0, // Lower threshold when showing all
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
   * Handle file upload
   */
  const handleFileUpload = async (file: File, domain?: string, source?: string, year?: number, author?: string) => {
    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    setUploadProgress(0);

    try {
      // Simulate progress (since we can't track actual upload progress easily)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await ClinicalMemoryService.uploadKnowledgeFile(file, {
        domain,
        source,
        year,
        author,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (response.success && response.data) {
        setUploadSuccess(`Successfully uploaded "${response.data.title}". Created ${response.data.chunks_created} chunks.`);
        setShowUploadModal(false);
        
        // Refresh the knowledge base
        setTimeout(() => {
          handleSearch(1);
        }, 1000);
      } else {
        setUploadError(response.error || 'Failed to upload file');
      }
    } catch (err: any) {
      console.error('Upload error:', err);
      // Extract error message from ApiError or other error types
      let errorMessage = 'Failed to upload file';
      if (err?.message) {
        errorMessage = err.message;
      } else if (typeof err === 'string') {
        errorMessage = err;
      } else if (err?.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err?.response?.data?.message) {
        errorMessage = err.response.data.message;
      }
      setUploadError(errorMessage);
    } finally {
      setUploading(false);
      setTimeout(() => {
        setUploadProgress(0);
        setUploadError(null);
        setUploadSuccess(null);
      }, 5000);
    }
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
            disabled={isSearching}
            className="px-6 py-3 bg-[#2563EB] dark:bg-[#3B82F6] text-white rounded-lg hover:bg-[#1E3A8A] dark:hover:bg-[#2563EB] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2"
            aria-label={isSearching ? 'Searching...' : searchQuery.trim() ? 'Search knowledge base' : 'Refresh knowledge base'}
            aria-disabled={isSearching}
          >
            <MagnifyingGlassIcon className="h-5 w-5" aria-hidden="true" />
            <span>{isSearching ? 'Searching...' : searchQuery.trim() ? 'Search' : 'Refresh'}</span>
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
          <button
            type="button"
            onClick={() => setShowUploadModal(true)}
            className="px-4 py-3 bg-green-600 dark:bg-green-500 text-white rounded-lg hover:bg-green-700 dark:hover:bg-green-600 transition-colors flex items-center space-x-2 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
            aria-label="Upload file to knowledge base"
          >
            <PlusIcon className="h-5 w-5" aria-hidden="true" />
            <span>Upload File</span>
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
                {searchQuery.trim() ? 'Search Results' : 'Knowledge Base'}
              </h2>
              <p className="text-sm text-[#64748B] dark:text-[#94A3B8]">
                {searchQuery.trim() 
                  ? `Found ${totalFound} ${totalFound === 1 ? 'entry' : 'entries'}`
                  : `Showing ${totalFound} ${totalFound === 1 ? 'entry' : 'entries'}`
                }
                {selectedDomain && ` in ${selectedDomain}`}
                {selectedSource && ` from ${selectedSource}`}
                {searchQuery.trim() && ` for "${searchQuery}"`}
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
      {!isSearching && entries.length === 0 && !error && (
        <div className="text-center py-12 bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30">
          <BookOpenIcon className="h-12 w-12 text-[#64748B] dark:text-[#94A3B8] mx-auto mb-3" />
          <p className="text-[#64748B] dark:text-[#94A3B8]">
            {searchQuery.trim() ? 'No results found' : 'No entries available'}
          </p>
          <p className="text-sm text-[#64748B] dark:text-[#94A3B8] mt-2">
            {searchQuery.trim() 
              ? 'Try adjusting your search query or filters'
              : 'The knowledge base appears to be empty. Please populate it first.'
            }
          </p>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50" onClick={() => !uploading && setShowUploadModal(false)}>
          <div className="bg-white dark:bg-[#1E293B] rounded-lg p-6 max-w-md w-full mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-[#1E3A8A] dark:text-white">Upload File to Knowledge Base</h3>
              <button
                type="button"
                onClick={() => !uploading && setShowUploadModal(false)}
                className="text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white"
                disabled={uploading}
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <FileUploadForm
              onUpload={handleFileUpload}
              uploading={uploading}
              uploadProgress={uploadProgress}
              error={uploadError}
              success={uploadSuccess}
              availableDomains={availableDomains}
              onClose={() => setShowUploadModal(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * File Upload Form Component
 */
interface FileUploadFormProps {
  onUpload: (file: File, domain?: string, source?: string, year?: number, author?: string) => Promise<void>;
  uploading: boolean;
  uploadProgress: number;
  error: string | null;
  success: string | null;
  availableDomains: string[];
  onClose: () => void;
}

function FileUploadForm({
  onUpload,
  uploading,
  uploadProgress,
  error,
  success,
  availableDomains,
  onClose,
}: FileUploadFormProps) {
  const [file, setFile] = useState<File | null>(null);
  const [domain, setDomain] = useState('');
  const [source, setSource] = useState('');
  const [year, setYear] = useState<number | undefined>(undefined);
  const [author, setAuthor] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const allowedTypes = ['.pdf', '.docx', '.doc', '.txt', '.md'];
      const fileExt = selectedFile.name.toLowerCase().substring(selectedFile.name.lastIndexOf('.'));
      
      if (!allowedTypes.includes(fileExt)) {
        alert(`Unsupported file type. Allowed: ${allowedTypes.join(', ')}`);
        return;
      }
      
      setFile(selectedFile);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      alert('Please select a file');
      return;
    }
    await onUpload(file, domain || undefined, source || undefined, year, author || undefined);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* File Input */}
      <div>
        <label htmlFor="file-upload" className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
          Select File (PDF, DOCX, TXT, MD)
        </label>
        <div className="flex items-center space-x-4">
          <label
            htmlFor="file-upload"
            className="flex-1 cursor-pointer px-4 py-3 border-2 border-dashed border-[#64748B] dark:border-[#475569] rounded-lg hover:border-[#2563EB] dark:hover:border-[#3B82F6] transition-colors flex items-center justify-center space-x-2"
          >
            <DocumentArrowUpIcon className="h-5 w-5 text-[#64748B] dark:text-[#94A3B8]" />
            <span className="text-sm text-[#64748B] dark:text-[#94A3B8]">
              {file ? file.name : 'Choose file...'}
            </span>
          </label>
          <input
            id="file-upload"
            type="file"
            accept=".pdf,.docx,.doc,.txt,.md"
            onChange={handleFileChange}
            className="hidden"
            disabled={uploading}
          />
        </div>
      </div>

      {/* Domain */}
      <div>
        <label htmlFor="upload-domain" className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
          Domain (Optional)
        </label>
        <select
          id="upload-domain"
          value={domain}
          onChange={(e) => setDomain(e.target.value)}
          className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
          disabled={uploading}
        >
          <option value="">Select domain...</option>
          {availableDomains.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
          <option value="clinical_reference">Clinical Reference</option>
          <option value="guidelines">Guidelines</option>
          <option value="research">Research</option>
        </select>
      </div>

      {/* Source */}
      <div>
        <label htmlFor="upload-source" className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
          Source (Optional)
        </label>
        <input
          id="upload-source"
          type="text"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder="e.g., Medical Journal, Textbook, etc."
          className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
          disabled={uploading}
        />
      </div>

      {/* Year & Author */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="upload-year" className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
            Year (Optional)
          </label>
          <input
            id="upload-year"
            type="number"
            value={year || ''}
            onChange={(e) => setYear(e.target.value ? parseInt(e.target.value) : undefined)}
            placeholder="2024"
            min="1900"
            max={new Date().getFullYear()}
            className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
            disabled={uploading}
          />
        </div>
        <div>
          <label htmlFor="upload-author" className="block text-sm font-medium text-[#0F172A] dark:text-white mb-2">
            Author (Optional)
          </label>
          <input
            id="upload-author"
            type="text"
            value={author}
            onChange={(e) => setAuthor(e.target.value)}
            placeholder="Author name"
            className="w-full px-3 py-2 border border-slate/30 dark:border-[#475569]/30 rounded-lg bg-white dark:bg-[#334155] text-[#0F172A] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30"
            disabled={uploading}
          />
        </div>
      </div>

      {/* Progress */}
      {uploading && (
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-[#64748B] dark:text-[#94A3B8]">Uploading...</span>
            <span className="text-sm text-[#64748B] dark:text-[#94A3B8]">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-[#F8FAFC] dark:bg-[#334155] rounded-full h-2">
            <div
              className="bg-[#2563EB] dark:bg-[#3B82F6] h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
        </div>
      )}

      {/* Success */}
      {success && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <p className="text-sm text-green-800 dark:text-green-300">{success}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-end space-x-3 pt-4">
        <button
          type="button"
          onClick={onClose}
          disabled={uploading}
          className="px-4 py-2 text-sm font-medium text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!file || uploading}
          className="px-4 py-2 bg-[#2563EB] dark:bg-[#3B82F6] text-white rounded-lg hover:bg-[#1E3A8A] dark:hover:bg-[#2563EB] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      </div>
    </form>
  );
}

