'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { Brain, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        // Store auth token or user data
        localStorage.setItem('auth_token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Always use window.location.href for reliable navigation in all environments
        window.location.href = '/dashboard';
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Quick login buttons for demo
  const quickLogin = (userEmail: string, userPassword: string) => {
    setEmail(userEmail);
    setPassword(userPassword);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
      <div className="w-full max-w-md px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Home
          </Link>
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
              <Brain className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">SmartSPD</h1>
              <p className="text-sm text-gray-500">Powered by Onyx AI</p>
            </div>
          </div>
          <h2 className="text-xl font-semibold text-gray-900">Sign in to your account</h2>
          <p className="text-gray-600 mt-2">Access your TPA dashboard and AI assistant</p>
        </div>

        {/* Demo Login Cards */}
        <div className="mb-6 space-y-3">
          <h3 className="text-sm font-medium text-gray-700 text-center">Demo Accounts</h3>
          <div className="grid grid-cols-2 gap-3">
            <Button
              variant="outline"
              onClick={() => quickLogin('admin@kemptongroup.com', 'KemptonAdmin2024!')}
              className="text-left h-auto p-3"
            >
              <div>
                <div className="font-medium text-sm">Admin</div>
                <div className="text-xs text-gray-500">Full Access</div>
              </div>
            </Button>
            <Button
              variant="outline"
              onClick={() => quickLogin('agent1@kemptongroup.com', 'KemptonAgent1!')}
              className="text-left h-auto p-3"
            >
              <div>
                <div className="font-medium text-sm">Agent</div>
                <div className="text-xs text-gray-500">CS Support</div>
              </div>
            </Button>
          </div>
        </div>

        {/* Login Form */}
        <Card className="p-6 shadow-lg border-0">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email address</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="admin@kemptongroup.com"
                className="mt-1"
              />
            </div>
            
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className="mt-1"
              />
            </div>

            {error && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md">
                {error}
              </div>
            )}

            <Button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700"
              disabled={isLoading}
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              Demo Environment - Use the quick login buttons above
            </p>
          </div>
        </Card>

        {/* Footer */}
        <div className="text-center mt-8 text-sm text-gray-500">
          <p>&copy; 2024 SmartSPD by Onyx AI. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
}