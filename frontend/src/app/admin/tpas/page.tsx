'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Building, 
  Plus,
  Search,
  Edit,
  Trash2,
  MoreHorizontal,
  Users,
  FileText,
  MessageSquare,
  Eye,
  Settings,
  AlertTriangle
} from 'lucide-react';

interface TPA {
  id: string;
  name: string;
  slug: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface TPAWithStats extends TPA {
  user_count?: number;
  document_count?: number;
  conversation_count?: number;
}

export default function AdminTPAsPage() {
  const router = useRouter();
  const [tpas, setTPAs] = useState<TPAWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showActiveOnly, setShowActiveOnly] = useState(false);
  const [showTPAMenu, setShowTPAMenu] = useState<string | null>(null);
  const [selectedTPA, setSelectedTPA] = useState<TPA | null>(null);

  useEffect(() => {
    fetchTPAs();
  }, [showActiveOnly]);

  const fetchTPAs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (showActiveOnly) params.append('active_only', 'true');
      
      const response = await fetch(`/api/v1/admin/tpas?${params}`);
      if (!response.ok) throw new Error('Failed to fetch TPAs');
      
      const data = await response.json();
      
      // Fetch metrics for each TPA
      const metricsResponse = await fetch('/api/v1/admin/metrics');
      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        const tpaMetrics = metricsData.tpa_overview || [];
        
        // Merge TPA data with metrics
        const enrichedTPAs = data.map((tpa: TPA) => {
          const metrics = tpaMetrics.find((m: any) => m.id === tpa.id);
          return {
            ...tpa,
            user_count: metrics?.user_count || 0,
            document_count: metrics?.document_count || 0,
            conversation_count: metrics?.conversation_count || 0
          };
        });
        
        setTPAs(enrichedTPAs);
      } else {
        setTPAs(data);
      }
    } catch (error) {
      console.error('Failed to fetch TPAs:', error);
    } finally {
      setLoading(false);
    }
  };

  const deleteTPA = async (tpaId: string, force: boolean = false) => {
    const tpa = tpas.find(t => t.id === tpaId);
    if (!tpa) return;

    const hasUsers = (tpa.user_count || 0) > 0;
    
    if (hasUsers && !force) {
      const confirmed = confirm(
        `This TPA has ${tpa.user_count} users. Are you sure you want to delete it? This will also delete all associated users and data.`
      );
      if (!confirmed) return;
    } else if (!hasUsers) {
      const confirmed = confirm('Are you sure you want to delete this TPA? This action cannot be undone.');
      if (!confirmed) return;
    }

    try {
      const response = await fetch(`/api/v1/admin/tpas/${tpaId}?force=${force || hasUsers}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete TPA');
      }
      
      fetchTPAs(); // Refresh the list
      setShowTPAMenu(null);
    } catch (error) {
      console.error('Failed to delete TPA:', error);
      alert('Failed to delete TPA. Please try again.');
    }
  };

  const toggleTPAStatus = async (tpaId: string) => {
    const tpa = tpas.find(t => t.id === tpaId);
    if (!tpa) return;

    try {
      const response = await fetch(`/api/v1/admin/tpas/${tpaId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          is_active: !tpa.is_active
        }),
      });
      
      if (!response.ok) throw new Error('Failed to update TPA status');
      
      fetchTPAs(); // Refresh the list
      setShowTPAMenu(null);
    } catch (error) {
      console.error('Failed to update TPA status:', error);
    }
  };

  const filteredTPAs = tpas.filter(tpa =>
    tpa.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tpa.slug.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (isActive: boolean) => {
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
        isActive 
          ? 'bg-green-100 text-green-800' 
          : 'bg-red-100 text-red-800'
      }`}>
        {isActive ? 'Active' : 'Inactive'}
      </span>
    );
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">TPA Management</h1>
          <p className="text-gray-600">Manage Third Party Administrators</p>
        </div>
        <button
          onClick={() => router.push('/admin/tpas/new')}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="w-4 h-4" />
          Add TPA
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search TPAs..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showActiveOnly}
              onChange={(e) => setShowActiveOnly(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Active only</span>
          </label>
        </div>
      </div>

      {/* TPAs Grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : filteredTPAs.length === 0 ? (
        <div className="text-center py-12">
          <Building className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No TPAs found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm ? 'No TPAs match your search criteria.' : 'Get started by creating a new TPA.'}
          </p>
          {!searchTerm && (
            <div className="mt-6">
              <button
                onClick={() => router.push('/admin/tpas/new')}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add TPA
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTPAs.map((tpa) => (
            <div key={tpa.id} className="bg-white rounded-lg shadow border border-gray-200 hover:shadow-md transition-shadow">
              <div className="p-6">
                {/* Header */}
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <Building className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">{tpa.name}</h3>
                      <p className="text-sm text-gray-500">/{tpa.slug}</p>
                    </div>
                  </div>
                  
                  <div className="relative">
                    <button
                      onClick={() => setShowTPAMenu(showTPAMenu === tpa.id ? null : tpa.id)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <MoreHorizontal className="w-5 h-5" />
                    </button>
                    
                    {showTPAMenu === tpa.id && (
                      <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg z-10 border">
                        <div className="py-1">
                          <button
                            onClick={() => router.push(`/admin/tpas/${tpa.id}`)}
                            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                          >
                            <Eye className="w-4 h-4" />
                            View Details
                          </button>
                          <button
                            onClick={() => router.push(`/admin/tpas/${tpa.id}/edit`)}
                            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                          >
                            <Edit className="w-4 h-4" />
                            Edit TPA
                          </button>
                          <button
                            onClick={() => router.push(`/admin/users?tpa_id=${tpa.id}`)}
                            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                          >
                            <Users className="w-4 h-4" />
                            Manage Users
                          </button>
                          <button
                            onClick={() => toggleTPAStatus(tpa.id)}
                            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 w-full text-left"
                          >
                            <Settings className="w-4 h-4" />
                            {tpa.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                          <div className="border-t border-gray-100">
                            <button
                              onClick={() => deleteTPA(tpa.id)}
                              className="flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 w-full text-left"
                            >
                              <Trash2 className="w-4 h-4" />
                              Delete TPA
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Status */}
                <div className="mb-4">
                  {getStatusBadge(tpa.is_active)}
                </div>

                {/* Description */}
                {tpa.description && (
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">{tpa.description}</p>
                )}

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-1">
                      <Users className="w-4 h-4 text-gray-400" />
                    </div>
                    <div className="text-lg font-semibold text-gray-900">{tpa.user_count || 0}</div>
                    <div className="text-xs text-gray-500">Users</div>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-1">
                      <FileText className="w-4 h-4 text-gray-400" />
                    </div>
                    <div className="text-lg font-semibold text-gray-900">{tpa.document_count || 0}</div>
                    <div className="text-xs text-gray-500">Documents</div>
                  </div>
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-1">
                      <MessageSquare className="w-4 h-4 text-gray-400" />
                    </div>
                    <div className="text-lg font-semibold text-gray-900">{tpa.conversation_count || 0}</div>
                    <div className="text-xs text-gray-500">Chats</div>
                  </div>
                </div>

                {/* Footer */}
                <div className="flex justify-between items-center text-xs text-gray-500 pt-4 border-t border-gray-100">
                  <span>Created {new Date(tpa.created_at).toLocaleDateString()}</span>
                  {!tpa.is_active && (
                    <div className="flex items-center gap-1 text-amber-600">
                      <AlertTriangle className="w-3 h-3" />
                      <span>Inactive</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary */}
      {!loading && filteredTPAs.length > 0 && (
        <div className="mt-6 text-sm text-gray-600 text-center">
          Showing {filteredTPAs.length} of {tpas.length} TPAs
        </div>
      )}
    </div>
  );
}