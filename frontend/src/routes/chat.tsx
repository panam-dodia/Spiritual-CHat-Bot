import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import ChatInterface from '../components/Chat/ChatInterface'
import DocumentUpload from '../components/Upload/DocumentUpload'

function ChatPage() {
  const [showUpload, setShowUpload] = useState(false)
  const [uploadedDocuments, setUploadedDocuments] = useState([])

  return (
    <div className="h-screen">
      <ChatInterface onUploadClick={() => setShowUpload(true)} />
      <DocumentUpload
        isOpen={showUpload}
        onClose={() => setShowUpload(false)}
        onDocumentUploaded={(doc) => setUploadedDocuments(prev => [...prev, doc])}
      />
    </div>
  )
}

export const Route = createFileRoute('/chat')({
  component: ChatPage,
})