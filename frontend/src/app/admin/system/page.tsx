'use client';

import { useState, useEffect } from 'react';
import { 
  Activity, 
  Server, 
  Database, 
  Cpu, 
  HardDrive, 
  Wifi, 
  AlertTriangle, 
  CheckCircle, 
  RefreshCw,
  BarChart3,
  Zap,
  Clock
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical';
  uptime_seconds: number;
  services: {
    api: { status: string; response_time_ms: number; last_check: string };
    database: { status: string; connection_pool: number; active_connections: number };
    redis: { status: string; memory_usage_mb: number; connected_clients: number };
    neo4j: { status: string; memory_usage_mb: number; active_transactions: number };
  };
  performance: {
    cpu_usage_percent: number;
    memory_usage_percent: number;
    disk_usage_percent: number;
    network_io_mbps: number;
  };
  recent_errors: Array<{
    timestamp: string;
    service: string;
    error: string;
    severity: string;
  }>;
  metrics: {
    requests_per_minute: number;
    avg_response_time_ms: number;
    error_rate_percent: number;
    active_users: number;
  };
}

export default function SystemHealthPage() {
  const [healthData, setHealthData] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchSystemHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock health data since backend endpoint doesn't exist yet
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate API call
      
      const mockData: SystemHealth = {
        status: 'healthy',
        uptime_seconds: 604800, // 7 days
        services: {
          api: {
            status: 'healthy',
            response_time_ms: 120,
            last_check: new Date().toISOString()
          },
          database: {
            status: 'healthy',
            connection_pool: 20,
            active_connections: 8
          },
          redis: {
            status: 'healthy',
            memory_usage_mb: 256,
            connected_clients: 15
          },
          neo4j: {
            status: 'warning',
            memory_usage_mb: 512,
            active_transactions: 3
          }
        },
        performance: {
          cpu_usage_percent: 45.2,
          memory_usage_percent: 62.8,
          disk_usage_percent: 34.5,
          network_io_mbps: 12.4
        },
        recent_errors: [
          {
            timestamp: new Date(Date.now() - 300000).toISOString(),
            service: 'neo4j',
            error: 'Connection timeout during query execution',
            severity: 'warning'
          },
          {
            timestamp: new Date(Date.now() - 1800000).toISOString(),
            service: 'api',
            error: 'Rate limit exceeded for IP 192.168.1.100',
            severity: 'info'
          }
        ],
        metrics: {
          requests_per_minute: 125,
          avg_response_time_ms: 340,
          error_rate_percent: 0.8,
          active_users: 24
        }
      };
      
      setHealthData(mockData);
      setLastUpdated(new Date());
      
    } catch (err) {
      console.error('Failed to fetch system health:', err);
      setError('Failed to load system health data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemHealth();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchSystemHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h ${minutes}m`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
      case 'critical':
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      default:
        return <Activity className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-50 border-green-200';
      case 'warning': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  if (loading && !healthData) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center min-h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Health</h1>
          <p className="text-gray-600">Monitor system performance and service status</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </span>
          <Button
            onClick={fetchSystemHealth}
            disabled={loading}
            variant="outline"
            size="sm"
            className="flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {healthData && (
        <>
          {/* Overall Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {getStatusIcon(healthData.status)}
                System Status: {healthData.status.charAt(0).toUpperCase() + healthData.status.slice(1)}
              </CardTitle>
              <CardDescription>
                System uptime: {formatUptime(healthData.uptime_seconds)}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className={`px-4 py-2 rounded-lg border ${getStatusColor(healthData.status)}`}>
                <div className="flex items-center justify-between">
                  <span className="font-medium">
                    {healthData.status === 'healthy' ? 'All systems operational' : 
                     healthData.status === 'warning' ? 'Some issues detected' : 
                     'Critical issues require attention'}
                  </span>
                  <span className="text-sm">
                    {Object.values(healthData.services).filter(s => s.status === 'healthy').length}/
                    {Object.values(healthData.services).length} services healthy
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Performance Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                <Cpu className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{healthData.performance.cpu_usage_percent}%</div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${healthData.performance.cpu_usage_percent}%` }}
                  ></div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{healthData.performance.memory_usage_percent}%</div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full" 
                    style={{ width: `${healthData.performance.memory_usage_percent}%` }}
                  ></div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Disk Usage</CardTitle>
                <HardDrive className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{healthData.performance.disk_usage_percent}%</div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div 
                    className="bg-purple-600 h-2 rounded-full" 
                    style={{ width: `${healthData.performance.disk_usage_percent}%` }}
                  ></div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Network I/O</CardTitle>
                <Wifi className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{healthData.performance.network_io_mbps}</div>
                <p className="text-xs text-muted-foreground">Mbps</p>
              </CardContent>
            </Card>
          </div>

          {/* Services Status */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="w-5 h-5" />
                Services Status
              </CardTitle>
              <CardDescription>
                Individual service health and performance
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(healthData.services.api.status)}
                      <div>
                        <p className="font-medium">API Server</p>
                        <p className="text-sm text-gray-500">Response time: {healthData.services.api.response_time_ms}ms</p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(healthData.services.api.status)}`}>
                      {healthData.services.api.status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(healthData.services.database.status)}
                      <div>
                        <p className="font-medium">PostgreSQL Database</p>
                        <p className="text-sm text-gray-500">
                          {healthData.services.database.active_connections}/{healthData.services.database.connection_pool} connections
                        </p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(healthData.services.database.status)}`}>
                      {healthData.services.database.status}
                    </span>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(healthData.services.redis.status)}
                      <div>
                        <p className="font-medium">Redis Cache</p>
                        <p className="text-sm text-gray-500">
                          {healthData.services.redis.memory_usage_mb}MB, {healthData.services.redis.connected_clients} clients
                        </p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(healthData.services.redis.status)}`}>
                      {healthData.services.redis.status}
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(healthData.services.neo4j.status)}
                      <div>
                        <p className="font-medium">Neo4j Knowledge Graph</p>
                        <p className="text-sm text-gray-500">
                          {healthData.services.neo4j.memory_usage_mb}MB, {healthData.services.neo4j.active_transactions} transactions
                        </p>
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(healthData.services.neo4j.status)}`}>
                      {healthData.services.neo4j.status}
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Application Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Requests/Min</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{healthData.metrics.requests_per_minute}</div>
                <p className="text-xs text-muted-foreground">API requests per minute</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Response</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{healthData.metrics.avg_response_time_ms}ms</div>
                <p className="text-xs text-muted-foreground">Average response time</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{healthData.metrics.error_rate_percent}%</div>
                <p className="text-xs text-muted-foreground">Error rate</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Users</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{healthData.metrics.active_users}</div>
                <p className="text-xs text-muted-foreground">Currently online</p>
              </CardContent>
            </Card>
          </div>

          {/* Recent Errors */}
          {healthData.recent_errors.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  Recent Errors
                </CardTitle>
                <CardDescription>
                  Latest system errors and warnings
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {healthData.recent_errors.map((error, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${
                          error.severity === 'critical' ? 'bg-red-500' :
                          error.severity === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
                        }`}></div>
                        <div>
                          <p className="font-medium">{error.service}</p>
                          <p className="text-sm text-gray-600">{error.error}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          error.severity === 'critical' ? 'bg-red-100 text-red-800' :
                          error.severity === 'warning' ? 'bg-yellow-100 text-yellow-800' : 'bg-blue-100 text-blue-800'
                        }`}>
                          {error.severity}
                        </span>
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(error.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}