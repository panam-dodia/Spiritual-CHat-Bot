import tempfile
import os
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException
import PyPDF2
import tiktoken
from app.core.config import settings

class PDFService:
    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_types = ["application/pdf"]
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
    async def validate_file(self, file: UploadFile) -> bool:
        """Validate uploaded PDF file."""
        # Check file type
        if file.content_type not in self.allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Only PDF files are allowed."
            )
        
        # Check file size (read content to check)
        content = await file.read()
        if len(content) > self.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum limit of {self.max_file_size // (1024*1024)}MB"
            )
        
        # Reset file pointer
        await file.seek(0)
        return True
    
    async def extract_text_from_pdf(self, file: UploadFile) -> str:
        """Extract text content from PDF file."""
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            # Extract text using PyPDF2
            text_content = ""
            with open(temp_file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():  # Only add non-empty pages
                            text_content += f"\n--- Page {page_num + 1} ---\n"
                            text_content += page_text + "\n"
                    except Exception as e:
                        print(f"Error extracting page {page_num + 1}: {str(e)}")
                        continue
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            if not text_content.strip():
                raise HTTPException(
                    status_code=400,
                    detail="No readable text found in PDF. Please ensure the PDF contains text content."
                )
                
            return text_content.strip()
            
        except Exception as e:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing PDF: {str(e)}"
            )
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
        """Split text into manageable chunks for embedding."""
        chunk_size = chunk_size or settings.CHUNK_SIZE
        overlap = overlap or settings.CHUNK_OVERLAP
        
        # Split text into sentences first (basic sentence splitting)
        sentences = text.replace('\n', ' ').split('. ')
        sentences = [s.strip() + '.' for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.encoding.encode(sentence))
            
            # If adding this sentence would exceed chunk size, finalize current chunk
            if current_tokens + sentence_tokens > chunk_size and current_chunk:
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": current_chunk.strip(),
                    "token_count": current_tokens,
                    "char_count": len(current_chunk)
                })
                
                # Start new chunk with overlap from previous chunk
                if overlap > 0:
                    overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                    current_chunk = overlap_text + " " + sentence
                    current_tokens = len(self.encoding.encode(current_chunk))
                else:
                    current_chunk = sentence
                    current_tokens = sentence_tokens
                
                chunk_index += 1
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_tokens += sentence_tokens
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                "chunk_index": chunk_index,
                "text": current_chunk.strip(),
                "token_count": current_tokens,
                "char_count": len(current_chunk)
            })
        
        return chunks
    
    async def process_pdf(self, file: UploadFile, document_name: str = None) -> Dict[str, Any]:
        """Complete PDF processing pipeline."""
        # Validate file
        await self.validate_file(file)
        
        # Extract text
        text_content = await self.extract_text_from_pdf(file)
        
        # Create chunks
        chunks = self.chunk_text(text_content)
        
        # Prepare document metadata
        document_name = document_name or file.filename or "Unknown Document"
        
        result = {
            "document_name": document_name,
            "total_characters": len(text_content),
            "total_chunks": len(chunks),
            "chunks": chunks,
            "processing_status": "success"
        }
        
        return result

# Create singleton instance
pdf_service = PDFService()