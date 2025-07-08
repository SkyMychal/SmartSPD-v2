'use client';

import { useEffect, useState } from 'react';
import { Bell, Search } from 'lucide-react';

export function DashboardHeader() {
  const [user, setUser] = useState<any>(null);

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
    <div className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          {/* Search */}
          <div className="flex-1 max-w-lg">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Search health plans, documents, or ask a question..."
              />
            </div>
          </div>

          {/* Right side */}
          <div className="flex items-center space-x-4">
            {/* Notifications */}
            <button
              type="button"
              className="relative p-2 text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded-md"
            >
              <span className="sr-only">View notifications</span>
              <Bell className="h-6 w-6" />
              {/* Notification badge */}
              <span className="absolute top-0 right-0 block h-2 w-2 rounded-full bg-red-400 ring-2 ring-white" />
            </button>

            {/* User info */}
            <div className="flex items-center space-x-3">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-gray-900">
                  {user?.first_name ? `${user.first_name} ${user.last_name}` : user?.email || 'User'}
                </p>
                <p className="text-xs text-gray-500">
                  {user?.role === 'tpa_admin' ? 'TPA Administrator' : 'Customer Service Agent'}
                </p>
              </div>
              <img
                className="h-10 w-10 rounded-full border-2 border-gray-200"
                src={`https://ui-avatars.com/api/?name=${encodeURIComponent(user?.first_name ? `${user.first_name} ${user.last_name}` : user?.email || 'User')}&background=3b82f6&color=fff`}
                alt=""
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}