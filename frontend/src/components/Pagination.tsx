/**
 * Pagination Component
 * 
 * Pagination controls for case results.
 */

import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  pageSize: number;
  totalItems: number;
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  pageSize,
  totalItems,
}: PaginationProps) {
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  const getPageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisible = 5;

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) {
          pages.push(i);
        }
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) {
          pages.push(i);
        }
        pages.push('...');
        pages.push(totalPages);
      }
    }

    return pages;
  };

  return (
    <div className="flex items-center justify-between border-t border-slate/20 px-4 py-3 sm:px-6">
      <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className={clsx(
                'relative inline-flex items-center px-4 py-2 border border-slate/30 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2',
                currentPage === 1
                  ? 'bg-slate/20 text-slate cursor-not-allowed'
                  : 'bg-white text-charcoal hover:bg-slate/5'
              )}
              aria-label="Go to previous page"
              aria-disabled={currentPage === 1}
            >
              Previous
            </button>
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className={clsx(
                'ml-3 relative inline-flex items-center px-4 py-2 border border-neutral-slate/30 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2',
                currentPage === totalPages
                  ? 'bg-neutral-slate/20 text-neutral-slate cursor-not-allowed'
                  : 'bg-white text-neutral-charcoal hover:bg-neutral-snow'
              )}
              aria-label="Go to next page"
              aria-disabled={currentPage === totalPages}
            >
              Next
            </button>
      </div>
      <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-charcoal" role="status" aria-live="polite">
            Showing <span className="font-medium">{startItem}</span> to{' '}
            <span className="font-medium">{endItem}</span> of{' '}
            <span className="font-medium">{totalItems}</span> results
          </p>
        </div>
        <div>
          <nav
            className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px"
            aria-label="Pagination"
          >
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className={clsx(
                'relative inline-flex items-center px-2 py-2 rounded-l-md border border-slate/30 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2',
                currentPage === 1
                  ? 'bg-slate/20 text-slate cursor-not-allowed'
                  : 'bg-white text-charcoal hover:bg-slate/5'
              )}
              aria-label="Go to previous page"
              aria-disabled={currentPage === 1}
            >
              <ChevronLeftIcon className="h-5 w-5" aria-hidden="true" />
            </button>
            {getPageNumbers().map((page, index) => (
              <button
                key={index}
                onClick={() => typeof page === 'number' && onPageChange(page)}
                disabled={page === '...'}
                className={clsx(
                  'relative inline-flex items-center px-4 py-2 border border-slate/30 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2',
                    page === currentPage
                    ? 'z-10 bg-accentLight/20 border-primary text-primary'
                    : page === '...'
                    ? 'bg-white text-charcoal cursor-default'
                    : 'bg-white text-charcoal hover:bg-slate/5'
                )}
                aria-label={page === '...' ? 'More pages' : `Go to page ${page}`}
                aria-current={page === currentPage ? 'page' : undefined}
                aria-disabled={page === '...'}
              >
                {page}
              </button>
            ))}
            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className={clsx(
                'relative inline-flex items-center px-2 py-2 rounded-r-md border border-slate/30 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#2563EB] focus:ring-offset-2',
                currentPage === totalPages
                  ? 'bg-slate/20 text-slate cursor-not-allowed'
                  : 'bg-white text-charcoal hover:bg-slate/5'
              )}
              aria-label="Go to next page"
              aria-disabled={currentPage === totalPages}
            >
              <ChevronRightIcon className="h-5 w-5" aria-hidden="true" />
            </button>
          </nav>
        </div>
      </div>
    </div>
  );
}

