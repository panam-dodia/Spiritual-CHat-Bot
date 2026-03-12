from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
from app.services.pdf_service import pdf_service
from app.services.embedding_service import embedding_service
from app.services.vector_service import vector_service

router = APIRouter()

@router.post("/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    document_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """
    Upload and process a PDF document.
    
    - **file**: PDF file to upload
    - **document_name**: Custom name for the document (optional)
    - **description**: Description of the document content (optional)
    """
    try:
        # Process the PDF
        result = await pdf_service.process_pdf(file, document_name)
        
        # Add metadata
        result["description"] = description
        result["original_filename"] = file.filename
        result["content_type"] = file.content_type
        
        return {
            "status": "success",
            "message": f"PDF processed successfully. Created {result['total_chunks']} chunks.",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@router.post("/pdf/with-embeddings")
async def upload_pdf_with_embeddings(
    file: UploadFile = File(...),
    document_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """
    Upload PDF and create embeddings for all chunks.
    
    - **file**: PDF file to upload
    - **document_name**: Custom name for the document (optional) 
    - **description**: Description of the document content (optional)
    """
    try:
        # Process the PDF
        result = await pdf_service.process_pdf(file, document_name)
        
        # Create embeddings for each chunk
        embeddings_data = []
        for chunk in result["chunks"]:
            try:
                embedding = await embedding_service.create_embedding(chunk["text"])
                chunk_with_embedding = chunk.copy()
                chunk_with_embedding["embedding"] = embedding
                embeddings_data.append(chunk_with_embedding)
            except Exception as e:
                print(f"Error creating embedding for chunk {chunk['chunk_index']}: {str(e)}")
                # Continue processing other chunks
                continue
        
        return {
            "status": "success",
            "message": f"PDF processed with embeddings. Created {len(embeddings_data)} embedded chunks.",
            "data": {
                "document_name": result["document_name"],
                "description": description,
                "original_filename": file.filename,
                "total_chunks": result["total_chunks"],
                "embedded_chunks": len(embeddings_data),
                "chunks_with_embeddings": embeddings_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF with embeddings: {str(e)}")

@router.post("/pdf/to-vector-db")
async def upload_pdf_to_vector_db(
    file: UploadFile = File(...),
    document_name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    collection_name: Optional[str] = Form(None)
):
    """
    Upload PDF, create embeddings, and store in vector database.
    
    - **file**: PDF file to upload
    - **document_name**: Custom name for the document (optional)
    - **description**: Description of the document content (optional)
    - **collection_name**: Vector database collection name (optional)
    """
    try:
        # Process the PDF
        result = await pdf_service.process_pdf(file, document_name)
        
        # Prepare document metadata
        document_metadata = {
            "description": description,
            "original_filename": file.filename,
            "content_type": file.content_type
        }
        
        # Store in vector database
        vector_result = await vector_service.add_document_chunks(
            chunks=result["chunks"],
            document_name=result["document_name"],
            document_metadata=document_metadata,
            collection_name=collection_name
        )
        
        return {
            "status": "success",
            "message": f"PDF uploaded and stored in vector database. Created {vector_result['chunks_added']} searchable chunks.",
            "data": {
                "document_id": vector_result["document_id"],
                "document_name": vector_result["document_name"],
                "collection": vector_result["collection"],
                "chunks_stored": vector_result["chunks_added"],
                "original_filename": file.filename,
                "description": description
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading PDF to vector database: {str(e)}")

@router.get("/test-chunking")
async def test_text_chunking(text: str, chunk_size: int = 1000, overlap: int = 200):
    """
    Test text chunking functionality with custom text.
    
    - **text**: Text to chunk
    - **chunk_size**: Maximum tokens per chunk
    - **overlap**: Overlap between chunks in characters
    """
    try:
        chunks = pdf_service.chunk_text(text, chunk_size, overlap)
        
        return {
            "status": "success",
            "original_text": text,
            "chunk_size": chunk_size,
            "overlap": overlap,
            "total_chunks": len(chunks),
            "chunks": chunks
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error chunking text: {str(e)}")