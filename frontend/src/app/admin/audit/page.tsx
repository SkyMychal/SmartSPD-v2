'use client';

import { useState, useEffect } from 'react';
import { 
  Shield, 
  Search,
  Filter,
  Calendar,
  Download,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  User,
  FileText,
  Activity,
  Eye
} from 'lucide-react';

interface AuditLog {
  id: string;
  user_id?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  description: string;
  severity: string;
  success: boolean;
  ip_address?: string;
  created_at: string;
  error_message?: string;
  metadata?: any;
}

interface AuditSummary {
  total_events: number;
  failed_events: number;
  failure_rate: number;
  action_breakdown: Record<string, number>;
  severity_breakdown: Record<string, number>;
  resource_breakdown: Record<string, number>;
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');
  const [showFailedOnly, setShowFailedOnly] = useState(false);
  const [dateRange, setDateRange] = useState(7); // days

  useEffect(() => {
    fetchAuditData();
  }, [actionFilter, severityFilter, resourceFilter, showFailedOnly, dateRange]);

  const fetchAuditData = async () => {
    try {
      setLoading(true);
      
      // Build query parameters
      const params = new URLSearchParams();
      if (actionFilter) params.append('action', actionFilter);
      if (severityFilter) params.append('severity', severityFilter);
      if (resourceFilter) params.append('resource_type', resourceFilter);
      if (showFailedOnly) params.append('success', 'false');
      
      // Fetch logs and summary in parallel
      const [logsRes, summaryRes] = await Promise.all([
        fetch(`/api/v1/audit/logs?${params}&limit=100`),
        fetch(`/api/v1/audit/summary?days=${dateRange}`)
      ]);

      if (!logsRes.ok || !summaryRes.ok) {
        throw new Error('Failed to fetch audit data');
      }

      const [logsData, summaryData] = await Promise.all([
        logsRes.json(),
        summaryRes.json()
      ]);

      setLogs(logsData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to fetch audit data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter(log =>
    log.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.action.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (log.user_id && log.user_id.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getSeverityBadge = (severity: string) => {
    const severityConfig = {
      low: { color: 'bg-green-100 text-green-800', icon: CheckCircle },
      medium: { color: 'bg-yellow-100 text-yellow-800', icon: Clock },
      high: { color: 'bg-red-100 text-red-800', icon: AlertTriangle },
      critical: { color: 'bg-red-200 text-red-900', icon: XCircle }
    };

    const config = severityConfig[severity as keyof typeof severityConfig] || severityConfig.low;
    const IconComponent = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
        <IconComponent className="w-3 h-3" />
        {severity.charAt(0).toUpperCase() + severity.slice(1)}
      </span>
    );
  };

  const getActionIcon = (action: string) => {
    const iconMap: Record<string, any> = {
      create: Plus,
      update: Edit,
      delete: Trash2,
      read: Eye,
      login: User,
      logout: User,
      query: MessageSquare,
      upload: Upload,
      download: Download,
      admin_action: Shield,
      security_event: AlertTriangle
    };

    const IconComponent = iconMap[action] || Activity;
    return <IconComponent className="w-4 h-4" />;
  };

  const exportAuditLogs = async () => {
    try {
      const params = new URLSearchParams();
      if (actionFilter) params.append('action', actionFilter);
      if (severityFilter) params.append('severity', severityFilter);
      if (resourceFilter) params.append('resource_type', resourceFilter);
      params.append('limit', '1000');
      
      const response = await fetch(`/api/v1/audit/logs?${params}`);
      const data = await response.json();
      
      // Convert to CSV
      const headers = ['Timestamp', 'User', 'Action', 'Resource', 'Description', 'Severity', 'Success', 'IP Address'];
      const csvContent = [
        headers.join(','),
        ...data.map((log: AuditLog) => [
          new Date(log.created_at).toISOString(),
          log.user_id || 'system',
          log.action,
          log.resource_type,
          `"${log.description.replace(/"/g, '""')}"`,
          log.severity,
          log.success,
          log.ip_address || ''
        ].join(','))
      ].join('\n');
      
      // Download file
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export audit logs:', error);
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Trail</h1>
          <p className="text-gray-600">System activity and compliance logging</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={exportAuditLogs}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Events</p>
                <p className="text-2xl font-bold text-gray-900">{summary.total_events}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-600" />
            </div>
            <p className="text-xs text-gray-500 mt-2">Last {dateRange} days</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Failed Events</p>
                <p className="text-2xl font-bold text-red-600">{summary.failed_events}</p>
              </div>
              <XCircle className="w-8 h-8 text-red-600" />
            </div>
            <p className="text-xs text-gray-500 mt-2">{summary.failure_rate.toFixed(1)}% failure rate</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Security Events</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {summary.resource_breakdown.security || 0}
                </p>
              </div>
              <Shield className="w-8 h-8 text-yellow-600" />
            </div>
            <p className="text-xs text-gray-500 mt-2">Requires attention</p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Admin Actions</p>
                <p className="text-2xl font-bold text-purple-600">
                  {summary.action_breakdown.admin_action || 0}
                </p>
              </div>
              <User className="w-8 h-8 text-purple-600" />
            </div>
            <p className="text-xs text-gray-500 mt-2">Administrative changes</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search logs..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
          >
            <option value="">All Actions</option>
            <option value="create">Create</option>
            <option value="update">Update</option>
            <option value="delete">Delete</option>
            <option value="login">Login</option>
            <option value="query">Query</option>
            <option value="admin_action">Admin Action</option>
          </select>
          
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="">All Severities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={resourceFilter}
            onChange={(e) => setResourceFilter(e.target.value)}
          >
            <option value="">All Resources</option>
            <option value="user">User</option>
            <option value="document">Document</option>
            <option value="conversation">Conversation</option>
            <option value="security">Security</option>
            <option value="admin">Admin</option>
          </select>
          
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={dateRange}
            onChange={(e) => setDateRange(Number(e.target.value))}
          >
            <option value={1}>Last 24 hours</option>
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showFailedOnly}
              onChange={(e) => setShowFailedOnly(e.target.checked)}
              className="rounded border-gray-300 text-red-600 focus:ring-red-500"
            />
            <span className="text-sm text-gray-700">Failed only</span>
          </label>
        </div>
      </div>

      {/* Audit Logs */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Audit Logs ({filteredLogs.length})
          </h3>
        </div>
        
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-center py-12">
            <Shield className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No audit logs found</h3>
            <p className="mt-1 text-sm text-gray-500">
              No audit events match your current filters.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Action
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    IP Address
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {getActionIcon(log.action)}
                        <span className="text-sm font-medium text-gray-900">
                          {log.action}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {log.user_id || 'System'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div className="max-w-xs truncate" title={log.description}>
                        {log.description}
                      </div>
                      {log.error_message && (
                        <div className="text-xs text-red-600 mt-1">
                          Error: {log.error_message}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getSeverityBadge(log.severity)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {log.success ? (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                          <CheckCircle className="w-3 h-3" />
                          Success
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">
                          <XCircle className="w-3 h-3" />
                          Failed
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {log.ip_address || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}