/**
 * Header Component
 * 
 * Application header with logo, navigation, and user menu.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Bars3Icon, 
  XMarkIcon,
  UserCircleIcon,
  Cog6ToothIcon,
  MoonIcon,
  SunIcon,
} from '@heroicons/react/24/outline';
import { useTheme } from '../hooks/useTheme';
import { UserMenu } from './UserMenu';
import { Sidebar } from './Sidebar';
import { OfflineStatusBadge } from './OfflineStatusBadge';

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="bg-white dark:bg-[#1E293B] shadow-sm border-b border-[#64748B]/20 dark:border-[#475569]/30 sticky top-0 z-50">
      <div className="mx-auto px-4 sm:px-6 lg:px-8 max-w-full">
        <div className="flex justify-between items-center h-14">
          {/* Logo and Mobile Menu Button */}
          <div className="flex items-center">
            <button
              type="button"
              className="lg:hidden p-2 rounded-lg text-[#64748B] dark:text-[#94A3B8] hover:text-[#0F172A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30 transition-all"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? (
                <XMarkIcon className="h-5 w-5" />
              ) : (
                <Bars3Icon className="h-5 w-5" />
              )}
            </button>
            <Link
              to="/"
              className="ml-2 lg:ml-0 flex items-center space-x-2.5 hover:opacity-80 transition-opacity"
            >
              <div className="h-8 w-8 bg-gradient-to-br from-[#2563EB] to-[#8B5CF6] rounded-lg flex items-center justify-center shadow-sm">
                <span className="text-white font-bold text-sm">H</span>
              </div>
              <span className="text-lg font-semibold text-[#1E3A8A] dark:text-white" style={{ fontWeight: 600 }}>
                HygiaAI
              </span>
            </Link>
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center space-x-2">
            {/* Offline Status Badge */}
            <OfflineStatusBadge />

            {/* Theme Toggle */}
            <button
              type="button"
              onClick={toggleTheme}
              className="p-2 rounded-lg text-[#64748B] dark:text-[#94A3B8] hover:text-[#0F172A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30 transition-all"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? (
                <SunIcon className="h-5 w-5" />
              ) : (
                <MoonIcon className="h-5 w-5" />
              )}
            </button>

            {/* User Menu */}
            <UserMenu />
          </div>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="lg:hidden">
          <div
            className="fixed inset-0 bg-[#0F172A] bg-opacity-50 z-40 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 w-64 bg-[#1E3A8A] z-50 shadow-xl">
            <Sidebar onClose={() => setMobileMenuOpen(false)} />
          </div>
        </div>
      )}
    </header>
  );
}

