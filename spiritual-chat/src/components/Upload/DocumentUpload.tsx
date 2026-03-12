import React, { useState } from 'react';
import { Upload, X, FileText, CheckCircle, AlertCircle, Loader, BookOpen } from 'lucide-react';
import { DocumentUploadProps, UploadedDocument } from '../../types';

const DocumentUpload: React.FC<DocumentUploadProps> = ({ isOpen, onClose, onDocumentUploaded }) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [documentName, setDocumentName] = useState('');
  const [description, setDescription] = useState('');

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setDocumentName(selectedFile.name.replace('.pdf', ''));
    }
  };

  const uploadDocument = async () => {
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_name', documentName || file.name);
    formData.append('description', description);

    try {
      const response = await fetch('/api/v1/upload/pdf/to-vector-db', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        const uploadedDoc: UploadedDocument = {
          id: data.data.document_id,
          name: data.data.document_name,
          chunks: data.data.chunks_stored,
          status: 'success',
          description: data.data.description
        };
        onDocumentUploaded(uploadedDoc);
        setTimeout(() => {
          onClose();
          setFile(null);
          setDocumentName('');
          setDescription('');
        }, 2000);
      }
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setIsUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-800">Upload Spiritual Document</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center mb-6">
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer text-blue-600 hover:text-blue-700"
          >
            Click to select PDF file
          </label>
          {file && (
            <div className="mt-4">
              <FileText className="w-8 h-8 text-green-500 mx-auto mb-2" />
              <p className="font-medium">{file.name}</p>
            </div>
          )}
        </div>

        {file && (
          <div className="space-y-4 mb-6">
            <input
              type="text"
              value={documentName}
              onChange={(e) => setDocumentName(e.target.value)}
              placeholder="Document name"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description (optional)"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={uploadDocument}
            disabled={!file || isUploading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isUploading && <Loader className="w-4 h-4 animate-spin" />}
            <span>{isUploading ? 'Uploading...' : 'Upload Document'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;