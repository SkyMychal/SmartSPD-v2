'use client';

import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  MessageCircle,
  FileText,
  Users,
  BarChart3,
  Settings,
  Brain,
  X,
  Menu,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Chat Assistant', href: '/dashboard/chat', icon: MessageCircle },
  { name: 'Documents', href: '/dashboard/documents', icon: FileText },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  { name: 'Users', href: '/dashboard/users', icon: Users },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export function DashboardSidebar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [user, setUser] = useState<any>(null);
  const pathname = usePathname();

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Failed to parse user data:', error);
      }
    }
  }, []);

  return (
    <>
      {/* Mobile menu */}
      <div className={cn(
        'fixed inset-0 z-50 lg:hidden',
        mobileMenuOpen ? 'block' : 'hidden'
      )}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setMobileMenuOpen(false)} />
        <div className="fixed inset-y-0 left-0 z-50 w-64 bg-white">
          <SidebarContent pathname={pathname} user={user} onClose={() => setMobileMenuOpen(false)} />
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-40 lg:flex lg:w-64 lg:flex-col">
        <div className="flex min-h-0 flex-1 flex-col border-r border-gray-200 bg-white">
          <SidebarContent pathname={pathname} user={user} />
        </div>
      </div>

      {/* Mobile menu button */}
      <div className="lg:hidden">
        <button
          type="button"
          className="fixed top-4 left-4 z-40 inline-flex items-center justify-center rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          onClick={() => setMobileMenuOpen(true)}
        >
          <Menu className="h-6 w-6" aria-hidden="true" />
        </button>
      </div>
    </>
  );
}

function SidebarContent({ 
  pathname, 
  user, 
  onClose 
}: { 
  pathname: string; 
  user: any; 
  onClose?: () => void;
}) {
  return (
    <div className="flex flex-1 flex-col overflow-y-auto pt-5 pb-4">
      {/* Close button for mobile */}
      {onClose && (
        <div className="flex items-center justify-between px-4 mb-4">
          <div /> {/* Spacer */}
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-500"
            onClick={onClose}
          >
            <X className="h-6 w-6" />
          </button>
        </div>
      )}

      {/* Logo */}
      <div className="flex items-center flex-shrink-0 px-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">SmartSPD</h1>
            <p className="text-xs text-gray-500">Powered by Onyx AI</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="mt-8 flex-1 space-y-1 bg-white px-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <a
              key={item.name}
              href={item.href}
              className={cn(
                'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors',
                isActive
                  ? 'bg-blue-100 text-blue-900'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              )}
              onClick={onClose}
            >
              <item.icon
                className={cn(
                  'mr-3 h-5 w-5 flex-shrink-0',
                  isActive ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-500'
                )}
                aria-hidden="true"
              />
              {item.name}
            </a>
          );
        })}
      </nav>

      {/* User info */}
      <div className="flex-shrink-0 border-t border-gray-200 p-4">
        <div className="flex items-center">
          <div>
            <img
              className="inline-block h-10 w-10 rounded-full"
              src={`https://ui-avatars.com/api/?name=${encodeURIComponent(user?.first_name ? `${user.first_name} ${user.last_name}` : user?.email || 'User')}&background=3b82f6&color=fff`}
              alt=""
            />
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-700">
              {user?.first_name ? `${user.first_name} ${user.last_name}` : user?.email || 'User'}
            </p>
            <p className="text-xs text-gray-500">
              {user?.email}
            </p>
          </div>
        </div>
        <div className="mt-3">
          <button
            onClick={() => {
              localStorage.removeItem('auth_token');
              localStorage.removeItem('user');
              window.location.href = '/';
            }}
            className="block w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
          >
            Sign out
          </button>
        </div>
      </div>
    </div>
  );
}