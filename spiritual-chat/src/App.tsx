import React, { useState } from 'react';
import ChatInterface from './components/Chat/ChatInterface';
import DocumentUpload from './components/Upload/DocumentUpload';
import { UploadedDocument } from './types';
import './App.css';

function App() {
  const [showUpload, setShowUpload] = useState(false);
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);

  const handleDocumentUploaded = (doc: UploadedDocument) => {
    setUploadedDocuments(prev => [...prev, doc]);
  };

  const handleUploadClick = () => {
    setShowUpload(true);
  };

  const handleUploadClose = () => {
    setShowUpload(false);
  };

  return (
    <div className="App">
      <ChatInterface onUploadClick={handleUploadClick} />
      <DocumentUpload
        isOpen={showUpload}
        onClose={handleUploadClose}
        onDocumentUploaded={handleDocumentUploaded}
      />
    </div>
  );
}

export default App;