'use client';

import { useUser } from '@auth0/nextjs-auth0/client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  FileText, 
  Download, 
  Upload, 
  History, 
  RefreshCw, 
  ArrowLeft,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  Edit,
  Trash2
} from 'lucide-react';
import { documentApi } from '@/lib/api';

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
  error_message?: string;
}

interface DocumentChunk {
  id: string;
  content: string;
  chunk_index: number;
  page_number?: number;
  section_title?: string;
  chunk_type: string;
  keywords: string[];
  relevance_score: number;
  confidence_score: number;
}

interface DocumentVersion {
  document_id: string;
  version_number: number;
  filename: string;
  file_size: number;
  file_hash: string;
  created_at: string;
  processing_status: string;
  metadata: any;
}

export default function DocumentDetailPage({ params }: { params: { id: string } }) {
  const { user } = useUser();
  const router = useRouter();
  const [document, setDocument] = useState<Document | null>(null);
  const [chunks, setChunks] = useState<DocumentChunk[]>([]);
  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'chunks' | 'versions'>('overview');
  const [chunksLoading, setChunksLoading] = useState(false);
  const [versionsLoading, setVersionsLoading] = useState(false);

  useEffect(() => {
    fetchDocument();
  }, [params.id]);

  useEffect(() => {
    if (activeTab === 'chunks' && document && chunks.length === 0) {
      fetchChunks();
    } else if (activeTab === 'versions' && document && versions.length === 0) {
      fetchVersions();
    }
  }, [activeTab, document]);

  const fetchDocument = async () => {
    try {
      setLoading(true);
      const data = await documentApi.getDocument(params.id);
      setDocument(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch document:', err);
      setError('Failed to load document');
    } finally {
      setLoading(false);
    }
  };

  const fetchChunks = async () => {
    if (!document) return;
    
    try {
      setChunksLoading(true);
      const response = await fetch(`/api/v1/documents/${document.id}/chunks`);
      const data = await response.json();
      setChunks(data.chunks || []);
    } catch (err) {
      console.error('Failed to fetch chunks:', err);
    } finally {
      setChunksLoading(false);
    }
  };

  const fetchVersions = async () => {
    if (!document) return;
    
    try {
      setVersionsLoading(true);
      const response = await fetch(`/api/v1/documents/${document.id}/versions`);
      const data = await response.json();
      setVersions(data.versions || []);
    } catch (err) {
      console.error('Failed to fetch versions:', err);
    } finally {
      setVersionsLoading(false);
    }
  };

  const handleReprocess = async () => {
    if (!document) return;
    
    if (!confirm('Are you sure you want to reprocess this document? This will overwrite existing processed data.')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/documents/${document.id}/reprocess`, {
        method: 'POST'
      });
      
      if (response.ok) {
        await fetchDocument();
        alert('Document reprocessing started');
      } else {
        alert('Failed to start reprocessing');
      }
    } catch (error) {
      console.error('Failed to reprocess document:', error);
      alert('Failed to start reprocessing');
    }
  };

  const handleDelete = async () => {
    if (!document) return;
    
    if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
      return;
    }

    try {
      await documentApi.deleteDocument(document.id);
      router.push('/dashboard/documents');
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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'processing':
        return <Clock className="w-5 h-5 text-yellow-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-600" />;
    }
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
      <span className={`px-3 py-1 text-sm font-medium rounded-full ${config.color}`}>
        {config.label}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Documents
        </button>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-red-800 mb-2">Error</h2>
          <p className="text-red-600">{error || 'Document not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{document.filename}</h1>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>{formatFileSize(document.file_size)}</span>
              <span>•</span>
              <span>{document.document_type.toUpperCase()}</span>
              <span>•</span>
              <span>Uploaded {new Date(document.created_at).toLocaleDateString()}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {getStatusBadge(document.processing_status)}
          
          <div className="flex items-center gap-2">
            <button
              onClick={handleReprocess}
              className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center gap-2"
              title="Reprocess Document"
            >
              <RefreshCw className="w-4 h-4" />
              Reprocess
            </button>
            
            <button
              className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center gap-2"
              title="Download Document"
            >
              <Download className="w-4 h-4" />
              Download
            </button>
            
            <button
              onClick={handleDelete}
              className="px-3 py-2 border border-red-300 text-red-600 rounded-md hover:bg-red-50 flex items-center gap-2"
              title="Delete Document"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
          </div>
        </div>
      </div>

      {/* Status Alert */}
      {document.processing_status === 'failed' && document.error_message && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <XCircle className="w-5 h-5 text-red-600" />
            <h3 className="font-medium text-red-800">Processing Failed</h3>
          </div>
          <p className="text-red-600 mt-1">{document.error_message}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview', icon: Eye },
            { id: 'chunks', label: 'Content Chunks', icon: FileText },
            { id: 'versions', label: 'Version History', icon: History }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow">
        {activeTab === 'overview' && (
          <DocumentOverview document={document} />
        )}
        
        {activeTab === 'chunks' && (
          <DocumentChunks 
            chunks={chunks} 
            loading={chunksLoading}
            onRefresh={fetchChunks}
          />
        )}
        
        {activeTab === 'versions' && (
          <DocumentVersions 
            versions={versions} 
            loading={versionsLoading}
            documentId={document.id}
            onRefresh={fetchVersions}
          />
        )}
      </div>
    </div>
  );
}

// Document Overview Component
function DocumentOverview({ document }: { document: Document }) {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Document Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Filename</label>
              <p className="mt-1 text-sm text-gray-900">{document.filename}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Document Type</label>
              <p className="mt-1 text-sm text-gray-900">{document.document_type.toUpperCase()}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">File Size</label>
              <p className="mt-1 text-sm text-gray-900">{document.file_size} bytes</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Health Plan</label>
              <p className="mt-1 text-sm text-gray-900">
                {document.health_plan_id || 'Not specified'}
              </p>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Processing Status</label>
              <p className="mt-1 text-sm text-gray-900">{document.processing_status}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Created</label>
              <p className="mt-1 text-sm text-gray-900">
                {new Date(document.created_at).toLocaleString()}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Last Updated</label>
              <p className="mt-1 text-sm text-gray-900">
                {new Date(document.updated_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {document.metadata && (
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Metadata</h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <pre className="text-sm text-gray-700 whitespace-pre-wrap">
              {JSON.stringify(document.metadata, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

// Document Chunks Component
function DocumentChunks({ 
  chunks, 
  loading, 
  onRefresh 
}: { 
  chunks: DocumentChunk[], 
  loading: boolean,
  onRefresh: () => void 
}) {
  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="border border-gray-200 rounded-lg p-4">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Content Chunks ({chunks.length})
        </h2>
        <button
          onClick={onRefresh}
          className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {chunks.length > 0 ? (
        <div className="space-y-4">
          {chunks.map((chunk) => (
            <div key={chunk.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>Chunk {chunk.chunk_index + 1}</span>
                  {chunk.page_number && <span>Page {chunk.page_number}</span>}
                  {chunk.section_title && <span>• {chunk.section_title}</span>}
                  <span>• {chunk.chunk_type}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span>Relevance: {(chunk.relevance_score * 100).toFixed(0)}%</span>
                  <span>Confidence: {(chunk.confidence_score * 100).toFixed(0)}%</span>
                </div>
              </div>
              
              <div className="text-sm text-gray-900 mb-3 max-h-32 overflow-y-auto">
                {chunk.content}
              </div>
              
              {chunk.keywords.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {chunk.keywords.slice(0, 10).map((keyword, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                    >
                      {keyword}
                    </span>
                  ))}
                  {chunk.keywords.length > 10 && (
                    <span className="text-xs text-gray-500">
                      +{chunk.keywords.length - 10} more
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No chunks found</h3>
          <p className="text-gray-500">This document hasn't been processed into chunks yet.</p>
        </div>
      )}
    </div>
  );
}

// Document Versions Component
function DocumentVersions({ 
  versions, 
  loading, 
  documentId, 
  onRefresh 
}: { 
  versions: DocumentVersion[], 
  loading: boolean,
  documentId: string,
  onRefresh: () => void 
}) {
  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          {[1, 2].map((i) => (
            <div key={i} className="border border-gray-200 rounded-lg p-4">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Version History ({versions.length})
        </h2>
        <div className="flex gap-2">
          <label className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer flex items-center gap-2">
            <Upload className="w-4 h-4" />
            Upload New Version
            <input type="file" className="hidden" accept=".pdf,.xlsx,.xls" />
          </label>
          <button
            onClick={onRefresh}
            className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {versions.length > 0 ? (
        <div className="space-y-4">
          {versions.map((version) => (
            <div key={version.document_id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-medium text-gray-900">
                    Version {version.version_number}
                  </h3>
                  <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                    <span>{version.filename}</span>
                    <span>• {version.file_size} bytes</span>
                    <span>• {new Date(version.created_at).toLocaleDateString()}</span>
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      version.processing_status === 'completed' 
                        ? 'bg-green-100 text-green-800'
                        : version.processing_status === 'failed'
                        ? 'bg-red-100 text-red-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {version.processing_status}
                    </span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <button className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50">
                    Compare
                  </button>
                  <button className="px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-50">
                    Download
                  </button>
                  {version.version_number > 1 && (
                    <button className="px-3 py-1 text-sm border border-blue-300 text-blue-600 rounded-md hover:bg-blue-50">
                      Rollback
                    </button>
                  )}
                </div>
              </div>
              
              {version.metadata?.change_notes && (
                <div className="mt-3 text-sm text-gray-600">
                  <strong>Changes:</strong> {version.metadata.change_notes}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          <History className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No versions found</h3>
          <p className="text-gray-500">Upload a new version to start tracking changes.</p>
        </div>
      )}
    </div>
  );
}