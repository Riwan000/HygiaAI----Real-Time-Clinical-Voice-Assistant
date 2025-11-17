/**
 * Breadcrumb Navigation Component
 * 
 * Displays navigation breadcrumbs for hierarchical page structure.
 */

import { Link } from 'react-router-dom';
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

export type BreadcrumbItem = {
  name: string;
  href?: string;
};

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  return (
    <nav className="flex mb-4" aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2">
        <li>
                  <Link
                    to="/"
                    className="text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white transition-colors"
                  >
                    <HomeIcon className="h-4 w-4" aria-hidden="true" />
                    <span className="sr-only">Home</span>
                  </Link>
                </li>
                {items.map((item, index) => {
                  const isLast = index === items.length - 1;
                  return (
                    <li key={item.name}>
                      <div className="flex items-center">
                        <ChevronRightIcon
                          className="h-4 w-4 text-[#64748B] dark:text-[#94A3B8] mx-2"
                          aria-hidden="true"
                        />
                        {isLast || !item.href ? (
                          <span
                            className={clsx(
                              'text-sm font-medium',
                              isLast
                                ? 'text-[#1E3A8A] dark:text-white'
                                : 'text-[#64748B] dark:text-[#94A3B8]'
                            )}
                            aria-current={isLast ? 'page' : undefined}
                          >
                            {item.name}
                          </span>
                        ) : (
                          <Link
                            to={item.href}
                            className="text-sm font-medium text-[#64748B] dark:text-[#94A3B8] hover:text-[#1E3A8A] dark:hover:text-white transition-colors"
                          >
                            {item.name}
                          </Link>
                        )}
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

