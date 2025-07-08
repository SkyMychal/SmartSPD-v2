'use client';

import { useState, useEffect } from 'react';
import { 
  Users, 
  TrendingUp, 
  Activity,
  AlertTriangle,
  CheckCircle,
  BarChart,
  Eye,
  MessageSquare,
  FileText,
  UserCheck,
  UserX
} from 'lucide-react';

interface EngagementMetrics {
  total_users: number;
  active_users: number;
  engagement_rate: number;
  highly_engaged_users: number;
  moderately_engaged_users: number;
  lightly_engaged_users: number;
  inactive_users: number;
  avg_activities_per_active_user: number;
}

interface FeatureUsage {
  feature_usage_counts: Record<string, number>;
  feature_unique_users: Record<string, number>;
  most_used_feature: string;
  least_used_feature: string;
}

interface ActivityInsights {
  insights: string[];
  recommendations: string[];
  engagement_summary: {
    engagement_rate: number;
    total_users: number;
    active_users: number;
  };
  top_features: [string, number][];
}

export default function UserActivityPage() {
  const [engagementMetrics, setEngagementMetrics] = useState<EngagementMetrics | null>(null);
  const [featureUsage, setFeatureUsage] = useState<FeatureUsage | null>(null);
  const [insights, setInsights] = useState<ActivityInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState(30);
  const [selectedTPA] = useState<string>('');

  useEffect(() => {
    fetchActivityData();
  }, [dateRange, selectedTPA]);

  const fetchActivityData = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      params.append('days', dateRange.toString());
      if (selectedTPA) params.append('tpa_id', selectedTPA);

      const [engagementRes, featureRes, insightsRes] = await Promise.all([
        fetch(`/api/v1/user-activity/engagement-metrics?${params}`),
        fetch(`/api/v1/user-activity/feature-usage?${params}`),
        fetch(`/api/v1/user-activity/insights?${params}`)
      ]);

      if (!engagementRes.ok || !featureRes.ok || !insightsRes.ok) {
        throw new Error('Failed to fetch activity data');
      }

      const [engagementData, featureData, insightsData] = await Promise.all([
        engagementRes.json(),
        featureRes.json(),
        insightsRes.json()
      ]);

      setEngagementMetrics(engagementData);
      setFeatureUsage(featureData);
      setInsights(insightsData);
    } catch (error) {
      console.error('Failed to fetch activity data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEngagementColor = (rate: number) => {
    if (rate >= 80) return 'text-green-600';
    if (rate >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getFeatureIcon = (feature: string) => {
    const iconMap: Record<string, any> = {
      chat_queries: MessageSquare,
      document_management: FileText,
      user_management: Users,
      analytics_viewing: BarChart,
      admin_functions: UserCheck,
      authentication: Eye
    };
    
    const IconComponent = iconMap[feature] || Activity;
    return <IconComponent className="w-5 h-5" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">User Activity Analytics</h1>
          <p className="text-gray-600">Monitor user engagement and platform usage patterns</p>
        </div>
        <div className="flex gap-2">
          <select
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={dateRange}
            onChange={(e) => setDateRange(Number(e.target.value))}
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Engagement Overview */}
      {engagementMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Users</p>
                <p className="text-2xl font-bold text-gray-900">{engagementMetrics.total_users}</p>
              </div>
              <Users className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Users</p>
                <p className="text-2xl font-bold text-green-600">{engagementMetrics.active_users}</p>
              </div>
              <UserCheck className="w-8 h-8 text-green-600" />
            </div>
            <p className="text-xs text-gray-500 mt-2">{engagementMetrics.engagement_rate.toFixed(1)}% engagement rate</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Highly Engaged</p>
                <p className="text-2xl font-bold text-purple-600">{engagementMetrics.highly_engaged_users}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-purple-600" />
            </div>
            <p className="text-xs text-gray-500 mt-2">100+ activities</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Inactive Users</p>
                <p className="text-2xl font-bold text-red-600">{engagementMetrics.inactive_users}</p>
              </div>
              <UserX className="w-8 h-8 text-red-600" />
            </div>
            <p className="text-xs text-gray-500 mt-2">No recent activity</p>
          </div>
        </div>
      )}

      {/* Engagement Distribution */}
      {engagementMetrics && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">User Engagement Distribution</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{engagementMetrics.highly_engaged_users}</div>
              <div className="text-sm text-gray-600">Highly Engaged</div>
              <div className="text-xs text-gray-500">100+ activities</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{engagementMetrics.moderately_engaged_users}</div>
              <div className="text-sm text-gray-600">Moderately Engaged</div>
              <div className="text-xs text-gray-500">20-100 activities</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{engagementMetrics.lightly_engaged_users}</div>
              <div className="text-sm text-gray-600">Lightly Engaged</div>
              <div className="text-xs text-gray-500">1-19 activities</div>
            </div>
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">{engagementMetrics.inactive_users}</div>
              <div className="text-sm text-gray-600">Inactive</div>
              <div className="text-xs text-gray-500">No activities</div>
            </div>
          </div>
        </div>
      )}

      {/* Feature Usage */}
      {featureUsage && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Feature Usage</h3>
            <div className="space-y-4">
              {Object.entries(featureUsage.feature_usage_counts).map(([feature, count]) => {
                const userCount = featureUsage.feature_unique_users[feature] || 0;
                const maxCount = Math.max(...Object.values(featureUsage.feature_usage_counts));
                const percentage = (count / maxCount) * 100;
                
                return (
                  <div key={feature} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        {getFeatureIcon(feature)}
                        <span className="text-sm font-medium text-gray-900">
                          {feature.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600">
                        {count} uses • {userCount} users
                      </div>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage Insights</h3>
            <div className="space-y-4">
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <span className="font-medium text-green-900">Most Used Feature</span>
                </div>
                <p className="text-sm text-green-700 mt-1">
                  {featureUsage.most_used_feature?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </p>
              </div>
              
              <div className="p-4 bg-yellow-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-600" />
                  <span className="font-medium text-yellow-900">Least Used Feature</span>
                </div>
                <p className="text-sm text-yellow-700 mt-1">
                  {featureUsage.least_used_feature?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                </p>
              </div>
              
              {engagementMetrics && (
                <div className="p-4 bg-blue-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-blue-600" />
                    <span className="font-medium text-blue-900">Average Activity</span>
                  </div>
                  <p className="text-sm text-blue-700 mt-1">
                    {engagementMetrics.avg_activities_per_active_user.toFixed(1)} actions per active user
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Insights and Recommendations */}
      {insights && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Key Insights</h3>
            <div className="space-y-3">
              {insights.insights.length > 0 ? (
                insights.insights.map((insight, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg">
                    <Eye className="w-5 h-5 text-blue-600 mt-0.5" />
                    <p className="text-sm text-blue-900">{insight}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">No significant insights detected for this period.</p>
              )}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendations</h3>
            <div className="space-y-3">
              {insights.recommendations.length > 0 ? (
                insights.recommendations.map((recommendation, index) => (
                  <div key={index} className="flex items-start gap-3 p-3 bg-green-50 rounded-lg">
                    <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                    <p className="text-sm text-green-900">{recommendation}</p>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">No specific recommendations at this time.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      {engagementMetrics && insights && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Statistics</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 border border-gray-200 rounded-lg">
              <div className={`text-2xl font-bold ${getEngagementColor(engagementMetrics.engagement_rate)}`}>
                {engagementMetrics.engagement_rate.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Overall Engagement Rate</div>
            </div>
            
            <div className="text-center p-4 border border-gray-200 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {insights.top_features.length > 0 ? insights.top_features[0][1] : 0}
              </div>
              <div className="text-sm text-gray-600">
                {insights.top_features.length > 0 ? 
                  `${insights.top_features[0][0].replace(/_/g, ' ')} uses` : 
                  'No data'
                }
              </div>
            </div>
            
            <div className="text-center p-4 border border-gray-200 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{dateRange}</div>
              <div className="text-sm text-gray-600">Days Analyzed</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}