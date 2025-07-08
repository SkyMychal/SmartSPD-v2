'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { LandingPage } from '@/components/landing/landing-page';
import { LoadingSpinner } from '@/components/ui/loading-spinner';

export default function Home() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const router = useRouter();

  useEffect(() => {
    // Check for stored auth token
    const token = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('user');
    
    if (token && storedUser) {
      try {
        const user = JSON.parse(storedUser);
        setUser(user);
        
        // Always use window.location.href for reliable navigation in all environments
        window.location.href = '/dashboard';
        return;
      } catch (err) {
        // Invalid stored data, clear it
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
      }
    }
    
    // No valid authentication found, show landing page
    setIsLoading(false);
  }, [router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-2">Authentication Error</h1>
          <p className="text-gray-600">{error.message}</p>
          <a 
            href="/login"
            className="mt-4 inline-block bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Try Again
          </a>
        </div>
      </div>
    );
  }

  // Show landing page for non-authenticated users
  return <LandingPage />;
}
