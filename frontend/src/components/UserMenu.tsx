/**
 * User Menu Component
 * 
 * User profile dropdown menu with settings and logout options.
 */

import { Fragment, useState } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { UserCircleIcon, Cog6ToothIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline';
import { Link } from 'react-router-dom';
import { clsx } from '../utils/clsx';

export function UserMenu() {
  const [user] = useState({
    name: 'Dr. User',
    email: 'doctor@hygiaai.com',
  });

  const menuItems = [
    {
      name: 'Profile',
      href: '/profile',
      icon: UserCircleIcon,
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Cog6ToothIcon,
    },
    {
      name: 'Sign out',
      href: '/logout',
      icon: ArrowRightOnRectangleIcon,
      onClick: () => {
        // Handle logout
        console.log('Logout');
      },
    },
  ];

  return (
    <Menu as="div" className="relative">
      <Menu.Button className="flex items-center space-x-2.5 p-2 rounded-lg text-[#64748B] dark:text-[#94A3B8] hover:text-[#0F172A] dark:hover:text-white hover:bg-[#64748B]/10 dark:hover:bg-[#475569]/30 focus:outline-none focus:ring-2 focus:ring-[#2563EB]/30 transition-all">
        <UserCircleIcon className="h-5 w-5" />
        <span className="hidden sm:block text-sm font-medium text-[#0F172A] dark:text-white">
          {user.name}
        </span>
      </Menu.Button>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right divide-y divide-[#64748B]/20 dark:divide-[#475569]/30 rounded-xl bg-white dark:bg-[#1E293B] shadow-lg ring-1 ring-[#64748B]/10 dark:ring-[#475569]/30 border border-[#64748B]/20 dark:border-[#475569]/30 focus:outline-none">
          <div className="px-4 py-3">
            <p className="text-sm font-semibold text-[#1E3A8A] dark:text-white" style={{ fontWeight: 600 }}>{user.name}</p>
            <p className="text-sm text-[#64748B] dark:text-[#94A3B8] truncate">{user.email}</p>
          </div>
          <div className="py-1">
            {menuItems.map((item) => (
              <Menu.Item key={item.name}>
                {({ active }) => (
                  <Link
                    to={item.href}
                    onClick={item.onClick}
                    className={clsx(
                      active
                        ? 'bg-white dark:bg-[#334155] text-[#1E3A8A] dark:text-white'
                        : 'text-[#0F172A] dark:text-[#F1F5F9]',
                      'group flex items-center px-4 py-2.5 text-sm transition-colors rounded-lg mx-1'
                    )}
                  >
                    <item.icon
                      className="mr-3 h-5 w-5 text-[#64748B] dark:text-[#94A3B8] group-hover:text-[#1E3A8A] dark:group-hover:text-white transition-colors"
                      aria-hidden="true"
                    />
                    {item.name}
                  </Link>
                )}
              </Menu.Item>
            ))}
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
}

