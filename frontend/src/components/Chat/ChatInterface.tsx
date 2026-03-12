import { OpenAPI } from '../../client'
import React, { useState, useRef, useEffect } from 'react';
import { Send, Upload, BookOpen, AlertTriangle, Heart, MessageCircle } from 'lucide-react';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  contextUsed?: ContextChunk[];
  contentFiltered?: boolean;
  crisisDetected?: boolean;
}

interface ContextChunk {
  text: string;
  document: string;
  similarity: number;
}

interface ChatInterfaceProps {
  onUploadClick: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onUploadClick }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'system',
      content: 'Welcome! I\'m your spiritual guide. I can help answer questions based on uploaded spiritual documents like the Bible, religious texts, and spiritual books. How can I assist you in your faith journey today?',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showContext, setShowContext] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/chat/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: inputMessage,
          max_context_chunks: 3
        })
      });

      const data = await response.json();

      let assistantMessage: ChatMessage;

      if (data.status === 'content_filtered' && data.crisis_detected) {
        // Crisis detected
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          type: 'system',
          content: data.answer,
          timestamp: new Date(),
          crisisDetected: true
        };
      } else if (data.status === 'success') {
        // Normal response
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: data.answer,
          timestamp: new Date(),
          contextUsed: data.context_used,
          contentFiltered: data.content_filtered
        };
      } else if (data.status === 'no_context') {
        // No relevant documents found
        assistantMessage = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: data.answer + '\n\n📚 Consider uploading spiritual documents like Bible chapters, religious texts, or spiritual books to get more personalized guidance.',
          timestamp: new Date()
        };
      } else {
        throw new Error('Unexpected response format');
      }

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: 'I apologize, but I\'m having trouble connecting right now. Please try again in a moment. 🙏',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.type === 'user';
    const isCrisis = message.crisisDetected;

    return (
      <div
        key={message.id}
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}
      >
        <div
          className={`max-w-3xl rounded-2xl px-4 py-3 shadow-sm ${
            isCrisis
              ? 'bg-red-50 border-2 border-red-200'
              : isUser
              ? 'bg-blue-600 text-white'
              : message.type === 'system'
              ? 'bg-purple-50 border border-purple-200'
              : 'bg-gray-50 border border-gray-200'
          }`}
        >
          {isCrisis && (
            <div className="flex items-center mb-2 text-red-600">
              <AlertTriangle className="w-4 h-4 mr-2" />
              <span className="text-sm font-medium">Crisis Support</span>
            </div>
          )}
          
          <div className="whitespace-pre-wrap text-sm leading-relaxed">
            {message.content}
          </div>
          
          <div className="flex items-center justify-between mt-2 text-xs opacity-60">
            <span>{formatTime(message.timestamp)}</span>
            {message.contextUsed && message.contextUsed.length > 0 && (
              <button
                onClick={() => setShowContext(showContext === message.id ? null : message.id)}
                className="flex items-center hover:opacity-80 transition-opacity"
              >
                <BookOpen className="w-3 h-3 mr-1" />
                {message.contextUsed.length} sources
              </button>
            )}
          </div>

          {/* Context Sources */}
          {showContext === message.id && message.contextUsed && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="text-xs font-medium mb-2">📖 Sources used:</div>
              {message.contextUsed.map((context, idx) => (
                <div key={idx} className="mb-2 p-2 bg-white rounded text-xs">
                  <div className="font-medium text-gray-700 mb-1">
                    {context.document} (Relevance: {(context.similarity * 100).toFixed(1)}%)
                  </div>
                  <div className="text-gray-600 leading-relaxed">
                    {context.text.substring(0, 200)}...
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
              <Heart className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-800">Spiritual Guide</h1>
              <p className="text-sm text-gray-500">AI-powered spiritual guidance</p>
            </div>
          </div>
          <button
            onClick={onUploadClick}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Documents</span>
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto">
          {messages.map(renderMessage)}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3 max-w-xs">
                <div className="flex items-center space-x-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                  <span className="text-sm text-gray-500">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end space-x-3">
            <div className="flex-1 relative">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask me about faith, spirituality, or any questions about your uploaded documents..."
                className="w-full px-4 py-3 border border-gray-300 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={inputMessage.split('\n').length}
                maxLength={1000}
                disabled={isLoading}
              />
              <div className="absolute bottom-2 right-2 text-xs text-gray-400">
                {inputMessage.length}/1000
              </div>
            </div>
            <button
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="p-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <div className="mt-2 text-xs text-gray-500 text-center">
            💡 Tip: Upload spiritual documents for more personalized guidance
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;