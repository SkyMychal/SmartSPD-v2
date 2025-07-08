'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Users, 
  Building, 
  Activity, 
  Settings, 
  Shield,
  BarChart3,
  Database,
  Bell
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const adminNavigation = [
  { name: 'Dashboard', href: '/admin', icon: BarChart3 },
  { name: 'TPAs', href: '/admin/tpas', icon: Building },
  { name: 'Users', href: '/admin/users', icon: Users },
  { name: 'System Health', href: '/admin/system', icon: Activity },
  { name: 'Security', href: '/admin/security', icon: Shield },
  { name: 'Database', href: '/admin/database', icon: Database },
  { name: 'Notifications', href: '/admin/notifications', icon: Bell },
  { name: 'Settings', href: '/admin/settings', icon: Settings },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('user');
    
    if (!token || !storedUser) {
      router.push('/login');
      return;
    }
    
    try {
      const userData = JSON.parse(storedUser);
      setUser(userData);
      
      // Check if user is admin
      if (userData.role !== 'TPA_ADMIN') {
        router.push('/dashboard');
        return;
      }
    } catch (error) {
      console.error('Failed to parse user data:', error);
      router.push('/login');
      return;
    }
    
    setIsLoading(false);
  }, [router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Admin Header */}
      <div className="bg-red-600 border-b border-red-700">
        <div className="px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-red-100" />
              <span className="text-red-100 font-medium">System Administration</span>
            </div>
            <Link 
              href="/dashboard"
              className="text-red-100 hover:text-white text-sm font-medium"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Admin Sidebar */}
        <div className="w-64 bg-white shadow-sm border-r border-gray-200 min-h-screen">
          <nav className="p-4 space-y-2">
            {adminNavigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-100 text-blue-900'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <item.icon className={`w-5 h-5 ${
                    isActive ? 'text-blue-600' : 'text-gray-500'
                  }`} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1">
          {children}
        </div>
      </div>
    </div>
  );
}