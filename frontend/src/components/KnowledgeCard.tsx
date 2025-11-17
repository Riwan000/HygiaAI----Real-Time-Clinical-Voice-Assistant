/**
 * KnowledgeCard Component
 * 
 * Displays a single knowledge base entry in a card format
 */

import { useState } from 'react';
import {
  BookOpenIcon,
  LinkIcon,
  BookmarkIcon,
  BookmarkSlashIcon,
  ArrowDownTrayIcon,
  CalendarIcon,
  TagIcon,
} from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';
import type { KnowledgeEntry } from '../types';

interface KnowledgeCardProps {
  entry: KnowledgeEntry;
  isBookmarked?: boolean;
  onBookmark?: (entry: KnowledgeEntry, bookmarked: boolean) => void;
  onExport?: (entry: KnowledgeEntry) => void;
  className?: string;
}

export function KnowledgeCard({
  entry,
  isBookmarked = false,
  onBookmark,
  onExport,
  className = '',
}: KnowledgeCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [bookmarked, setBookmarked] = useState(isBookmarked);

  const handleBookmark = () => {
    const newBookmarked = !bookmarked;
    setBookmarked(newBookmarked);
    onBookmark?.(entry, newBookmarked);
  };

  const handleExport = () => {
    onExport?.(entry);
  };

  // Truncate content for preview
  const previewLength = 200;
  const contentPreview = entry.content.length > previewLength
    ? entry.content.substring(0, previewLength) + '...'
    : entry.content;

  // Format similarity score as percentage
  const similarityPercent = Math.round(entry.similarity_score * 100);

  return (
    <div
      className={clsx(
        'bg-white dark:bg-[#1E293B] rounded-lg border border-slate/20 dark:border-[#475569]/30 p-6 hover:shadow-md transition-shadow',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <BookOpenIcon className="h-5 w-5 text-[#2563EB] dark:text-[#60A5FA]" />
            <h3 className="text-lg font-semibold text-[#1E3A8A] dark:text-white" style={{ fontWeight: 600 }}>
              {entry.title}
            </h3>
          </div>

          {/* Metadata */}
          <div className="flex flex-wrap items-center gap-3 text-sm text-[#64748B] dark:text-[#94A3B8]">
            {entry.source && (
              <span className="flex items-center">
                <span className="font-medium">Source:</span> {entry.source}
              </span>
            )}
            {entry.domain && (
              <span className="flex items-center">
                <TagIcon className="h-4 w-4 mr-1" />
                {entry.domain}
              </span>
            )}
            {entry.year && (
              <span className="flex items-center">
                <CalendarIcon className="h-4 w-4 mr-1" />
                {entry.year}
              </span>
            )}
            <span className="px-2 py-0.5 bg-[#2563EB]/10 dark:bg-[#2563EB]/20 text-[#2563EB] dark:text-[#60A5FA] rounded text-xs font-semibold">
              {similarityPercent}% match
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center space-x-2 ml-4">
          {onBookmark && (
            <button
              type="button"
              onClick={handleBookmark}
              className={clsx(
                'p-2 rounded-lg transition-colors',
                bookmarked
                  ? 'text-yellow-500 dark:text-yellow-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20'
                  : 'text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30'
              )}
              aria-label={bookmarked ? 'Remove bookmark' : 'Add bookmark'}
            >
              {bookmarked ? (
                <BookmarkIcon className="h-5 w-5 fill-current" />
              ) : (
                <BookmarkSlashIcon className="h-5 w-5" />
              )}
            </button>
          )}
          {onExport && (
            <button
              type="button"
              onClick={handleExport}
              className="p-2 rounded-lg text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 transition-colors"
              aria-label="Export entry"
            >
              <ArrowDownTrayIcon className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="mb-4">
        <p className="text-sm text-[#0F172A] dark:text-white leading-relaxed">
          {expanded ? entry.content : contentPreview}
        </p>
        {entry.content.length > previewLength && (
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="mt-2 text-sm text-[#2563EB] dark:text-[#60A5FA] hover:underline"
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-slate/20 dark:border-[#475569]/30">
        {entry.provenance_url && (
          <a
            href={entry.provenance_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center text-sm text-[#2563EB] dark:text-[#60A5FA] hover:underline"
          >
            <LinkIcon className="h-4 w-4 mr-1" />
            View source
          </a>
        )}
        <div className="text-xs text-[#64748B] dark:text-[#94A3B8]">
          ID: {entry.id.substring(0, 8)}...
        </div>
      </div>
    </div>
  );
}

