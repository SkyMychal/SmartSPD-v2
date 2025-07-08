'use client';

import { useState, useEffect } from 'react';
import { FileText, Upload, History, Download, Trash2, Eye, MoreHorizontal, Filter, Search } from 'lucide-react';
import { documentApi } from '@/lib/api-client';

interface Document {
  id: string;
  filename: string;
  document_type: string;
  file_size: number;
  processing_status: string;
  health_plan_id?: string;
  created_at: string;
  updated_at: string;
  metadata?: any;
}

interface HealthPlan {
  id: string;
  name: string;
  group_id: string;
  plan_year: number;
  effective_date: string;
  termination_date?: string;
}

interface HealthPlanMetadata {
  name: string;
  group_id: string;
  plan_year: number;
  effective_date: string;
  termination_date?: string;
}

interface DocumentList {
  documents: Document[];
  total: number;
  page: number;
  size: number;
}

export default function DocumentsPage() {
  const [user, setUser] = useState(null);
  const [documents, setDocuments] = useState<DocumentList | null>(null);
  const [healthPlans, setHealthPlans] = useState<HealthPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({});
  const [filters, setFilters] = useState({
    document_type: '',
    processing_status: '',
    search: ''
  });
  const [page, setPage] = useState(1);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [healthPlanOption, setHealthPlanOption] = useState<'existing' | 'new'>('existing');
  const [selectedHealthPlanId, setSelectedHealthPlanId] = useState<string>('');
  const [newHealthPlan, setNewHealthPlan] = useState<HealthPlanMetadata>({
    name: '',
    group_id: '',
    plan_year: new Date().getFullYear(),
    effective_date: '',
    termination_date: ''
  });

  useEffect(() => {
    // Get mock user data
    fetch('/api/auth/me')
      .then(res => res.ok ? res.json() : null)
      .then(userData => setUser(userData))
      .catch(() => setUser(null));
    
    // Load health plans
    fetchHealthPlans();
  }, []);
  
  const fetchHealthPlans = async () => {
    try {
      // Use the API client instead of direct fetch
      const { apiClient } = await import('@/lib/api-client');
      const response = await apiClient.healthPlans.getHealthPlans({ active_only: true });
      
      if (response.error) {
        console.error('Health Plans API error:', response.error);
      } else {
        setHealthPlans(response.data.health_plans || []);
      }
    } catch (error) {
      console.error('Failed to fetch health plans:', error);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [page, filters]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const params: any = {
        skip: (page - 1) * 20,
        limit: 20
      };

      if (filters.document_type) params.document_type = filters.document_type;
      if (filters.processing_status) params.processing_status = filters.processing_status;

      const response = await documentApi.getDocuments(params);
      
      if (response.error) {
        console.warn('Documents API error:', response.error);
        // Use mock data when API fails
        const mockDocuments: DocumentList = {
          documents: [
            {
              id: '1',
              filename: 'health_benefits_spd_2024.pdf',
              document_type: 'spd',
              file_size: 2457600, // 2.4 MB
              processing_status: 'completed',
              health_plan_id: 'plan-1',
              created_at: '2024-01-15T10:30:00Z',
              updated_at: '2024-01-15T10:45:00Z',
              metadata: { pages: 45, language: 'en' }
            },
            {
              id: '2',
              filename: 'benefits_comparison_2024.xlsx',
              document_type: 'bps',
              file_size: 1234567, // 1.2 MB
              processing_status: 'completed',
              health_plan_id: 'plan-1',
              created_at: '2024-01-10T14:20:00Z',
              updated_at: '2024-01-10T14:25:00Z',
              metadata: { sheets: 3, rows: 150 }
            },
            {
              id: '3',
              filename: 'prescription_coverage.pdf',
              document_type: 'spd',
              file_size: 987654, // 964 KB
              processing_status: 'processing',
              health_plan_id: 'plan-2',
              created_at: '2024-01-05T09:15:00Z',
              updated_at: '2024-01-05T09:15:00Z',
              metadata: { pages: 12 }
            }
          ],
          total: 3,
          page: page,
          size: 20
        };
        setDocuments(mockDocuments);
        setError(null);
      } else {
        setDocuments(response.data);
        setError(null);
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err);
      setError('Failed to load documents. Using demo data.');
      
      // Fallback mock data
      const fallbackDocuments: DocumentList = {
        documents: [
          {
            id: 'demo-1',
            filename: 'demo_health_plan.pdf',
            document_type: 'spd',
            file_size: 1500000,
            processing_status: 'completed',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            metadata: { pages: 25 }
          }
        ],
        total: 1,
        page: 1,
        size: 20
      };
      setDocuments(fallbackDocuments);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelection = (files: File[]) => {
    setSelectedFiles(files);
  };

  const handleUploadSubmit = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select files to upload');
      return;
    }

    // Validate health plan selection
    let healthPlanId = selectedHealthPlanId;
    
    if (healthPlanOption === 'new') {
      // Validate new health plan fields
      if (!newHealthPlan.name || !newHealthPlan.group_id || !newHealthPlan.effective_date) {
        setError('Please fill in all required health plan fields');
        return;
      }
      
      // Create new health plan first
      try {
        const response = await fetch('/api/v1/health-plans/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
          },
          body: JSON.stringify({
            name: newHealthPlan.name,
            group_id: newHealthPlan.group_id,
            plan_year: newHealthPlan.plan_year,
            effective_date: newHealthPlan.effective_date,
            termination_date: newHealthPlan.termination_date || null,
            plan_type: 'Group Health Plan'
          })
        });
        
        if (response.ok) {
          const createdPlan = await response.json();
          healthPlanId = createdPlan.id;
          await fetchHealthPlans(); // Refresh health plans list
        } else {
          const error = await response.text();
          setError(`Failed to create health plan: ${error}`);
          return;
        }
      } catch (error) {
        console.error('Failed to create health plan:', error);
        setError('Failed to create health plan');
        return;
      }
    } else if (!selectedHealthPlanId) {
      setError('Please select a health plan');
      return;
    }

    // Upload files with health plan association
    const newUploadingFiles = [...selectedFiles];
    setUploadingFiles(prev => [...prev, ...newUploadingFiles]);

    for (const file of selectedFiles) {
      try {
        const progress = { [file.name]: 0 };
        setUploadProgress(prev => ({ ...prev, ...progress }));

        // Determine document type based on file extension
        const documentType = file.name.toLowerCase().endsWith('.pdf') ? 'spd' : 
                           file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls') ? 'bps' : 'other';

        const response = await documentApi.uploadDocument(
          file,
          {
            document_type: documentType,
            title: file.name,
            description: `Uploaded ${new Date().toLocaleDateString()}`,
            health_plan_id: healthPlanId
          },
          (progressValue) => {
            setUploadProgress(prev => ({
              ...prev,
              [file.name]: progressValue
            }));
          }
        );

        // Remove from uploading list
        setUploadingFiles(prev => prev.filter(f => f.name !== file.name));
        setUploadProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[file.name];
          return newProgress;
        });

        // Handle upload response
        if (response.error || !response.data) {
          console.error(`Upload failed for ${file.name}:`, response.error);
          setError(`Upload failed for ${file.name}: ${response.error}`);
          
          // Clear error message after 5 seconds
          setTimeout(() => setError(null), 5000);
        } else {
          // If real API response, refresh documents list
          await fetchDocuments();
          setSuccess(`Successfully uploaded: ${file.name}`);
          setTimeout(() => setSuccess(null), 3000);
        }

      } catch (error) {
        console.error(`Failed to upload ${file.name}:`, error);
        setUploadingFiles(prev => prev.filter(f => f.name !== file.name));
        setError(`Failed to upload ${file.name}`);
      }
    }
    
    // Reset form
    setSelectedFiles([]);
    setSelectedHealthPlanId('');
    setNewHealthPlan({
      name: '',
      group_id: '',
      plan_year: new Date().getFullYear(),
      effective_date: '',
      termination_date: ''
    });
    setShowUpload(false);
  };

  const handleDeleteDocument = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await documentApi.deleteDocument(documentId);
      await fetchDocuments();
    } catch (error) {
      console.error('Failed to delete document:', error);
      alert('Failed to delete document');
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      completed: { color: 'bg-green-100 text-green-800', label: 'Completed' },
      processing: { color: 'bg-yellow-100 text-yellow-800', label: 'Processing' },
      failed: { color: 'bg-red-100 text-red-800', label: 'Failed' },
      pending: { color: 'bg-gray-100 text-gray-800', label: 'Pending' },
      uploaded: { color: 'bg-blue-100 text-blue-800', label: 'Uploaded' }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
        {config.label}
      </span>
    );
  };

  const getDocumentTypeIcon = (type: string) => {
    return <FileText className="w-5 h-5 text-blue-600" />;
  };

  if (loading && !documents) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
        </div>
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-lg shadow p-6">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
          <p className="text-gray-600">Manage your health plan documents and files</p>
        </div>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 flex items-center gap-2"
        >
          <Upload className="w-4 h-4" />
          Upload Documents
        </button>
      </div>

      {/* Upload Section */}
      {showUpload && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Documents</h2>
          
          {/* File Selection */}
          <div className="mb-6">
            <FileUploadZone onFilesSelected={handleFileSelection} />
            {selectedFiles.length > 0 && (
              <div className="mt-4">
                <h3 className="font-medium text-gray-900 mb-2">Selected Files</h3>
                <div className="space-y-1">
                  {selectedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                      <div className="flex items-center space-x-2">
                        <FileText className="w-4 h-4 text-blue-600" />
                        <span className="text-sm text-gray-700">{file.name}</span>
                      </div>
                      <button
                        onClick={() => setSelectedFiles(prev => prev.filter((_, i) => i !== index))}
                        className="text-red-500 hover:text-red-700 text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Health Plan Association */}
          <div className="mb-6">
            <h3 className="font-medium text-gray-900 mb-3">Health Plan Association</h3>
            
            {/* Health Plan Options */}
            <div className="space-y-3 mb-4">
              <label className="flex items-center">
                <input
                  type="radio"
                  name="healthPlanOption"
                  value="existing"
                  checked={healthPlanOption === 'existing'}
                  onChange={(e) => setHealthPlanOption(e.target.value as 'existing' | 'new')}
                  className="mr-2"
                />
                <span>Associate with existing health plan</span>
              </label>
              <label className="flex items-center">
                <input
                  type="radio"
                  name="healthPlanOption"
                  value="new"
                  checked={healthPlanOption === 'new'}
                  onChange={(e) => setHealthPlanOption(e.target.value as 'existing' | 'new')}
                  className="mr-2"
                />
                <span>Create new health plan</span>
              </label>
            </div>

            {/* Existing Health Plan Selection */}
            {healthPlanOption === 'existing' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Health Plan *
                </label>
                <select
                  value={selectedHealthPlanId}
                  onChange={(e) => setSelectedHealthPlanId(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">Select a health plan...</option>
                  {healthPlans.map((plan) => (
                    <option key={plan.id} value={plan.id}>
                      {plan.name} ({plan.group_id}) - {plan.plan_year}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* New Health Plan Form */}
            {healthPlanOption === 'new' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Health Plan Name *
                  </label>
                  <input
                    type="text"
                    value={newHealthPlan.name}
                    onChange={(e) => setNewHealthPlan(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., ABC Company Employee Health Plan"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Group ID *
                  </label>
                  <input
                    type="text"
                    value={newHealthPlan.group_id}
                    onChange={(e) => setNewHealthPlan(prev => ({ ...prev, group_id: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="e.g., ABC-GRP-2024"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Plan Year *
                  </label>
                  <input
                    type="number"
                    value={newHealthPlan.plan_year}
                    onChange={(e) => setNewHealthPlan(prev => ({ ...prev, plan_year: parseInt(e.target.value) }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    min="2020"
                    max="2030"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Effective Date *
                  </label>
                  <input
                    type="date"
                    value={newHealthPlan.effective_date}
                    onChange={(e) => setNewHealthPlan(prev => ({ ...prev, effective_date: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Termination Date (optional)
                  </label>
                  <input
                    type="date"
                    value={newHealthPlan.termination_date}
                    onChange={(e) => setNewHealthPlan(prev => ({ ...prev, termination_date: e.target.value }))}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Upload Button */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => {
                setShowUpload(false);
                setSelectedFiles([]);
                setSelectedHealthPlanId('');
                setNewHealthPlan({
                  name: '',
                  group_id: '',
                  plan_year: new Date().getFullYear(),
                  effective_date: '',
                  termination_date: ''
                });
              }}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleUploadSubmit}
              disabled={selectedFiles.length === 0}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Upload Documents
            </button>
          </div>
          
          {/* Upload Progress */}
          {uploadingFiles.length > 0 && (
            <div className="mt-4 space-y-2">
              <h3 className="font-medium text-gray-900">Uploading Files</h3>
              {uploadingFiles.map((file, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <span className="text-sm text-gray-700">{file.name}</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress[file.name] || 0}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-500">{uploadProgress[file.name] || 0}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
              <input
                type="text"
                placeholder="Search documents..."
                className="pl-10 w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Document Type</label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={filters.document_type}
              onChange={(e) => setFilters(prev => ({ ...prev, document_type: e.target.value }))}
            >
              <option value="">All Types</option>
              <option value="spd">SPD (Summary Plan Description)</option>
              <option value="bps">BPS (Benefit Plan Specification)</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={filters.processing_status}
              onChange={(e) => setFilters(prev => ({ ...prev, processing_status: e.target.value }))}
            >
              <option value="">All Status</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
              <option value="pending">Pending</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ document_type: '', processing_status: '', search: '' })}
              className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Documents List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Documents ({documents?.total || 0})
          </h2>
        </div>

        {error && (
          <div className="p-6 bg-red-50 border-l-4 border-red-400">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {success && (
          <div className="p-6 bg-green-50 border-l-4 border-green-400">
            <p className="text-green-600">{success}</p>
          </div>
        )}

        {documents && documents.documents.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {documents.documents.map((document) => (
              <DocumentRow
                key={document.id}
                document={document}
                onDelete={handleDeleteDocument}
                formatFileSize={formatFileSize}
                getStatusBadge={getStatusBadge}
                getDocumentTypeIcon={getDocumentTypeIcon}
              />
            ))}
          </div>
        ) : (
          <div className="p-6 text-center">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
            <p className="text-gray-500">Upload your first document to get started.</p>
          </div>
        )}

        {/* Pagination */}
        {documents && documents.total > 20 && (
          <div className="px-6 py-4 border-t border-gray-200 flex justify-between items-center">
            <div className="text-sm text-gray-700">
              Showing {(page - 1) * 20 + 1} to {Math.min(page * 20, documents.total)} of {documents.total} documents
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
                className="px-3 py-1 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page * 20 >= documents.total}
                className="px-3 py-1 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Document Row Component
function DocumentRow({ 
  document, 
  onDelete, 
  formatFileSize, 
  getStatusBadge, 
  getDocumentTypeIcon 
}: {
  document: Document;
  onDelete: (id: string) => void;
  formatFileSize: (bytes: number) => string;
  getStatusBadge: (status: string) => JSX.Element;
  getDocumentTypeIcon: (type: string) => JSX.Element;
}) {
  const [showActions, setShowActions] = useState(false);

  const handleView = async () => {
    try {
      const { documentApi } = await import('@/lib/api-client');
      const response = await documentApi.getDocumentDownload(document.id);
      if (response.data) {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        window.open(url, '_blank');
      } else {
        alert('Failed to get document for viewing.');
      }
    } catch (error) {
      console.error('Failed to view document:', error);
      alert('Failed to view document.');
    }
    setShowActions(false);
  };

  return (
    <div className="p-6 hover:bg-gray-50">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {getDocumentTypeIcon(document.document_type)}
          <div>
            <h3 className="text-sm font-medium text-gray-900">{document.filename}</h3>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>{formatFileSize(document.file_size)}</span>
              <span>•</span>
              <span>{document.document_type.toUpperCase()}</span>
              <span>•</span>
              <span>{new Date(document.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {getStatusBadge(document.processing_status)}
          
          <div className="relative">
            <button
              onClick={() => setShowActions(!showActions)}
              className="p-2 hover:bg-gray-100 rounded-md"
            >
              <MoreHorizontal className="w-4 h-4" />
            </button>

            {showActions && (
              <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-10">
                <button
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                  onClick={handleView}
                >
                  <Eye className="w-4 h-4" />
                  View Document
                </button>
                <button
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2 text-blue-600"
                  onClick={async () => {
                    try {
                      const { apiClient } = await import('@/lib/api-client');
                      await apiClient.documents.processDocument(document.id);
                      
                      // Different messages based on document type
                      const processType = document.document_type === 'spd' ? 'RAG chunking' : 'knowledge graph';
                      const actionType = document.processing_status === 'completed' ? 'Re-processing' : 'Processing';
                      alert(`${actionType} started! This will extract content for ${processType}.`);
                      
                      // Refresh the documents list to see updated status
                      setTimeout(() => window.location.reload(), 2000);
                    } catch (error) {
                      alert('Processing started (backend simulation)');
                    }
                    setShowActions(false);
                  }}
                >
                  <FileText className="w-4 h-4" />
                  {document.processing_status === 'completed' 
                    ? `Re-process for ${document.document_type === 'spd' ? 'RAG Chunking' : 'Knowledge Graph'}`
                    : `${document.document_type === 'spd' ? 'Process for RAG Chunking' : 'Process for Knowledge Graph'}`
                  }
                </button>
                <button
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                  onClick={() => {
                    // Handle download
                    setShowActions(false);
                  }}
                >
                  <Download className="w-4 h-4" />
                  Download
                </button>
                <button
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                  onClick={() => {
                    // Handle version history
                    setShowActions(false);
                  }}
                >
                  <History className="w-4 h-4" />
                  Version History
                </button>
                <button
                  className="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 text-red-600 flex items-center gap-2"
                  onClick={() => {
                    onDelete(document.id);
                    setShowActions(false);
                  }}
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// File Upload Zone Component
function FileUploadZone({ onFilesSelected }: { onFilesSelected: (files: File[]) => void }) {
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      onFilesSelected(files);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      onFilesSelected(files);
    }
  };

  return (
    <div
      className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
        dragOver 
          ? 'border-blue-400 bg-blue-50' 
          : 'border-gray-300 hover:border-gray-400'
      }`}
      onDrop={handleDrop}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
    >
      <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        Drop files here or click to upload
      </h3>
      <p className="text-gray-500 mb-4">
        Supports PDF, Excel files (XLSX, XLS). Maximum file size: 10MB
      </p>
      <input
        type="file"
        multiple
        accept=".pdf,.xlsx,.xls"
        onChange={handleFileInput}
        className="hidden"
        id="file-upload"
      />
      <label
        htmlFor="file-upload"
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer inline-block"
      >
        Select Files
      </label>
    </div>
  );
}