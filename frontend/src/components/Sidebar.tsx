/**
 * Sidebar Navigation Component
 * 
 * Main navigation sidebar with menu items and responsive behavior.
 */

import { Link, useLocation } from 'react-router-dom';
import {
  HomeIcon,
  DocumentTextIcon,
  MicrophoneIcon,
  ChartBarIcon,
  ClockIcon,
  BookOpenIcon,
  Cog6ToothIcon,
  ArrowUpTrayIcon,
  EyeIcon,
} from '@heroicons/react/24/outline';
import { clsx } from '../utils/clsx';

interface SidebarProps {
  onClose?: () => void;
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Case Viewer', href: '/case-viewer', icon: EyeIcon },
  { name: 'SOAP Notes', href: '/soap-notes', icon: DocumentTextIcon },
  { name: 'Live Transcription', href: '/transcription', icon: MicrophoneIcon },
  { name: 'Multimodal Input', href: '/multimodal-input', icon: ArrowUpTrayIcon },
  { name: 'Trends & Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Case Timeline', href: '/timeline', icon: ClockIcon },
  { name: 'Knowledge Base', href: '/knowledge', icon: BookOpenIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

export function Sidebar({ onClose }: SidebarProps) {
  const location = useLocation();

  return (
    <aside 
      id="main-navigation"
      className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 lg:pt-14 bg-[#1E3A8A] dark:bg-[#0F172A] border-r border-primaryDark/20 dark:border-[#1E293B]"
      role="navigation"
      aria-label="Main navigation"
      tabIndex={-1}
    >
      <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto" role="list">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.name}
              to={item.href}
              onClick={onClose}
              className={clsx(
                'group flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-[#1E3A8A] dark:focus:ring-offset-[#0F172A]',
                isActive
                  ? 'bg-primary/20 dark:bg-[#2563EB]/20 text-white border-l-4 border-primary dark:border-[#2563EB] shadow-sm'
                  : 'text-white/90 dark:text-[#94A3B8] hover:bg-primary/10 dark:hover:bg-[#2563EB]/10 hover:text-white'
              )}
              aria-current={isActive ? 'page' : undefined}
              role="listitem"
            >
              <item.icon
                className={clsx(
                  'mr-3 h-5 w-5 flex-shrink-0 transition-all',
                  isActive
                    ? 'text-white'
                    : 'text-white/90 group-hover:text-white group-hover:scale-110'
                )}
                aria-hidden="true"
              />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Footer Section */}
      <div className="px-4 py-4 border-t border-white/10">
        <p className="text-xs text-white/60 dark:text-[#64748B]">
          HygiaAI v1.0.0
        </p>
      </div>
    </aside>
  );
}

