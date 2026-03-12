export interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  contextUsed?: ContextChunk[];
  contentFiltered?: boolean;
  crisisDetected?: boolean;
}

export interface ContextChunk {
  text: string;
  document: string;
  similarity: number;
}

export interface UploadedDocument {
  id: string;
  name: string;
  chunks: number;
  status: 'success' | 'error';
  description?: string;
}

export interface ChatInterfaceProps {
  onUploadClick: () => void;
}

export interface DocumentUploadProps {
  isOpen: boolean;
  onClose: () => void;
  onDocumentUploaded: (doc: UploadedDocument) => void;
}