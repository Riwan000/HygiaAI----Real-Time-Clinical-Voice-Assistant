/**
 * Knowledge Base Page
 * 
 * Displays searchable interface for browsing medical knowledge base
 */

import { Breadcrumbs } from '../components/Breadcrumbs';
import { KnowledgeBrowser } from '../components/KnowledgeBrowser';
import { BookOpenIcon } from '@heroicons/react/24/outline';

export function Knowledge() {
  return (
    <div className="max-w-7xl mx-auto">
      <Breadcrumbs items={[{ name: 'Knowledge Base' }]} />

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-3">
          <BookOpenIcon className="h-8 w-8 text-[#2563EB] dark:text-[#60A5FA]" />
          <h1 className="text-3xl font-semibold text-[#1E3A8A] dark:text-white font-heading" style={{ fontWeight: 600 }}>
            Knowledge Base
          </h1>
        </div>
        <p className="text-[#64748B] dark:text-[#94A3B8] text-base">
          Search and browse medical knowledge, guidelines, textbook content, and research summaries
        </p>
      </div>

      {/* Knowledge Browser */}
      <KnowledgeBrowser />
    </div>
  );
}

