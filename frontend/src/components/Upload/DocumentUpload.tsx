import React, { useState, useCallback } from 'react';
import { Upload, X, FileText, CheckCircle, AlertCircle, Loader, BookOpen } from 'lucide-react';

interface UploadedDocument {
  id: string;
  name: string;
  chunks: number;
  status: 'success' | 'error';
  description?: string;
}

interface DocumentUploadProps {
  isOpen: boolean;
  onClose: () => void;
  onDocumentUploaded: (doc: UploadedDocument) => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ isOpen, onClose, onDocumentUploaded }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [documentName, setDocumentName] = useState('');
  const [description, setDescription] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === 'application/pdf') {
        setFile(droppedFile);
        setDocumentName(droppedFile.name.replace('.pdf', ''));
      } else {
        setErrorMessage('Please upload only PDF files');
      }
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type === 'application/pdf') {
        setFile(selectedFile);
        setDocumentName(selectedFile.name.replace('.pdf', ''));
        setErrorMessage('');
      } else {
        setErrorMessage('Please upload only PDF files');
      }
    }
  };

  const removeFile = () => {
    setFile(null);
    setDocumentName('');
    setDescription('');
    setUploadStatus('idle');
    setErrorMessage('');
  };

  const uploadDocument = async () => {
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatus('idle');
    setErrorMessage('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_name', documentName || file.name);
    formData.append('description', description);

    try {
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 100);

      const response = await fetch('/api/v1/upload/pdf/to-vector-db', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        setUploadStatus('success');
        const uploadedDoc: UploadedDocument = {
          id: data.data.document_id,
          name: data.data.document_name,
          chunks: data.data.chunks_stored,
          status: 'success',
          description: data.data.description
        };
        onDocumentUploaded(uploadedDoc);
        
        // Auto close after success
        setTimeout(() => {
          onClose();
          resetForm();
        }, 2000);
      } else {
        setUploadStatus('error');
        setErrorMessage(data.detail || 'Upload failed');
      }
    } catch (error) {
      setUploadStatus('error');
      setErrorMessage('Network error. Please check your connection and try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const resetForm = () => {
    setFile(null);
    setDocumentName('');
    setDescription('');
    setUploadProgress(0);
    setUploadStatus('idle');
    setErrorMessage('');
    setDragActive(false);
  };

  const handleClose = () => {
    if (!isUploading) {
      resetForm();
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-600 rounded-full flex items-center justify-center">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-800">Upload Spiritual Document</h2>
              <p className="text-sm text-gray-500">Add Bible chapters, religious texts, or spiritual books</p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={isUploading}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          {/* Upload Area */}
          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
              dragActive
                ? 'border-blue-500 bg-blue-50'
                : file
                ? 'border-green-400 bg-green-50'
                : 'border-gray-300 hover:border-blue-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {file ? (
              <div className="space-y-4">
                <div className="flex items-center justify-center">
                  <FileText className="w-12 h-12 text-green-500" />
                </div>
                <div>
                  <p className="text-lg font-medium text-gray-800">{file.name}</p>
                  <p className="text-sm text-gray-500">
                    {(file.size / 1024 / 1024).toFixed(2)} MB • PDF Document
                  </p>
                </div>
                <button
                  onClick={removeFile}
                  disabled={isUploading}
                  className="text-red-500 hover:text-red-700 text-sm disabled:opacity-50"
                >
                  Remove file
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-center">
                  <Upload className="w-12 h-12 text-gray-400" />
                </div>
                <div>
                  <p className="text-lg font-medium text-gray-700">
                    Drag & drop your PDF here
                  </p>
                  <p className="text-sm text-gray-500">
                    or click to browse files
                  </p>
                </div>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                  disabled={isUploading}
                />
                <label
                  htmlFor="file-upload"
                  className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors"
                >
                  Browse Files
                </label>
              </div>
            )}
          </div>

          {/* Document Details */}
          {file && (
            <div className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Document Name
                </label>
                <input
                  type="text"
                  value={documentName}
                  onChange={(e) => setDocumentName(e.target.value)}
                  placeholder="e.g., Psalms Chapter 23, Gospel of Matthew"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isUploading}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Brief description of the document content..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  disabled={isUploading}
                />
              </div>
            </div>
          )}

          {/* Progress */}
          {isUploading && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Uploading...</span>
                <span className="text-sm text-gray-500">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Processing document and creating embeddings...
              </p>
            </div>
          )}

          {/* Status Messages */}
          {uploadStatus === 'success' && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                <span className="text-green-800 font-medium">Upload successful!</span>
              </div>
              <p className="text-green-700 text-sm mt-1">
                Your document has been processed and is ready for spiritual guidance.
              </p>
            </div>
          )}

          {uploadStatus === 'error' && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                <span className="text-red-800 font-medium">Upload failed</span>
              </div>
              <p className="text-red-700 text-sm mt-1">{errorMessage}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-8 flex justify-end space-x-3">
            <button
              onClick={handleClose}
              disabled={isUploading}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={uploadDocument}
              disabled={!file || isUploading || uploadStatus === 'success'}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 transition-colors"
            >
              {isUploading && <Loader className="w-4 h-4 animate-spin" />}
              <span>{isUploading ? 'Uploading...' : 'Upload Document'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;