'use client';

import { MessageCircle, FileText, Users, BarChart3 } from 'lucide-react';
import { useEffect, useState } from 'react';

interface DashboardStats {
  active_conversations: number;
  documents_processed: number;
  active_users: number;
  avg_response_time: string;
  total_queries_today: number;
  success_rate: number;
  user_satisfaction: number;
  recent_activity: Array<{
    action: string;
    description: string;
    time: string;
  }>;
}

export default function DashboardPage() {
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Get user data from localStorage
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (error) {
        console.error('Failed to parse user data:', error);
      }
    }
  }, []);

  useEffect(() => {
    const fetchDashboardStats = async () => {
      try {
        setLoading(true);
        // For now, simulate API call with test data since analytics endpoint is disabled
        setTimeout(() => {
          setStats({
            active_conversations: 12,
            documents_processed: 45,
            active_users: 8,
            avg_response_time: "1.2s",
            total_queries_today: 156,
            success_rate: 94.5,
            user_satisfaction: 4.7,
            recent_activity: [
              { action: "Document Upload", description: "New SPD document processed", time: "2 minutes ago" },
              { action: "User Query", description: "Member question about deductibles", time: "5 minutes ago" },
              { action: "System Update", description: "Backend health check completed", time: "10 minutes ago" }
            ]
          });
          setLoading(false);
        }, 500);
      } catch (err) {
        console.error('Failed to fetch dashboard stats:', err);
        setError('Failed to load dashboard data');
        setLoading(false);
      }
    };

    fetchDashboardStats();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-lg shadow p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-3/4"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-white rounded-lg shadow p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">
              Welcome back, {user?.first_name || user?.email || 'User'}!
            </h1>
            <p className="text-sm sm:text-base text-gray-600">
              Here's an overview of your SmartSPD dashboard. Ready to assist your members?
            </p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 w-full sm:w-auto min-h-[44px]"
          >
            Refresh
          </button>
        </div>
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <StatCard
          title="Active Conversations"
          value={stats?.active_conversations.toString() || "0"}
          icon={<MessageCircle className="w-6 h-6 text-blue-600" />}
          change="+2.5%"
          changeType="increase"
        />
        <StatCard
          title="Documents Processed"
          value={stats?.documents_processed.toString() || "0"}
          icon={<FileText className="w-6 h-6 text-green-600" />}
          change="+12.3%"
          changeType="increase"
        />
        <StatCard
          title="Active Users"
          value={stats?.active_users.toString() || "0"}
          icon={<Users className="w-6 h-6 text-purple-600" />}
          change="+5.1%"
          changeType="increase"
        />
        <StatCard
          title="Avg Response Time"
          value={stats?.avg_response_time || "0.0s"}
          icon={<BarChart3 className="w-6 h-6 text-orange-600" />}
          change="-8.2%"
          changeType="decrease"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <div className="bg-white rounded-lg shadow p-4 sm:p-6">
          <h2 className="text-base sm:text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <QuickActionButton
              href="/dashboard/chat"
              icon={<MessageCircle className="w-5 h-5" />}
              title="Start New Conversation"
              description="Help a member with their health plan questions"
            />
            <QuickActionButton
              href="/dashboard/documents"
              icon={<FileText className="w-5 h-5" />}
              title="Upload Documents"
              description="Add new SPD or BPS files to the system"
            />
            <QuickActionButton
              href="/dashboard/analytics"
              icon={<BarChart3 className="w-5 h-5" />}
              title="View Analytics"
              description="Check performance metrics and insights"
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4 sm:p-6">
          <h2 className="text-base sm:text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
          <div className="space-y-4">
            {stats?.recent_activity && stats.recent_activity.length > 0 ? (
              stats.recent_activity.map((activity, index) => (
                <ActivityItem
                  key={index}
                  action={activity.action}
                  description={activity.description}
                  time={activity.time}
                />
              ))
            ) : (
              <div className="text-gray-500 text-sm">No recent activity</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ 
  title, 
  value, 
  icon, 
  change, 
  changeType 
}: {
  title: string;
  value: string;
  icon: React.ReactNode;
  change: string;
  changeType: 'increase' | 'decrease';
}) {
  const changeColor = changeType === 'increase' ? 'text-green-600' : 'text-red-600';
  
  return (
    <div className="bg-white rounded-lg shadow p-4 sm:p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs sm:text-sm font-medium text-gray-600">{title}</p>
          <p className="text-xl sm:text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className="flex-shrink-0">
          {icon}
        </div>
      </div>
      <div className="mt-3 sm:mt-4">
        <span className={`text-xs sm:text-sm font-medium ${changeColor}`}>
          {change}
        </span>
        <span className="text-xs sm:text-sm text-gray-500"> from last week</span>
      </div>
    </div>
  );
}

function QuickActionButton({
  href,
  icon,
  title,
  description
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <a
      href={href}
      className="flex items-center p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors min-h-[60px] touch-manipulation"
    >
      <div className="flex-shrink-0 mr-3 text-blue-600">
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">{title}</p>
        <p className="text-xs sm:text-sm text-gray-500">{description}</p>
      </div>
    </a>
  );
}

function ActivityItem({
  action,
  description,
  time
}: {
  action: string;
  description: string;
  time: string;
}) {
  return (
    <div className="flex items-start space-x-3">
      <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900">{action}</p>
        <p className="text-sm text-gray-500">{description}</p>
        <p className="text-xs text-gray-400">{time}</p>
      </div>
    </div>
  );
}