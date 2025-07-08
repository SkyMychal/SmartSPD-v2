'use client';

import { useUser } from '@auth0/nextjs-auth0/client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Upload, 
  FileText, 
  Archive, 
  CheckCircle, 
  XCircle, 
  Clock, 
  ArrowLeft,
  Download,
  AlertCircle,
  RefreshCw,
  Eye
} from 'lucide-react';
import { documentApi } from '@/lib/api';

interface BatchStatus {
  batch_id: string;
  total_documents: number;
  status_breakdown: { [key: string]: number };
  documents: Array<{
    id: string;
    filename: string;
    status: string;
    error_message?: string;
    created_at: string;
    updated_at: string;
  }>;
}

export default function BatchUploadPage() {
  const { user } = useUser();
  const router = useRouter();
  const [uploadMethod, setUploadMethod] = useState<'files' | 'zip'>('files');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(false);
  const [metadata, setMetadata] = useState({
    health_plan_id: '',
    batch_notes: '',
    extract_notes: ''
  });

  useEffect(() => {
    if (batchId) {
      const interval = setInterval(() => {
        fetchBatchStatus();
      }, 5000); // Poll every 5 seconds

      return () => clearInterval(interval);
    }
  }, [batchId]);

  const fetchBatchStatus = async () => {
    if (!batchId) return;
    
    try {
      setStatusLoading(true);
      const status = await documentApi.getBatchStatus(batchId);
      setBatchStatus(status);
    } catch (error) {
      console.error('Failed to fetch batch status:', error);
    } finally {
      setStatusLoading(false);
    }
  };

  const handleFileSelection = (files: File[]) => {
    setSelectedFiles(files);
  };

  const handleZipSelection = (file: File) => {
    setZipFile(file);
  };

  const handleUpload = async () => {
    if (uploadMethod === 'files' && selectedFiles.length === 0) {
      alert('Please select files to upload');
      return;
    }
    
    if (uploadMethod === 'zip' && !zipFile) {
      alert('Please select a ZIP file to upload');
      return;
    }

    try {
      setUploading(true);
      
      let response;
      if (uploadMethod === 'files') {
        response = await documentApi.uploadBatchDocuments(selectedFiles, {
          health_plan_id: metadata.health_plan_id || undefined,
          batch_notes: metadata.batch_notes || undefined
        });
      } else {
        response = await documentApi.uploadZipArchive(zipFile!, {
          health_plan_id: metadata.health_plan_id || undefined,
          extract_notes: metadata.extract_notes || undefined
        });
      }

      // Extract batch ID from response (assuming it's returned)
      // This would need to be adjusted based on actual API response format
      const newBatchId = `batch_${Date.now()}`; // Placeholder
      setBatchId(newBatchId);
      
      // Clear selections
      setSelectedFiles([]);
      setZipFile(null);
      
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handleRetryFailures = async () => {
    if (!batchId) return;
    
    try {
      await documentApi.retryBatchFailures(batchId);
      await fetchBatchStatus();
      alert('Retry initiated for failed documents');
    } catch (error) {
      console.error('Failed to retry batch:', error);
      alert('Failed to retry batch processing');
    }
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
      pending: { color: 'bg-gray-100 text-gray-800', label: 'Pending' }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${config.color}`}>
        {config.label}
      </span>
    );
  };

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
            Back to Documents
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Batch Upload</h1>
            <p className="text-gray-600">Upload multiple documents at once</p>
          </div>
        </div>
      </div>

      {/* Upload Section */}
      {!batchId && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Upload Method</h2>
          
          {/* Method Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <button
              onClick={() => setUploadMethod('files')}
              className={`p-4 border-2 rounded-lg text-left transition-colors ${
                uploadMethod === 'files' 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-3">
                <FileText className="w-6 h-6 text-blue-600" />
                <div>
                  <h3 className="font-medium text-gray-900">Multiple Files</h3>
                  <p className="text-sm text-gray-500">Select individual files to upload</p>
                </div>
              </div>
            </button>
            
            <button
              onClick={() => setUploadMethod('zip')}
              className={`p-4 border-2 rounded-lg text-left transition-colors ${
                uploadMethod === 'zip' 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-3">
                <Archive className="w-6 h-6 text-blue-600" />
                <div>
                  <h3 className="font-medium text-gray-900">ZIP Archive</h3>
                  <p className="text-sm text-gray-500">Upload a ZIP file with multiple documents</p>
                </div>
              </div>
            </button>
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Health Plan ID (Optional)
              </label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={metadata.health_plan_id}
                onChange={(e) => setMetadata(prev => ({ ...prev, health_plan_id: e.target.value }))}
                placeholder="Enter health plan ID"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {uploadMethod === 'files' ? 'Batch Notes' : 'Extract Notes'} (Optional)
              </label>
              <input
                type="text"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={uploadMethod === 'files' ? metadata.batch_notes : metadata.extract_notes}
                onChange={(e) => setMetadata(prev => ({ 
                  ...prev, 
                  [uploadMethod === 'files' ? 'batch_notes' : 'extract_notes']: e.target.value 
                }))}
                placeholder={`Enter ${uploadMethod === 'files' ? 'batch' : 'extract'} notes`}
              />
            </div>
          </div>

          {/* File Selection */}
          {uploadMethod === 'files' ? (
            <FileSelectionZone 
              selectedFiles={selectedFiles}
              onFilesSelected={handleFileSelection}
            />
          ) : (
            <ZipSelectionZone
              selectedFile={zipFile}
              onFileSelected={handleZipSelection}
            />
          )}

          {/* Upload Button */}
          <div className="mt-6">
            <button
              onClick={handleUpload}
              disabled={uploading || (uploadMethod === 'files' && selectedFiles.length === 0) || (uploadMethod === 'zip' && !zipFile)}
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {uploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Start Batch Upload
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Batch Status */}
      {batchId && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Batch Status: {batchId}
            </h2>
            <div className="flex gap-2">
              <button
                onClick={fetchBatchStatus}
                disabled={statusLoading}
                className="px-3 py-2 border border-gray-300 rounded-md hover:bg-gray-50 flex items-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${statusLoading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
              {batchStatus?.status_breakdown?.failed > 0 && (
                <button
                  onClick={handleRetryFailures}
                  className="px-3 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 flex items-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Retry Failures
                </button>
              )}
            </div>
          </div>

          {batchStatus ? (
            <div className="space-y-4">
              {/* Status Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">
                    {batchStatus.total_documents}
                  </div>
                  <div className="text-sm text-gray-500">Total Documents</div>
                </div>
                <div className="bg-green-50 p-3 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {batchStatus.status_breakdown?.completed || 0}
                  </div>
                  <div className="text-sm text-gray-500">Completed</div>
                </div>
                <div className="bg-yellow-50 p-3 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">
                    {batchStatus.status_breakdown?.processing || 0}
                  </div>
                  <div className="text-sm text-gray-500">Processing</div>
                </div>
                <div className="bg-red-50 p-3 rounded-lg">
                  <div className="text-2xl font-bold text-red-600">
                    {batchStatus.status_breakdown?.failed || 0}
                  </div>
                  <div className="text-sm text-gray-500">Failed</div>
                </div>
              </div>

              {/* Document List */}
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                  <h3 className="font-medium text-gray-900">Document Details</h3>
                </div>
                <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                  {batchStatus.documents.map((doc) => (
                    <div key={doc.id} className="px-4 py-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {getStatusIcon(doc.status)}
                          <div>
                            <h4 className="text-sm font-medium text-gray-900">{doc.filename}</h4>
                            <div className="text-xs text-gray-500">
                              Created: {new Date(doc.created_at).toLocaleString()}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {getStatusBadge(doc.status)}
                          <button
                            onClick={() => router.push(`/dashboard/documents/${doc.id}`)}
                            className="p-1 text-gray-400 hover:text-gray-600"
                            title="View Document"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      {doc.error_message && (
                        <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                          {doc.error_message}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-500">Loading batch status...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// File Selection Zone Component
function FileSelectionZone({ 
  selectedFiles, 
  onFilesSelected 
}: { 
  selectedFiles: File[], 
  onFilesSelected: (files: File[]) => void 
}) {
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    onFilesSelected([...selectedFiles, ...files]);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      onFilesSelected([...selectedFiles, ...files]);
    }
  };

  const removeFile = (index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    onFilesSelected(newFiles);
  };

  return (
    <div className="space-y-4">
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
          Drop files here or click to select
        </h3>
        <p className="text-gray-500 mb-4">
          Supports PDF, Excel files (XLSX, XLS). Maximum 20 files per batch.
        </p>
        <input
          type="file"
          multiple
          accept=".pdf,.xlsx,.xls"
          onChange={handleFileInput}
          className="hidden"
          id="files-upload"
        />
        <label
          htmlFor="files-upload"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer inline-block"
        >
          Select Files
        </label>
      </div>

      {/* Selected Files */}
      {selectedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-900">Selected Files ({selectedFiles.length})</h4>
          <div className="max-h-40 overflow-y-auto space-y-1">
            {selectedFiles.map((file, index) => (
              <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-600" />
                  <span className="text-sm text-gray-700">{file.name}</span>
                  <span className="text-xs text-gray-500">
                    ({(file.size / 1024 / 1024).toFixed(1)} MB)
                  </span>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="text-red-600 hover:text-red-800"
                >
                  <XCircle className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ZIP Selection Zone Component
function ZipSelectionZone({ 
  selectedFile, 
  onFileSelected 
}: { 
  selectedFile: File | null, 
  onFileSelected: (file: File) => void 
}) {
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    const zipFile = files.find(file => file.name.toLowerCase().endsWith('.zip'));
    if (zipFile) {
      onFileSelected(zipFile);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelected(e.target.files[0]);
    }
  };

  return (
    <div className="space-y-4">
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
        <Archive className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Drop ZIP file here or click to select
        </h3>
        <p className="text-gray-500 mb-4">
          ZIP archive containing PDF and Excel files. Maximum file size: 100MB.
        </p>
        <input
          type="file"
          accept=".zip"
          onChange={handleFileInput}
          className="hidden"
          id="zip-upload"
        />
        <label
          htmlFor="zip-upload"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer inline-block"
        >
          Select ZIP File
        </label>
      </div>

      {/* Selected ZIP File */}
      {selectedFile && (
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Archive className="w-6 h-6 text-blue-600" />
              <div>
                <h4 className="font-medium text-gray-900">{selectedFile.name}</h4>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(1)} MB
                </p>
              </div>
            </div>
            <button
              onClick={() => onFileSelected(null as any)}
              className="text-red-600 hover:text-red-800"
            >
              <XCircle className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}